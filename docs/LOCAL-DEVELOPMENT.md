---
name: LOCAL-DEVELOPMENT
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: 内部项目（未公开）
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# Windows 本地运行

在项目根目录执行 `python -m venv .venv`、`.venv\Scripts\python.exe -m pip install -r requirements.txt`，然后在 `sau_frontend` 执行 `npm install`。双击 `start-omnisocial.bat` 访问 http://127.0.0.1:5173，停止使用 `stop-omnisocial.bat`。

文章渲染器还需要在 `utils/article_renderer` 执行 `npm install`；当前项目使用 Node.js 24，可满足其 Node.js 22+ 要求。
