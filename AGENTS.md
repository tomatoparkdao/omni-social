# OmniSocial 项目协作规范

## Skill 读取与路由

- 处理平台发布任务前，必须读取 `skills/omni-social-manager/SKILL.md`。
- 确定平台后，再读取对应的 `skills/<platform>-upload/SKILL.md` 及任务所需 references；不得猜测命令参数。
- 小红书、抖音、快手、B站分别使用 `sau xiaohongshu`、`sau douyin`、`sau kuaishou`、`sau bilibili`。
- 执行前使用对应命令的 `--help`，确认当前代码真实支持的动作和参数。

## 安全检查

- 默认只生成计划，不执行真实发布。
- 真实发布必须得到用户明确确认，并再次核对平台、账号、素材、标题、正文、标签和发布时间。
- 不索取或写入密码、Token、Cookie；不覆盖账号信息，不删除登录状态。
- 素材路径必须存在且位于用户明确授权范围；账号状态只读检查。
- 失败、超时或未知结果必须如实报告，不重复提交。

## 实现边界

保留 `uploader/` 为唯一发布引擎。Skill 只负责说明、路由和安全编排，不在 Skill 中重写浏览器自动化或平台发布逻辑。网页自然语言入口使用 `/agent/plan` 生成非执行计划，未来扩展时也必须遵守上述确认规则。
