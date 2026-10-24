"""The Web/CLI bridge is tested with local dummy files and a mocked uploader."""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import AsyncMock, patch

from myUtils import web_task_adapter


class WebTaskAdapterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'db').mkdir()
        (self.root / 'cookiesFile').mkdir()
        (self.root / 'videoFile').mkdir()
        self.cookie = self.root / 'cookiesFile' / 'web-account.json'
        self.cookie.write_text('{}', encoding='utf-8')
        self.video = self.root / 'videoFile' / 'sample.mp4'
        self.video.write_bytes(b'mock-video')
        self.image = self.root / 'videoFile' / 'sample.png'
        self.image.write_bytes(b'mock-image')
        with closing(sqlite3.connect(self.root / 'db' / 'database.db')) as conn:
            conn.execute('CREATE TABLE user_info (id INTEGER PRIMARY KEY, type INTEGER, filePath TEXT, userName TEXT, status INTEGER)')
            conn.execute('CREATE TABLE file_records (id INTEGER PRIMARY KEY, filename TEXT, file_path TEXT)')
            conn.execute('INSERT INTO file_records VALUES (1, ?, ?)', ('sample.mp4', self.video.name))
            conn.execute('INSERT INTO file_records VALUES (2, ?, ?)', ('sample.png', self.image.name))
            for platform in (1, 2, 3, 4):
                conn.execute('INSERT INTO user_info VALUES (?, ?, ?, ?, 1)',
                             (platform, platform, self.cookie.name, 'test-web-account'))
            conn.commit()

    def task(self, platform=1, content_type='video', **changes):
        result = {'platform': platform, 'account_id': platform, 'content_type': content_type,
                  'material_ids': [1] if content_type == 'video' else [2],
                  'title': '测试标题', 'body': '测试正文', 'tags': ['测试'], 'options': {}}
        result.update(changes)
        return result

    def test_prepares_web_session_without_copying_or_changing_cli_session(self):
        for platform in (1, 2, 3, 4):
            prepared = web_task_adapter.prepare_task(self.root, self.task(platform))
            self.assertEqual(prepared['account_file'], self.cookie)
            self.assertEqual(prepared['files'], [self.video])
        self.assertEqual(web_task_adapter.prepare_task(self.root, self.task(1, 'note'))['files'], [self.image])
        self.assertFalse((self.root / 'cookies').exists())

    def test_rejects_missing_or_unsafe_inputs(self):
        with self.assertRaisesRegex(ValueError, 'account_unavailable'):
            web_task_adapter.prepare_task(self.root, self.task(1, account_id=2))
        with closing(sqlite3.connect(self.root / 'db' / 'database.db')) as conn:
            conn.execute("UPDATE user_info SET filePath = '../outside.json' WHERE id = 1")
            conn.commit()
        with self.assertRaisesRegex(ValueError, 'account_session_unavailable'):
            web_task_adapter.prepare_task(self.root, self.task())
        with self.assertRaisesRegex(ValueError, 'unsupported_content_type'):
            web_task_adapter.prepare_task(self.root, self.task(2, 'note'))
        with self.assertRaisesRegex(ValueError, 'unsupported_options'):
            web_task_adapter.prepare_task(self.root, self.task(3, options={'is_original': True}))

    async def test_execution_is_default_denied_and_mocked_bridge_uses_web_file(self):
        with patch.dict(os.environ, {'OMNISOCIAL_ENABLE_REAL_PUBLISH': '0'}):
            with self.assertRaises(PermissionError):
                await web_task_adapter.execute_task(self.root, self.task())
        uploader = AsyncMock()
        with patch.dict(os.environ, {'OMNISOCIAL_ENABLE_REAL_PUBLISH': '1'}), patch(
            'sau_commands.xiaohongshu.upload_xiaohongshu_video', uploader
        ):
            result = await web_task_adapter.execute_task(self.root, self.task())
        self.assertEqual(result, 'submitted_unverified')
        uploader.assert_awaited_once()
        request = uploader.await_args.args[0]
        self.assertEqual(request.account_file, self.cookie)
        self.assertEqual(request.video_file, self.video)


if __name__ == '__main__':
    unittest.main()
