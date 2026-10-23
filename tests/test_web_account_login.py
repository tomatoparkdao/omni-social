import asyncio
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from queue import Queue
from unittest.mock import AsyncMock, patch

import sau_backend


class WebAccountLoginTests(unittest.TestCase):
    def test_xiaohongshu_qr_and_verified_account_record(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / "db").mkdir()
            with closing(sqlite3.connect(base / "db" / "database.db")) as conn:
                conn.execute(
                    "CREATE TABLE user_info (id INTEGER PRIMARY KEY, type INTEGER, filePath TEXT, userName TEXT, status INTEGER)"
                )
            image = base / "qr.png"
            image.write_bytes(b"example-qr-image")
            queue = Queue()

            async def login(account_file, **kwargs):
                kwargs["qrcode_callback"]({"image_path": str(image)})
                Path(account_file).write_text("{}", encoding="utf-8")
                return {"success": True, "status": "success"}

            with patch.object(sau_backend, "BASE_DIR", base), patch.object(
                sau_backend, "xiaohongshu_setup", side_effect=login
            ):
                asyncio.run(sau_backend.login_xiaohongshu_web("测试账号", queue))

            self.assertEqual(queue.get_nowait()["type"], "qr")
            self.assertEqual(queue.get_nowait(), {"type": "success"})
            with closing(sqlite3.connect(base / "db" / "database.db")) as conn:
                row = conn.execute("SELECT type, filePath, userName, status FROM user_info").fetchone()
            self.assertEqual((row[0], row[2], row[3]), (1, "测试账号", 1))
            self.assertTrue((base / "cookiesFile" / row[1]).exists())

    def test_login_failure_reports_error_without_creating_account(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / "db").mkdir()
            with closing(sqlite3.connect(base / "db" / "database.db")) as conn:
                conn.execute(
                    "CREATE TABLE user_info (id INTEGER PRIMARY KEY, type INTEGER, filePath TEXT, userName TEXT, status INTEGER)"
                )
            queue = Queue()
            result = {"success": False, "status": "failed", "message": "未在扫一扫登录区域找到小红书二维码图片"}
            with patch.object(sau_backend, "BASE_DIR", base), patch.object(
                sau_backend, "xiaohongshu_setup", new=AsyncMock(return_value=result)
            ):
                asyncio.run(sau_backend.login_xiaohongshu_web("测试账号", queue))
            self.assertEqual(queue.get_nowait()["code"], "qr_unavailable")
            with closing(sqlite3.connect(base / "db" / "database.db")) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM user_info").fetchone()[0], 0)

    def test_sse_stream_ends_after_error(self):
        queue = Queue()
        queue.put({"type": "error", "code": "qr_unavailable", "message": "二维码未加载"})
        messages = list(sau_backend.sse_stream(queue))
        self.assertEqual(len(messages), 1)
        self.assertEqual(json.loads(messages[0][6:])["code"], "qr_unavailable")

    def test_missing_browser_is_reported_to_sse_client(self):
        queue = Queue()
        with patch.object(
            sau_backend, "login_xiaohongshu_web", new=AsyncMock(side_effect=RuntimeError("Executable doesn't exist"))
        ):
            sau_backend.run_async_function("1", "测试账号", queue)
        self.assertEqual(queue.get_nowait()["code"], "browser_missing")

    def test_login_route_returns_sse_headers(self):
        with patch.object(sau_backend.threading, "Thread"), patch.object(
            sau_backend, "sse_stream", return_value=iter([": heartbeat\n\n"])
        ):
            response = sau_backend.app.test_client().get("/login?type=1&id=test", buffered=False)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("text/event-stream"))
        response.close()

    def test_account_refresh_uses_current_xiaohongshu_cookie_check(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / "db").mkdir()
            with closing(sqlite3.connect(base / "db" / "database.db")) as conn:
                conn.execute(
                    "CREATE TABLE user_info (id INTEGER PRIMARY KEY, type INTEGER, filePath TEXT, userName TEXT, status INTEGER)"
                )
                conn.execute("INSERT INTO user_info VALUES (1, 1, 'test.json', '测试账号', 1)")
                conn.commit()
            with patch.object(sau_backend, "BASE_DIR", base), patch.object(
                sau_backend, "xiaohongshu_cookie_auth", new=AsyncMock(return_value=True)
            ) as auth:
                response = sau_backend.app.test_client().get("/getValidAccounts")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["data"][0][4], 1)
            auth.assert_awaited_once_with(base / "cookiesFile" / "test.json")
            with patch.object(sau_backend, "BASE_DIR", base), patch.object(
                sau_backend, "xiaohongshu_cookie_auth", new=AsyncMock(return_value=False)
            ):
                response = sau_backend.app.test_client().get("/getValidAccounts")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["data"][0][4], 0)
