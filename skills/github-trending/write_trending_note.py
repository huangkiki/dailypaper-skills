#!/usr/bin/env python3
"""把 fetch_trending.py 的 JSON 结果写成 Obsidian 笔记。

用法:
    python3 write_trending_note.py /tmp/github_trending.json

- 读取共享配置里的 vault 路径与 github_trending_folder（默认 GitHubTrending）。
- 文件名按 ISO 周编号，如 `GitHubTrending/2026-W28 GitHub周榜.md`。
- 顶部先列「与研究方向相关」的项目，再给全量排名表。
- 纯标准库；进度日志走 stderr，最终笔记路径走 stdout。
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from user_config import obsidian_vault_path, paths_config  # noqa: E402

PERIOD_LABEL = {"daily": "日榜", "weekly": "周榜", "monthly": "月榜"}
PERIOD_UNIT = {"daily": "今日", "weekly": "本周", "monthly": "本月"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def target_dir() -> Path:
    folder = paths_config().get("github_trending_folder", "GitHubTrending")
    return obsidian_vault_path() / folder


def note_filename(period: str, today: date) -> str:
    label = PERIOD_LABEL.get(period, "榜单")
    if period == "weekly":
        iso = today.isocalendar()
        return f"{iso.year}-W{iso.week:02d} GitHub{label}.md"
    return f"{today.isoformat()} GitHub{label}.md"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def build_markdown(repos: list[dict], period: str, today: date) -> str:
    unit = PERIOD_UNIT.get(period, "")
    label = PERIOD_LABEL.get(period, "榜单")
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
        f"> {unit} star 涨得最快的 {len(repos)} 个项目，其中 **{len(relevant)}** 个与你的研究方向相关。"
    )
    lines.append("")

    if relevant:
        lines.append("## 🎯 与研究方向相关")
        lines.append("")
        for r in relevant:
            kws = "、".join(r.get("matched_keywords", []))
            lang = f" · `{r['language']}`" if r.get("language") else ""
            lines.append(
                f"- **[{r['repo']}]({r['url']})** — ⭐ +{r['stars_period']:,} {unit}"
                f"（累计 {r['stars_total']:,}）{lang}"
            )
            if r.get("description"):
                lines.append(f"  - {r['description']}")
            if kws:
                lines.append(f"  - 命中关键词: {kws}")
        lines.append("")

    lines.append(f"## 📊 完整{label}")
    lines.append("")
    lines.append(f"| # | 项目 | {unit}新增⭐ | 累计⭐ | 语言 | 相关 | 简介 |")
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
        f"*生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 数据源 github.com/trending?since={period}*"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        log("用法: python3 write_trending_note.py <input.json>")
        return 1
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not data:
        log("⚠️  输入为空，未生成笔记")
        return 1

    period = data[0].get("period", "weekly")
    today = date.today()

    out_dir = target_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / note_filename(period, today)

    out_path.write_text(build_markdown(data, period, today), encoding="utf-8")
    log(f"✅ 已写入: {out_path}")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
