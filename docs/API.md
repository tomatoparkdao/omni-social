# Web API（以当前源码为准）

开发地址 `http://127.0.0.1:5173/api`，Vite 代理至 `127.0.0.1:5409`。生产环境经同源反向代理提供 `/api/`；生产敏感接口要求 `/auth/session` 建立的服务端会话。跨站写请求被拒绝，无通配 CORS。

| 方法 | 路径 | 行为 |
|:---|:---|:---|
| GET/POST/DELETE | `/auth/session` | 查询、建立、退出管理会话；生产需配置口令哈希与会话密钥 |
| GET | `/health` | 不含账号信息的健康检查 |
| GET | `/system/status` | 环境、存储、浏览器依赖与发布闸门状态 |
| GET | `/getAccounts` | 账号元数据；Cookie 文件名不返回 |
| GET | `/getValidAccounts` | 校验并返回账号状态；不返回 Cookie 文件名 |
| GET | `/login?type=1&id=...` | SSE 扫码登录；`qr`/`success`/`error` 和心跳，连接关闭会取消小红书临时任务 |
| POST | `/uploadSave` | 图片/视频素材入库，返回素材 ID 与相对路径 |
| GET | `/getFiles`、`/getFile?filename=...` | 素材列表与预览 |
| DELETE | `/deleteFile?id=...`、`/deleteAccount?id=...` | 显式删除，仅供有权用户；账号删除同时删除对应会话文件 |
| POST | `/updateUserinfo` | 修改账号备注 |
| GET/POST | `/tasks` | 查询或创建发布前草稿；创建须提供 `idempotency_key` |
| POST | `/tasks/<id>/cancel` | 取消草稿或模拟排队任务 |
| POST | `/tasks/<id>/queue` | 默认 403；仅启用真实发布闸门后才能排队，排队不代表已发布 |
| POST | `/tasks/<id>/simulate` | **仅隔离测试环境**入模拟队列，不访问平台 |
| POST | `/agent/plan` | 仅生成非执行计划 |
| POST | `/postVideo`、`/postVideoBatch` | 旧接口；默认返回 403，绝不在当前测试中启用真实发布 |
| POST/GET | `/uploadCookie`、`/downloadCookie` | 安全禁用，固定返回 403 |

任务 JSON 至少包含：`platform`（1–4）、`account_id`、`content_type`（`note`/`video`）、`title`、`material_ids`、`idempotency_key`；可选 `body`、`tags`、`schedule_at`（未来、带时区 ISO 时间）、`options`。视频任务只允许一个视频素材；图文不支持视频号。

> © OmniAiLab ｜ 开发者：Mochiball ｜ 使用与分发遵循 [MIT License](../LICENSE) 及第三方 NOTICE。
