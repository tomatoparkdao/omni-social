import argparse
import asyncio
import os
import unittest
from unittest.mock import patch

import sau_backend
import sau_cli
from myUtils import auth_mode, postVideo

_ENV_PATCH = None


def setUpModule():
    """Web 发布闸门用例直接调用接口，按本机开发模式（local_dev）运行。"""
    global _ENV_PATCH
    _ENV_PATCH = patch.dict(os.environ, {'OMNISOCIAL_AUTH_MODE': 'local_dev', 'OMNISOCIAL_BIND_HOST': '127.0.0.1'})
    _ENV_PATCH.start()
    auth_mode.clear_cache()


def tearDownModule():
    _ENV_PATCH.stop()
    auth_mode.clear_cache()


class PublishGuardTests(unittest.TestCase):
    def test_web_publish_routes_do_not_call_engine_by_default(self):
        with patch.dict(os.environ, {"OMNISOCIAL_ENABLE_REAL_PUBLISH": "0"}), patch.object(
            sau_backend, "post_video_xhs"
        ) as engine:
            client = sau_backend.app.test_client()
            self.assertEqual(client.post("/postVideo", json={"type": 1}).status_code, 403)
            self.assertEqual(client.post("/postVideoBatch", json=[]).status_code, 403)
            engine.assert_not_called()

    def test_cli_upload_is_blocked_before_platform_dispatch(self):
        args = argparse.Namespace(platform="xiaohongshu", action="upload-note")
        with patch.dict(os.environ, {"OMNISOCIAL_ENABLE_REAL_PUBLISH": "0"}), patch.object(
            sau_cli.PLATFORMS["xiaohongshu"], "run"
        ) as run:
            with self.assertRaises(PermissionError):
                asyncio.run(sau_cli.dispatch(args))
            run.assert_not_called()

    def test_legacy_engine_is_blocked_before_accessing_account_files(self):
        with patch.dict(os.environ, {"OMNISOCIAL_ENABLE_REAL_PUBLISH": "0"}):
            with self.assertRaises(PermissionError):
                postVideo.post_video_xhs("title", [], [], [])

    def test_cookie_export_and_overwrite_are_disabled(self):
        client = sau_backend.app.test_client()
        self.assertEqual(client.get("/downloadCookie?filePath=anything.json").status_code, 403)
        self.assertEqual(client.post("/uploadCookie").status_code, 403)


if __name__ == "__main__":
    unittest.main()
