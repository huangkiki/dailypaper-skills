---
name: daily-papers-fetch
description: |
  论文抓取（3 步流水线的第 1 步）。抓取 arXiv + HuggingFace 最新论文，打分筛选，富化信息，
  输出 daily_papers_enriched.json 到共享临时目录，供后续 skill 使用。

  触发词："论文抓取"、"跑一下论文抓取"
  支持多天模式："过去3天论文推荐"、"过去一周论文推荐"、"过去一周的论文"、"抓 3 天的论文"、"最近5天"
---

## 执行环境

开始前读取 [Agent 运行约定](../_shared/agent-runtime.md)，解析当前 Skill 目录、有效配置和 `TEMP_DIR`，再执行下文。

> **开始前**: 先说一声 "开始抓取论文 🐕" 并告知今天日期。如果是多天模式，告知抓取范围。

# 论文抓取 (Fetch + Score + Enrich)

你是 用户的论文抓取系统（3 步流水线的第 1 步）。抓取最新论文 → 打分筛选 → 富化信息 → 保存到临时文件。

## Step 0: 读取共享配置

运行 `python3 ../_shared/user_config.py`，使用其输出的合并配置（含个人配置和环境变量覆盖）。

显式生成并在后续统一使用这些变量：

- `VAULT_PATH`
- `DAILY_PAPERS_PATH`
- `KEYWORDS`
- `NEGATIVE_KEYWORDS`
- `DOMAIN_BOOST_KEYWORDS`
- `ARXIV_CATEGORIES`
- `MIN_SCORE`
- `TOP_N`（默认 10）
- `RESEARCH_INTERESTS`
- `RANKING`

其中：

- `DAILY_PAPERS_PATH = {VAULT_PATH}/{daily_papers_folder}`
- 所有关键词、分类、阈值都以共享配置为准

后续统一以共享配置和上面的变量为准。

## 解析天数

从用户输入中解析 `--days N` 参数。匹配规则：
- "过去一周"、"最近7天"、"一周的论文" → `--days 7`
- "过去3天"、"最近三天"、"抓3天" → `--days 3`
- "过去两周" → `--days 14`
- 无特殊指定 / "跑一下论文抓取" → 不加 `--days`（默认当天）

将解析出的天数存为变量 `DAYS_ARG`，在后续脚本调用中使用。

## 配置来源

配置优先级见 [Agent 运行约定](../_shared/agent-runtime.md)。所有阶段使用同一份有效配置和 `TEMP_DIR`。

## 工作流程

### Phase 1+2: Python 召回 + Jev 语义评分

用 `fetch_and_score.py` 完成 HF + arXiv 抓取、关键词召回和去重，再调用 TypeSafe Jev 的 Score 按研究兴趣评分。默认每日候选最多 30 篇，推荐最多 10 篇；多天按天数扩展。只有选中的论文进入富化和点评。

检查宿主环境有 `TYPESAFE_API_KEY`；不要输出密钥。缺失或 API 失败时停止并说明，不静默退回关键词模式。用户明确选择 `ranking.backend=keyword` 或 `--ranker keyword` 时，才跳过 Jev。

```bash
# 默认：当天
python3 ../daily-papers/fetch_and_score.py --output "{TEMP_DIR}/daily_papers_selected.json"

# 多天模式（将 N 替换为解析出的天数）
python3 ../daily-papers/fetch_and_score.py --days N --output "{TEMP_DIR}/daily_papers_selected.json"
```

根据前面解析的 `DAYS_ARG`，如果用户指定了天数就加 `--days N`，否则不加。

脚本自动完成：
- 抓取 HuggingFace Daily + Trending API 和 arXiv API
- 关键词打分（正向/负向/领域加分/trending 加分）
- 按 arXiv ID 合并去重
- 读取 `.history.json` 跨天去重（含周末模式放宽规则）
- 候选池较小时允许带历史标记的回填；相关论文不足时不凑数
- Jev 对候选逐篇给出 0–4 相关性分，保留达到 `ranking.min_score` 的前 `top_n × days` 篇
- 输出中 `score` 为 Jev 分数乘 25；保留 `keyword_score`、`jev.score`、概率分布与 confidence
- 将完整请求、结果和实际 token 用量写入 `{TEMP_DIR}/daily_papers_ranking.json`；失败报告 `usage_complete=false`，已知用量不代表完整账单

进度日志输出到 stderr，`--output` 直接写 UTF-8 JSON，避免 PowerShell 重定向改变编码；省略该参数时仍输出到 stdout。

**检查输出**：必须退出码为 0，确认输出来自本次运行；旧文件不能作为成功证据。确认 `{TEMP_DIR}/daily_papers_selected.json` 存在且包含有效 JSON 数组。如果为空数组或文件不存在，检查 stderr 诊断问题。

### Phase 3: 批量富化（enrich_papers.py 脚本）

用 `enrich_papers.py` 脚本一次性富化所有论文。脚本使用 `asyncio` + `curl` 子进程并发请求，纯 regex 解析 HTML，无需 WebFetch。

**先把 Phase 2 的最终入选结果保存到临时文件**，然后运行：

```bash
python3 ../daily-papers/enrich_papers.py "{TEMP_DIR}/daily_papers_selected.json" "{TEMP_DIR}/daily_papers_enriched.json"
```

注意：使用**两个文件路径参数（输入 + 输出）**，避免 sandbox 环境下 stdout/stderr 混淆。脚本会把第一个 `.json` 参数当作输入路径、第二个当作输出路径；如果只传一个 `.json` 它会被当作输入路径，结果走 stdout。

脚本自动完成以下工作（Semaphore(10) 限制并发，单篇超时 30 秒）：
- 并行抓取 HTML 页面 + PDF 页面
- 从 HTML 提取：figure_url、authors、affiliations、section_headers、captions、has_real_world、method_names、method_summary
- 从 PDF 提取：affiliations（通过 `pdftotext | extract_affiliations.py`）
- 如果 HTML authors 为空，fallback 到 abs 页面 `<meta>` 标签提取 authors/affiliations
- 合并优先级（脚本内部处理）：
  - figure_url: HTML curl
  - affiliations: PDF > HTML > abs fallback > Phase 1 data
  - authors: HTML > abs fallback > Phase 1 data
  - 其他字段: HTML regex 提取

**输出格式**：与输入相同的 JSON 数组，每篇论文增加以下字段：
- `figure_url` (string): 首图 URL
- `affiliations` (string): 机构列表，逗号分隔
- `authors` (string): 作者列表（可能被更完整的来源覆盖）
- `section_headers` (array): 章节标题
- `captions` (array): 图表标题
- `has_real_world` (bool): 是否包含真实实验
- `method_names` (array): 方法名列表
- `method_summary` (string): 方法描述（300-500 字）

## 输出

完成后检查 `{TEMP_DIR}/daily_papers_enriched.json` 存在且包含有效 JSON 数组。告知用户：
- 抓取了多少篇论文
- 富化成功多少篇
- 总入口调用时自动继续点评；用户单独调用本阶段时，提示下一步：`跑一下论文点评`

## 注意事项

- Phase 1+2 使用 `fetch_and_score.py` 脚本，**无需子 Agent**，默认由脚本调用 Jev API，并记录实际 token 用量
- Phase 3 使用 `enrich_papers.py` 脚本，同样无需子 Agent
- 如果脚本执行失败，检查 stderr 输出诊断问题
- 如果 arXiv API 抓取失败，脚本自动 fallback 到仅 HuggingFace 源
- 每天默认最多推荐 10 篇，若达标论文不足，有多少处理多少；不从未入选的候选中补足
- **周末策略**：arXiv 周末不更新，HF daily 周末基本为空，但 HF trending 持续更新。周末主要依赖 trending 来源
- **不做 git 操作**，不生成推荐文件，只输出临时 JSON
