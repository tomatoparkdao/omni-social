<h1 align="center">OmniSocial — Social Media Operations System</h1>

<p align="center">
  <b>One local workbench for accounts, assets and publishing — plan first, publish only after confirmation, report failures honestly</b><br>
  17 publishing targets　｜　16 platform command groups　｜　19 agent skills　｜　5 web pages　｜　6 publishing stages × 6 human gates<br>
  Assets in → account login → content assembly → plan → confirmed publishing → result check<br>
  Plan-only by default　｜　uploader/ is the single publishing engine　｜　creation stays in OmniAiLab　｜　runs locally, never stores passwords
</p>

<p align="center">
  <a href="https://github.com/tomatoparkdao/omni-social"><img src="https://img.shields.io/badge/%E7%89%88%E6%9C%AC-0.1.0-1f6feb?style=flat-square" alt="Version 0.1.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/%E8%AE%B8%E5%8F%AF-MIT-2ea043?style=flat-square" alt="License MIT"></a>
  <a href="https://www.omniailabx.com/"><img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-OmniAiLab-8957e5?style=flat-square" alt="Platform OmniAiLab"></a>
  <img src="https://img.shields.io/badge/%E5%85%A5%E5%8F%A3-Web_%7C_CLI_%7C_Skill-0969da?style=flat-square" alt="Entry Web / CLI / Skill">
  <img src="https://img.shields.io/badge/%E5%8F%91%E5%B8%83%E7%9B%AE%E6%A0%87-17_%E5%B9%B3%E5%8F%B0-0e8a16?style=flat-square" alt="17 publishing targets">
  <img src="https://img.shields.io/badge/%E8%BF%90%E8%A1%8C%E6%97%B6-Python_3.10--3.12-3776AB?style=flat-square" alt="Python 3.10 - 3.12">
  <img src="https://img.shields.io/badge/%E5%89%8D%E7%AB%AF-Vue_3_%2B_Vite-42b883?style=flat-square" alt="Vue 3 + Vite">
</p>

<p align="center">
  <a href="README.md">简体中文</a>　｜　<b>English</b>
</p>

> © OmniAiLab ｜ Developer: Mochiball ｜ Platform: [omniailabx.com](https://www.omniailabx.com/)

More than "push one video to a dozen platforms". **It breaks publishing into checkable moves**: assets land locally and their paths are verified, accounts log in and are then checked read-only, content becomes a plan that waits for your confirmation, and only then does a real browser deliver it — with every result written down. One workbench covering 5 pages, 16 platform command groups and 19 agent skills, turning "can we publish, where, and what" from a verbal agreement into gates the system can actually stop on.

| Item | Value | Notes |
|---|---|---|
| Product name | OmniSocial | The social operations subsystem under OmniAiLab; the repository directory is `omni-social` |
| Version | v0.1.0 | Kept identical to `project.version` in `pyproject.toml`; release flow and records live in `CHANGELOG.md` |
| Publisher / Developer | Published by OmniAiLab, maintained by Mochiball | All public attribution uses OmniAiLab, never a personal identity |
| License | MIT (see [LICENSE](LICENSE)) | Use and redistribution are governed by that file; each skill under `skills/` follows the license in its own frontmatter, and third-party components keep their original licenses and notices |
| Three entry points | Web workbench / CLI `sau` / agent skills | The web app owns accounts, assets and batch publishing; the CLI owns precise single actions; skills own task routing and safety confirmation — all three share one publishing engine |
| Web backend | Python 3.10–3.12 + Flask 3.1 | Port `5409` by default; the code currently binds `0.0.0.0`, so change it to `127.0.0.1` for local-only use and add access control before exposing it |
| Web frontend | Vue 3 + Vite + Element Plus + Pinia | Port `5173` by default; the dark workbench visual spec lives in [design.md](design.md), with no blue default theme and no light admin template |
| Publishing engine | Per-platform implementations in `uploader/` | The single publishing engine: both web endpoints and agent skills call it, and nothing else re-implements browser automation, so two implementations never overwrite each other |
| Runtime dependencies | patchright / playwright + a local browser | Login and delivery go through a real browser; QR scans and human verification are completed by you, and the system never touches or stores account passwords |
| Data and sessions | SQLite `db/database.db` + `cookies/` | Everything stays on this machine and never enters version control; a cookie is an account credential, treat a leak as a hijacked account |
| Repository | [tomatoparkdao/omni-social](https://github.com/tomatoparkdao/omni-social) | Source, documentation and tests; the `main` branch is authoritative |

> **Three names, one trap, explained once**: the repository is `omni-social`, the product is `OmniSocial`, and the command is `sau`.
> The package name in `pyproject.toml` is still the upstream `social-auto-upload` (kept so the installable entry point keeps working — it is not the product name).
> **They are not duplicate names** — the directory is the repository, the product is the display name, and `sau` is the only command-line entry.


---

## Separate three things first: publishing targets, creation platform, execution engine

The sentence "post this video" actually carries three separate things, and mixing them causes mistakes:

- **Publishing target**: the delivery address of one of 17 platforms. It decides *where*, and implies no creation capability at all;
- **Creation platform**: OmniAiLab and only OmniAiLab. Images, copy, video, visual design and layout are all produced there;
- **Execution engine**: the browser automation inside `uploader/`. It decides *how* a file reaches the platform.

Treating a platform as a creation tool sends people elsewhere to generate content; treating a skill as the engine produces a second automation that fights `uploader/`; treating a plan as an execution publishes the content for real, and it cannot be taken back.

```bash
sau --help                      # 17 command groups: 16 platforms + 1 local article renderer
sau douyin --help               # only the actions and arguments Douyin really supports
sau xiaohongshu --help          # Xiaohongshu: login / check / upload-video / upload-note
```


## In one sentence

Hand it a batch of assets, one account and a draft, and it first turns them into a publishing plan awaiting confirmation — platform, content type, account, files, title, body, tags and time, item by item. After you confirm, it opens a real browser to deliver, and writes the outcome into a record you can check afterwards.

**It does not say "it is published". It says "this one returned a work URL / this one stopped at unverified"** — every task carries an explicit state, unknown is reported as unknown, and "it probably worked" is never dressed up as success.

| Scope | What it covers |
|---|---|
| **Applies · many platforms, many accounts** | The same assets delivered to 17 publishing targets; the CLI isolates sessions by account alias while the web app tracks login state per account |
| **Applies · semi-automatic and controllable** | Plan before execution: `/agent/plan` returns only a plan awaiting confirmation, `--prepare-only` uploads and fills without clicking publish, `check` reads login state without side effects |
| **Applies · notes and long-form** | Video, image-text notes and long articles are all in scope; Zhihu and Dayu insert inline images at their original positions, and Xueqiu handles long-form posts |
| **Not applicable (said plainly)** | No content creation (creation happens in OmniAiLab only), no password custody, no promise about platform review outcomes, no guarantee that a scheduled post fires, and no ability to bypass captchas or platform risk controls; rejection, account limits and content violations are decided by the platform |


## Three entry points, each with a boundary

| Entry | What you use it for | Boundary |
|---|---|---|
| **Web workbench** | Dashboard overview, account management, asset management, batch delivery from the publishing centre | Direct UI operation, best for daily work; batch publishing currently covers 4 platforms, everything else goes through the CLI or a skill |
| **CLI `sau`** | Precise single actions: login, check, upload video, upload note, upload article, verify result | Arguments come from `--help`; one action at a time, which suits scripting and troubleshooting |
| **Agent skills** | Turn a one-line task into a plan and route it to the right platform command | Explanation, routing and safety orchestration only — **skills never re-implement uploading** |


## Capability overview

**It is not "a pile of scripts that push files at platforms", but a publishing system that asks for a plan first, writes its judgement into the flow, and states plainly what it did not do.**

| Layer | What it gives you |
|---|---|
| **① Plan and execution are separated** | `/agent/plan` accepts natural language and returns only `awaiting_confirmation` plus `publish_executed: false`, together with the missing fields; real delivery needs a separate, explicit instruction. Planning and execution each have their own entry, never one shared click. |
| **② One publishing engine** | `uploader/` is where every platform's delivery is implemented and `myUtils/` carries login and helper logic; web endpoints and skills only call into it. Adding a platform means adding the uploader, the CLI group, the skill, tests and docs — miss one and the platform is not really supported. |
| **③ Accounts are local assets** | Sessions land under `cookies/` per platform and account metadata lives in SQLite; the CLI separates multiple identities on one platform by account alias. The system never asks for a password — QR scans and human verification are yours to complete. |
| **④ Read-only checks come first** | Every platform has `check`; Facebook, Instagram, Zhihu, Xueqiu and Dayu also offer `verify`, which re-reads a saved work URL without any second submission. |
| **⑤ A rehearsal is cheaper than regret** | Dayu, Xueqiu and Zhihu video/article commands support `--prepare-only`: upload, fill the editor, inspect, and stop before the publish button. Changing copy is far cheaper before the post than after it. |
| **⑥ Results are reported honestly** | Success requires a work URL or an explicit success state; timeouts, unresolved dialogs and unreadable links are marked unverified while keeping the facts of what did happen — no resubmission, no assumed success. |
| **⑦ Visuals follow the product** | The 5 pages follow the OmniAiLab dark workbench spec: near-black canvas, `#c8ff00` accent, left navigation, with no default blue controls and no light admin template. |


### Platform matrix (17 publishing targets)

| Platform | Content types | Schedule / batch | CLI command | Login and limits |
|---|---|---|---|---|
| Douyin | Video · Note | Schedule ✅ · Web batch ✅ | `sau douyin` | QR login; supports self-declaration, collections, product links and both cover ratios, and its arguments move with page revisions |
| Kuaishou | Video · Note | Schedule ✅ · Web batch ✅ | `sau kuaishou` | QR login; the publish dialog carries schedule and location options, so verify title and topics before submitting |
| Xiaohongshu | Video · Note | Schedule ✅ · Web batch ✅ | `sau xiaohongshu` | QR login; notes go through the image-list entry while video has its own command, and image order is display order |
| Bilibili | Video | Schedule ✅ · Web batch — | `sau bilibili` | Session maintained by biliup; video only, no notes or articles, and partitions and tags follow the submission type |
| WeChat Channels | Video | Schedule ✅ · Web batch ✅ | `sau tencent` | QR login; a human verification dialog often appears, so someone must be present or the task waits at the dialog |
| Baijiahao | Video | Schedule — · Web batch — | `sau baijiahao` | Video only; the session comes from the browser session and must be renewed when it expires, with no scheduling or batch support |
| Dayu | Video · Article | Schedule ✅ · Web batch — | `sau dayu` | Separate commands for video and article; `--prepare-only` uploads and fills without publishing, which suits layout checks |
| Alipay Life Account | Video | Schedule — · Web batch — | `sau alipay` | Video only; the session lives under `cookies/alipay_uploader`, and switching accounts means another alias |
| Weibo | Video | Schedule — · Web batch — | `sau weibo` | Video only; multiple account aliases isolate sessions on the same platform, and post and topic length follow platform limits |
| Hupu | Video | Schedule — · Web batch — | `sau hupu` | Video only; a community publishing entry where title, topics and section need checking item by item, and a wrong section can only be fixed by hand |
| YouTube | Video | Schedule in progress · Web batch — | `sau youtube` | Video only; patchright ignores the system proxy, so set `YT_PROXY` in `conf.py` when the network is restricted |
| TikTok | Video | Schedule ✅ · Web batch — | Skill only, no CLI | Uses the existing Chrome uploader in this repository; there is no `sau` group, so read `skills/tiktok-upload` for arguments and steps |
| Xueqiu | Article | Schedule — · Web batch — | `sau xueqiu` | Long-form posts only; `--prepare-only` saves a remote draft, so a rehearsal is not traceless and the draft needs cleaning up |
| Zhihu | Video · Article | Schedule experimental · Web batch — | `sau zhihu` | Inline images are inserted at their original positions; the scheduling window is 30 minutes to 48 hours, Beijing time |
| Facebook | Video · Note | Schedule — · Web batch — | `sau facebook` | Personal timeline posts; video and note have separate commands, plus verify and delete, and deletion is permanent |
| Facebook Page | Video · Note | Schedule ✅ · Web batch — | `sau facebook-page` | Page publishing goes through Business Suite; scheduling and batch are supported, and page admin rights are required |
| Instagram | Video · Note | Schedule — · Web batch — | `sau instagram` | Web entry only; images and video have separate commands, an independent logged-in session is required, and there is no mobile delivery |

> `✅` means the current code provides that entry and `—` means it does not; "in progress" and "experimental" are not stable capabilities. Real publishing needs you to complete login and authorisation yourself, and **no real publishing runs without explicit confirmation**.


### Command surface (sau)

| Action | Shape | When to use it |
|---|---|---|
| `sau <platform> login` | Opens a visible browser and writes the session under `cookies/` after a QR scan or human verification | First-time onboarding or an expired session; someone must be present for this step |
| `sau <platform> check` | Read-only check of login state and page identity, returning the currently bound account | Before every publish, to confirm "this is the account I meant"; it never triggers delivery |
| `sau <platform> upload-video` | Uploads and publishes one video, with `--schedule` and dual-ratio `--thumbnail` options | Precise single delivery; arguments differ per platform, so read `--help` first |
| `sau <platform> upload-note` | Uploads an image-text note where `--images` order is display order | Xiaohongshu, Douyin and Kuaishou notes; swapping images means changing arguments, not renaming files |
| `sau <platform> upload-article` | Publishes long-form from a source file, inserting inline images at their original positions | Zhihu, Dayu and Xueqiu; keep long bodies in files and pass only the path on the command line |
| `sau <platform> verify` | Read-only re-check against a saved work URL, with no second submission | When you need to know whether yesterday's post actually went out — and always before retrying |


## Quick start

> **First time here? These five steps are enough.** It does not open with "what do you want to post"; it collects what you have on hand, whether the account is logged in, and where the copy lives.

### 1. What to install: four pieces, none optional

| Component | Version | How to install | What breaks without it |
|---|---|---|---|
| Python environment | 3.10–3.12 (<3.13) | `python -m venv .venv`, then install `requirements.txt` with that interpreter | Neither the backend nor the CLI starts; 3.13 is outside the supported range and dependency installation fails outright |
| Frontend dependencies | Node.js 22+ (24 currently) | Run `npm install` inside `sau_frontend` | The web workbench renders a blank page; the CLI and publishing still work normally |
| Article renderer | Node.js 22+ | Run `npm install` again inside `utils/article_renderer` | Long-form rendering fails, Markdown to HTML does not work, and Zhihu or Dayu articles cannot be published |
| Browser engine | Chromium shipped with patchright | `patchright install chromium`, with a proxy configured first if the network is restricted | Login and publishing report "browser not found", the symptom most often mistaken for broken code |

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
cd sau_frontend && npm install
cd ..\utils\article_renderer && npm install
```

> **Do not stop after installing Python.** The frontend, the article renderer and the browser engine are three independent dependencies; skipping one produces a blank workbench, a failed long-form render or a missing browser — all of which look like "the code is broken".

### 2. Where assets come from (pick one)

1. **Point at local files** — `--file` or `--images` in the CLI, or upload through the asset page in the web app; the system only checks existence and size and never modifies the source file.
2. **Create in OmniAiLab, then land locally** — image, video and copy creation happen on the platform; download the assets and connect them as above. This system provides no creation entry.
3. **Already in a local folder** — publishing only references paths, so **do not move or delete source files after publishing**; scheduled tasks would lose their inputs.

> **One question worth answering carefully**: which platforms and accounts is this batch actually for? If that stays open, every downstream argument gets reworked — title length, cover ratio, tag rules and scheduling windows all differ per platform.

### 3. Start command

On Windows, double-click `start-omnisocial.bat`. The script checks the environment, starts the backend and the frontend, and opens:

```text
http://127.0.0.1:5173
```

Stop the services with `stop-omnisocial.bat`. Manual start and command-line use:

```bash
python sau_backend.py                                  # backend on 5409
cd sau_frontend && npm run dev -- --host 127.0.0.1     # frontend on 5173
sau douyin check --account creator                     # read-only CLI check
```

### 4. Two things to settle before publishing

- **Is this a rehearsal or a real publish?** Rehearse with `--prepare-only` (Dayu, Xueqiu, Zhihu) or by reading the plan first; a real publish consumes the account's daily quota and most platforms offer no one-click undo.
- **Whose account is it, and who owns the outcome?** One alias maps to one real account, and posting to the wrong one is the most common production incident; run `check` first and confirm the identity on the page is the one you intend.

### 5. You only ever answer two kinds of sentence

1. **Release the execution** — state platform, account and content, or it will not move:

```text
Publish now: Douyin creator, videos/demo.mp4, title "Sample title"
```

2. **Ask for a change and point at it** — it stays at the plan stage and reworks in place:

```text
Change the title to "Dynamic menus in three minutes" and drop the second tag
Swap in the landscape cover
```

**When you only want one capability**, name it directly instead of running the whole flow:

| What you want | Say this | What you get back |
|---|---|---|
| Login state only | `Check Douyin creator's login state, do not publish` | A read-only `check` result with page identity; no delivery action at all, safe to repeat |
| A plan only | `Give me a publishing plan, do not publish yet` | A plan awaiting confirmation: platform, account, files, title, tags, time and missing fields, with nothing guessed or auto-filled |
| A rehearsal only | `Upload and fill this Zhihu draft, do not click publish` | A `--prepare-only` run so you can inspect layout and image order before deciding |
| One single post | `Post demo.mp4 to Xiaohongshu creator, title as drafted` | A single delivery result with a work URL, and a clear stop point if it fails |
| A result check only | `Verify whether yesterday's video actually went out` | A read-only verdict from the saved URL, with no resubmission and no second quota use |
| Arguments only | `List the arguments the Dayu article command supports` | The real arguments and defaults, straight from the command's own `--help` output |


---

## Pipeline overview

| Stage | Name | Stage output | Gate |
|---|---|---|---|
| P1 | Asset intake | Local asset files, asset records, size and format check results, plus a "is the path still there" confirmation; any missing item stops the flow | G1 asset confirmation: file exists, single file ≤160MB, path inside the authorised scope |
| P2 | Account login | Platform session, account alias, page identity and the bound account, all stored locally under `cookies/` | G2 login confirmation: `check` passes read-only and the page identity matches the target account |
| P3 | Content assembly | Title, body, tags, covers, note image order, long-form source and image positions, mapped onto real arguments | G3 content confirmation: item-by-item human review, missing fields stop the flow, never auto-written |
| P4 | Plan generation | A publishing plan awaiting confirmation, a missing-field list, platform differences and flagged risks | G4 plan confirmation: the user explicitly releases it; without that the flow never reaches delivery |
| P5 | Execution | A single delivery or a web batch task, schedule configuration, execution log and the exact stop point | G5 real-publish confirmation: an explicit "publish now", with no defaults and no vague answers |
| P6 | Result check | Work URLs, success or unverified states, failure reasons and the re-check required before retrying | G6 archive confirmation: links and account binding are filed, and failures are re-checked rather than retried |

**Six stages are the rhythm; 19 skills are the roles — do not conflate them.** One platform skill serves several stages: `login` at P2, `check` at P2 and before P5, `upload-*` at P5; the manager skill spans P3–P6.

### Seven non-negotiable rules

| ID | Rule | Why |
|---|---|---|
| **R1** | Plan by default; never publish for real without instruction | A wrong plan costs time, a wrong publish costs an apology; the default must sit on the safe side |
| **R2** | Real publishing requires item-by-item confirmation of platform, account, asset, title, body, tags and time | Any one of those seven going wrong produces public content that cannot be recalled |
| **R3** | `uploader/` is the only publishing engine; skills only explain, route and orchestrate | With two automations alive, fixing one leaves the other quietly broken and nobody knows where |
| **R4** | Never request, store or write passwords, tokens or cookies into the repo, docs or logs | A credential that reaches version control is leaked forever; changing the password does not rewrite history |
| **R5** | Asset paths must exist before publishing and source files must not move afterwards | Scheduled tasks and batch queues read by path; a broken path means an empty or failed delivery |
| **R6** | Report failures, timeouts and unknown results honestly; never resubmit blindly | A retry becomes a duplicate post; a second item on the platform is harder to handle than a failure |
| **R7** | Creation happens only in OmniAiLab; a publishing platform is not a creation platform | A platform is only a delivery address; treating it as a creation entry misleads users, adds compliance risk and makes asset provenance untraceable |


## Per-stage operating notes

| Stage | What you decide | Common commands | Watch out for |
|---|---|---|---|
| **P1** Asset intake | Whether the files are right, whether size is within limits, whether the format is accepted | Web asset page / `--file`, `--images` | The upload ceiling is 160MB per file; keep assets where they are and do not reorganise folders before publishing |
| **P2** Login | Whether the logged-in account is the intended one | `login`, `check` | QR scans and human verification are yours to complete; never hand a cookie to someone else to log in for you |
| **P3** Content assembly | Title length, tag conventions, cover ratio, note image order | Each platform's `upload-*` arguments | One draft reused across platforms must be trimmed per platform; portrait and landscape covers use different arguments |
| **P4** Plan | What is missing and where platforms differ | `/agent/plan`, the manager skill | `publish_executed` is always `false` in a plan; saying "ok" does not start anything |
| **P5** Execution | Publish now, or rehearse first | `upload-video`, `upload-note`, `upload-article`, `--prepare-only` | Scheduling is not set-and-forget: the CLI process must stay alive until the trigger time, and web batches need the backend running |
| **P6** Result check | Whether it actually went out | `verify`, work URLs, execution logs | When the URL cannot be read, keep the fact of submission and mark it unverified; never repost just to feel better |


## Plan first: /agent/plan and --prepare-only

**Neither of these publishes anything, and neither is a no-op**: one produces a plan awaiting confirmation, the other really uploads files and fills the editor, missing only the final click.

| Step | What happens | Where it lives |
|---|---|---|
| Natural-language plan | Accepts one sentence and returns `awaiting_confirmation` with a missing-field list, without turning it into an execution | `/agent/plan` in `sau_backend.py`; it always returns `publish_executed: false` |
| Plan fields | Platform, content type, account, files, title, body, tags and time — eight in total | If any of the eight is missing the plan is incomplete and must not reach P5; the system does not guess |
| Editor rehearsal | Uploads and fills, then stops before the publish button | `--prepare-only`: Dayu video and article, Xueqiu article, Zhihu video and article |
| The real cost of a rehearsal | A Xueqiu rehearsal saves a remote draft; a Zhihu rehearsal uploads inline images | A rehearsal is not traceless — drafts and images stay on the account and must be cleaned up |
| Read-only verification | Re-reads a result from a saved URL without creating anything | `verify`: Facebook, Instagram, Zhihu, Xueqiu, Dayu |

**Three lines that must not be crossed**: never call a delivering command without an explicit "publish now"; keep credentials on this machine, out of the repository, out of docs and out of logs; when the result is unknown, say unknown — **never write "probably published" as "published"**.


## Pitfalls

Hit any one of these and you lose a post at best, an account at worst.

| # | Pitfall | Consequence | How to avoid it |
|---|---|---|---|
| 1 | Treating "ok" or "sure" as publishing authorisation | The content really goes live and most platforms cannot undo it | Authorisation must name platform, account and content; vague answers count as "not authorised", with no charitable guessing or filling in |
| 2 | Treating `/agent/plan` as an execution entry | You think it published; nothing moved | It always returns `publish_executed: false`; real publishing goes through the `upload-*` commands |
| 3 | Committing cookies or account files | The account is hijacked and a password change cannot rewrite history | `cookies/` and `db/` never enter the repository; treat credentials as keys, and assume one leak is a full leak |
| 4 | Assuming the backend only listens locally | The code binds `0.0.0.0`, so anyone on the same network can reach it | Change it to `127.0.0.1` for local use, and add authentication before exposing it |
| 5 | Building the environment on Python 3.13 | Dependencies fail to install or crash at runtime | The supported range is 3.10–3.12; `requires-python` pins the upper bound — do not force it |
| 6 | Running login before installing the browser engine | "Browser not found", easily mistaken for broken code | Run `patchright install chromium` first, and configure the proxy first if the network is restricted |
| 7 | Connecting to YouTube directly on a restricted network | Endless timeouts that look like an account problem | patchright ignores the system proxy; set `YT_PROXY` in `conf.py` to your local proxy port |
| 8 | Only running `npm install` at the repository root | Long-form rendering fails | The article renderer lives in `utils/article_renderer` and needs its own install |
| 9 | Tidying the asset folder before publishing | Scheduled tasks find no files at trigger time | Keep asset paths fixed: no moving, renaming or deleting before publishing finishes |
| 10 | Assuming web batch covers every platform | Batch tasks for the other 13 platforms never run | Web batch covers 4 platforms; run the rest one by one through the CLI or a skill |
| 11 | Rewriting automation because a skill was mistaken for the engine | Two implementations fight and overwrite each other | Skills explain, route and orchestrate; delivery logic lives only in `uploader/` |
| 12 | Treating scheduling as set-and-forget | Nothing fires and the task fails silently | The CLI process must stay alive until the trigger time, and web batches need the backend running; shutting the machine down breaks the promise |
| 13 | Uploading a Zhihu video under 100KB | Rejected before upload | Check the file size first; finish the edit before publishing instead of retrying the same file |
| 14 | Treating Zhihu's experimental scheduling as stable | Nothing fires, or the time window is rejected | The window is 30 minutes to 48 hours ahead, Beijing time; publish important content manually |
| 15 | Believing `--prepare-only` leaves no trace | Xueqiu keeps a remote draft and Zhihu keeps uploaded images | Clean drafts on the account afterwards, and never rehearse with assets that should not appear |
| 16 | Waiting on the verification dialog for Channels or Dayu | The task sits at the dialog until it times out | These platforms need a human to click through; do not schedule them unattended |
| 17 | Rerunning immediately after a failure | A duplicate item appears on the platform | Run `verify` first; only repost once you have confirmed it did not succeed, and note why in the log |
| 18 | Not using aliases for multiple accounts on one platform | Publishing to the wrong account | One account, one alias; run `check` for page identity, because a wrong account is harder to undo than a wrong time |
| 19 | Uploading a video above 160MB | The request is rejected by the backend | Compress or split; the web upload ceiling is in `MAX_CONTENT_LENGTH`, so do not only change the frontend |
| 20 | Copying ports from docs when they disagree with the code | The whole troubleshooting path goes the wrong way | Treat `sau_backend.py` as the source of truth for ports and binding, and update docs with the code |


## Repository layout

```
omni-social/                     ← repository root
├── README.md / README_EN.md     Chinese and English docs (this file)
├── AGENTS.md                    Collaboration rules: skill routing, safety checks, implementation boundaries
├── OMNISOCIAL.md                Product positioning and local-run notes
├── design.md                    Dark workbench visual and interaction spec
├── CHANGELOG.md                 Version history and release flow
├── conf.example.py              Configuration template (proxy / Chrome path / debug switch)
├── sau_backend.py               ★ Flask web API and service entry (port 5409)
├── sau_cli.py                   ★ CLI entry: registration and dispatch only
├── sau_commands/                Per-platform command groups (16 platforms + article renderer)
├── uploader/                    ★ The single publishing engine: login and delivery per platform
│   ├── douyin_uploader/         Douyin, Kuaishou, Xiaohongshu, Bilibili, Channels…
│   └── meta_uploader/           Facebook, Instagram and scheduling logic
├── myUtils/、utils/             Login, cookies, assets, article rendering and shared helpers
│   └── article_renderer/        Long-form rendering (needs its own npm install)
├── sau_frontend/                Vue 3 + Vite admin UI (port 5173)
│   └── src/views/               Dashboard / accounts / assets / publishing centre / about
├── skills/                      19 agent skills (manager + platforms + upstream)
├── db/                          SQLite schema and local database (not committed)
├── cookies/                     Per-platform sessions (not committed, treat as keys)
├── docs/                        Development, API, platform modules, skill architecture and migration notes
├── examples/                    Sample assets and scripts
└── tests/                       Platform modules, CLI, web interaction and utility tests (17 modules)
```

---

## Runtime artefacts and data

| Type | Location | Notes |
|---|---|---|
| Sessions | `cookies/<platform>/` | One directory per platform; equivalent to account credentials, never committed, never shared, never logged anywhere |
| Accounts and assets | `db/database.db` | A single SQLite file; backup is a copy and restore is an overwrite, so stop the service before migrating to avoid a half-written database, and run `check` once after restoring |
| Uploaded assets | `media/`, `videos/`, `static/` | Local files; publishing references paths only, so do not move them before publishing finishes or scheduled and batch tasks lose their inputs |
| Runtime logs | `logs/` | The first stop for troubleshooting; before pasting a log anywhere, confirm it holds no cookies, account data or sensitive asset details |
| Frontend build | `sau_frontend/dist/` | Output of `npm run build`; static hosting serves from here, so rebuild after frontend changes |
| Article rendering output | `utils/article_renderer/` outputs | Intermediate body produced from long-form sources; inline images still follow their positions in the source |
| Temporary upload files | System temp directory and the `media/` cache | The web app writes to disk before delivering; clean these periodically and never treat them as asset sources |


## FAQ

**Will it publish on its own?**
No. It plans by default; `/agent/plan` always returns an unexecuted state and `--prepare-only` never clicks publish. Real delivery needs an explicit instruction naming platform, account and content.

**Do I have to log in through a browser?**
Yes. These platforms expose no delivery API, so login goes through a real browser QR scan or human verification; the session stays in local `cookies/` and an expired session only needs a fresh login, not a config change.

**Can scheduled posting run unattended?**
Depends on the platform. Scheduling relies on a live process and an interactive page, and platforms like WeChat Channels still show a human verification dialog; unattended runs only suit platforms you have already validated, and someone must still check the results.

**Do the web app and the CLI conflict?**
No, they call the same `uploader/`. They differ in entry: the web app suits daily batch work, the CLI suits precise single actions and troubleshooting, and skills suit turning one sentence into a plan.

**What do I do first when a publish fails?**
Run `verify` or check the account dashboard and confirm whether it actually succeeded — **do not rerun first**. Repost only after confirming failure, and record the reason in the changelog or an issue.

**Can I add a new platform?**
Yes, but deliver all five pieces together: the `uploader/` implementation, the `sau_commands/` group, `skills/<platform>-upload`, tests and docs. Miss any one and the platform is only "apparently supported".

**How does it justify saying a post went out?**
With a work URL or an explicit success state. An unreadable link becomes "unverified" while the fact of submission is kept; the system never offers "it probably worked" as a conclusion.

**Does changing the frontend styling affect publishing?**
No. Visual work touches only the presentation layer of `sau_frontend`; APIs and delivery logic stay untouched, and section 8 of `design.md` is the acceptance checklist for that boundary.


## Runtime and dependencies

| Purpose | What is used | Notes |
|---|---|---|
| Web backend | Flask 3.1 + flask-cors | Port 5409 by default; the bind address is at the end of `sau_backend.py`, narrow it to localhost as needed and add auth before exposing it |
| Browser automation | patchright (primary), playwright (a few legacy modules) | Both need a browser engine; login and delivery depend on it, and a missing engine fails every platform at once, which looks like "all the code broke" |
| Frontend | Vue 3 + Vite + Element Plus + Pinia | Dark workbench; see `design.md`, with no blue default theme and no light admin template |
| Long-form rendering | Node.js 22+ in `utils/article_renderer` | Turns Markdown / HTML / TXT into a body that can be pasted into editors, inserting images at their source positions; needs a separate install |
| Video handling | biliup for Bilibili, direct page upload everywhere else | No local transcoding; format, bitrate and duration limits follow each platform's own rules |
| Data storage | SQLite (single file) | No server-side database; backup and migration are file operations, and one file moves the whole state |
| Creation capability | **OmniAiLab platform** (the only authorised party) | Images, video, copy, visual design and layout are produced on the platform; this system only receives assets and delivers them |


## Hardware requirements

| Item | Minimum | Recommended | Notes |
|---|---|---|---|
| OS | Windows 10 / 11 | Match the environment the target platforms expect | The start scripts and paths are written for Windows; Linux and macOS need their own launchers |
| Python | 3.10 | 3.11 / 3.12 | 3.13 is outside the supported range and installation fails; use `requirements.txt` rather than installing by hand |
| Node.js | 22 | 24 | The frontend and the article renderer each need an `npm install`; do both, not just one |
| RAM | 4 GB | 8 GB or more | Every browser instance is memory-hungry; run batch jobs sequentially instead of stacking them until memory runs out |
| Disk | 2 GB | 20 GB or more (assets and video) | Video dominates; the per-file upload ceiling is 160MB, so size the total and the cleanup plan before a batch run |
| Network | Reachable target platforms | Per-platform proxy (YouTube, for example) | patchright ignores the system proxy, so configure it explicitly in `conf.py` or requests keep timing out |
| Accounts | Real accounts on each platform | One alias per account | No accounts are provided, no registration or verification is done for you, and platform limits are decided by the platform |
| Display | A desktop session for QR login | A local desktop session | Headless mode can deliver with an existing session, but first login and human verification need a visible window |

---

## Brand and creative-tool exclusivity

**Public naming**: OmniSocial / OmniSocial Social Media Operations System; repository directory `omni-social`; command entry `sau`.
The official platform is the [China site](https://www.omniailabx.com/) and the [international site](https://www.omniailab.cn/) only.

**AI image, copy, video and visual design have exactly one upstream: OmniAiLab.** The only authorised party in the creative capability domain is the OmniAiLab platform; when the platform is unavailable this system **does not generate and does not reroute** — it keeps delivering assets already on disk. Names such as Douyin, Xiaohongshu, WeChat Channels, Bilibili, YouTube and TikTok denote **publishing targets only** and imply no recommendation of a creation tool.

| Boundary | What it means in practice | Where it is enforced |
|---|---|---|
| Allowed | Receive assets created in OmniAiLab and deliver them to the platforms and accounts the user explicitly names | Per-platform implementations in `uploader/`, which only read local files and generate no content |
| Allowed | Explain publishing arguments, content limits and risk-control differences so content is posted correctly and stably | Each `skills/<platform>-upload` and `docs/PLATFORM-UPLOADERS.md`, kept consistent with the repository |
| Not allowed | Guiding users to other image, video or copywriting generation platforms in the UI, docs or skills | Section 1.1 of `design.md` and `skills/omni-social-manager/SKILL.md`, applied repository-wide |
| Not allowed | Claiming creative capabilities this system does not have, or presenting a platform review result as a system guarantee | The safety checks and implementation boundaries in `AGENTS.md`, with no exaggeration and no false reassurance |


## Getting help

When something breaks, or you want to file a bug or a feature request, work down this list — it is the shortest path:

| Channel | Address | Best for |
|---|---|---|
| **Local development docs (offline, fastest)** | [docs/LOCAL-DEVELOPMENT.md](docs/LOCAL-DEVELOPMENT.md) | Environment, dependencies, start and stop; most Windows pitfalls are here, readable offline with the troubleshooting order |
| **CLI guide** | [docs/CLI.md](docs/CLI.md) | Commands, arguments and examples, grouped by platform; faster than reading source and safer than trusting memory |
| **Web API and platform modules** | [docs/WEB-API.md](docs/WEB-API.md) · [docs/PLATFORM-UPLOADERS.md](docs/PLATFORM-UPLOADERS.md) | API fields and per-platform implementation locations, to trace exactly where a run broke |
| **Built-in command help** | `sau <platform> <action> --help` | The only authoritative source for arguments; when docs disagree, this wins |
| **Repository issues** | [tomatoparkdao/omni-social/issues](https://github.com/tomatoparkdao/omni-social/issues) | Bug reports and platform requests; logs plus the exact command locate the problem fastest |
| **OmniAiLab official** | [China site](https://www.omniailabx.com/) · [International site](https://www.omniailab.cn/) | Creation, accounts and platform capabilities; publishing questions still go through the channels above |

> Before asking, skim the [pitfalls](#pitfalls). Include the **platform, account alias, exact command, exact error and a log excerpt**, and confirm the log holds no cookies or sensitive account data — that usually settles it in one round.


## Documentation map

| To understand | Read | What is inside |
|---|---|---|
| **How to run it locally** | [docs/LOCAL-DEVELOPMENT.md](docs/LOCAL-DEVELOPMENT.md) | Virtual environment, dependencies, start/stop scripts and ports; the full Windows walkthrough, common errors, port conflicts and how to roll back a bad dependency install |
| How to use the commands | [docs/CLI.md](docs/CLI.md) | The `sau` command tree, arguments and examples, grouped by platform and by video / note / article |
| How to call the API | [docs/WEB-API.md](docs/WEB-API.md) | Flask routes, fields and response shapes, including the plan endpoint, batch publishing and asset management |
| Where platform code lives | [docs/PLATFORM-UPLOADERS.md](docs/PLATFORM-UPLOADERS.md) | Locations, entries and call relationships of each uploader, and which places to touch when adding a platform |
| Why the layout is like this | [docs/PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md) | Directory responsibilities, dependency direction and which layer a new module belongs to |
| How skills are organised | [docs/SKILLS-ARCHITECTURE.md](docs/SKILLS-ARCHITECTURE.md) | The 19 skills, the manager-to-platform routing, load order and how to add one more |
| How skills are distributed | [docs/skill-distribution.md](docs/skill-distribution.md) | Where each host expects them, why TikTok is skill-only, plus install, verification and update steps |
| How long-form rendering works | [docs/article.md](docs/article.md) | HTML / Markdown / TXT source formats, image position conventions and renderer installation |
| What the visual spec is | [design.md](design.md) | Colour tokens, components, page mapping and the section 8 acceptance checklist |
| Where it came from | [docs/MIGRATION-REPORT.md](docs/MIGRATION-REPORT.md) | Upstream scope, what was kept, what was not migrated, and how licenses and attribution were handled |
| What has been fixed | [docs/REPAIR-LOG.md](docs/REPAIR-LOG.md) | Item-by-item repair records and full test results, usable as a regression baseline |
| How versions ship | [CHANGELOG.md](CHANGELOG.md) | Change records, version synchronisation and the five-step release flow |

---

## Contributing

This repository is open source under **MIT** (full text in [LICENSE](LICENSE)) and contributions are welcome. One premise applies: **extend publishing capability and documentation only — never add a second publishing engine, and never steer users to another creation platform.**

| Direction | What it covers | Where it goes |
|---|---|---|
| New platform | The uploader implementation, command group, skill, tests and docs delivered together | `uploader/`, `sau_commands/`, `skills/`, `tests/`, `docs/` |
| Platform behaviour fixes | Broken selectors after a page revision, changed dialog order, insufficient waits | The matching `uploader/<platform>/`, plus a reproducible test |
| Docs | Command arguments, ports, dependencies, failure symptoms and fixes; when docs and code disagree, fix the docs first, then the code, and keep all three copies in sync with working anchors | `docs/`, `README.md`, `README_EN.md` |
| Visual fixes | Hierarchy, contrast and state colours of the dark workbench; no blue default theme and no light admin surface | `sau_frontend/`, accepted against section 8 of `design.md` |
| Security | Credential leaks, unauthorised access, paths that publish without confirmation | Open an issue marked security; never paste credentials in a public PR |

**Run these before you finish**:

```bash
.venv\Scripts\python.exe -m pytest tests -q      # full suite (last recorded run: 137 passed / 71 subtests)
cd sau_frontend && npm run build                  # the frontend build must pass
git diff --check                                  # whitespace and conflict-marker check
```


## License and legal

| Item | Content |
|---|---|
| Repository license | **MIT**, full text in [LICENSE](LICENSE) |
| Skill licenses | Each file under `skills/` follows its own frontmatter; `omni-social-manager` is MIT-0 |
| Upstream | Migrated from the `social-auto-upload` source; the original license and copyright files are retained, and the scope is recorded in [docs/MIGRATION-REPORT.md](docs/MIGRATION-REPORT.md) |
| Attribution | Public attribution is OmniAiLab with developer Mochiball; upstream and third-party notices must not be removed |
| No false authorship | Upstream code and third-party components are never presented as original OmniAiLab work |
| Accounts and credentials | Cookies, tokens and account files are sensitive: never commit, share or log them; the risk of a leak sits with the user |
| Platform terms | Each platform sets its own terms, publishing rules and automation limits, and users must comply with them |
| Disclaimer | The system does not guarantee review approval, scheduled delivery or any platform position; the authors and maintainers accept no liability for losses caused by content violations, account restrictions or data loss; using it means you have read this clause |

---

## Credits

- Published and maintained by **OmniAiLab** ([omniailabx.com](https://www.omniailabx.com/))
- Developer: **Mochiball**
- Built by migrating and adapting **social-auto-upload**, keeping its directory layout, CLI, web front and back ends and platform upload modules, with the original license and copyright notices intact.
- Platform login and delivery rely on a real browser driven by **patchright / playwright**; Bilibili delivery uses **biliup**. These are execution-layer tools and imply no endorsement of any third-party creation platform.
- All creative capability is provided by **OmniAiLab**; this repository ships no generative model and never reroutes to a third-party generation platform.

---

<div align="right">

[简体中文](README.md) ｜ **English**

</div>

> © OmniAiLab ｜ Developer: Mochiball ｜ OmniSocial Social Media Operations System (omniailabx.com) — unauthorised copying, redistribution or sublicensing is prohibited.

