---
name: github-trending
description: |
  抓取 GitHub 上 star 涨得最快的项目（Trending 榜），打分标注是否与研究方向相关，
  生成 Obsidian 笔记到 GitHubTrending 文件夹。默认周榜。

  触发词："GitHub 周榜"、"star 涨得最快"、"过去一周 GitHub 热门"、"GitHub trending"、
  "看看这周 GitHub 上火了什么"、"GitHub 日榜"、"GitHub 月榜"
---

## 执行环境

开始前读取 [Agent 运行约定](../_shared/agent-runtime.md)，解析当前 Skill 目录、有效配置和 `TEMP_DIR`，再执行下文。

> **开始前**: 先说一声 "开始抓 GitHub 榜单 🐙" 并告知今天日期与抓取周期（默认周榜）。

# GitHub Trending 抓取

抓取 GitHub Trending + 按主题搜索仿真新项目 / 近期更新 → 标注研究相关性 → 写成 Obsidian 笔记。纯 Python 脚本，脚本本身不调用大模型。

## Step 0: 读取共享配置

运行 `python3 ../_shared/user_config.py` 读取有效配置及 `runtime.temp_dir`。
脚本内部已通过 `../_shared/user_config.py` 自动加载，无需手动传参。相关字段：

- `paths.obsidian_vault` — vault 根路径
- `paths.github_trending_folder` — 输出文件夹（默认 `GitHubTrending`）
- `daily_papers.keywords / negative_keywords / domain_boost_keywords` — 复用它们给项目打分、标注相关性
- `daily_papers.project_queries` — 广泛检索仿真引擎、求解器与相关基础设施；项目名示例不构成白名单

## 解析周期与语言

从用户输入解析 `--since`：
- "周榜"、"过去一周"、"这周"、"本周" → `--since weekly`（默认）
- "日榜"、"今天"、"今日" → `--since daily`
- "月榜"、"这个月"、"本月" → `--since monthly`

可选 `--language`（如 "只看 Python" → `--language python`），不指定则抓全部语言。

## 工作流程

### Phase 1: 抓取 + 打分（fetch_trending.py）

```bash
python3 fetch_trending.py --since weekly --output "{TEMP_DIR}/github_trending.json"
# 指定语言示例：
# python3 fetch_trending.py --since weekly --language python --output "{TEMP_DIR}/github_trending.json"
```

脚本自动完成：
- 抓取 `github.com/trending?since=<周期>`（兼容 SSL 拦截环境，自动退回不验证证书）
- regex 解析：repo、简介、语言、累计 star/fork、本周期新增 star
- 用共享配置关键词打分，标注 `relevant`（命中正向/领域词且未被负向词压过），**不丢弃非相关项**
- 按本周期新增 star 降序排序

**检查输出**：确认 `{TEMP_DIR}/github_trending.json` 是非空 JSON 数组。为空则看 stderr 诊断。

### Phase 1b: 发现新项目和生态更新

```bash
python3 discover_projects.py --days 7 --output "{TEMP_DIR}/github_projects.json"
```

按用户周期选择天数（日榜 1、周榜 7、月榜 30）。该步骤使用 GitHub Repository Search，在研究主题范围中分别查询 `created` 与 `pushed` 日期，补足 Trending 未收录的新项目。每个查询最多 10 个项目，不保证穷尽。可从环境读取 `GITHUB_TOKEN` / `GH_TOKEN`；不输出或保存密钥。

MuJoCo、Newton、Isaac Sim、PhysX、Genesis、SuperDex、mjlab、unlib、mjbatch 等仅是兴趣示例；不能因为一个新引擎不在列表中就排除。区分“近期创建的仓库”“已有项目代码更新”“正式版本发布”；搜索结果中的 `pushed_at` 只能证明代码更新。必要时阅读原仓库 README / Releases 核实，不推断发布内容。

若 API 限流或失败，JSON 标记 `status=partial` 并保留成功结果与错误；不要把空结果写成“没有新增项目”。将已生成的完整或部分结果传给笔记脚本，笔记会保留限制说明。

### Phase 2: 写 Obsidian 笔记（write_trending_note.py）

```bash
python3 write_trending_note.py "{TEMP_DIR}/github_trending.json" --projects "{TEMP_DIR}/github_projects.json"
```

- 输出到 `{vault}/{github_trending_folder}/`
- 周榜文件名按 ISO 周编号，如 `2026-W28 GitHub周榜.md`；日/月榜用日期
- 笔记结构：摘要 → 「🎯 与研究方向相关」列表 → 「📊 完整榜单」表格（含 ✅ 相关标记）
- 脚本把最终笔记路径打到 stdout

## 输出

完成后告知用户：
- 抓取了多少个热门项目、其中多少个与研究方向相关
- 新建仿真项目和近期更新项目各多少，检索是否完整
- 生成的笔记路径

## 注意事项

- 两个脚本都无需子 Agent，脚本本身不调用大模型
- **不做 git 操作**（与 daily-papers 一致，git 自动化默认关闭）
- 网络不通时检查当前宿主的网络与代理设置，不假设用户使用某个固定代理端口
- GitHub Trending 只有 daily/weekly/monthly 三档，无法自定义任意天数
