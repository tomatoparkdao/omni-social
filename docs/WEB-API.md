---
name: WEB-API
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# Web API

Flask 入口为 `sau_backend.py`，默认监听 `127.0.0.1:5409`（原代码绑定 `0.0.0.0`）。接口包括文件上传/下载、素材管理、账号管理、Cookie 登录与发布队列；完整路由以该文件中的 `@app.route` 为准。

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniSocial 自媒体运营系统（omniailabx.com）- 未经授权禁止复制、传播或二次分发。
