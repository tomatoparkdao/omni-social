---
name: omni-social-manager
description: OmniSocial 项目级总控 Skill。解析多平台发布任务并安全分发到现有平台 Skill 或 sau CLI；默认只生成执行计划，不进行真实发布。
license: MIT-0
slug: omni-social-manager
displayName: OmniSocial 多平台发布总控
version: 1.0.0
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# OmniSocial 总控 Skill

用于识别并校验平台、内容类型、账号、素材路径、标题、正文、标签和发布时间，然后选择现有平台 Skill 与 CLI。总控层不实现上传逻辑，不修改 `uploader/`。

## 安全规则

1. 先读取目标平台的 `skills/<platform>-upload/SKILL.md`，再读取其必要 references。
2. 平台、账号、素材路径、标题、正文或发布时间缺失时停止并要求补全，不猜测。
3. 默认只生成计划；只有用户明确确认“执行发布”后，才能调用会提交发布的命令。
4. 不索取密码、Token 或 Cookie；登录和人工验证交由用户完成。
5. 执行前检查素材存在、账号文件状态、内容类型和发布时间；不覆盖账号文件，不删除登录状态。
6. 只报告 CLI 返回的明确结果；超时或未知状态不得声称发布成功。

## 平台路由

| 平台 | Skill | CLI |
| --- | --- | --- |
| 小红书 | `xiaohongshu-upload` | `sau xiaohongshu ...` |
| 抖音 | `douyin-upload` | `sau douyin ...` |
| 快手 | `kuaishou-upload` | `sau kuaishou ...` |
| B站 | `bilibili-upload` | `sau bilibili ...` |
| 其他已迁移平台 | 对应 `skills/*-upload` | 以 `sau --help` 和平台 Skill 为准 |

## 计划格式

先整理以下字段：`platforms[]`、`content_type`、`account`、`files[]`、`title`、`body`、`tags[]`、`schedule`、`confirmed`。`confirmed=false` 时仅输出待确认计划。

## CLI 选择

- 视频：通常使用 `sau <platform> upload-video`。
- 图文/笔记：通常使用 `sau <platform> upload-note`。
- 登录状态：使用 `sau <platform> check --account <name>`；缺失时提示用户自行执行 login。
- 具体参数以当前 CLI 的 `--help` 和平台 Skill 为准，不复制或重写 Uploader 实现。

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniAiLab AI建筑与室内设计总设计师（omniailabx.com）- 未经授权禁止复制、传播或二次分发。
