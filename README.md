# dailypaper-skills 🗞️

**简体中文** | [English](README.en.md)

**每天一句话，筛论文、看锐评，把值得读的研究变成自己的笔记。**

这是我自己平时追论文、读论文用的一套 Agent skills。从 HuggingFace 和 arXiv 找新论文，按研究兴趣挑重点，再把重点论文读完，整理成带公式、图表和概念链接的 Markdown 笔记。

```text
今日论文推荐
```

一次跑完 **抓取 → 筛选 → 点评 → 重点论文笔记**。也可以直接给一篇论文，让它精读。

[🎬 看演示](#-先看效果) · [🧭 常用指令](#-平时怎么用) · [🚀 开始使用](#-开始使用) · [📖 详细指南](docs/usage.md)

## 🎬 先看效果

> ### [▶ 用 Claude Code 打造我的论文流水线｜小红书视频](http://xhslink.com/o/1dhQCn40EWY)
>
> 我录的一段实际使用演示。想先看看这套东西怎么用，可以从这里开始。
>
> 视频展示的是早期 Claude Code 工作流；当前版本也提供 Codex、Cursor 等 Agent 的安装入口，安装方法以下文为准。

跑完后，你会拿到三类相互链接的内容：

| 产物 | 你可以用它做什么 |
| --- | --- |
| 🗞️ **每日推荐页** | 先看“必读 / 值得看 / 可跳过”，决定今天读哪几篇；默认每天最多推荐 10 篇 |
| 📝 **重点论文笔记** | 跟着研究问题、方法、公式、图表、实验和局限读懂一篇论文 |
| 🔗 **概念笔记与目录** | 遇到术语顺着链接查，读到相关方法时找到以前的积累 |

**点评是这套 skills 的一个重点。** 每篇都要说清楚：做了什么、和你的研究有什么关系、哪个设计值得借鉴、哪些结论还需要追问。可以尖锐，但要给出依据；摘要里没说的内容，会标明需要全文确认。

推荐页链接到重点论文，论文再链接到 `[[概念]]`。以下是默认目录下的产物结构示意，文件名和分类会随实际内容变化：

```text
你的笔记目录/
├── DailyPapers/
│   └── YYYY-MM-DD-论文推荐.md    ← 今日锐评、阅读优先级、逐篇点评
└── 论文笔记/
    ├── 具体分类/MethodName.md    ← 方法、公式、图表、实验与局限
    └── _概念/主题/Concept.md     ← 定义、相关方法、关联论文
```

[查看完整论文笔记模板](obsidian-templates/论文笔记模板.md)。用 Obsidian 浏览双向链接很方便，也可以用普通 Markdown 编辑器或项目自带的 [Web Viewer](docs/usage.md#可选在浏览器里看笔记)。

## 🧭 平时怎么用

装好后，在 Agent 对话里说你想做什么：

| 场景 | 直接这样说 |
| --- | --- |
| 今天有哪些论文值得看 | `今日论文推荐` |
| 几天没跟进，补一下 | `过去3天论文推荐` / `过去一周论文推荐` |
| 精读指定论文 | `读一下这篇论文 <arXiv 链接或 PDF 路径>` |
| 先抓住核心贡献 | `快速看一下这篇论文 <PDF 路径>` |
| 带着问题看方法 | `批判性分析这篇论文 <PDF 路径>` |
| 读已有收藏 | `读一下 Zotero 里的 Diffusion Policy` |
| 看开源项目进展 | `GitHub 周榜` |
| 移动笔记后刷新导航 | `更新索引` |

**研究方向由你设置。** 默认关注大模型 RL、RL infra、世界模型 / JEPA、灵巧手与物理仿真；可以改成你自己的方向。推荐会结合历史去重，相关论文不足时不凑数。“必读”继续生成完整笔记，已有笔记会匹配并链接。

**中英文跟随你的提问。** `Recommend papers from the past week` 会生成英文推荐和笔记；也可以明确说“用英文输出”或 “write in Chinese”。切换语言不会重命名已有目录和笔记。[语言说明](docs/usage.md#中英文自动切换)

## 🚀 开始使用

需要一个能读写文件、执行命令和联网的 Agent，以及 **Python 3.10+、Git、curl**。精读 PDF 需要 **Poppler**；Obsidian、Zotero 按需使用。[环境准备](docs/usage.md#1-准备运行环境)

### 1. 安装完整技能包

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills
python3 install.py --agent codex
```

把 `codex` 换成你使用的 Agent：`claude`、`cursor`、`copilot`、`gemini`、`opencode` 或 `openclaw`。Windows 可将 `python3` 换成 `py -3`。安装器会一起复制七个技能及共享依赖。

### 2. 告诉它你的研究方向和保存位置

先创建个人配置，已有配置不会被覆盖：

```bash
python3 skills/_shared/user_config.py --init
```

刷新或重启 Agent 会话，然后在对话中输入，替换成自己的目录和方向：

```text
帮我配置 dailypaper-skills，使用跨 Agent 的共享配置。
把 Markdown 保存到 /path/to/my-research-notes。
我关注 robot learning、VLA、世界模型和物理仿真。
每天最多推荐 10 篇。
```

**默认无需额外 API key。** 筛选、点评和精读使用当前 Agent 的模型额度。输出目录可以是普通文件夹，也可以是你指定的 Obsidian 库。

### 3. 开始第一次推荐

```text
今日论文推荐
```

Agent 会完成筛选、点评和重点论文笔记，并告诉你产物位置。想从一篇论文试起，也可以直接发送 `读一下这篇论文 <链接或 PDF 路径>`。

升级、多 Agent 安装、自定义目录和排错见 [使用指南](docs/usage.md)。

## 🧩 里面有哪些 Skills

日常用 `daily-papers` 追新论文，用 `paper-reader` 读指定论文。抓取、点评和笔记三个阶段会自动衔接，需要补跑时也能单独调用。

| Skill | 负责什么 |
| --- | --- |
| [`daily-papers`](skills/daily-papers/SKILL.md) | 一句话启动完整每日论文流程 |
| [`paper-reader`](skills/paper-reader/SKILL.md) | 精读、快速摘要、批判性分析；支持 arXiv、本地 PDF、Zotero |
| [`daily-papers-fetch`](skills/daily-papers-fetch/SKILL.md) | 从 HuggingFace Daily / Trending 与 arXiv 抓取、筛选、富化 |
| [`daily-papers-review`](skills/daily-papers-review/SKILL.md) | 生成锐评、阅读优先级和推荐页 |
| [`daily-papers-notes`](skills/daily-papers-notes/SKILL.md) | 重点笔记、概念补充、链接回填 |
| [`generate-mocs`](skills/generate-mocs/SKILL.md) | 更新论文和概念的目录页 |
| [`github-trending`](skills/github-trending/SKILL.md) | 开源项目日榜 / 周榜 / 月榜，以及仿真主题检索 |

我也会搭配 [Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar)：用这套 skills 筛选和积累笔记，在 Zotero 里打开 PDF 时，用 Sidebar 即时问答、点译和追问。

## 💬 使用前你可能想知道

**必须用 Obsidian 吗？** 不需要，指定一个本地 Markdown 输出目录即可。Zotero 也只在读取自己的文献库时需要。

**会每天自动运行、自动上传笔记吗？** 默认由你发起，安装不会创建定时任务；Git 自动提交、推送默认关闭。定时运行用宿主或系统调度，归档与同步按你指定的目标和授权执行。

**这些 Agent 都能完整跑通吗？** 安装器提供多个目标，但完整流程需要文件、命令和网络能力。安装与脚本测试通过，不代表所有客户端都完成了端到端实测。[兼容与验证范围](docs/agents.md)

**能换论文筛选方式吗？** 默认 `agent` 使用当前 Agent 评分，也可选 `keyword` 关键词筛选或 `jev` 专用 API；只有 Jev 需要额外的 `TYPESAFE_API_KEY`。[配置与旧版本迁移](docs/usage.md#3-配置并开始使用)

<details>
<summary>⚡ 可选 Jev：历史评分费用与耗时对照</summary>

<!-- JEV_BENCHMARK_START -->
2026-10-05 的一次对照中，同一批 30 篇候选、两组均选 10 篇：GPT-6 Astra 评分约 **$0.109264 / 10.35 秒**，Jev 1.13.0 约 **$0.000576408 / 0.52 秒**，入选重合 **9/10**。按当时标准 API 标价折算，评分费用降低 **99.47%**，调用约快 **20 倍**。

这是计入主模型缓存的**单次评分环节测量**，不代表整个阅读流程的费用或账户实际账单；重合率也不等于人工质量评价。[原始证据与复现方法](docs/jev-benchmark.md)
<!-- JEV_BENCHMARK_END -->

</details>

## 🛠️ 开发与贡献

[架构说明](ARCHITECTURE.md) · [Agent 接入](docs/agents.md) · [使用指南](docs/usage.md)

```bash
python3 -m pip install -r web-viewer/requirements.txt
python3 -m unittest discover -s tests -v
```

欢迎分享用法、适配反馈，或提交 Issue / PR。反馈问题时请附 Agent 与系统版本、失败阶段，以及去除敏感信息的日志。

[![Star History Chart](https://star-history.dera.page/svg?repos=huangkiki/dailypaper-skills&type=Date)](https://star-history.dera.page/#huangkiki/dailypaper-skills&Date)

## 📄 License

Apache-2.0. See [LICENSE](LICENSE).
