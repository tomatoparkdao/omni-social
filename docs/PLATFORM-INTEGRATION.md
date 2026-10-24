# 平台集成状态

- `uploader/` 保留全部现有平台引擎，`sau_commands/` 与 `sau_cli.py` 保留原有命令组，`skills/` 保留平台 Skill。
- 旧 Web 登录与视频接口覆盖小红书、视频号、抖音、快手；**旧 Web 真实发布接口现在默认拒绝执行**。
- 新 Web 草稿表单接受这四个平台的视频素材，以及小红书、抖音、快手图文素材；四个平台 Web 任务已能经受限适配器调用现有 `sau_commands`，但默认闸门关闭且没有真实平台执行验证，不能声称已发布。
- CLI 使用 `cookies/` 下的平台账号别名；旧 Web 使用 `cookiesFile/` 与 `user_info`。现在 `myUtils/web_task_adapter.py` 会在执行前重新核对 Web 账号与素材，并把经过路径验证的 Web Cookie 文件显式传给四个平台的现有 `sau_commands` 请求对象；CLI 的默认别名路径保持不变。仅覆盖 Web 已支持的四个平台/七种内容组合，不能说全部 CLI 平台已经接入 Web。
- 独立 `sau_publish_worker.py` 已有定时到期领取、未知结果不自动重试和显式的 `submitted_unverified` 状态。真实发布闸门默认关闭，本轮**没有启动该 Worker 执行真实任务**，平台作品链接与实际执行结果仍未验证。模拟 Worker 仍不导入 `uploader/`。
- 部分旧发布中心高级参数（例如“原创”复选项）不能无损映射到新版命令，适配层会明确拒绝不支持的参数，不能静默丢弃；需继续完成 UI/平台字段一致性验证。

安全边界：整个当前任务期间不得执行真实平台最终发布。平台支持情况以各命令 `--help`、源码及独立测试为准，不把 Mock 结果写成真实作品链接。

> © OmniAiLab ｜ 开发者：Mochiball ｜ 使用与分发遵循 [MIT License](../LICENSE) 及第三方 NOTICE。
