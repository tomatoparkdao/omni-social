import sqlite3
import asyncio
import os
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import AsyncMock, patch

import sau_backend
import sau_worker
import sau_publish_worker
from myUtils import auth_mode, task_store

_ENV_PATCH = None


def setUpModule():
    """任务接口用例直接调用 Web API，按本机开发模式（local_dev）运行。"""
    global _ENV_PATCH
    _ENV_PATCH = patch.dict(os.environ, {'OMNISOCIAL_AUTH_MODE': 'local_dev', 'OMNISOCIAL_BIND_HOST': '127.0.0.1'})
    _ENV_PATCH.start()
    auth_mode.clear_cache()


def tearDownModule():
    _ENV_PATCH.stop()
    auth_mode.clear_cache()


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / 'db').mkdir()
        (self.base / 'videoFile').mkdir()
        (self.base / 'cookiesFile').mkdir()
        (self.base / 'cookiesFile' / 'opaque.json').write_text('{}', encoding='utf-8')
        (self.base / 'videoFile' / 'sample.mp4').write_bytes(b'test-only')
        with closing(sqlite3.connect(self.base / 'db' / 'database.db')) as conn:
            conn.execute('CREATE TABLE user_info (id INTEGER PRIMARY KEY, type INTEGER, filePath TEXT, userName TEXT, status INTEGER)')
            conn.execute('INSERT INTO user_info VALUES (1, 1, ?, ?, 1)', ('opaque.json', 'test-account'))
            conn.execute('CREATE TABLE file_records (id INTEGER PRIMARY KEY, filename TEXT, filesize REAL, file_path TEXT)')
            conn.execute('INSERT INTO file_records VALUES (2, ?, 1, ?)', ('sample.mp4', 'sample.mp4'))
            conn.commit()
        self.patch = patch.object(sau_backend, 'BASE_DIR', self.base)
        self.patch.start()
        self.client = sau_backend.app.test_client()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def payload(self):
        return {
            'platform': 1, 'account_id': 1, 'content_type': 'video',
            'title': '测试任务', 'body': '', 'tags': ['test'],
            'material_ids': [2], 'idempotency_key': 'test-key-123',
        }

    def test_create_list_idempotency_and_cancel_without_publish(self):
        with patch.object(sau_backend, 'post_video_xhs') as engine:
            first = self.client.post('/tasks', json=self.payload())
            self.assertEqual(first.status_code, 200)
            self.assertTrue(first.json['created'])
            task = first.json['data']
            self.assertEqual(task['status'], 'draft')
            self.assertNotIn('filePath', str(task))
            second = self.client.post('/tasks', json=self.payload())
            self.assertFalse(second.json['created'])
            self.assertEqual(second.json['data']['id'], task['id'])
            self.assertEqual(len(self.client.get('/tasks').json['data']), 1)
            self.assertEqual(self.client.post(f"/tasks/{task['id']}/cancel").status_code, 200)
            self.assertEqual(self.client.get('/tasks').json['data'][0]['status'], 'cancelled')
            engine.assert_not_called()

    def test_invalid_account_and_traversal_material_rejected(self):
        bad = self.payload()
        bad['account_id'] = 999
        self.assertEqual(self.client.post('/tasks', json=bad).status_code, 400)
        with closing(sqlite3.connect(self.base / 'db' / 'database.db')) as conn:
            conn.execute("UPDATE file_records SET file_path = '../sample.mp4' WHERE id = 2")
            conn.commit()
        self.assertEqual(self.client.post('/tasks', json=self.payload()).status_code, 400)
        self.assertEqual(len(self.client.get('/tasks').json['data']), 0)

    def test_mock_worker_recovery_and_failure_are_isolated(self):
        task_id = self.client.post('/tasks', json=self.payload()).json['data']['id']
        with patch.dict(os.environ, {'OMNISOCIAL_ENV': 'test'}), patch.object(sau_backend, 'post_video_xhs') as real_engine:
            self.assertEqual(self.client.post(f'/tasks/{task_id}/simulate').status_code, 200)
            claimed = task_store.claim_mock_task(self.base)
            self.assertEqual(claimed['id'], task_id)
            self.assertIsNone(task_store.claim_mock_task(self.base))
            self.assertEqual(task_store.recover_mock_tasks(self.base), 1)
            self.assertTrue(sau_worker.run_once(self.base, lambda task: None))
            self.assertFalse(sau_worker.run_once(self.base, lambda task: None))
            self.assertEqual(self.client.get('/tasks').json['data'][0]['status'], 'succeeded_mock')
            real_engine.assert_not_called()

    def test_mock_worker_records_failure_code(self):
        task_id = self.client.post('/tasks', json=self.payload()).json['data']['id']
        with patch.dict(os.environ, {'OMNISOCIAL_ENV': 'test'}):
            self.client.post(f'/tasks/{task_id}/simulate')
            def fail(_task):
                raise RuntimeError('sensitive-error-must-not-be-logged')
            self.assertTrue(sau_worker.run_once(self.base, fail))
        result = self.client.get('/tasks').json['data'][0]
        self.assertEqual(result['status'], 'failed_mock')
        self.assertEqual(result['error_code'], 'mock_adapter_failed')
        self.assertNotIn('sensitive-error', str(result))

    def test_real_queue_is_default_denied_without_state_change(self):
        task_id = self.client.post('/tasks', json=self.payload()).json['data']['id']
        with patch.dict(os.environ, {'OMNISOCIAL_ENABLE_REAL_PUBLISH': '0'}):
            self.assertEqual(self.client.post(f'/tasks/{task_id}/queue').status_code, 403)
            with self.assertRaises(PermissionError):
                asyncio.run(sau_publish_worker.run_once(self.base, AsyncMock()))
        self.assertEqual(task_store.list_tasks(self.base)[0]['status'], 'draft')

    def test_mocked_real_worker_never_retries_unknown_outcome(self):
        task_id = self.client.post('/tasks', json=self.payload()).json['data']['id']
        self.assertTrue(task_store.enqueue_task(self.base, task_id))
        self.assertFalse(task_store.enqueue_task(self.base, task_id))
        with patch.dict(os.environ, {'OMNISOCIAL_ENABLE_REAL_PUBLISH': '1'}):
            executor = AsyncMock(side_effect=RuntimeError('do-not-store-private-detail'))
            self.assertTrue(asyncio.run(sau_publish_worker.run_once(self.base, executor)))
            executor.assert_awaited_once()
        result = task_store.list_tasks(self.base)[0]
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['error_code'], 'execution_unknown')
        self.assertNotIn('private-detail', str(result))
        self.assertIsNone(task_store.claim_due_task(self.base))

    def test_interrupted_running_task_requires_review(self):
        task_id = self.client.post('/tasks', json=self.payload()).json['data']['id']
        task_store.enqueue_task(self.base, task_id)
        self.assertEqual(task_store.claim_due_task(self.base)['id'], task_id)
        self.assertEqual(task_store.recover_running_tasks(self.base), 1)
        self.assertIsNone(task_store.claim_due_task(self.base))
        self.assertEqual(task_store.list_tasks(self.base)[0]['status'], 'needs_review')


if __name__ == '__main__':
    unittest.main()
