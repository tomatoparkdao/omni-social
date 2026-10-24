"""Browser UI regression with mocked login and task APIs; never publishes real content."""
import base64
import json
import unittest
from urllib.request import urlopen

from patchright.sync_api import sync_playwright


BASE = 'http://127.0.0.1:5173'
PIXEL = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl52ZkAAAAASUVORK5CYII=')


class WebE2ETests(unittest.TestCase):
    def test_navigation_mock_login_preview_and_queue(self):
        with urlopen(f'{BASE}/api/health', timeout=5) as response:
            self.assertEqual(json.load(response)['code'], 200)
        with urlopen(f'{BASE}/api/getAccounts', timeout=5) as response:
            existing_accounts = json.load(response)['data']
        self.assertGreaterEqual(sum(row[1] == 1 for row in existing_accounts), 1)
        fake_account = [999999, 1, None, '模拟扫码账号', 1]
        fake_material = {'id': 777777, 'filename': 'mock-image.jpg', 'filesize': 0.01,
                         'file_path': 'mock-image.jpg', 'upload_time': '2026-01-01 00:00:00'}
        mock_tasks = []
        mock_authorized = [False]
        console_errors = []

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chromium', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.on('pageerror', lambda error: console_errors.append(str(error)))
            page.add_init_script(f'''(() => {{
                const NativeEventSource = window.EventSource;
                window.EventSource = class {{
                  constructor(url) {{
                    if (!url.includes('/api/login')) return new NativeEventSource(url);
                    setTimeout(() => this.onmessage?.({{data: JSON.stringify({{type:'qr', image:'data:image/png;base64,{base64.b64encode(PIXEL).decode()}'}})}}), 400);
                    setTimeout(() => this.onmessage?.({{data: JSON.stringify({{type:'success'}})}}), 2500);
                  }}
                  close() {{}}
                }};
              }})();''')

            def route_accounts(route):
                rows = existing_accounts + ([fake_account] if mock_authorized[0] else [])
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'data': rows}))

            def route_tasks(route):
                if route.request.method == 'GET':
                    route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'data': mock_tasks}))
                else:
                    payload = route.request.post_data_json
                    task = {**payload, 'id': 'mock-task-1', 'status': 'draft', 'created_at': '2026-01-01T00:00:00Z',
                            'updated_at': '2026-01-01T00:00:00Z', 'error_code': None}
                    mock_tasks.append(task)
                    route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'data': task, 'created': True}))

            page.route('**/api/getAccounts', route_accounts)
            page.route('**/api/getValidAccounts', route_accounts)
            page.route('**/api/getFiles', lambda route: route.fulfill(status=200, content_type='application/json',
                       body=json.dumps({'code': 200, 'data': [fake_material]})))
            page.route('**/api/getFile?*', lambda route: route.fulfill(status=200, content_type='image/png', body=PIXEL))
            page.route('**/api/tasks', route_tasks)

            page.goto(BASE, wait_until='networkidle')
            self.assertTrue(page.get_by_role('heading', name='自媒体自动化运营系统').is_visible())
            page.get_by_text('账号管理', exact=True).first.click()
            page.get_by_role('button', name='添加账号').first.click()
            page.wait_for_timeout(500)
            dialog = page.locator('.el-dialog').last
            state = page.evaluate("() => ({hash: location.hash, dialogs: document.querySelectorAll('.el-dialog').length, selects: document.querySelectorAll('.el-dialog .el-select').length})")
            self.assertGreater(state['selects'], 0, str(state))
            page.locator('.el-dialog .el-select').first.click()
            options = page.evaluate("() => ({roles: document.querySelectorAll('[role=option]').length, dropdowns: document.querySelectorAll('.el-select-dropdown__item').length, visible: [...document.querySelectorAll('[role=option]')].filter(el => el.getBoundingClientRect().width > 0).length})")
            self.assertGreater(options['visible'], 0, str(options))
            page.get_by_role('option', name='小红书').click()
            page.get_by_placeholder('请输入账号名称').fill('模拟扫码账号')
            page.locator('.el-dialog__footer button').last.click()
            page.get_by_alt_text('登录二维码').wait_for(state='visible', timeout=5000)
            mock_authorized[0] = True
            page.get_by_text('模拟扫码账号').first.wait_for(state='visible', timeout=10000)

            page.get_by_text('素材管理', exact=True).first.click()
            self.assertTrue(page.get_by_role('heading', name='素材管理').is_visible())
            page.get_by_role('button', name='上传素材').first.click()
            self.assertTrue(page.get_by_text('上传素材', exact=True).last.is_visible())
            page.goto(f'{BASE}/#/new-task', wait_until='networkidle')
            self.assertTrue(page.get_by_role('heading', name='新建发布任务').is_visible())
            page.locator('label.el-checkbox').filter(has_text='模拟扫码账号').click()
            page.locator('label.el-checkbox').filter(has_text='mock-image.jpg').click()
            page.locator('input[maxlength="200"]').fill('模拟图文任务')
            page.get_by_role('button', name='发布前预览').click()
            preview_image = page.locator('.el-dialog img[alt="mock-image.jpg"]')
            preview_image.wait_for(state='visible', timeout=5000)
            self.assertTrue(preview_image.is_visible())
            page.keyboard.press('Escape')
            page.get_by_role('button', name='保存任务草稿').click()
            page.get_by_text('任务草稿已保存，未执行真实发布').wait_for(state='visible', timeout=5000)
            page.goto(f'{BASE}/#/queue', wait_until='networkidle')
            self.assertTrue(page.get_by_text('模拟图文任务').is_visible())
            page.goto(f'{BASE}/#/calendar', wait_until='networkidle')
            self.assertTrue(page.get_by_role('heading', name='发布日历').is_visible())
            page.goto(f'{BASE}/#/history', wait_until='networkidle')
            self.assertTrue(page.get_by_role('heading', name='历史记录').is_visible())
            page.goto(f'{BASE}/#/settings', wait_until='networkidle')
            self.assertTrue(page.get_by_text('真实发布：已关闭').is_visible())
            self.assertEqual(console_errors, [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
