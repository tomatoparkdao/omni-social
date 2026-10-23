---
name: REPAIR-LOG
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# 修复记录

- 新增 `conf.py`：参考项目仅提供 `conf.example.py`，后端直接导入 `conf`，因此补齐本地默认配置。
- 新增 OmniSocial 启停脚本和项目文档；未重写原业务代码。
- 已在 `utils/article_renderer` 安装渲染依赖，Markdown 渲染测试通过；前端自身构建也已通过。
- 修复了抖音旧位置参数兼容、声明失败时浏览器资源释放、Instagram 可选提示清理，以及小红书候选项等待时间的回归问题。
- 最终全量测试：137 passed，71 subtests passed。

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniSocial 自媒体运营系统（omniailabx.com）- 未经授权禁止复制、传播或二次分发。
