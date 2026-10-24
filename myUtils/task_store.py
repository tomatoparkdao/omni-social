"""Persistent preparation queue. This module never invokes a real uploader."""
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def connect(base_dir):
    database = Path(base_dir) / 'db' / 'database.db'
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=5000')
    conn.execute('''CREATE TABLE IF NOT EXISTS publish_tasks (
        id TEXT PRIMARY KEY,
        idempotency_key TEXT UNIQUE NOT NULL,
        platform INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL DEFAULT '',
        tags_json TEXT NOT NULL DEFAULT '[]',
        options_json TEXT NOT NULL DEFAULT '{}',
        material_ids_json TEXT NOT NULL,
        schedule_at TEXT,
        status TEXT NOT NULL,
        error_code TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )''')
    conn.commit()
    return conn


def _safe_task(row):
    task = dict(row)
    task['tags'] = json.loads(task.pop('tags_json'))
    task['options'] = json.loads(task.pop('options_json'))
    task['material_ids'] = json.loads(task.pop('material_ids_json'))
    return task


def create_task(base_dir, payload):
    platform = payload.get('platform')
    account_id = payload.get('account_id')
    content_type = payload.get('content_type')
    title = payload.get('title')
    body = payload.get('body', '')
    tags = payload.get('tags', [])
    options = payload.get('options', {})
    material_ids = payload.get('material_ids')
    idempotency_key = payload.get('idempotency_key')
    schedule_at = payload.get('schedule_at')
    if type(platform) is not int or platform not in (1, 2, 3, 4):
        raise ValueError('无效的平台')
    if type(account_id) is not int or account_id < 1:
        raise ValueError('请选择有效账号')
    if content_type not in ('video', 'note'):
        raise ValueError('无效的内容类型')
    if content_type == 'note' and platform == 2:
        raise ValueError('视频号当前只支持视频素材')
    if not isinstance(title, str) or not title.strip() or len(title) > 200:
        raise ValueError('标题不能为空且不得超过 200 字')
    if not isinstance(body, str) or len(body) > 10000:
        raise ValueError('正文过长')
    if not isinstance(tags, list) or len(tags) > 30 or any(not isinstance(tag, str) or len(tag) > 60 for tag in tags):
        raise ValueError('话题格式无效')
    if not isinstance(options, dict) or any(key not in {'category', 'product_link', 'product_title', 'is_draft', 'is_original'} for key in options):
        raise ValueError('发布参数无效')
    if not isinstance(material_ids, list) or not material_ids or any(type(item) is not int or item < 1 for item in material_ids):
        raise ValueError('请选择素材')
    if content_type == 'video' and len(material_ids) != 1:
        raise ValueError('每个视频任务只能包含一个视频素材')
    if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 128:
        raise ValueError('缺少有效的幂等键')
    if schedule_at is not None:
        try:
            parsed = datetime.fromisoformat(schedule_at)
            if parsed.tzinfo is None or parsed <= datetime.now(timezone.utc):
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError('发布时间必须是未来的带时区时间') from None

    with closing(connect(base_dir)) as conn:
        previous = conn.execute('SELECT * FROM publish_tasks WHERE idempotency_key = ?', (idempotency_key,)).fetchone()
        if previous:
            return _safe_task(previous), False
        account = conn.execute('SELECT type FROM user_info WHERE id = ?', (account_id,)).fetchone()
        if not account or account['type'] != platform:
            raise ValueError('账号不存在或平台不匹配')
        placeholders = ','.join('?' for _ in material_ids)
        materials = conn.execute(
            f'SELECT id, filename, file_path FROM file_records WHERE id IN ({placeholders})', material_ids
        ).fetchall()
        if len(materials) != len(set(material_ids)):
            raise ValueError('素材不存在或重复')
        suffixes = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm'} if content_type == 'video' else {'.jpg', '.jpeg', '.png', '.webp'}
        root = (Path(base_dir) / 'videoFile').resolve()
        for material in materials:
            location = (root / material['file_path']).resolve()
            if location.suffix.lower() not in suffixes or not location.is_relative_to(root) or not location.is_file():
                raise ValueError('素材格式或文件路径无效')
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute('''INSERT INTO publish_tasks
            (id, idempotency_key, platform, account_id, content_type, title, body, tags_json, options_json,
             material_ids_json, schedule_at, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)''',
            (task_id, idempotency_key, platform, account_id, content_type, title.strip(), body,
             json.dumps(tags, ensure_ascii=False), json.dumps(options, ensure_ascii=False), json.dumps(material_ids), schedule_at, now, now))
        conn.commit()
        return _safe_task(conn.execute('SELECT * FROM publish_tasks WHERE id = ?', (task_id,)).fetchone()), True


def list_tasks(base_dir):
    with closing(connect(base_dir)) as conn:
        return [_safe_task(row) for row in conn.execute('SELECT * FROM publish_tasks ORDER BY created_at DESC')]


def cancel_task(base_dir, task_id):
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = 'cancelled', updated_at = ?
            WHERE id = ? AND status IN ('draft', 'queued_mock', 'queued')''',
            (datetime.now(timezone.utc).isoformat(), task_id))
        conn.commit()
        return updated.rowcount == 1


def enqueue_task(base_dir, task_id):
    """Queue once; an already running or reviewed task cannot be resubmitted."""
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = 'queued', updated_at = ?
            WHERE id = ? AND status = 'draft' ''',
            (datetime.now(timezone.utc).isoformat(), task_id))
        conn.commit()
        return updated.rowcount == 1


def claim_due_task(base_dir, now=None):
    now = now or datetime.now(timezone.utc)
    with closing(connect(base_dir)) as conn:
        conn.execute('BEGIN IMMEDIATE')
        for row in conn.execute("SELECT * FROM publish_tasks WHERE status = 'queued' ORDER BY created_at"):
            schedule_at = row['schedule_at']
            if schedule_at and datetime.fromisoformat(schedule_at) > now:
                continue
            conn.execute("UPDATE publish_tasks SET status = 'running', updated_at = ? WHERE id = ?",
                         (now.isoformat(), row['id']))
            conn.commit()
            task = _safe_task(row)
            task['status'] = 'running'
            return task
        conn.rollback()
        return None


def finish_task(base_dir, task_id, status, error_code=None):
    if status not in {'submitted_unverified', 'failed', 'needs_review'}:
        raise ValueError('invalid_task_status')
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = ?, error_code = ?, updated_at = ?
            WHERE id = ? AND status = 'running' ''',
            (status, error_code, datetime.now(timezone.utc).isoformat(), task_id))
        conn.commit()
        return updated.rowcount == 1


def recover_running_tasks(base_dir):
    """Unknown platform outcome after a crash must never be retried automatically."""
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks
            SET status = 'needs_review', error_code = 'interrupted_unknown', updated_at = ?
            WHERE status = 'running' ''', (datetime.now(timezone.utc).isoformat(),))
        conn.commit()
        return updated.rowcount


def enqueue_mock(base_dir, task_id):
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = 'queued_mock', updated_at = ?
            WHERE id = ? AND status = 'draft' ''',
            (datetime.now(timezone.utc).isoformat(), task_id))
        conn.commit()
        return updated.rowcount == 1


def recover_mock_tasks(base_dir):
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = 'queued_mock', updated_at = ?
            WHERE status = 'running_mock' ''', (datetime.now(timezone.utc).isoformat(),))
        conn.commit()
        return updated.rowcount


def claim_mock_task(base_dir):
    with closing(connect(base_dir)) as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute("SELECT * FROM publish_tasks WHERE status = 'queued_mock' ORDER BY created_at LIMIT 1").fetchone()
        if row is None:
            conn.rollback()
            return None
        conn.execute("UPDATE publish_tasks SET status = 'running_mock', updated_at = ? WHERE id = ?",
                     (datetime.now(timezone.utc).isoformat(), row['id']))
        conn.commit()
        task = _safe_task(row)
        task['status'] = 'running_mock'
        return task


def finish_mock_task(base_dir, task_id, success, error_code=None):
    status = 'succeeded_mock' if success else 'failed_mock'
    with closing(connect(base_dir)) as conn:
        updated = conn.execute('''UPDATE publish_tasks SET status = ?, error_code = ?, updated_at = ?
            WHERE id = ? AND status = 'running_mock' ''',
            (status, None if success else (error_code or 'mock_error'), datetime.now(timezone.utc).isoformat(), task_id))
        conn.commit()
        return updated.rowcount == 1
