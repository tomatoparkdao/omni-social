---
name: SKILLS-ARCHITECTURE
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

# OmniSocial Skill 架构

## 迁移清单

当前 `skills/` 保留 19 个原有 Skill：`alipay-upload`、`baijiahao-upload`、`bilibili-upload`、`dayu-upload`、`douyin-upload`、`facebook-upload`、`hupu-upload`、`instagram-upload`、`kuaishou-upload`、`meta-upload`、`social-auto-upload`、`tencent-upload`、`tiktok-upload`、`weibo-upload`、`xiaohongshu-upload`、`xueqiu-upload`、`youtube-upload`、`zhihu-upload`，以及新增的 `omni-social-manager`。

原有 Skill 的 `SKILL.md`、references、scripts 和相关资源保持原路径；未删除或重写原有 Skill。

## 调用关系

```text
自然语言/网页请求
        |
        v
omni-social-manager -- 解析字段、确认平台、执行安全检查
        |
        +--> skills/<platform>-upload/SKILL.md
        |       |
        |       v
        +--> sau <platform> <action> ...
                |
                v
          sau_commands/<platform>.py
                |
                v
             uploader/
```

`/agent/plan` 是网页侧预留接口，目前只返回待确认计划，不调用发布命令。

## CLI 对应关系

| Skill | CLI 平台 | 典型动作 | 状态 |
| --- | --- | --- | --- |
| xiaohongshu-upload | `xiaohongshu` | `login`、`check`、`upload-video`、`upload-note` | 已验证 parser/help |
| douyin-upload | `douyin` | `login`、`check`、`upload-video`、`upload-note` | 已验证 parser/help |
| kuaishou-upload | `kuaishou` | `login`、`check`、`upload-video`、`upload-note` | 已验证 parser/help |
| bilibili-upload | `bilibili` | `login`、`check`、`upload-video` | 已验证 parser/help |
| 其他原有 Skill | 见各自 `SKILL.md` 与 `sau --help` | 以实际 CLI 为准 | 保留原说明 |

## 验证结果

- 原有 Skill 目录与 `SKILL.md` 已完整存在；四个平台 Skill 的 Python CLI 模块均存在。
- 四个平台使用 `--help` 的基础命令解析验证不触发登录或发布。
- 项目全量 Python 测试：137 passed，71 subtests passed。
- 网页 Agent 预留接口：`POST /agent/plan`，空请求返回 400，带 prompt 返回 `awaiting_confirmation`，并明确 `publish_executed=false`。
- 未执行任何真实平台发布、账号覆盖或登录状态删除。

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniAiLab AI建筑与室内设计总设计师（omniailabx.com）- 未经授权禁止复制、传播或二次分发。
