"""Translate a Web task to the existing four platform command adapters.

No platform call is permitted until the shared real-publish gate is enabled.
"""
import sqlite3
from contextlib import closing
from pathlib import Path

from myUtils.publish_guard import require_real_publish_enabled


PLATFORM_NAMES = {1: 'xiaohongshu', 2: 'tencent', 3: 'douyin', 4: 'kuaishou'}


def _validate_options(platform, options):
    if not isinstance(options, dict):
        raise ValueError('unsupported_options')
    if options.get('is_original') or options.get('category') not in (None, 0, '') and not (
        platform == 2 and isinstance(options['category'], str)
    ):
        raise ValueError('unsupported_options')
    if options.get('is_draft') and platform != 2:
        raise ValueError('unsupported_options')
    if (options.get('product_link') or options.get('product_title')) and platform != 3:
        raise ValueError('unsupported_options')


def prepare_task(base_dir, task):
    """Re-read records at execution time so deleted or moved inputs cannot be used."""
    base_dir = Path(base_dir)
    platform = task['platform']
    if platform not in PLATFORM_NAMES:
        raise ValueError('unsupported_platform')
    if task['content_type'] not in ('video', 'note'):
        raise ValueError('unsupported_content_type')
    _validate_options(platform, task['options'])
    with closing(sqlite3.connect(base_dir / 'db' / 'database.db')) as conn:
        conn.row_factory = sqlite3.Row
        account = conn.execute('SELECT type, filePath, userName FROM user_info WHERE id = ?',
                               (task['account_id'],)).fetchone()
        if not account or account['type'] != platform:
            raise ValueError('account_unavailable')
        ids = task['material_ids']
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('material_unavailable')
        placeholders = ','.join('?' for _ in ids)
        materials = conn.execute(
            f'SELECT id, file_path FROM file_records WHERE id IN ({placeholders})', ids
        ).fetchall()
    if len(materials) != len(ids):
        raise ValueError('material_unavailable')

    cookie_root = (base_dir / 'cookiesFile').resolve()
    cookie_file = (cookie_root / account['filePath']).resolve()
    if cookie_file.suffix.lower() != '.json' or not cookie_file.is_relative_to(cookie_root) or not cookie_file.is_file():
        raise ValueError('account_session_unavailable')
    material_root = (base_dir / 'videoFile').resolve()
    by_id = {row['id']: row['file_path'] for row in materials}
    suffixes = {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm'} if task['content_type'] == 'video' else {'.jpg', '.jpeg', '.png', '.webp'}
    files = []
    for material_id in ids:
        path = (material_root / by_id[material_id]).resolve()
        if not path.is_relative_to(material_root) or path.suffix.lower() not in suffixes or not path.is_file():
            raise ValueError('material_unavailable')
        files.append(path)
    if task['content_type'] == 'video' and len(files) != 1:
        raise ValueError('material_unavailable')
    if task['content_type'] == 'note' and platform == 2:
        raise ValueError('unsupported_content_type')
    return {'platform': platform, 'content_type': task['content_type'], 'account_name': account['userName'],
            'account_file': cookie_file, 'files': files, 'title': task['title'], 'body': task['body'],
            'tags': task['tags'], 'options': task['options']}


async def execute_task(base_dir, task):
    """Invoke the existing CLI platform adapter; return is not proof of publication."""
    require_real_publish_enabled()
    prepared = prepare_task(base_dir, task)
    platform, content_type = prepared['platform'], prepared['content_type']
    common = {'account_name': prepared['account_name'], 'title': prepared['title'],
              'tags': prepared['tags'], 'publish_date': 0, 'account_file': prepared['account_file']}
    if platform == 1:
        from sau_commands import xiaohongshu as command
        if content_type == 'video':
            request = command.XiaohongshuVideoUploadRequest(
                **common, video_file=prepared['files'][0], description=prepared['body'])
            await command.upload_xiaohongshu_video(request)
        else:
            request = command.XiaohongshuNoteUploadRequest(
                **common, image_files=prepared['files'], note=prepared['body'])
            await command.upload_xiaohongshu_note(request)
    elif platform == 2:
        from sau_commands import tencent as command
        request = command.TencentVideoUploadRequest(
            **common, video_file=prepared['files'][0], description=prepared['body'],
            category=prepared['options'].get('category') or None, is_draft=bool(prepared['options'].get('is_draft')))
        await command.upload_tencent_video(request)
    elif platform == 3:
        from sau_commands import douyin as command
        if content_type == 'video':
            request = command.DouyinVideoUploadRequest(
                **common, video_file=prepared['files'][0], description=prepared['body'],
                product_link=prepared['options'].get('product_link') or '',
                product_title=prepared['options'].get('product_title') or '')
            await command.upload_video(request)
        else:
            request = command.DouyinNoteUploadRequest(
                **common, image_files=prepared['files'], note=prepared['body'])
            await command.upload_note(request)
    else:
        from sau_commands import kuaishou as command
        if content_type == 'video':
            request = command.KuaishouVideoUploadRequest(
                **common, video_file=prepared['files'][0], description=prepared['body'])
            await command.upload_kuaishou_video(request)
        else:
            request = command.KuaishouNoteUploadRequest(
                **common, image_files=prepared['files'], note=prepared['body'])
            await command.upload_kuaishou_note(request)
    return 'submitted_unverified'
