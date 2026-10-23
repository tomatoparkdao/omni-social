# 小红书网页添加账号故障定位与修复

## 根本原因

1. 本机安装了 Playwright 使用的 Chromium，但缺少当前 Patchright 版本要求的 `chromium-1208`。小红书登录线程启动浏览器时因此抛异常。原 `/login` 线程没有兜底上报，SSE 客户端无法收到明确的失败状态。
2. 网页登录仍调用旧版小红书二维码实现，依赖固定页面选择器；项目现有 CLI 已有较新的二维码获取、扫码后登录态校验流程，但网页没有复用。旧 SSE 没有心跳和可靠的结束信号，前端断线提示也无法区分服务端失败。
3. 登录后的账号刷新仍使用旧版小红书 Cookie 校验地址；`/getValidAccounts` 在失效分支修改 SQLite 返回的不可变行，还会导致刷新异常。

网络链路本身可用：前端运行于 `127.0.0.1:5173`，开发环境 `VITE_API_BASE_URL=/api`，Vite 将 `/api/login` 转发到监听 `5409` 的后端 `/login`。实际请求返回 HTTP 200 和 `text/event-stream`，不是 404、502 或 CORS 问题。

## 修复

- `sau_backend.py`：网页小红书登录最小适配现有 CLI 流程；二维码经 SSE 发送到网页，只有 Cookie 校验成功且数据库提交完成后才发送成功事件。登录线程异常、二维码获取失败、超时、Cookie 校验失败分别返回可识别错误；SSE 增加心跳、终态结束和断开清理。日志只记平台、错误代码和异常类型，不记录 Cookie 或账号凭据。
- `sau_backend.py`：小红书账号刷新改用与 CLI 一致的 Cookie 校验；修正失效状态更新时的行类型问题。
- `sau_frontend/src/views/AccountManagement.vue`：处理二维码、成功与明确失败事件；避免正常 SSE 结束被误报为连接失败；登录成功后刷新账号列表。
- `start-omnisocial.bat`：用非交互方式等待服务启动，修复重定向终端下 `timeout` 报错。
- `tests/test_web_account_login.py`：覆盖二维码事件、数据库写入、失败不写入、浏览器缺失分类、SSE 响应头与账号刷新。

已在本机安装项目使用的 Patchright Chromium（`patchright install chromium --no-shell`；项目使用 `channel="chromium"`，不依赖额外的 headless shell）。其他平台的登录与发布实现未替换，参考项目源码未修改，原有数据库和 Cookie 未清空。

## 验证

- 后端 5409、前端 5173 均正常监听；直接与代理后的 `/getAccounts` 都返回 200。
- 修正后的一键启动脚本可启动服务，没有先前的 `timeout` 输入重定向错误。
- 浏览器点击“添加账号 → 小红书 → 确认”后，`/api/login` 返回 200、`text/event-stream`，真实页面显示 196×196 二维码；浏览器未出现 JavaScript 错误。
- 账号所有者扫码授权后，网页收到真实成功事件。SQLite `user_info` 中新增 1 条小红书记录，Cookie 文件存在且包含 19 个 Cookie；代理后的 `/getAccounts`、`/getValidAccounts` 均返回该账号且状态为正常。
- 刷新账号管理页后账号可见；再次走已有有效 Cookie 的成功事件时，网页自动请求 `/getValidAccounts` 并保持账号可见，控制台无错误。
- Python 相关测试 16 项通过，前端 `npm run build` 通过（Vite 仍有现存的 `NODE_ENV` 提示）。

若其他机器出现 `browser_missing`，在项目虚拟环境中运行 `.venv\Scripts\patchright.exe install chromium --no-shell` 后重启服务。
