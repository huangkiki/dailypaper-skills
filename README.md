# dailypaper-skills 🗞️

这是我自己平时读论文用的一套 Claude Code skills。

简单说，就是跟 Claude 说一句话，它会帮我从每天的新论文里筛一轮，挑出值得看的，再把重点论文读完、写成 Obsidian 笔记。日常不用记一堆命令，基本就是：

```text
今日论文推荐
读一下这篇论文 https://arxiv.org/abs/2509.24527
```

如果你也有“每天想看看新论文，但不想每天从一堆页面里手动捞”的痛苦，这个仓库大概就是为这种场景准备的。

> **🧊 Codex / Humanoid 适配**
> 想看 Codex 适配版的话，可以先看 [`codex+humanoid`](https://github.com/huangkiki/dailypaper-skills/tree/codex%2Bhumanoid) 分支。

> **🧩 顺手推荐**
> 如果你主要在 Zotero 里读 PDF，可以搭配我另一个插件 [Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar)。这个插件是在 Zotero 右侧加一个 AI 侧栏，适合边读边问、点译、全文翻译、截图追问、写回 Zotero 笔记。
>
> ![Zotero AI Sidebar 阅读侧栏](https://raw.githubusercontent.com/huangkiki/zotero-ai-sidebar/master/docs/assets/zotero-real-overview.png)
>
> 我的习惯是：用这个仓库做每日筛选和 Obsidian 深度笔记；真正在 Zotero 里打开 PDF 精读时，用 Zotero AI Sidebar 做即时问答和点译。

> **🎬 视频演示**：[用 Claude Code 打造我的论文流水线](http://xhslink.com/o/1dhQCn40EWY)

## ✨ 它会帮你做什么

- 抓 HuggingFace Daily、Trending 和 arXiv 上的新论文。
- 按你关心的方向打分，先筛掉明显不相关的。
- 生成每日推荐页，分成“必读 / 值得看 / 可跳过”。
- 对重点论文生成结构化笔记，包括方法、实验、公式、图表、局限和后续可追的问题。
- 自动写进 Obsidian，并维护论文目录页和概念索引。
- 如果你用 Zotero，也可以直接按标题搜索，或者按分类批量读论文。
- 顺手还能抓 GitHub 周榜，看看最近哪些开源项目 star 涨得最快，并按你的方向标注相关性。

最后在 Obsidian 里大概会长这样：

```text
ObsidianVault/
├── DailyPapers/
│   └── YYYY-MM-DD-论文推荐.md
├── 论文笔记/
│   ├── 具体分类/
│   │   └── MethodName.md
│   ├── _概念/
│   │   └── ...概念笔记.md
│   └── _待整理/
└── ...
```

笔记模板可以看这里：[obsidian-templates/论文笔记模板.md](obsidian-templates/论文笔记模板.md)

## 🧭 怎么用

最常用的就是这几句：

```text
今日论文推荐
过去3天论文推荐
过去一周论文推荐
```

想看看最近 GitHub 上 star 涨得最快的项目：

```text
GitHub 周榜
过去一周 GitHub 热门
GitHub 日榜
```

生成的榜单会写到 Obsidian 的 `GitHubTrending/` 目录，并按你的研究方向自动标注哪些和你相关。

读单篇论文：

```text
读一下这篇论文 https://arxiv.org/abs/2509.24527
快速看一下这篇论文 ~/Downloads/paper.pdf
批判性分析这篇论文 ~/Downloads/paper.pdf
```

如果你配好了 Zotero，也可以这样：

```text
读一下 Zotero 里的 Diffusion Policy
批量读一下 Zotero 里 VLA 分类下的论文
```

目录页一般会自动刷新。如果你手动移动过笔记，或者觉得目录没同步，再补一句：

```text
更新索引
```

## ⚙️ 安装

需要这些东西：

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Obsidian](https://obsidian.md/)
- [Python 3.8+](https://www.python.org/)
- [`poppler-utils`](https://poppler.freedesktop.org/)，macOS 可以 `brew install poppler`
- [Zotero](https://www.zotero.org/)，可选，但如果你已经用 Zotero 管论文会很方便

把 skills 复制到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills

mkdir -p ~/.claude/skills
cp -r ./skills/* ~/.claude/skills/
```

再准备一下 Obsidian 目录。把下面的 `VAULT` 改成你自己的库路径：

```bash
VAULT=~/ObsidianVault

mkdir -p "$VAULT/DailyPapers" \
  "$VAULT/GitHubTrending" \
  "$VAULT/论文笔记/_概念/0-待分类" \
  "$VAULT/论文笔记/_待整理"
```

我自己在本地日常用的时候，通常会这样启动 Claude Code：

```bash
claude --dangerously-skip-permissions
```

这样会少很多权限确认，但它确实会跳过部分权限检查。所以更适合自己的个人机器，不建议在不熟悉的机器或共享环境里直接这么跑。

## 配置

配置文件在：

```text
~/.claude/skills/_shared/user-config.json
```

你可以自己改，也可以直接让 Claude 帮你改，比如：

```text
帮我配置 dailypaper-skills。我的 Obsidian 库在 XXX，研究方向是 robot learning、VLA、diffusion policy。
```

主要会改这几项：

| 配置项 | 说明 |
| --- | --- |
| `paths.obsidian_vault` | 你的 Obsidian 库路径 |
| `paths.zotero_db` | Zotero 数据库路径，不用 Zotero 可以留空 |
| `paths.zotero_storage` | Zotero 附件存储路径 |
| `daily_papers.keywords` | 你关心的研究方向，用来给论文加分 |
| `daily_papers.negative_keywords` | 你不想看的方向 |
| `daily_papers.domain_boost_keywords` | 额外加分的领域词 |

Zotero 分类批量阅读不需要你另外写映射文件。只要 `paths.zotero_db` 和 `paths.zotero_storage` 配好，脚本会直接从 Zotero 分类树里查。

## 🖥️ 网页可视化（可选）

如果你想在浏览器里翻每日推荐、论文笔记、概念库和 GitHub 周榜，仓库自带一个轻量 Web Viewer（FastAPI + 原生前端，无需打包）。

```bash
cd web-viewer
pip install -r requirements.txt
python3 app.py
```

然后打开 `http://localhost:8080`。它会自动读取你 `~/.claude/skills/_shared/user-config.json` 里的 `obsidian_vault`，把这些内容渲染出来：

- 📰 **Daily Papers**：每日/每周推荐，带“必读 / 值得看 / 可跳过”分流卡片。
- 🔥 **GitHub Trending**：`GitHubTrending/` 里的周榜笔记。
- 📝 **Paper Notes** / 🧠 **Concepts**：论文笔记和概念库，支持 `[[双向链接]]` 跳转、LaTeX 公式、全文搜索。

页面里还内置了一个 Claude 对话框，可以直接在浏览器里喊“今日论文推荐”“GitHub 周榜”触发流程（它在后台调用本机的 `claude` CLI）。

## 我一般怎么搭配 Zotero AI Sidebar

这个仓库和 [Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar) 不是替代关系，更像是两个不同位置的工具。

`dailypaper-skills` 更适合做这些事：

- 每天批量筛新论文。
- 把一篇论文完整读完，沉淀成 Obsidian 笔记。
- 顺手维护概念库和目录页。
- 对 Zotero 里某个分类的论文做批量整理。

Zotero AI Sidebar 更适合在读 PDF 的时候用：

- 看到一段看不顺，直接点译。
- 围绕当前论文提问，不用手动复制标题、摘要、选区。
- 截图问图表、公式或实验结果。
- 把回答写回 Zotero 子笔记。

所以我自己的工作流通常是：

1. 早上跑 `今日论文推荐`，先知道今天有没有值得看的。
2. 对特别重要的论文跑 `读一下这篇论文 ...`，生成 Obsidian 深度笔记。
3. 真正在 Zotero 里打开 PDF 细读时，用 Zotero AI Sidebar 做临场问答、点译和截图追问。
4. 一段时间后，对 Zotero 某个分类跑批量阅读，把已有文献库再整理进 Obsidian。

## 它内部大概怎么跑

`今日论文推荐` 其实会拆成三步：

1. **抓取**：从 HuggingFace Daily、Trending 和 arXiv API 抓候选论文，按你的关键词打分去重。
2. **点评**：Claude 读候选列表，分成“必读 / 值得看 / 可跳过”，写到 Obsidian 的 `DailyPapers/` 目录。
3. **笔记**：对“必读”论文逐篇调用 `paper-reader`，生成完整论文笔记，补概念库，再刷新目录页。

正常不用手动跑这三步。如果你只是想调试某一步，也可以说：

```text
跑一下论文抓取
跑一下论文点评
跑一下论文笔记
```

`读一下这篇论文 ...` 走的是 `paper-reader`。它支持 arXiv 链接、本地 PDF、Zotero 搜索和 Zotero 分类。生成笔记时会尽量从 arXiv HTML、项目主页和 PDF 里把图表找出来，写完后还会检查图片链接，坏掉的外链会尽量下载到本地。

`更新索引` 走的是 `generate-mocs`，会递归扫描论文笔记和概念库，生成 Obsidian 可用的目录页。

更多实现细节见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 🔒 默认不会动你的 git

默认配置比较保守：

- 自动刷新 Obsidian 目录页：开。
- 自动 git commit：关。
- 自动 git push：关。

也就是说，它会生成和更新 Markdown，但不会默认提交或推送你的 Obsidian 仓库。

如果你的 Obsidian 库已经用 git 管理，并且想让流程结束后自动提交，可以自己打开配置。笔记多了以后，有个版本历史还是很安心的。

## 仓库里有什么

```text
skills/
├── daily-papers/          # 每日推荐总入口
├── paper-reader/          # 单篇论文阅读与笔记生成
├── generate-mocs/         # Obsidian 目录页生成
├── github-trending/       # GitHub 周榜（star 涨最快的项目）
├── daily-papers-fetch/    # 内部：抓取候选论文
├── daily-papers-review/   # 内部：生成推荐点评
├── daily-papers-notes/    # 内部：生成重点论文笔记
└── _shared/               # 共享配置和索引脚本

web-viewer/                # 可选：本地网页可视化（FastAPI）
obsidian-templates/
└── 论文笔记模板.md
```

日常真正会直接用到的，基本就是：

- `daily-papers`
- `paper-reader`
- `github-trending`
- `generate-mocs`

另外几个是流水线内部拆出来的步骤，主要方便调试和重跑。

## FAQ

**可以一步跑完整流程吗？**

可以。直接说 `今日论文推荐`。

**不用 Zotero 可以吗？**

可以。每日推荐不依赖 Zotero；单篇阅读也支持 arXiv 链接和本地 PDF。Zotero 主要是用来搜索已有文献库、读取分类和批量处理。

**不用 Obsidian 可以吗？**

也可以。输出本质上就是 Markdown 文件。不过如果你想用 `[[双向链接]]`、图谱、概念库和目录页，Obsidian 会更顺手。

**能每天自动跑吗？**

可以。你可以让 Claude 按你的系统环境配置定时任务，比如 macOS 的 `launchd` 或 Linux 的 `cron`。定时任务建议只触发 `今日论文推荐`，不要手写三条内部命令。

**生成的笔记能直接放进论文写作里吗？**

建议把它当成 related work 整理、阅读记录和追问提纲。AI 生成内容可能会有误，正式写作前还是要回到原文核验。

## 免责声明

这是我个人研究工作流的开源整理，不是一个保证完全稳定的产品。AI 生成的推荐、点评和笔记可能有事实错误、遗漏或误读，更适合作为辅助工具，而不是替代自己的研究判断。

如果你遇到问题，欢迎提 issue、PR，或者直接让 AI 和你一起改。

## 支持这个项目

如果这套 workflow 对你有帮助，欢迎点 Star、提 PR，或者分享你的适配版本。像 [`codex+humanoid`](https://github.com/huangkiki/dailypaper-skills/tree/codex%2Bhumanoid) 这种兼容性适配也很欢迎。

[![Star History Chart](https://star-history.dera.page/svg?repos=huangkiki/dailypaper-skills&type=Date)](https://star-history.dera.page/#huangkiki/dailypaper-skills&Date)

## License

Apache-2.0. See [LICENSE](LICENSE).
