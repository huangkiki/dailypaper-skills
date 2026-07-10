# Architecture

这份文档记录各模块的实现逻辑，方便想改代码或理解内部机制的人参考。

## 整体架构

```
用户说一句话
    │
    ├─ "今日论文推荐" ──→ daily-papers（编排器）
    │                        ├─ Step 1: daily-papers-fetch（Python，零 token）
    │                        ├─ Step 2: daily-papers-review（Claude 点评）
    │                        └─ Step 3: daily-papers-notes（Claude + paper-reader）
    │
    ├─ "读一下这篇论文" ──→ paper-reader（独立 fork）
    │
    ├─ "GitHub 周榜" ──→ github-trending（Python，零 token）
    │
    └─ "更新索引" ──→ generate-mocs（Python 脚本）
```

三步流水线的设计主要是为了控制单次上下文长度。每步之间通过 `/tmp` 下的 JSON 文件传数据。

---

## Step 1: daily-papers-fetch

**纯 Python，不消耗 Claude token。**

### 1.1 抓取 + 打分（fetch_and_score.py）

数据源：
- HuggingFace Daily Papers API：`https://huggingface.co/api/daily_papers?date=YYYY-MM-DD`
- HuggingFace Trending API：`https://huggingface.co/api/daily_papers?sort=trending`
- arXiv API：`https://export.arxiv.org/api/query`，搜索 `cs.RO, cs.CV, cs.AI, cs.LG`

打分规则：
- 命中 `negative_keywords` → 直接 -999 排除
- 命中 `keywords`：标题 +3，摘要 +1
- 命中 `domain_boost_keywords`：+1~2
- Trending 加分：根据 upvotes 分档（5 / 10 / 20），相关论文 +1~3，不相关的只有 20+ upvotes 才加分

去重：
- 按 arXiv ID 合并，保留高分
- 单天模式：跟 `.history.json` 交叉去重
- 周末模式：保留 5+ upvotes 的热门论文作为"再推荐"
- 多天模式（days > 1）：跳过历史去重
- 候选不足 20 篇时从历史回补

输出：`/tmp/daily_papers_top30.json`

### 1.2 元数据富化（enrich_papers.py）

用 `asyncio + curl` 并发（Semaphore=10）请求 arXiv 页面，每个请求 30s 超时 + 指数退避重试。

提取内容：
- 从 arXiv HTML 提取：首图 URL、作者、机构、章节标题、图表标题、方法名、是否有真机实验
- HTML 取不到时 fallback 到 `pdftotext` 提取机构
- 再 fallback 到 arXiv abs 页面的 `<meta>` 标签

输出：`/tmp/daily_papers_enriched.json`

---

## Step 2: daily-papers-review

**Claude 主导，读候选列表写点评。**

### 2.1 扫描已有笔记

Glob 扫描 Obsidian 的论文笔记和概念库目录，把候选论文跟已有笔记做匹配（方法名 / 标题模糊匹配），标记 `has_existing_note`。

### 2.2 写锐评

Claude 以"毒舌但有料的资深研究员"角色点评每篇论文：
- 分流表：🔥 必读 / 👀 值得看 / 💤 可跳过
- 每篇包含：作者、机构、链接、来源、核心方法（带 `[[概念]]` 链接）、对比方法、借鉴意义、锐评
- 已有笔记的论文走简化格式
- 跟用户方向完全无关的论文可以跳过，列出跳过原因

硬性约束：
- 不能凭空说"只有仿真"——必须检查 `has_real_world` 字段
- 不能说某篇是"山寨"——除非有具体方法论证据
- 不确定的信息必须注明"摘要未提及"

### 2.3 保存

- 写入 `{DAILY_PAPERS_PATH}/YYYY-MM-DD-论文推荐.md`
- 更新 `.history.json`：追加今日推荐的 arXiv ID + 标题，只保留最近 30 天
- 可选：git commit

---

## Step 3: daily-papers-notes

**Claude 编排 + 多次调用 paper-reader。**

### 3.1 概念库补充

1. 扫描推荐文件里所有 `[[概念]]` 链接 + enriched JSON 的 `method_names`
2. 过滤：只保留方法 / 模型 / 数据集 / 仿真器 / 技术概念名，排除通用词、论文标题、人名
3. 自动分类到 16 个概念子目录（生成模型 / 强化学习 / 机器人策略 / 3D 视觉 / 仿真器 / 数据集等）
4. 创建概念笔记：定义 + 数学形式 + 核心要点 + 代表工作 + 相关概念

### 3.2 论文笔记生成

- 只为"🔥 必读"论文生成完整笔记
- 已有笔记如果 < 100 行或缺少关键 section → 删除重新生成
- 逐篇调用 paper-reader skill

质量校验（每篇）：
- 文件 ≥ 120 行
- 包含 LaTeX 公式（≥ 2 处）
- 包含图片引用（≥ 1 处）
- 包含 `## 关键公式` 和 `## 实验结果` section
- 不达标 → 删了重来

### 3.3 链接回填

在推荐文件中，给已有笔记的论文插入 `📒 **笔记**: [[NoteName]]` 链接。

### 3.4 刷新目录页 + git

- 调用 `generate_concept_mocs.py` 和 `generate_paper_mocs.py`
- 可选：git commit & push

---

## paper-reader

**独立 fork 运行，完整工具链（Bash / Read / Write / Edit / WebFetch / WebSearch）。**

### 输入源

| 来源 | 处理方式 |
|------|----------|
| arXiv 链接 | WebFetch 抓取 |
| 本地 PDF | 直接读取 |
| Zotero 搜索 | 查 DB → 定位 PDF / 在线源 |
| Zotero 分类批量 | 递归子分类 → 去重 → 逐篇处理 |

找不到 PDF 时的 fallback 顺序：
1. `zotero_helper.py info` 拿元数据
2. 提取 arXiv ID → WebFetch HTML 版本（优先，能拿图）
3. Fallback：PDF 版本 / DOI 页面
4. 最后：WebSearch 论文标题
5. 都不行 → 跳过

### 阅读模式

| 模式 | 触发词 | 输出 |
|------|--------|------|
| 快速摘要 | "快速看一下" | 3-5 句核心贡献 |
| 完整解析 | 默认 | 结构化笔记（模板） |
| 批判性分析 | "批判性分析" | 优缺点评估 |
| 知识提取 | "提取公式" | 公式 + 算法伪代码 |

### 图片获取（多路 fallback）

1. arXiv HTML：提取 `<figure>` 标签的图片 URL（优先）
2. 项目主页：从摘要 / HTML 找项目链接，抓 teaser 图
3. PDF 提取：`pdfimages -png`，过滤 > 10KB 的
4. 写完后跑 `download_note_images.py` 做可达性检查，不可达的自动下载到本地

### 笔记生成

严格按 `paper-note-template.md` 模板：
- 所有 Figure、所有公式、所有 Table 都必须出现
- 技术术语首次出现必须用 `[[概念]]` 链接
- 每个公式需要：名称、LaTeX、含义、符号说明
- 文件名只用方法 / 模型名（如 `Pi05.md`），不加年份前缀

### 存储

- 路径：`{NOTES_PATH}/{zotero_collection_path}/{MethodName}.md`
- 不确定分类 → `_待整理/`
- YAML frontmatter：title / method_name / authors / year / venue / tags / zotero_collection / image_source / created

### 概念库维护

每篇论文读完后：
1. 扫描笔记中所有 `[[概念]]` 链接
2. 检查概念笔记是否存在
3. 不存在的按 16 类自动分类并创建

### 批量处理（paper_daemon.py）

```bash
python3 paper_daemon.py -c "VLA"     # 处理 VLA 分类
python3 paper_daemon.py --status     # 查看进度
python3 paper_daemon.py --list       # 列出所有分类
```

- API 限流：指数退避（60s → 最大 12h）
- 配额监控：每 3 篇检查一次，> 85% 自动等待
- 断点续跑：checkpoint 持久化
- 进程锁：防止并发
- 自动跳过已有笔记（> 100 行）

---

## generate-mocs

**纯 Python，递归扫目录生成索引页。**

核心函数 `build_tree_mocs()`：
- 递归遍历目录
- 每个目录生成一个 `目录名.md` 索引文件
- 包含：子目录链接（带笔记数统计）+ 当前目录笔记列表
- 幂等：内容没变的文件不重写
- 用 wikilink 格式

分两个入口：
- `generate_concept_mocs.py`：扫描概念库（`_概念/`）
- `generate_paper_mocs.py`：扫描论文笔记（排除概念目录）

---

## github-trending

**纯 Python，不消耗 Claude token。** 抓 GitHub Trending 榜（star 涨得最快的项目），打分标注，写成 Obsidian 笔记。

### fetch_trending.py

- 数据源：`https://github.com/trending?since={daily|weekly|monthly}`，可选 `&l={language}` 按语言过滤。
- SSL 兜底：默认走验证连接；遇到证书验证失败（含被包成 `URLError` 的情况，常见于有中间人代理的环境），自动退回不验证证书的 SSL context 重试。
- 解析：regex 从每个 `Box-row` 提取 repo、简介、语言、累计 star/fork、本周期新增 star。
- 打分：复用 `_shared/user-config.json` 的 `keywords`（+2）/`domain_boost_keywords`（+1）/`negative_keywords`（-3），
  标注 `relevant`（命中正向或领域词且未被负向词压过）。**不丢弃非相关项**，只标注。
- 按本周期新增 star 降序，输出 JSON（stdout）。

### write_trending_note.py

- 读 JSON，写到 `{VAULT}/{github_trending_folder}/`（默认 `GitHubTrending/`）。
- 周榜文件名按 ISO 周编号（如 `2026-W28 GitHub周榜.md`），日/月榜用日期。
- 笔记结构：摘要 → 「🎯 与研究方向相关」列表 → 「📊 完整榜单」表格（含 ✅ 相关标记）。

---

## web-viewer（可选）

**本地网页可视化，FastAPI 后端 + 原生前端（无构建）。** 只读渲染 Obsidian 内容，不改文件。

### 配置解析（app.py `load_config()`）

按优先级找 `user-config.json`：①`~/.claude/skills/_shared/user-config.json`（安装后用户实际编辑的部署副本，优先）
②`web-viewer/../skills/_shared/user-config.json`（仓库自带模板）。用第一个 `obsidian_vault` 真实存在的配置；都不行则兜底到仓库根目录。
所有目录名（DailyPapers / GitHubTrending / 论文笔记 / _概念）都从 config 读取，带默认值。

### 后端端点

| 端点 | 说明 |
|------|------|
| `GET /api/daily-papers` `/{filename}` | 每日推荐列表 / 详情（含 tier 分流表解析） |
| `GET /api/github-trending` `/{filename}` | GitHub 周榜列表 / 详情 |
| `GET /api/paper-notes` `/{filename}` | 论文笔记列表 / 详情 |
| `GET /api/concepts` `/{category}/{filename}` | 概念库分类 / 详情 |
| `GET /api/search?q=` | 全文搜索（文件名 + 正文） |
| `GET /api/wikilink-index` | `[[双向链接]]` 解析索引（启动时构建） |
| `POST /api/claude` | 调本机 `claude` CLI，SSE 流式返回（浏览器里触发流程） |

### 前端（static/app.js）

hash 路由：`route(pattern, handler)` + `resolve()`。列表/详情页复用同一套 `api()` + `renderMd()`（marked + KaTeX + 自定义 wikilink/callout 扩展）。
加新页面只需三步：注册 `route()`、写 `pageXxx` 渲染函数、在 `updateActiveNav()` 加高亮分支（Trending 页即照此实现）。

---

## _shared 公共模块

### user-config.json

所有路径、关键词、打分规则、自动化开关的集中配置：

```json
{
  "paths": {
    "obsidian_vault": "~/ObsidianVault",
    "paper_notes_folder": "论文笔记",
    "daily_papers_folder": "DailyPapers",
    "github_trending_folder": "GitHubTrending",
    "concepts_folder": "_概念",
    "zotero_db": "~/Zotero/zotero.sqlite",
    "zotero_storage": "~/Zotero/storage"
  },
  "daily_papers": {
    "keywords": ["world model", "diffusion model", "embodied ai", ...],
    "negative_keywords": ["medical imaging", "weather forecast", ...],
    "domain_boost_keywords": ["robot", "manipulation", ...],
    "arxiv_categories": ["cs.RO", "cs.CV", "cs.AI", "cs.LG"],
    "min_score": 2,
    "top_n": 30
  },
  "automation": {
    "auto_refresh_indexes": true,
    "git_commit": false,
    "git_push": false
  }
}
```

### user_config.py

Python 配置加载器，带缓存。提供 `load_user_config()` / `paths_config()` / `daily_papers_config()` / `automation_config()` 等便捷函数。会校验 `git_push` 不能在 `git_commit` 关闭时开启。

### moc_builder.py

MOC 生成引擎，被 `generate_concept_mocs.py` 和 `generate_paper_mocs.py` 调用。

---

## Obsidian 目录结构

```
~/ObsidianVault/
├── DailyPapers/
│   ├── YYYY-MM-DD-论文推荐.md      # 每日推荐
│   └── .history.json                # 跨天去重索引
├── GitHubTrending/
│   └── YYYY-Www GitHub周榜.md       # GitHub 周榜（github-trending 生成）
├── 论文笔记/
│   ├── 3-Robotics/
│   │   ├── 1-VLX/VLA/
│   │   │   ├── VLA.md               # 目录页（自动生成）
│   │   │   ├── OpenVLA.md
│   │   │   └── Pi05.md
│   │   └── ...
│   ├── _概念/
│   │   ├── 1-生成模型/
│   │   │   ├── DiT.md
│   │   │   └── Flow Matching.md
│   │   ├── 3-机器人策略/
│   │   │   └── Diffusion Policy.md
│   │   ├── ... (共 16 个分类)
│   │   └── 0-待分类/
│   └── _待整理/                     # 无法自动归类的论文
└── ...
```
