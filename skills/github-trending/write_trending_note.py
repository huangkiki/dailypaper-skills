#!/usr/bin/env python3
"""把 fetch_trending.py 的 JSON 结果写成 Obsidian 笔记。

用法:
    python3 write_trending_note.py /tmp/github_trending.json

- 读取共享配置里的 vault 路径与 github_trending_folder（默认 GitHubTrending）。
- 文件名按 ISO 周编号，如 `GitHubTrending/2026-W28 GitHub周榜.md`。
- 顶部先列「与研究方向相关」的项目，再给全量排名表。
- 纯标准库；进度日志走 stderr，最终笔记路径走 stdout。
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from user_config import obsidian_vault_path, paths_config  # noqa: E402

PERIOD_LABEL = {"daily": "日榜", "weekly": "周榜", "monthly": "月榜"}
PERIOD_UNIT = {"daily": "今日", "weekly": "本周", "monthly": "本月"}
EN_PERIOD_LABEL = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}
EN_PERIOD_UNIT = {"daily": "today", "weekly": "this week", "monthly": "this month"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def target_dir() -> Path:
    folder = paths_config().get("github_trending_folder", "GitHubTrending")
    return obsidian_vault_path() / folder


def note_filename(period: str, today: date, output_language: str = "zh") -> str:
    label = PERIOD_LABEL.get(period, "榜单")
    if output_language == "en":
        label = " " + EN_PERIOD_LABEL[period]
    if period == "weekly":
        iso = today.isocalendar()
        return f"{iso.year}-W{iso.week:02d} GitHub{label}.md"
    return f"{today.isoformat()} GitHub{label}.md"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def build_markdown(repos: list[dict], period: str, today: date, projects: dict | None = None,
                   output_language: str = "zh") -> str:
    if output_language not in {"zh", "en"}:
        raise ValueError("output_language must be zh or en")
    english = output_language == "en"
    unit = EN_PERIOD_UNIT[period] if english else PERIOD_UNIT.get(period, "")
    label = EN_PERIOD_LABEL[period] if english else PERIOD_LABEL.get(period, "榜单")
    relevant = [r for r in repos if r.get("relevant")]

    lines: list[str] = []
    lines.append("---")
    lines.append(f"date: {today.isoformat()}")
    lines.append(f"type: github-trending")
    lines.append(f"period: {period}")
    lines.append("tags: [github, trending]")
    lines.append("---")
    lines.append("")
    lines.append(f"# GitHub {label} · {today.isoformat()}")
    lines.append("")
    lines.append(
        f"> {len(repos)} trending repositories {unit}; **{len(relevant)}** match your research interests."
        if english else f"> {unit} star 涨得最快的 {len(repos)} 个项目，其中 **{len(relevant)}** 个与你的研究方向相关。"
    )
    lines.append("")

    if relevant:
        lines.append("## 🎯 Relevant to your research" if english else "## 🎯 与研究方向相关")
        lines.append("")
        for r in relevant:
            kws = (", " if english else "、").join(r.get("matched_keywords", []))
            lang = f" · `{r['language']}`" if r.get("language") else ""
            total = f" (total {r['stars_total']:,})" if english else f"（累计 {r['stars_total']:,}）"
            lines.append(
                f"- **[{r['repo']}]({r['url']})** — ⭐ +{r['stars_period']:,} {unit}"
                f"{total}{lang}"
            )
            if r.get("description"):
                lines.append(f"  - {r['description']}")
            if kws:
                lines.append(f"  - Matched keywords: {kws}" if english else f"  - 命中关键词: {kws}")
        lines.append("")

    if projects is not None:
        lines.extend([
            "## New simulation projects and ecosystem updates" if english else "## 仿真新项目与生态更新", "",
            f"Search window: {projects['start_date']} to {projects['end_date']}; topic-based discovery, not a fixed project list."
            if english else f"检索范围：{projects['start_date']} 至 {projects['end_date']}；按主题发现，不限已知项目名。",
            "At most 10 results per query; coverage is not exhaustive. A code push is not a release."
            if english else "每个检索式最多取 10 项，不保证穷尽；代码推送不等于新版本发布。", ""])
        if projects.get("status") != "complete":
            lines.extend(["> Some searches failed or returned incomplete results; an empty list does not prove there are no new projects."
                          if english else "> 部分检索失败或结果不完整；空列表不能证明没有新项目。", ""])
        headings = (("new_projects", "Newly created" if english else "期间新建"),
                    ("recently_updated", "Recently updated" if english else "已有项目近期更新"))
        for key, heading in headings:
            lines.extend([f"### {heading}", ""])
            items = projects.get(key, [])
            for repo in items:
                details = (f"(⭐ {repo['stars']:,}; created {repo['created_at'][:10]}; pushed {repo['pushed_at'][:10]})"
                           if english else f"（⭐ {repo['stars']:,}；创建 {repo['created_at'][:10]}；推送 {repo['pushed_at'][:10]}）")
                lines.append(f"- [{repo['repo']}]({repo['url']}) — {md_escape(repo['description'])} {details}")
            if not items:
                lines.append("No projects returned by this search." if english else "本次检索未返回项目。")
            lines.append("")

    lines.append(f"## 📊 Full {label.lower()} ranking" if english else f"## 📊 完整{label}")
    lines.append("")
    lines.append(f"| # | Repository | Stars {unit} | Total stars | Language | Relevant | Description |"
                 if english else f"| # | 项目 | {unit}新增⭐ | 累计⭐ | 语言 | 相关 | 简介 |")
    lines.append("| --- | --- | ---: | ---: | --- | :---: | --- |")
    for r in repos:
        flag = "✅" if r.get("relevant") else ""
        desc = md_escape(r.get("description", ""))
        if len(desc) > 80:
            desc = desc[:79] + "…"
        lines.append(
            f"| {r['rank']} | [{md_escape(r['repo'])}]({r['url']}) "
            f"| +{r['stars_period']:,} | {r['stars_total']:,} "
            f"| {r.get('language','')} | {flag} | {desc} |"
        )
    lines.append("")
    lines.append(
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Source: github.com/trending?since={period}*"
        if english else f"*生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 数据源 github.com/trending?since={period}*"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--projects", type=Path, help="Optional discover_projects.py result")
    parser.add_argument("--period", choices=tuple(PERIOD_LABEL), default="weekly")
    parser.add_argument("--output-language", choices=("zh", "en"), default="zh",
                        help="Language of the note; unrelated to the programming-language filter")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    projects = json.loads(args.projects.read_text(encoding="utf-8")) if args.projects else None
    if not data and projects is None:
        log("⚠️  Empty input; no note generated" if args.output_language == "en" else "⚠️  输入为空，未生成笔记")
        return 1

    period = data[0].get("period", args.period) if data else args.period
    today = date.today()

    out_dir = target_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / note_filename(period, today, args.output_language)

    out_path.write_text(build_markdown(data, period, today, projects, args.output_language), encoding="utf-8")
    log(f"✅ Written: {out_path}" if args.output_language == "en" else f"✅ 已写入: {out_path}")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
