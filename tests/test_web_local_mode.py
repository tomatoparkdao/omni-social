"""本地开发模式（local_dev）浏览器回归：不出现管理员密码页，直接进入工作台。

前置条件与 test_web_e2e 相同：后端 :5409 与前端 :5173 已按 local_dev 启动，
且不触发任何真实发布。
"""
import base64
import json
import unittest
from urllib.request import urlopen

from patchright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5173'
PIXEL = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl52ZkAAAAASUVORK5CYII=')


class LocalDevModeTests(unittest.TestCase):
    def test_local_dev_skips_login_and_keeps_existing_accounts(self):
        with urlopen(f'{BASE}/api/auth/session', timeout=5) as response:
            session = json.load(response)
        self.assertEqual(session['mode'], 'local_dev')
        self.assertTrue(session['authenticated'])

        errors = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chromium', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE, wait_until='networkidle')

            self.assertEqual(page.get_by_placeholder('管理员密码').count(), 0)
            self.assertTrue(page.get_by_role('heading', name='自媒体自动化运营系统').is_visible())

            for menu, marker in [('账号管理', '账号管理'), ('素材管理', '素材管理'), ('发布队列', '发布队列'),
                                 ('发布日历', '发布日历'), ('历史记录', '历史记录'), ('系统设置', '系统设置')]:
                page.get_by_text(menu, exact=True).first.click()
                page.wait_for_timeout(600)
                self.assertTrue(page.get_by_text(marker, exact=False).first.is_visible(), menu)

            page.goto(f'{BASE}/#/account-management', wait_until='networkidle')
            page.wait_for_timeout(1000)
            self.assertIn('小红书', page.inner_text('body'))
            self.assertEqual(errors, [])
            browser.close()

    def test_qr_login_dialog_still_renders(self):
        """只验证二维码弹窗与 SSE 前端流程，不发起真实小红书登录。"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chromium', headless=True)
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.add_init_script(f'''(() => {{
                const Native = window.EventSource;
                window.EventSource = class {{
                  constructor(url) {{
                    if (!url.includes('/api/login')) return new Native(url);
                    setTimeout(() => this.onmessage?.({{
                      data: JSON.stringify({{type: 'qr', image: 'data:image/png;base64,{base64.b64encode(PIXEL).decode()}'}})
                    }}), 300);
                  }}
                  close() {{}}
                }};
              }})();''')
            page.goto(f'{BASE}/#/account-management', wait_until='networkidle')
            page.get_by_role('button', name='添加账号').first.click()
            page.wait_for_timeout(400)
            page.locator('.el-dialog .el-select').first.click()
            page.get_by_role('option', name='小红书').click()
            page.get_by_placeholder('请输入账号名称').fill('二维码流程验证')
            page.locator('.el-dialog__footer button').last.click()
            page.get_by_alt_text('登录二维码').wait_for(state='visible', timeout=6000)
            browser.close()


if __name__ == '__main__':
    unittest.main()
