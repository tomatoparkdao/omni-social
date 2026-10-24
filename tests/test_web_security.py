import os
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

import sau_backend


class WebSecurityTests(unittest.TestCase):
    def test_production_api_requires_server_session(self):
        env = {
            "OMNISOCIAL_ENV": "production",
            "OMNISOCIAL_SESSION_SECRET": "test-only-secret",  # pragma: allowlist secret - test fixture only
            "OMNISOCIAL_ADMIN_PASSWORD_HASH": generate_password_hash("test-password"),
        }
        with patch.dict(os.environ, env):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/getAccounts').status_code, 401)
            self.assertFalse(client.get('/auth/session').json['authenticated'])
            self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}).status_code, 401)  # pragma: allowlist secret - invalid test input
            response = client.post('/auth/session', json={'password': 'test-password'})  # pragma: allowlist secret - test fixture only
            self.assertEqual(response.status_code, 200)
            self.assertIn('HttpOnly', response.headers['Set-Cookie'])
            self.assertIn('SameSite=Strict', response.headers['Set-Cookie'])
            self.assertIn('Secure', response.headers['Set-Cookie'])
            self.assertEqual(client.post('/uploadCookie').status_code, 403)
            self.assertEqual(client.get('/downloadCookie?filePath=x').status_code, 403)

    def test_production_auth_attempts_are_rate_limited(self):
        env = {
            "OMNISOCIAL_ENV": "production",
            "OMNISOCIAL_SESSION_SECRET": "test-only-secret-rate-limit",  # pragma: allowlist secret - test fixture only
            "OMNISOCIAL_ADMIN_PASSWORD_HASH": generate_password_hash("test-password"),
        }
        with patch.dict(os.environ, env):
            client = sau_backend.app.test_client()
            for _ in range(5):
                self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}, environ_base={'REMOTE_ADDR': '192.0.2.77'}).status_code, 401)  # pragma: allowlist secret - invalid test input
            self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}, environ_base={'REMOTE_ADDR': '192.0.2.77'}).status_code, 429)  # pragma: allowlist secret - invalid test input

    def test_wrong_origin_and_remote_address_are_rejected(self):
        with patch.dict(os.environ, {"OMNISOCIAL_ENV": "local"}):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/auth/session', environ_base={'REMOTE_ADDR': '192.0.2.5'}).status_code, 403)
            self.assertEqual(client.post('/agent/plan', json={'prompt': 'x'}, headers={'Origin': 'https://evil.example'}).status_code, 403)
            self.assertEqual(client.get('/deleteAccount?id=1').status_code, 405)
            self.assertEqual(client.get('/deleteFile?id=1').status_code, 405)


if __name__ == '__main__':
    unittest.main()
