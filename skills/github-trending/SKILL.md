---
name: github-trending
description: |
  抓取 GitHub 上 star 涨得最快的项目（Trending 榜），打分标注是否与研究方向相关，
  生成 Obsidian 笔记到 GitHubTrending 文件夹。默认周榜。

  触发词："GitHub 周榜"、"star 涨得最快"、"过去一周 GitHub 热门"、"GitHub trending"、
  "看看这周 GitHub 上火了什么"、"GitHub 日榜"、"GitHub 月榜"
---

> **开始前**: 先说一声 "开始抓 GitHub 榜单 🐙" 并告知今天日期与抓取周期（默认周榜）。

# GitHub Trending 抓取

抓取 GitHub Trending → 用关键词打分标注 → 写成 Obsidian 笔记。纯 Python 脚本，零 token。

## Step 0: 读取共享配置

配置在 `../_shared/user-config.json`，个人覆盖在 `../_shared/user-config.local.json`（存在则以 local 为准）。
脚本内部已通过 `../_shared/user_config.py` 自动加载，无需手动传参。相关字段：

- `paths.obsidian_vault` — vault 根路径
- `paths.github_trending_folder` — 输出文件夹（默认 `GitHubTrending`）
- `daily_papers.keywords / negative_keywords / domain_boost_keywords` — 复用它们给项目打分、标注相关性

## 解析周期与语言

从用户输入解析 `--since`：
- "周榜"、"过去一周"、"这周"、"本周" → `--since weekly`（默认）
- "日榜"、"今天"、"今日" → `--since daily`
- "月榜"、"这个月"、"本月" → `--since monthly`

可选 `--language`（如 "只看 Python" → `--language python`），不指定则抓全部语言。

## 工作流程

### Phase 1: 抓取 + 打分（fetch_trending.py）

```bash
python3 fetch_trending.py --since weekly > /tmp/github_trending.json
# 指定语言示例：
# python3 fetch_trending.py --since weekly --language python > /tmp/github_trending.json
```

脚本自动完成：
- 抓取 `github.com/trending?since=<周期>`（兼容 SSL 拦截环境，自动退回不验证证书）
- regex 解析：repo、简介、语言、累计 star/fork、本周期新增 star
- 用共享配置关键词打分，标注 `relevant`（命中正向/领域词且未被负向词压过），**不丢弃非相关项**
- 按本周期新增 star 降序排序

**检查输出**：确认 `/tmp/github_trending.json` 是非空 JSON 数组。为空则看 stderr 诊断。

### Phase 2: 写 Obsidian 笔记（write_trending_note.py）

```bash
python3 write_trending_note.py /tmp/github_trending.json
```

- 输出到 `{vault}/{github_trending_folder}/`
- 周榜文件名按 ISO 周编号，如 `2026-W28 GitHub周榜.md`；日/月榜用日期
- 笔记结构：摘要 → 「🎯 与研究方向相关」列表 → 「📊 完整榜单」表格（含 ✅ 相关标记）
- 脚本把最终笔记路径打到 stdout

## 输出

完成后告知用户：
- 抓取了多少个项目、其中多少个与研究方向相关
- 生成的笔记路径

## 注意事项

- 两个脚本都不启动 Task Agent，零 token 消耗
- **不做 git 操作**（与 daily-papers 一致，git 自动化默认关闭）
- 网络不通时参考全局 CLAUDE.md 的代理规则（17890 端口）；脚本已内置 SSL 兜底
- GitHub Trending 只有 daily/weekly/monthly 三档，无法自定义任意天数
