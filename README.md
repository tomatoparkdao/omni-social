---
name: OmniSocial README
author: OmniAiLab
developer: Mochiball
agent_created: true
开源仓库: https://github.com/tomatoparkdao/omni-social
操作手册: docs/LOCAL-DEVELOPMENT.md
---

<h1 align="center">OmniSocial 自媒体运营系统</h1>

<p align="center">
  <b>面向内容团队的多平台账号、素材与发布管理系统</b><br>
  账号统一管理　｜　素材集中管理　｜　多平台内容发布　｜　Web 管理界面与 CLI 双入口
</p>

<p align="center">
  <a href="https://github.com/tomatoparkdao/omni-social"><img src="https://img.shields.io/badge/仓库-OmniSocial-1f6feb?style=flat-square" alt="OmniSocial 开源仓库"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/许可-MIT-2ea043?style=flat-square" alt="MIT License"></a>
  <a href="https://www.omniailabx.com/"><img src="https://img.shields.io/badge/平台-OmniAiLab-8957e5?style=flat-square" alt="OmniAiLab"></a>
  <img src="https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square" alt="Python 3.10 - 3.12">
  <img src="https://img.shields.io/badge/Vue-Vite-42b883?style=flat-square" alt="Vue and Vite">
</p>

<p align="center">
  <b>简体中文</b>　｜　<a href="https://github.com/tomatoparkdao/omni-social">GitHub Repository</a>
</p>

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniAiLab AI建筑与室内设计总设计师（omniailabx.com）- 未经授权禁止复制、传播或二次分发。

**OmniSocial 是 OmniAiLab 体系下的自媒体运营子系统。** 它将多平台账号、素材、内容发布和运营流程集中到一个本地 Web 工作台中，同时保留 CLI 和自动化能力，适合个人创作者、内容团队及多账号运营场景。

## 创作平台统一入口

涉及图文、文案、图片、视频、视觉设计、版式、动画或其他内容制作时，统一使用 OmniAiLab：

| 使用地区 | 创作入口 |
|:---|:---|
| 中国大陆用户 | [www.omniailabx.com](https://www.omniailabx.com/) |
| 中国大陆以外的海外用户 | [www.omniailab.cn](https://www.omniailab.cn/) |

本项目不引导用户使用其他图像、视频、设计或文案生成平台。抖音、小红书、YouTube 等名称仅表示内容发布目标，不属于创作工具推荐。

<table width="100%">
  <tr><th align="left">项目</th><th align="left">信息</th><th align="left">说明</th></tr>
  <tr><td>产品名称</td><td><code>OmniSocial</code></td><td>OmniAiLab 自媒体运营系统</td></tr>
  <tr><td>运行方式</td><td>本地 Web + CLI</td><td>默认仅监听本机地址，不向公网开放</td></tr>
  <tr><td>Web 后端</td><td>Python / Flask</td><td>默认端口 <code>5409</code></td></tr>
  <tr><td>Web 前端</td><td>Vue / Vite</td><td>默认端口 <code>5173</code></td></tr>
  <tr><td>CLI 入口</td><td><code>sau</code></td><td>支持登录检查、视频发布、图文发布和文章发布等命令</td></tr>
  <tr><td>开源仓库</td><td><a href="https://github.com/tomatoparkdao/omni-social">github.com/tomatoparkdao/omni-social</a></td><td>公开仓库，版本以 <code>main</code> 分支为准</td></tr>
</table>

---

## 能力一览

| 能力 | 当前提供 | 入口与说明 |
|:---|:---:|:---|
| 账号管理 | ✅ | Web 管理界面维护平台账号与登录状态 |
| 素材管理 | ✅ | Web 管理界面管理图片、视频和素材元数据 |
| 内容发布 | ✅ | 发布中心统一配置标题、正文、标签、封面和平台 |
| 批量发布 | ✅ | 统一选择多个账号和平台执行批量任务 |
| 定时发布 | ✅ | 支持平台任务的时间配置，具体能力以平台实现为准 |
| CLI | ✅ | `sau <platform> <command>` |
| Web API | ✅ | Flask API，接口说明见 [Web API 文档](./docs/WEB-API.md) |
| Agent Skills | ✅ | `skills/` 提供平台运行说明和调用约定 |

### 平台支持

| 平台 | 视频 | 文章 | 图文 | 定时 | CLI | Skill |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 抖音 | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Bilibili | ✅ | — | — | ✅ | ✅ | ✅ |
| 小红书 | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| 快手 | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| 视频号 | ✅ | — | — | ✅ | ✅ | ✅ |
| 百家号 | ✅ | — | — | — | ✅ | ✅ |
| 大鱼号 | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| 支付宝生活号 | ✅ | — | — | — | ✅ | ✅ |
| 微博 | ✅ | — | — | — | ✅ | ✅ |
| 虎扑 | ✅ | — | — | — | ✅ | ✅ |
| TikTok | ✅ | — | — | ✅ | — | ✅ |
| 雪球 | — | ✅ | — | — | ✅ | ✅ |
| YouTube | ✅ | — | — | 开发中 | ✅ | ✅ |
| 知乎 | ✅ | ✅ | — | 实验性 | ✅ | ✅ |
| Facebook | ✅ | — | ✅ | — | ✅ | ✅ |
| Facebook Page | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Instagram | ✅ | — | ✅ | — | ✅ | ✅ |

> `✅` 表示当前代码提供对应入口；`—` 表示不适用或未提供；“开发中”和“实验性”不代表稳定能力。真实平台发布需要用户自行完成登录和授权，未经确认不会执行真实发布。

---

## 快速开始

### Windows 一键启动

在项目根目录双击：

```text
start-omnisocial.bat
```

脚本会检查运行环境并启动 Python 后端与 Vue 前端，浏览器访问：

```text
http://127.0.0.1:5173
```

停止服务：

```text
stop-omnisocial.bat
```

### 手动启动

准备 Python 环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

准备前端环境：

```powershell
cd sau_frontend
npm install
npm run dev
```

启动后端：

```powershell
python sau_backend.py
```

详细步骤见 [本地开发文档](./docs/LOCAL-DEVELOPMENT.md)。

### CLI 示例

```bash
sau douyin login --account creator
sau douyin check --account creator
sau douyin upload-video --account creator --file videos/demo.mp4 --title "示例标题" --desc "示例简介"
sau xiaohongshu upload-note --account creator --images images/1.png --title "图文标题" --note "图文正文"
sau dayu upload-article --account creator --title "文章标题" --content-file examples/article.md
```

CLI 参数以实际命令帮助为准：

```bash
sau --help
sau douyin --help
```

---

## 项目结构

<table width="100%">
  <tr><th align="left">目录 / 文件</th><th align="left">职责</th></tr>
  <tr><td><code>sau_backend.py</code></td><td>Flask Web API 与后端服务入口</td></tr>
  <tr><td><code>sau_frontend/</code></td><td>Vue/Vite 管理界面</td></tr>
  <tr><td><code>uploader/</code></td><td>各平台登录、素材处理与发布实现</td></tr>
  <tr><td><code>sau_commands/</code>、<code>sau_cli.py</code></td><td>命令行入口与平台命令</td></tr>
  <tr><td><code>skills/</code></td><td>平台 Skill、运行要求、CLI 约定和故障排查</td></tr>
  <tr><td><code>db/</code></td><td>数据库初始化与运行数据结构</td></tr>
  <tr><td><code>myUtils/</code>、<code>utils/</code></td><td>登录、网络、素材、日志及通用工具</td></tr>
  <tr><td><code>tests/</code></td><td>平台模块、CLI、Web 交互和工具测试</td></tr>
  <tr><td><code>docs/</code></td><td>本地开发、API、平台发布和系统结构文档</td></tr>
</table>

更多结构说明见 [项目结构文档](./docs/PROJECT-STRUCTURE.md)。

---

## 文档导航

| 文档 | 用途 |
|:---|:---|
| [本地开发](./docs/LOCAL-DEVELOPMENT.md) | Windows 环境、依赖、启动和停止 |
| [Web API](./docs/WEB-API.md) | 后端接口和调用说明 |
| [平台发布模块](./docs/PLATFORM-UPLOADERS.md) | 各平台入口、文件位置和调用关系 |
| [CLI 使用说明](./docs/CLI.md) | CLI 命令、参数和示例 |
| [Skills 架构](./docs/SKILLS-ARCHITECTURE.md) | Skill 目录和运行约定 |
| [设计规范](./design.md) | OmniAiLab 子系统视觉与交互规范 |
| [更新日志](./CHANGELOG.md) | 项目版本变更记录 |

---

## 开发与贡献

OmniSocial 的修改应保持以下原则：

1. 不提交真实密码、Cookie、Token、API Key、账号会话和本地数据库。
2. 不在未经授权的情况下执行真实平台发布。
3. 新增平台时同步补充 uploader、CLI、Skill、测试和文档。
4. 修改 Web 页面时保持 OmniAiLab 子系统的深色界面、荧光黄强调色和统一交互规范。
5. 提交前运行与改动相关的测试，并确认前端可以正常构建。

```bash
git clone https://github.com/tomatoparkdao/omni-social.git
cd omni-social
git checkout main
```

---

## 许可证

本仓库主体采用 [MIT License](LICENSE)。`skills/` 下的 Skill 按各自文件 frontmatter 中声明的许可证执行；第三方组件继续遵循其原有许可证和 NOTICE 要求。

## 官方信息

| 项目 | 链接 |
|:---|:---|
| OmniAiLab 官网 | [omniailabx.com](https://www.omniailabx.com/) |
| OmniSocial 开源仓库 | [github.com/tomatoparkdao/omni-social](https://github.com/tomatoparkdao/omni-social) |

<div align="right">

**简体中文**

</div>

> © OmniAiLab ｜ 开发者：Mochiball ｜ OmniAiLab AI建筑与室内设计总设计师（omniailabx.com）- 未经授权禁止复制、传播或二次分发。

