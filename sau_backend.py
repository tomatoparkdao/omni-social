import asyncio
import base64
import json
import importlib.util
import logging
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from contextlib import closing
from queue import Empty, Queue
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory, session
from werkzeug.security import check_password_hash
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from conf import BASE_DIR
from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs
from myUtils.publish_guard import require_real_publish_enabled
from myUtils import task_store
from myUtils.db_schema import ensure_schema
from uploader.xiaohongshu_uploader.main import cookie_auth as xiaohongshu_cookie_auth, xiaohongshu_setup

login_logger = logging.getLogger(__name__)

active_queues = {}
active_login_cancellations = {}
app = Flask(__name__)
ensure_schema(BASE_DIR)
app.secret_key = os.environ.get('OMNISOCIAL_SESSION_SECRET') or secrets.token_bytes(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    SESSION_COOKIE_SECURE=os.environ.get('OMNISOCIAL_ENV') == 'production',
)

# 开发和生产前端均使用同源代理访问 API。


def production_mode():
    return os.environ.get('OMNISOCIAL_ENV') == 'production'


@app.before_request
def protect_web_api():
    app.config['SESSION_COOKIE_SECURE'] = production_mode()
    if production_mode():
        if not os.environ.get('OMNISOCIAL_SESSION_SECRET') or not os.environ.get('OMNISOCIAL_ADMIN_PASSWORD_HASH'):
            return jsonify({'code': 503, 'msg': '生产环境身份认证未配置'}), 503
    elif request.remote_addr not in {'127.0.0.1', '::1'}:
        return jsonify({'code': 403, 'msg': '开发模式只允许本机访问'}), 403

    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        origin = request.headers.get('Origin')
        if origin:
            parsed = urlparse(origin)
            allowed = {request.host}
            if not production_mode():
                allowed.update({'127.0.0.1:5173', 'localhost:5173'})
            if parsed.scheme not in {'http', 'https'} or parsed.netloc not in allowed:
                return jsonify({'code': 403, 'msg': '请求来源不被允许'}), 403
        elif production_mode() and request.path != '/auth/session':
            return jsonify({'code': 403, 'msg': '缺少请求来源'}), 403

    if production_mode() and request.path not in {'/auth/session', '/health', '/favicon.ico', '/vite.svg'}:
        if request.path != '/' and not request.path.startswith('/assets/') and not session.get('authenticated'):
            return jsonify({'code': 401, 'msg': '请先登录 OmniSocial'}), 401


@app.route('/auth/session', methods=['GET', 'POST', 'DELETE'])
def auth_session():
    if not production_mode():
        return jsonify({'code': 200, 'authenticated': True, 'mode': 'local'}), 200
    if request.method == 'GET':
        return jsonify({'code': 200, 'authenticated': bool(session.get('authenticated')), 'mode': 'production'}), 200
    if request.method == 'DELETE':
        session.clear()
        return jsonify({'code': 200, 'authenticated': False}), 200
    password = (request.get_json(silent=True) or {}).get('password', '')
    if not isinstance(password, str) or not check_password_hash(os.environ['OMNISOCIAL_ADMIN_PASSWORD_HASH'], password):
        return jsonify({'code': 401, 'msg': '登录失败'}), 401
    session.clear()
    session['authenticated'] = True
    return jsonify({'code': 200, 'authenticated': True}), 200

@app.route('/agent/plan', methods=['POST'])
def agent_plan():
    """自然语言发布任务的安全预留入口；当前只解析并返回待确认计划，不执行发布。"""
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get('prompt', '')).strip()
    if not prompt:
        return jsonify({"code": 400, "msg": "prompt is required", "data": None}), 400
    return jsonify({
        "code": 200,
        "msg": "plan generated; explicit confirmation is required before publishing",
        "data": {
            "prompt": prompt,
            "status": "awaiting_confirmation",
            "publish_executed": False,
            "required_fields": ["platforms", "content_type", "account", "files", "title", "body", "schedule"],
        },
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'code': 200, 'status': 'ok', 'real_publish_enabled': os.environ.get('OMNISOCIAL_ENABLE_REAL_PUBLISH') == '1'}), 200


@app.route('/system/status', methods=['GET'])
def system_status():
    return jsonify({'code': 200, 'data': {
        'mode': os.environ.get('OMNISOCIAL_ENV', 'local'),
        'database_ready': (Path(BASE_DIR) / 'db' / 'database.db').is_file(),
        'material_storage_ready': (Path(BASE_DIR) / 'videoFile').is_dir(),
        'browser_library_ready': importlib.util.find_spec('patchright') is not None,
        'real_publish_enabled': os.environ.get('OMNISOCIAL_ENABLE_REAL_PUBLISH') == '1',
    }}), 200


@app.route('/tasks', methods=['GET', 'POST'])
def tasks_api():
    if request.method == 'GET':
        return jsonify({'code': 200, 'data': task_store.list_tasks(BASE_DIR)}), 200
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({'code': 400, 'msg': '任务必须是 JSON 对象'}), 400
    try:
        task, created = task_store.create_task(BASE_DIR, payload)
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    return jsonify({'code': 200, 'data': task, 'created': created}), 200


@app.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task_api(task_id):
    if not task_store.cancel_task(BASE_DIR, task_id):
        return jsonify({'code': 409, 'msg': '任务不存在或当前状态无法取消'}), 409
    return jsonify({'code': 200, 'msg': '任务已取消'}), 200


@app.route('/tasks/<task_id>/queue', methods=['POST'])
def queue_task_api(task_id):
    try:
        require_real_publish_enabled()
    except PermissionError:
        return jsonify({'code': 403, 'msg': '真实发布已关闭；仅可保存草稿'}), 403
    if not task_store.enqueue_task(BASE_DIR, task_id):
        return jsonify({'code': 409, 'msg': '任务不存在或已进入队列'}), 409
    return jsonify({'code': 200, 'msg': '任务已排队；尚未向平台提交'}), 200


@app.route('/tasks/<task_id>/simulate', methods=['POST'])
def simulate_task_api(task_id):
    if os.environ.get('OMNISOCIAL_ENV') != 'test':
        return jsonify({'code': 403, 'msg': '模拟队列只在隔离测试环境可用'}), 403
    if not task_store.enqueue_mock(BASE_DIR, task_id):
        return jsonify({'code': 409, 'msg': '任务不存在或状态不允许排队'}), 409
    return jsonify({'code': 200, 'msg': '任务已加入模拟队列'}), 200

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        safe_name = secure_filename(file.filename)
        if not safe_name:
            return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{safe_name}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{safe_name}"}), 200
    except Exception as e:
        return jsonify({"code":500,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return jsonify({"code": 400, "msg": "Invalid filename", "data": None}), 400

    # 拼接完整路径
    file_path = str(Path(BASE_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = secure_filename(custom_filename + "." + file.filename.split('.')[-1])
    else:
        filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400
    if Path(filename).suffix.lower() not in {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm', '.jpg', '.jpeg', '.png', '.webp'}:
        return jsonify({"code": 400, "data": None, "msg": "不支持的素材格式"}), 400

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{filename}")

        # 保存文件
        filepath.parent.mkdir(parents=True, exist_ok=True)
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            material_id = cursor.lastrowid
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename,
                "id": material_id
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [[row[0], row[1], None, row[3], row[4]] for row in rows]

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    with closing(sqlite3.connect(Path(BASE_DIR / "db" / "database.db"))) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        for row in rows_list:
            if row[1] == 1:
                flag = await xiaohongshu_cookie_auth(Path(BASE_DIR / "cookiesFile" / row[2]))
            else:
                flag = await check_cookie(row[1],row[2])
            if not flag:
                row[4] = 0
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (0,row[0]))
                conn.commit()
                print("✅ 用户状态已更新")
        for row in rows_list:
            row[2] = None  # Cookie 文件名属于服务端内部信息
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['DELETE'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            material_root = Path(BASE_DIR / "videoFile").resolve()
            file_path = (material_root / record['file_path']).resolve()
            if not file_path.is_relative_to(material_root):
                return jsonify({"code": 400, "msg": "素材路径无效", "data": None}), 400
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['DELETE'])
def delete_account():
    account_id = request.args.get('id')

    if not account_id or not account_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing account ID",
            "data": None
        }), 400

    account_id = int(account_id)

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除关联的cookie文件
            if record.get('filePath'):
                cookie_root = Path(BASE_DIR / "cookiesFile").resolve()
                cookie_file_path = (cookie_root / record['filePath']).resolve()
                if not cookie_file_path.is_relative_to(cookie_root):
                    return jsonify({"code": 400, "msg": "账号会话路径无效", "data": None}), 400
                if cookie_file_path.exists():
                    try:
                        cookie_file_path.unlink()
                        login_logger.info("用户主动删除账号后，关联会话文件已移除")
                    except Exception as e:
                        login_logger.error("删除账号关联会话文件失败：%s", e.__class__.__name__)

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"delete failed: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')
    if type not in {'1', '2', '3', '4'} or not id or not id.strip():
        return jsonify({"code": 400, "msg": "平台类型或账号名称无效"}), 400
    if id in active_queues:
        return jsonify({"code": 409, "msg": "该账号的登录会话仍在进行"}), 409

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    cancel_event = threading.Event()
    active_queues[id] = status_queue
    active_login_cancellations[id] = cancel_event
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue,cancel_event), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue), mimetype='text/event-stream')
    def finish_login_session():
        cancel_event.set()
        if active_queues.get(id) is status_queue:
            active_queues.pop(id, None)
            active_login_cancellations.pop(id, None)
    response.call_on_close(finish_login_session)
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    try:
        require_real_publish_enabled()
    except PermissionError as exc:
        return jsonify({"code": 403, "msg": str(exc), "data": None}), 403
    # 获取JSON数据
    data = request.get_json()

    if not data:
        return jsonify({"code": 400, "msg": "请求数据不能为空", "data": None}), 400

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None
    productLink = data.get('productLink', '')
    productTitle = data.get('productTitle', '')
    thumbnail_path = data.get('thumbnail', '')
    is_draft = data.get('isDraft', False)  # 新增参数：是否保存为草稿

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')

    # 参数校验
    if not file_list:
        return jsonify({"code": 400, "msg": "文件列表不能为空", "data": None}), 400
    if not account_list:
        return jsonify({"code": 400, "msg": "账号列表不能为空", "data": None}), 400
    if not type:
        return jsonify({"code": 400, "msg": "平台类型不能为空", "data": None}), 400
    if not title:
        return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

    # 打印获取到的数据（仅作为示例）

    try:
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, thumbnail_path, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case _:
                return jsonify({"code": 400, "msg": f"不支持的平台类型: {type}", "data": None}), 400

        # 返回响应给客户端
        return jsonify(
            {
                "code": 200,
                "msg": "发布任务已提交",
                "data": None
            }), 200
    except Exception as e:
        login_logger.error("旧版发布入口失败：%s", e.__class__.__name__)
        return jsonify({
            "code": 500,
            "msg": "发布失败，请查看服务端错误代码",
            "data": None
        }), 500


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    try:
        require_real_publish_enabled()
    except PermissionError as exc:
        return jsonify({"code": 403, "msg": str(exc), "data": None}), 403
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"code": 400, "msg": "Expected a JSON array", "data": None}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')
        is_draft = data.get('isDraft', False)

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days, is_draft)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    return jsonify({"code": 403, "msg": "网页端禁止直接覆盖 Cookie，请使用扫码重新登录", "data": None}), 403


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    return jsonify({"code": 403, "msg": "网页端禁止导出 Cookie", "data": None}), 403


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue,cancel_event=None):
    try:
        if type == '1':
            asyncio.run(login_xiaohongshu_web(id, status_queue, cancel_event))
        else:
            login_action = {'2': get_tencent_cookie, '3': douyin_cookie_gen, '4': get_ks_cookie}[type]
            asyncio.run(login_action(id, status_queue))
    except Exception as exc:
        browser_missing = "Executable doesn't exist" in str(exc)
        code = "browser_missing" if browser_missing else "login_exception"
        login_logger.error("登录线程失败（平台类型 %s，错误代码 %s，异常类型 %s）", type, code, exc.__class__.__name__)
        message = "浏览器内核未安装，请运行 patchright install chromium" if browser_missing else "登录流程异常，请查看后端日志"
        status_queue.put({"type": "error", "code": code, "message": message})


async def login_xiaohongshu_web(account_name, status_queue, cancel_event=None):
    with closing(sqlite3.connect(Path(BASE_DIR / "db" / "database.db"))) as conn:
        existing = conn.execute(
            "SELECT id, filePath FROM user_info WHERE type = 1 AND userName = ? ORDER BY id LIMIT 1",
            (account_name,),
        ).fetchone()
    filename = existing[1] if existing else f"{uuid.uuid4()}.json"
    account_file = Path(BASE_DIR / "cookiesFile" / filename)
    account_file.parent.mkdir(parents=True, exist_ok=True)
    qr_sent = False

    def on_qrcode(qrcode):
        nonlocal qr_sent
        if cancel_event and cancel_event.is_set():
            raise RuntimeError('login_cancelled')
        image_path = Path(qrcode["image_path"])
        image = base64.b64encode(image_path.read_bytes()).decode("ascii")
        status_queue.put({"type": "qr", "image": f"data:image/png;base64,{image}"})
        qr_sent = True

    result = await xiaohongshu_setup(
        str(account_file), handle=True, return_detail=True, qrcode_callback=on_qrcode,
        cancel_event=cancel_event,
    )
    if cancel_event and cancel_event.is_set():
        return
    if not result["success"]:
        status = result.get("status", "failed")
        login_logger.warning("小红书网页登录未完成：%s", status)
        if status == "timeout":
            code, public_message = "login_timeout", "扫码登录超时，请重新获取二维码"
        elif status == "cookie_invalid":
            code, public_message = "cookie_invalid", "扫码后登录态校验失败，请重试"
        elif not qr_sent:
            code, public_message = "qr_unavailable", "小红书登录页二维码未能加载，请检查网络或登录页面后重试"
        else:
            code, public_message = "login_failed", "小红书登录流程失败，请查看后端日志"
        status_queue.put({"type": "error", "code": code, "message": public_message})
        return

    with closing(sqlite3.connect(Path(BASE_DIR / "db" / "database.db"))) as conn:
        if existing:
            conn.execute("UPDATE user_info SET status = 1 WHERE id = ?", (existing[0],))
        else:
            conn.execute(
                "INSERT INTO user_info (type, filePath, userName, status) VALUES (1, ?, ?, 1)",
                (filename, account_name),
            )
        conn.commit()
    status_queue.put({"type": "success"})

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        try:
            msg = status_queue.get(timeout=15)
        except Empty:
            yield ": heartbeat\n\n"
            continue
        yield f"data: {json.dumps(msg, ensure_ascii=False) if isinstance(msg, dict) else msg}\n\n"
        if msg in ('200', '500') or isinstance(msg, dict) and msg.get('type') in ('success', 'error'):
            return

if __name__ == '__main__':
    app.run(host=os.environ.get('OMNISOCIAL_BIND_HOST', '127.0.0.1'), port=5409)
