# OmniSocial Web 架构（当前实现）

Vue/Vite 页面经同源 `/api` 代理访问 Flask。Flask 使用原有 `db/database.db` 的账号、素材表，并增建 `publish_tasks` 表；所有新增任务先保存为 `draft`，用 UUID 和唯一幂等键防止重试重复创建。`sau_worker.py` 目前仅在隔离测试环境消费 `queued_mock`，状态为 `running_mock`、`succeeded_mock` 或 `failed_mock`，重启时可将未完成的模拟任务重新排队。

原有 `uploader/`、CLI 和 Skills 完整保留。旧 Web `/postVideo`、`/postVideoBatch` 和 CLI 上传动作均受默认关闭的真实发布闸门限制。新建的 Web/CLI 适配器把四个平台的 Web 账号路径与素材映射到现有平台请求对象；独立 Worker 可按到期时间领取任务，但真实发布闸门默认关闭，本轮未执行任何真实平台任务。返回 `submitted_unverified` 仅表示适配器调用返回，**不代表平台发布成功**；执行中断或结果不明时标记 `needs_review`，不自动重试。

页面：仪表盘、账号管理、素材管理、旧版发布中心（现保存草稿）、新建图文/视频任务与预览、任务队列、日历、历史、系统设置、关于。日历仅列出已指定时间的草稿/模拟任务，尚无生产调度执行。

生产模式须由反向代理终止 HTTPS，Flask 使用服务端口令校验与签名的 HttpOnly/SameSite=Strict/Secure 会话 Cookie（会话内容由浏览器保存，不是服务端持久 Session）；应用容器不直接向宿主机开放后端端口。开发模式只接受 127.0.0.1/::1 请求。

> © OmniAiLab ｜ 开发者：Mochiball ｜ 使用与分发遵循 [MIT License](../LICENSE) 及第三方 NOTICE。
