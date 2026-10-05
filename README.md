# dailypaper-skills 🗞️

**让你的 Agent 帮你追论文、挑重点，把值得读的研究留在自己的知识库里。**

每天的新论文很多，真正费时间的是判断：哪些和自己的研究有关，哪些值得读全文，读过以后又能留下什么。dailypaper-skills 把这些步骤连成一套研究工作流：按你的兴趣筛选论文，给出有依据的锐评，再精读重点论文，整理成带公式、图表和概念链接的笔记。

在你常用的 Agent 里说一句：

```text
今日论文推荐
```

你会得到 **一份最多 10 篇的论文推荐、明确的阅读优先级，以及“必读”论文的完整笔记**。推荐页链接到笔记，笔记链接到概念，方便以后做研究、查方法、回顾相关工作。

面向 **AI 与机器人研究者、研究生，以及需要长期跟进技术进展的工程师**。可安装到 Claude Code、Codex、Cursor、GitHub Copilot、Gemini CLI、OpenCode、OpenClaw；其他能读取指令、执行 Python 和访问文件的 Agent 也可接入。[兼容范围](docs/usage.md#agent-兼容说明)

[你会得到什么](#-你会得到什么) · [有哪些 Skills](#-有哪些-skills) · [开始使用](#-开始使用) · [使用指南](docs/usage.md) · [视频演示](http://xhslink.com/o/1dhQCn40EWY)

<!-- JEV_BENCHMARK_START -->
> **每日论文评分，API 标价折算省 99.47%，实测约快 20 倍。** 同一批 30 篇候选、两组均推荐 10 篇：GPT-6 Astra 约 **$0.1093 / 10.35 秒**，Jev 约 **$0.000576 / 0.52 秒**。2026-10-05 单次对照，计入主模型缓存；仅评分环节，费用为官方标准标价折算，非账户实际账单。[完整结果与复现](docs/jev-benchmark.md)
<!-- JEV_BENCHMARK_END -->

## 🎁 你会得到什么

### 🔎 1. 一份围绕你研究方向的每日阅读清单

从 HuggingFace Daily / Trending 和 arXiv 发现论文，按你配置的研究兴趣筛选，结合推荐历史去重。默认每天最多 10 篇，相关论文不足时不凑数；漏看几天，也可以一次补看过去三天或一周。

每篇推荐都要回答：**做了什么、为什么和你有关、有什么可借鉴、哪些地方还值得追问。** 来源、论文链接和已有笔记一起保留，方便回到原文。

### 🎯 2. 有态度、有依据的阅读优先级

读推荐页，就能决定今天把注意力放在哪里：

| 分流 | 帮你做的决定 |
| --- | --- |
| 🔥 必读 | 值得展开读全文，工作流继续生成完整笔记 |
| 👀 值得看 | 先了解方法与贡献，按需要进一步追问 |
| 💤 可跳过 | 看清相关性或价值有限的原因，减少无效阅读 |

锐评保留这套 skills 的个性：具体指出方法假设、实验范围、工程成本和结论边界。判断要有证据，信息不足时说明需要全文确认。Jev 负责判断主题相关性，研究价值由 Agent 结合论文信息分析。

### 📝 3. 能反复使用的论文与概念笔记

对“必读”论文继续读全文，把研究问题、方法、关键公式、图表、实验结果和批判性思考整理成结构化 Markdown。遇到重要术语，补充 `[[概念]]` 链接和概念笔记，再把笔记链接回填到推荐页、刷新目录。

下次读到相似方法时，可以顺着链接找到已有积累。支持检查已有论文笔记，也能从 Zotero 文献库开始阅读。

**一次运行的交付物：**

| 产物 | 打开后能看到什么 |
| --- | --- |
| 每日推荐页 | 今日锐评、阅读分流、逐篇点评、原文与笔记入口 |
| 重点论文笔记 | 方法解析、公式说明、图表、实验与局限 |
| 概念库与目录页 | 方法和术语之间的链接，持续积累的研究索引 |

[查看完整论文笔记模板](obsidian-templates/论文笔记模板.md)。所有内容保存在你配置的本地目录；Obsidian 适合浏览双向链接，也可以用普通 Markdown 编辑器或项目自带的 Web Viewer 阅读。

## 🧩 有哪些 Skills

日常从三个入口开始：追新论文、读指定论文、看开源项目。其余技能在流程中自动衔接，也可以单独调用。

| 你想做什么 | 对 Agent 说 | 对应 Skill |
| --- | --- | --- |
| 找到今天值得读的论文，并整理重点笔记 | `今日论文推荐` | [`daily-papers`](skills/daily-papers/SKILL.md) |
| 补看最近的研究进展 | `过去一周论文推荐` | `daily-papers` |
| 精读一篇论文 | `读一下这篇论文 <arXiv 链接或 PDF 路径>` | [`paper-reader`](skills/paper-reader/SKILL.md) |
| 读自己的文献收藏 | `读一下 Zotero 里的 Diffusion Policy` | `paper-reader` |
| 先抓住核心贡献 | `快速看一下这篇论文 <PDF 路径>` | `paper-reader` |
| 跟进开源工具与仿真生态 | `GitHub 周榜` | [`github-trending`](skills/github-trending/SKILL.md) |
| 整理已有知识库的导航 | `更新索引` | [`generate-mocs`](skills/generate-mocs/SKILL.md) |

每日推荐内部由 [`daily-papers-fetch`](skills/daily-papers-fetch/SKILL.md)、[`daily-papers-review`](skills/daily-papers-review/SKILL.md)、[`daily-papers-notes`](skills/daily-papers-notes/SKILL.md) 完成抓取、点评和笔记生成。正常使用只需一句话；需要补跑某个阶段时，可以单独调用。

### 🐙 也帮你发现论文之外的开源项目

`GitHub 周榜` 汇总热门项目，标注与你研究方向的关系，并按主题检索仿真新项目和已有项目的近期更新。日榜、月榜也可用。

默认兴趣包括 **大模型 RL、RL infra、世界模型 / JEPA、灵巧手操作与物理仿真**。MuJoCo、Newton、Isaac Sim、PhysX、Genesis、SuperDex、mjlab 等只是例子，发现范围也覆盖新的引擎、求解器和仿真基础设施。你可以配置自己的研究方向与项目检索主题。

## 🚀 开始使用

准备一个能读写文件、执行命令和联网的 Agent，以及 **Python 3.10+、Git、curl**。PDF 文字与图片提取需要 **Poppler**；Obsidian 和 Zotero 按需使用。[完整环境说明](docs/usage.md#1-准备运行环境)

### 第一步：安装技能包

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills
python3 install.py --agent codex
```

将 `codex` 换成你使用的 Agent：`claude`、`cursor`、`copilot`、`gemini`、`opencode` 或 `openclaw`。Windows 可将 `python3` 换成 `py -3`。安装器会一起安装七个技能及共享依赖。

> [多 Agent、自定义目录与升级方法](docs/usage.md#2-安装到你使用的-agent)

### 第二步：告诉它你的研究兴趣

创建个人配置：

```bash
python3 skills/_shared/user_config.py --init
```

然后让 Agent 帮你完成设置：

```text
帮我配置 dailypaper-skills。
我的笔记库在 /path/to/ObsidianVault。
我关注大模型强化学习、RL infra、世界模型和 JEPA、灵巧手操作与物理仿真。
请使用跨 Agent 的共享配置，每天最多推荐 10 篇。
```

默认的 Jev 语义评分需要在启动 Agent 的环境中设置 `TYPESAFE_API_KEY`。点评与精读使用宿主 Agent 的模型。没有 TypeSafe key 时，也可以显式选择关键词筛选模式。[密钥设置与关键词模式](docs/usage.md#3-配置并开始使用)

### 第三步：开始你的第一次推荐

刷新或重启 Agent 会话，输入：

```text
今日论文推荐
```

Agent 会依次完成筛选、点评和重点笔记，并返回产物位置。也可以直接给它一篇论文开始精读。以上都是 **Agent 对话指令**。

## ⚡ 为什么用 Jev 做筛选

每天重复发生的相关性评分交给 Jev，把宿主模型用于论文点评和全文精读。相同 30 篇候选、两组都推荐 10 篇的一次真实 API 对照中：

| 评分环节 | GPT-6 Astra | Jev 1.13.0 |
| --- | ---: | ---: |
| 官方标准 API 标价折算 | $0.109264 | $0.000576408 |
| API 调用耗时 | 10.35 秒 | 0.52 秒 |
| 总 token | 11,932 | 14,198 |

**费用优势来自更低的单价。** Jev 在这次对照中使用了更多 token，但评分费用按标价折算降低 99.47%，两组入选重合 9/10。相对首版 Jev 请求，优化后的 token 用量减少了 25.12%。

这是 2026-10-05 的单次评分测量，计入主模型缓存；不代表整个阅读流程的费用，也不是订阅账户实际扣款。重合率不等于人工质量评价。[原始请求、用量、价格来源与复现方法](docs/jev-benchmark.md)

## 📚 接入你已有的阅读习惯

- **Obsidian**：推荐页、论文笔记、概念库和目录页相互链接；产物是可自行管理的 Markdown。
- **Zotero**：按标题查找文献，或按分类批量阅读，利用已有 PDF 收藏。
- **浏览器**：可选 [Web Viewer](docs/usage.md#可选在浏览器里看笔记) 浏览同一份笔记与公式。
- **多个 Agent**：共用研究兴趣和笔记库配置；宿主需要提供文件、命令和网络能力。[接入与验证范围](docs/agents.md)

我也会搭配 [Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar)：用这套 skills 筛选和积累研究笔记，在 PDF 阅读时用 Sidebar 即时问答、点译与追问。

## 💬 使用前你可能想知道

**必须安装 Obsidian 吗？** 不需要，配置一个 Markdown 输出目录即可。Zotero 也只在读取个人文献库时需要。

**会自动每天运行吗？** 默认由你发起。需要定时运行时，可以使用宿主或系统调度；安装不会创建后台任务。Git 自动提交、推送默认关闭。

**所有 Agent 都能用吗？** 技能包按文件与脚本组织，提供多种安装目标；纯聊天、无法访问文件或运行命令的客户端不能独立执行。安装与脚本测试不等于所有客户端都完成了端到端验证。

**想改研究方向、升级或排查失败？** 查看 [使用指南](docs/usage.md)，包含完整配置、安装目录、迁移、并行运行与常见问题。

## 🛠️ 开发与贡献

[架构说明](ARCHITECTURE.md) · [Agent 接入](docs/agents.md) · [评分基准](docs/jev-benchmark.md)

```bash
python3 -m pip install -r web-viewer/requirements.txt
python3 -m unittest discover -s tests -v
```

欢迎分享使用方式、适配反馈，或提交 Issue / PR。反馈问题时请提供 Agent 与系统版本、失败阶段及去除敏感信息后的日志。

[![Star History Chart](https://star-history.dera.page/svg?repos=huangkiki/dailypaper-skills&type=Date)](https://star-history.dera.page/#huangkiki/dailypaper-skills&Date)

## 📄 License

Apache-2.0. See [LICENSE](LICENSE).
