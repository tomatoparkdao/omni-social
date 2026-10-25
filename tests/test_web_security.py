import os
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

import sau_backend
from myUtils import auth_mode

PRODUCTION_ENV = {
    'OMNISOCIAL_ENV': 'production',
    'OMNISOCIAL_AUTH_MODE': 'production',
    'OMNISOCIAL_SESSION_SECRET': 'test-only-secret',  # pragma: allowlist secret - test fixture only
    'OMNISOCIAL_ADMIN_PASSWORD_HASH': generate_password_hash('test-password'),
}

LOCAL_DEV_ENV = {
    'OMNISOCIAL_ENV': 'local',
    'OMNISOCIAL_AUTH_MODE': 'local_dev',
    'OMNISOCIAL_BIND_HOST': '127.0.0.1',
}


class WebSecurityTests(unittest.TestCase):
    def setUp(self):
        auth_mode.clear_cache()

    def test_production_api_requires_server_session(self):
        with patch.dict(os.environ, PRODUCTION_ENV):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/getAccounts').status_code, 401)
            self.assertFalse(client.get('/auth/session').json['authenticated'])
            self.assertEqual(client.get('/auth/session').json['mode'], 'production')
            self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}).status_code, 401)  # pragma: allowlist secret - invalid test input
            response = client.post('/auth/session', json={'password': 'test-password'})  # pragma: allowlist secret - test fixture only
            self.assertEqual(response.status_code, 200)
            self.assertIn('HttpOnly', response.headers['Set-Cookie'])
            self.assertIn('SameSite=Strict', response.headers['Set-Cookie'])
            self.assertIn('Secure', response.headers['Set-Cookie'])
            self.assertEqual(client.post('/uploadCookie').status_code, 403)
            self.assertEqual(client.get('/downloadCookie?filePath=x').status_code, 403)

    def test_production_auth_attempts_are_rate_limited(self):
        with patch.dict(os.environ, {**PRODUCTION_ENV, 'OMNISOCIAL_SESSION_SECRET': 'test-only-secret-rate-limit'}):  # pragma: allowlist secret - test fixture only
            client = sau_backend.app.test_client()
            for _ in range(5):
                self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}, environ_base={'REMOTE_ADDR': '192.0.2.77'}).status_code, 401)  # pragma: allowlist secret - invalid test input
            self.assertEqual(client.post('/auth/session', json={'password': 'wrong'}, environ_base={'REMOTE_ADDR': '192.0.2.77'}).status_code, 429)  # pragma: allowlist secret - invalid test input

    def test_production_without_secrets_fails_closed(self):
        with patch.dict(os.environ, {'OMNISOCIAL_ENV': 'production', 'OMNISOCIAL_AUTH_MODE': 'production',
                                     'OMNISOCIAL_SESSION_SECRET': '', 'OMNISOCIAL_ADMIN_PASSWORD_HASH': ''}):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/getAccounts').status_code, 503)

    def test_missing_auth_mode_defaults_to_production(self):
        env = {**PRODUCTION_ENV, 'OMNISOCIAL_ENV': 'local', 'OMNISOCIAL_AUTH_MODE': ''}
        with patch.dict(os.environ, env):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/auth/session').json['mode'], 'production')
            self.assertFalse(client.get('/auth/session').json['authenticated'])
            self.assertEqual(client.get('/getAccounts').status_code, 401)

    def test_local_dev_grants_server_side_session_on_loopback(self):
        with patch.dict(os.environ, LOCAL_DEV_ENV):
            client = sau_backend.app.test_client()
            session = client.get('/auth/session').json
            self.assertEqual(session['mode'], 'local_dev')
            self.assertTrue(session['authenticated'])
            self.assertEqual(client.get('/getAccounts').status_code, 200)
            self.assertEqual(client.get('/tasks').status_code, 200)

    def test_local_dev_rejects_non_loopback_remote_address(self):
        with patch.dict(os.environ, LOCAL_DEV_ENV):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/auth/session', environ_base={'REMOTE_ADDR': '192.0.2.5'}).status_code, 403)
            self.assertEqual(client.get('/getAccounts', environ_base={'REMOTE_ADDR': '10.1.2.3'}).status_code, 403)

    def test_local_dev_rejects_proxy_headers_and_foreign_host(self):
        with patch.dict(os.environ, LOCAL_DEV_ENV):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/auth/session', headers={'X-Forwarded-For': '203.0.113.9'}).status_code, 403)
            self.assertEqual(client.get('/auth/session', headers={'Forwarded': 'for=203.0.113.9'}).status_code, 403)
            self.assertEqual(client.get('/auth/session', headers={'Host': 'social.example.com'}).status_code, 403)

    def test_local_dev_is_refused_when_configuration_is_unsafe(self):
        cases = [
            {**LOCAL_DEV_ENV, 'OMNISOCIAL_ENV': 'production'},
            {**LOCAL_DEV_ENV, 'OMNISOCIAL_BIND_HOST': '0.0.0.0'},
            {**LOCAL_DEV_ENV, 'OMNISOCIAL_PUBLIC_TUNNEL': '1'},
            {**LOCAL_DEV_ENV, 'OMNISOCIAL_AUTH_MODE': 'yes-please'},
        ]
        for env in cases:
            with self.subTest(env=env), patch.dict(os.environ, env):
                auth_mode.clear_cache()
                with self.assertRaises(auth_mode.AuthModeError):
                    auth_mode.resolve_auth_mode()

    def test_local_dev_unsafe_configuration_fails_closed_at_request_time(self):
        env = {**LOCAL_DEV_ENV, 'OMNISOCIAL_ENV': 'production'}
        with patch.dict(os.environ, env), patch.object(sau_backend, 'STARTUP_AUTH_ERROR', 'unsafe test config'):
            client = sau_backend.app.test_client()
            self.assertEqual(client.get('/auth/session').status_code, 503)

    def test_wrong_origin_is_rejected_in_both_modes(self):
        with patch.dict(os.environ, LOCAL_DEV_ENV):
            client = sau_backend.app.test_client()
            self.assertEqual(client.post('/agent/plan', json={'prompt': 'x'}, headers={'Origin': 'https://evil.example'}).status_code, 403)
            self.assertEqual(client.get('/deleteAccount?id=1').status_code, 405)
            self.assertEqual(client.get('/deleteFile?id=1').status_code, 405)
        with patch.dict(os.environ, PRODUCTION_ENV):
            client = sau_backend.app.test_client()
            self.assertEqual(client.post('/agent/plan', json={'prompt': 'x'}, headers={'Origin': 'https://evil.example'}).status_code, 403)
            self.assertEqual(client.post('/agent/plan', json={'prompt': 'x'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
