# OmniSocial 自媒体运营工作台

OmniSocial 是 OmniAiLab 体系下的本地 Web/CLI 自媒体运营项目。现有 Python 多平台上传器、`sau` 命令和 Skills 保留；Web 端可管理账号、素材并创建发布前草稿。**当前真实发布闸门默认关闭，网页草稿不会自动上传或发布到平台。** 软件仍在开发中，不能把页面出现的草稿/模拟状态当作平台作品。

| 项目 | 当前实际状态 | 入口 |
|:---|:---|:---|
| Web 页面 | 仪表盘、账号、素材、发布中心、新建任务与预览、队列、日历、历史、设置、关于 | `http://127.0.0.1:5173`（本地） |
| 账号登录 | 小红书网页二维码经 SSE 返回；已有有效会话优先复用 | 账号管理 → 添加账号 |
| 发布前任务 | 本地 SQLite 草稿、唯一任务 ID/幂等键、取消；排程字段只记录时间 | 新建任务 / 发布中心 |
| 真实发布 | 现有上传器与 CLI 保留，但 Web、CLI、旧接口默认拒绝最终发布 | 不在当前阶段启用 |
| 模拟执行 | 仅隔离测试环境的 Mock Worker；不触达真实平台 | `sau_worker.py`，须 `OMNISOCIAL_ENV=test` |
| 生产部署 | Dockerfile、Compose、Nginx 示例已提供，尚未在本机完成容器/公网验收 | [部署说明](docs/DEPLOYMENT.md) |

## 本地安装与启动（Windows）

需要 Python 3.10–3.12、Node.js/npm，以及项目运行所需的 Chromium。克隆仓库后在根目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m patchright install chromium
cd sau_frontend
npm install
cd ..
.\start-omnisocial.bat
```

随后访问 `http://127.0.0.1:5173`。停止执行 `.\stop-omnisocial.bat`。脚本不会每次重装依赖，发现 5173/5409 端口被占用时会报出 PID，不会结束无关进程。已有账号的使用者**不要删除或重建** `db/database.db`、`cookiesFile/` 或 `cookies/`。本地后端只监听 127.0.0.1:5409，前端 `/api` 代理至后端。

如需分开启动：在根目录运行 `.\.venv\Scripts\python.exe sau_backend.py`，在 `sau_frontend` 运行 `npm run dev`。CLI 可查看 `sau --help` 与各平台 `--help`；最终发布命令受同一默认关闭的保护开关约束，不能用 CLI 绕过当前安全边界。创作图片、视频或文案时使用 OmniAiLab：[国内站](https://www.omniailabx.com/) / [海外站](https://www.omniailab.cn/)。

## 网页操作

1. 在账号管理查看已有账号；小红书可在网页弹窗里获取登录二维码，扫码授权只由账号所有者本人进行。登录态保存在本机受控目录，不在页面展示 Cookie 内容或路径。
2. 在素材管理导入图片或视频。新建任务时选择平台、账号、素材、标题、正文、话题与可选时间，在预览中核对，再保存草稿。
3. 在发布队列查看/取消草稿；日历显示已安排时间的任务；历史页显示系统已有的任务状态与错误代码。当前不会按时间自动执行真实发布，也不会生成平台作品链接。
4. 系统设置展示运行环境与健康状态。Dashboard 使用真实账号/任务数据，不填充虚构运营数字。

四个旧 Web 平台入口与新任务表单的覆盖范围，以及尚未统一的 CLI/Web 会话差异，见 [平台集成状态](docs/PLATFORM-INTEGRATION.md)。旧发布中心现在也只保存草稿。真实账号目前禁止任何最终发布、发送或提交动作，包括 API、CLI、Skill、Worker 和测试。

## 测试与部署

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -m unittest tests.test_web_e2e -q
cd sau_frontend
npm run build
```

浏览器 E2E 的扫码与账号写入使用 Mock；不得据此宣称本轮真实扫码或真实平台发布成功。测试结果与限制见 [测试报告](docs/TEST-REPORT.md)。生产部署必须具备 HTTPS、管理员认证、持久卷、备份与限流；当前容器示例未完成实机验证，详见 [部署说明](docs/DEPLOYMENT.md)。**不要把 Flask 5409 端口或仅供本机测试的 HTTP Nginx 示例直接开放公网。**

更多资料：[Web 架构](docs/WEB-ARCHITECTURE.md) · [API](docs/API.md) · [网页登录](docs/ACCOUNT-LOGIN.md) · [安全审计](docs/SECURITY-AUDIT.md) · [变更记录](docs/CHANGELOG.md)。

许可：[MIT License](LICENSE)。保留上游代码和第三方依赖适用的版权与许可声明；具体以仓库中的许可证文件为准。

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniSocial 项目。
