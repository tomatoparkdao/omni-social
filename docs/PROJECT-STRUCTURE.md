---
name: PROJECT-STRUCTURE
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# 项目结构

- `sau_backend.py`：Flask Web API，默认端口 5409
- `sau_frontend/`：Vue/Vite 管理界面
- `uploader/`：各平台上传实现
- `sau_commands/`、`sau_cli.py`：CLI
- `db/`：数据库初始化与数据文件
- `myUtils/task_store.py`：非破坏性任务表、幂等键与模拟队列状态
- `myUtils/publish_guard.py`：默认关闭的真实发布闸门
- `sau_worker.py`：隔离测试环境的 Mock Worker，不调用真实平台
- `scripts/backup_db.py`：SQLite 一致性备份；备份文件不进 Git
- `scripts/omnisocial_service.py`：Windows 一键启动/停止时记录并核验进程归属
- `compose.yaml`、`Dockerfile`、`deploy/`：容器与反向代理配置（本机 Docker 未安装，尚未容器验证）
- `myUtils/`、`utils/`：登录、素材与通用工具
- `skills/`：平台运行说明与技能资源

> © OmniAiLab ｜ 开发者：Mochiball ｜ 使用与分发遵循 [MIT License](../LICENSE) 及第三方 NOTICE。
