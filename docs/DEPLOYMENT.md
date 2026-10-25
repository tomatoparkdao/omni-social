# OmniSocial 部署与运维（当前交付状态）

## 本地开发

Windows：安装 Python 3.10–3.12、Node.js；在仓库根目录执行 `python -m venv .venv`、`.venv\Scripts\python.exe -m pip install -r requirements.txt`、`.venv\Scripts\python.exe -m patchright install chromium`；在 `sau_frontend` 执行 `npm install`。双击根目录的 `start-omnisocial.bat`，打开 `http://127.0.0.1:5173`。停止用 `stop-omnisocial.bat`。脚本只停止自身记录且核对身份的进程。首次运行已有真实账号时，不要重建 `db/database.db` 或清理 `cookiesFile/`、`cookies/`。

单独运行时：后端 `.venv\Scripts\python.exe sau_backend.py`（须同时设置 `OMNISOCIAL_AUTH_MODE=local_dev`，否则按生产模式要求登录），前端在 `sau_frontend` 运行 `npm run dev`（127.0.0.1:5173，`/api` 代理至 127.0.0.1:5409）。`start-omnisocial.bat` 已显式写入 `OMNISOCIAL_AUTH_MODE=local_dev`、`OMNISOCIAL_ENV=local`、`OMNISOCIAL_BIND_HOST=127.0.0.1`，启动后直接进入工作台。本地免登录只在单机回环地址成立，不提供远程访问控制，只能在可信本机使用。`OMNISOCIAL_ENV=test` 仅供隔离测试库与 Mock Worker，不得指向真实账号数据。

## 容器草案与生产前提

`Dockerfile` 多阶段构建 Vue 与 Python 镜像，`compose.yaml` 创建 Web 和 Nginx 反代、SQLite/素材/会话卷。`.env.example` 是空模板。先为生产环境设置高熵 `OMNISOCIAL_SESSION_SECRET`，并用 `werkzeug.security.generate_password_hash` 生成 `OMNISOCIAL_ADMIN_PASSWORD_HASH`，将两项仅保存在服务器的 `.env`，不可提交。真实发布开关默认 `OMNISOCIAL_ENABLE_REAL_PUBLISH=0`。`worker` 被放在 `publish` Compose profile，默认不启动；只有完成平台审查并由运营者明确把开关设为 `1` 后才允许使用 `docker compose --profile publish up -d`。数据库备份可执行 `python scripts/backup_db.py`，备份仍含敏感账号元数据，必须限制权限并异地加密保存；Cookie 目录需单独进行受控备份。

仓库提供 `deploy/nginx.local.conf`（127.0.0.1:8080 的健康与静态入口）和 `deploy/nginx.https.example.conf`（需替换域名和证书路径）。**本机 HTTP 示例不能用于生产登录**：生产模式会设置 Secure 会话 Cookie，必须通过 HTTPS 访问。不得直接暴露 Flask 的 5409 端口。反代须保持 `/api/`、SSE 不缓冲与长读取超时，并在入口添加登录限速、访问日志脱敏及常规安全监控。

建议验证顺序：`docker compose config` → `docker compose build` → `docker compose up -d` → `docker compose ps` → `GET /api/health` → HTTPS 管理员登录/权限拒绝/SSE → 重启后卷与任务状态检查。迁移真实账号前先备份并核验恢复方案，不把真实 Cookie 拷贝进镜像或 Git。本轮工作机未安装 Docker，因此**上述容器步骤尚未执行，配置不能视作生产验收通过**。

## 运行边界与故障定位

- 当前 Web 保存发布草稿，不执行真实平台最终发布；测试环境 Worker 只消费 Mock 队列。生产 Worker 与四个平台 Web/CLI 会话适配代码已建立，但真实结果、完整平台调度、多实例互斥和容器运行仍未验证；`sau_publish_worker.py` 在闸门关闭时直接拒绝启动。不能以设置开关代替实际验证。
- 健康检查 `/api/health` 仅表明 Web 进程可响应；再检查 `/api/system/status`、账号元数据、存储目录、浏览器依赖和实际 SSE 链路。排障时仅记录错误类别与任务 ID，不记录 Cookie、二维码、密码或完整账号资料。
- SQLite 文件、WAL、素材与会话必须在持久卷；数据库备份脚本使用 SQLite 在线备份，不清空原库。恢复须在隔离副本演练后再操作真实数据。
- 服务器重启后 Web 可从卷读取草稿；测试环境模拟任务可恢复。真实 Worker 进程重启时会把仍标为执行中的任务记为 `needs_review`，防止未知结果重复提交；未经过容器与真实平台验证，不应对用户承诺到点发布。

> © OmniAiLab ｜ 开发者：Mochiball ｜ 使用与分发遵循 [MIT License](../LICENSE) 及第三方 NOTICE。
