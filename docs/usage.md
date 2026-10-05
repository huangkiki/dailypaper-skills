# 使用指南

[返回产品介绍](../README.md) · [Agent 接入细节](agents.md) · [评分实测](jev-benchmark.md)

## 快速开始

### 1. 准备运行环境

- 一个支持 Skills，或能读取本地指令文件的 Agent；需要文件读写、命令执行和网络访问能力。
- **Python 3.10+**、Git、`curl`。
- PDF 文字 / 图片提取需要 **Poppler**：macOS 可用 `brew install poppler`；Ubuntu / Debian 可用 `sudo apt install poppler-utils`。Windows 安装后，将 `pdftotext`、`pdfimages` 加入 `PATH`。
- **Obsidian 可选**：产物本身是 Markdown；Obsidian 更适合浏览双向链接、概念库和目录页。
- **Zotero 可选**：仅使用自己的 Zotero 文献库时需要。

核心脚本使用 Python 标准库，无需模型 SDK。语义评分需要 **TypeSafe API key**；点评与精读使用宿主 Agent 的模型。

### 2. 安装到你使用的 Agent

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills

# 选择你使用的 Agent；下面以 Codex 为例
python3 install.py --agent codex
```

| Agent | `--agent` 参数 | 个人技能目录 |
| --- | --- | --- |
| Claude Code | `claude` | `~/.claude/skills/` |
| Codex | `codex` | `~/.agents/skills/` |
| Cursor | `cursor` | `~/.cursor/skills/` |
| GitHub Copilot | `copilot` | `~/.copilot/skills/` |
| Gemini CLI | `gemini` | `~/.gemini/skills/` |
| OpenCode | `opencode` | `~/.config/opencode/skills/`，遵循 `XDG_CONFIG_HOME` |
| OpenClaw | `openclaw` | `~/.openclaw/skills/` |
| 识别共享目录的 Agent | `agents` | `~/.agents/skills/` |

**Windows PowerShell** 使用相同安装器，将命令里的 `python3` 换成 `py -3`（或可用的 `python`）。路径由 Python 处理，不需要 Bash 或符号链接。

也可以指定多个 Agent，或者直接指定技能目录：

```bash
python3 install.py --agent claude codex
python3 install.py --target "/path/to/project/.agents/skills"

# 先查看安装计划；不写入文件
python3 install.py --agent codex --dry-run
```

安装器会完整复制七个技能及 `_shared`，保留它们的相邻目录关系。**不要只复制单个 Skill**，也不要让通用安装工具漏掉 `_shared`。多个 Agent 若已经识别同一个目录，只安装一份即可。

### 3. 配置并开始使用

首次使用，创建一份跨 Agent 共用的个人配置：

```bash
python3 skills/_shared/user_config.py --init
```

它会打印配置路径，默认是 `~/.config/dailypaper-skills/user-config.json`。已有文件不会覆盖。编辑其中的 `paths.obsidian_vault` 和研究关键词，或让 Agent 帮你配置：

```text
帮我配置 dailypaper-skills。我的笔记库在 /path/to/ObsidianVault，
研究方向是 robot learning、VLA、diffusion policy。请使用跨 Agent 的共享配置。
```

在启动 Agent 的环境中设置 `TYPESAFE_API_KEY`（不要写进配置文件或提交到 Git）：

```bash
export TYPESAFE_API_KEY="你的 TypeSafe API key"
```

```powershell
$env:TYPESAFE_API_KEY = "你的 TypeSafe API key"
```

默认使用固定版本 `jev-1.13.0`，按标题与摘要打语义相关性分，每天最多推荐 10 篇。没有密钥时会明确报错；需要纯关键词模式，可把 `daily_papers.ranking.backend` 改为 `keyword`。升级不会覆盖已有个人配置，因此老用户需手动更新 `top_n`、`research_interests` 和 `ranking`。

重新启动 / 刷新 Agent 会话后，输入 `今日论文推荐`。在 Claude Code 中也可显式输入 `/daily-papers`，Codex 中可输入 `$daily-papers`。这些是**对话指令，不是终端命令**。

已有用户：原来的 `_shared/user-config.json` 和 `user-config.local.json` 仍然有效。迁移共享配置时，从原安装目录运行 `user_config.py --init`，可保留原来的个人设置；无需切换到 `codex+humanoid` 分支才能使用 Codex。

## 日常怎么用

| 想做什么 | 对 Agent 说 |
| --- | --- |
| 今天的新论文 | `今日论文推荐` |
| 补看几天 / 一周 | `过去3天论文推荐` / `过去一周论文推荐` |
| 单篇精读 | `读一下这篇论文 https://arxiv.org/abs/2509.24527` |
| 快速了解本地 PDF | `快速看一下这篇论文 /path/to/paper.pdf` |
| 判断方法的局限 | `批判性分析这篇论文 /path/to/paper.pdf` |
| 读取 Zotero 文献 | `读一下 Zotero 里的 Diffusion Policy` |
| 批量整理分类 | `批量读一下 Zotero 里 VLA 分类下的论文` |
| 看开源项目 | `GitHub 周榜` / `GitHub 日榜` / `GitHub 月榜` |
| 手动移动笔记后刷新目录 | `更新索引` |

总入口会自动完成**抓取 → 点评 → 重点论文笔记**，正常不需要手动拆三步。只有调试、补跑时，才用 `跑一下论文抓取`、`跑一下论文点评`、`跑一下论文笔记`。

## 配置研究方向与笔记库

配置集中管理，不需要改 Python 源码：

| 配置项 | 用途 |
| --- | --- |
| `paths.obsidian_vault` | 笔记库根路径 |
| `paths.paper_notes_folder` / `daily_papers_folder` / `concepts_folder` | 论文、推荐和概念目录名 |
| `paths.zotero_db` / `zotero_storage` | Zotero 数据库和附件路径；不用 Zotero 时无需配置 |
| `daily_papers.research_interests` | Jev 使用的完整研究兴趣描述；项目名只是示例 |
| `daily_papers.keywords` | Python 用于候选召回的关键词 |
| `daily_papers.negative_keywords` | 不想看的主题，注意检查是否误排自己的方向 |
| `daily_papers.domain_boost_keywords` | 额外加分的领域词 |
| `daily_papers.arxiv_categories` / `min_score` | arXiv 分类和关键词召回阈值 |
| `daily_papers.top_n` / `candidate_pool_size` | 每天最多推荐 10 篇；语义评分候选池默认最多 30 篇 |
| `daily_papers.project_queries` | GitHub 新项目 / 近期更新的主题检索式，不限已知项目名单 |
| `daily_papers.ranking` | `backend: jev`、固定模型版本、批大小和最低相关性分（0–4） |

各配置文件按下面的顺序合并，后者覆盖前者；数组整体替换：

```text
内置默认值 → 安装目录/_shared/user-config.json
          → 安装目录/_shared/user-config.local.json
          → ~/.config/dailypaper-skills/user-config.json
          → DAILYPAPER_CONFIG 指定的 JSON
          → OBSIDIAN_VAULT_PATH 覆盖笔记库路径
```

共享配置目录遵循 `XDG_CONFIG_HOME`。同时使用多个 Agent，推荐编辑共享配置；只想临时换一个库，可以设置环境变量：

```bash
# macOS / Linux
export OBSIDIAN_VAULT_PATH="/path/with spaces/ObsidianVault"
export DAILYPAPER_CONFIG="/path/to/my-config.json"  # 可选
```

```powershell
# Windows PowerShell
$env:OBSIDIAN_VAULT_PATH = "C:/Users/YourName/ObsidianVault"
$env:DAILYPAPER_CONFIG = "C:/Users/YourName/my-config.json"  # 可选
```

用 `python3 skills/_shared/user_config.py` 查看**最终生效的配置和临时目录**。环境变量要传给实际运行 Agent 的进程；在终端设置后，已打开的桌面应用不会自动继承。

默认自动刷新目录页，**自动 Git commit 和 push 均关闭**。需要同步时，显式配置 `automation.git_commit` / `git_push`，并遵循当前会话授权；只开 `git_push` 不会生效。

## Agent 兼容说明

核心流程采用标准 `SKILL.md` 加 Python 脚本，不强制依赖 Claude 的工具名、斜杠命令或子 Agent。没有原生 Skill 调用时，让 Agent 读取 `skills/daily-papers/SKILL.md` 并执行；没有子 Agent 时，在当前会话逐篇运行 `paper-reader`。

| 能力 / 入口 | 支持范围 |
| --- | --- |
| 七个 Skill、统一安装与配置 | 面向上表 Agent 和具备所需能力的其他 Agent |
| Web Viewer 浏览笔记 | 与生成笔记的 Agent 无关 |
| Web Viewer 的 Claude 对话按钮 | 仍需本机 `claude` CLI |
| `paper-reader/paper_daemon.py` 后台守护进程 | 仍是可选 Claude CLI 扩展；其他 Agent 可在会话中批量阅读 |
| 只有聊天、不能运行命令 / 访问文件的客户端 | 无法独立执行整条本地流水线 |

安装目录依据各宿主官方说明；**安装及脚本测试通过，不代表已逐一完成所有客户端的端到端实测**。云端 / 沙箱 Agent 还需要在它实际执行的环境里安装依赖并提供笔记库访问。

[接入细节、官方依据与验证方法](agents.md) · [Skill 内部运行约定](../skills/_shared/agent-runtime.md)

## 工作原理

```text
你说“今日论文推荐”
  → Python：HuggingFace Daily / Trending + arXiv 抓取、关键词召回、去重
  → Jev：按研究兴趣语义评分，选择最多 10 篇，再由 Python 富化
  → Agent：结合已有笔记和研究方向，写推荐点评与分流表
  → Agent：用 paper-reader 精读“必读”论文，补概念、回填链接、刷新目录
```

关键词召回不消耗模型 token；Jev 评分会调用 TypeSafe API，并把实际 `usage`、评分分布和耗时记录到 `daily_papers_ranking.json`。点评、精读和 Agent 编排仍消耗宿主模型额度。Jev 的相关性分与 confidence 不代表论文正确性或科学质量。

同数量的评分对照方法和结果见 [Jev 评分费用与耗时对照](jev-benchmark.md)。

| 技能 | 职责 |
| --- | --- |
| `daily-papers` | 一句话总入口 |
| `daily-papers-fetch` | 抓取、筛选和富化候选论文 |
| `daily-papers-review` | 研究点评、推荐页和历史记录 |
| `daily-papers-notes` | 重点笔记、概念补充和链接回填 |
| `paper-reader` | 独立精读 arXiv / 本地 PDF / Zotero 文献 |
| `generate-mocs` | 论文与概念目录页 |
| `github-trending` | 开源项目榜单及方向相关性 |

共享配置与工具在 `skills/_shared/`；更多实现细节见 [ARCHITECTURE.md](../ARCHITECTURE.md)。

## 可选：在浏览器里看笔记

Web Viewer 使用 FastAPI 和原生前端，无需 Node 构建：

```bash
python3 -m pip install -r web-viewer/requirements.txt
python3 web-viewer/app.py
```

打开 `http://localhost:8080`，浏览每日推荐、GitHub 周榜、论文笔记、概念库、公式和双向链接。它读取同一份共享配置，也兼容旧的 Claude 安装配置；自定义安装目录的个人配置可通过 `DAILYPAPER_CONFIG` 指定。

其中的 **Claude 对话按钮**是额外的 CLI 入口，未安装 Claude 时仍可正常浏览笔记。使用其他 Agent 时，在对应客户端触发技能，再回浏览器阅读结果。

## 常见问题

**安装后 Agent 没发现技能？** 先重启 / 刷新会话，确认目标目录有 `daily-papers/SKILL.md` 和同级 `_shared/`。检查宿主是否启用 Skills；也可直接提供 `SKILL.md` 的绝对路径让它读取。避免同一个技能在多个被扫描目录重复安装。

**如何升级？** 更新仓库后，再运行 `python3 install.py --agent codex --update`（换成自己的 Agent）。它替换项目文件，保留已有的 `user-config.json`、个人覆盖文件及无关技能。若自己改过 Skill 或脚本，先保存修改；可先加 `--dry-run` 检查冲突。

**不用 Obsidian / Zotero 可以吗？** 可以。配置一个 Markdown 输出目录即可；Zotero 只用于已有文献库的搜索和分类阅读。

**没抓到论文或出现 arXiv 429？** 查看脚本 stderr，确认网络、研究关键词和时间范围。arXiv 获取失败时可使用 HuggingFace 来源；周末也可能确实没有足够新论文。保留失败信息，稍后重试，别把空结果当成“今天没有相关研究”。

**能同时跑多个 Agent 吗？** 可以，但为每条流水线设置不同的 `DAILYPAPER_TEMP_DIR`，并避免同时改同一天的推荐文件。各阶段要沿用同一个临时目录。

**能每天自动跑吗？** 可以使用宿主的定时能力或系统调度，触发 `今日论文推荐`。本项目不会在安装时创建后台任务。

**生成内容能直接用于论文写作吗？** 把它当作阅读记录、related work 素材和追问提纲。正式引用前核对原文，尤其是公式、数据、实验条件和作者结论。
