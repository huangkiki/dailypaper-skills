#!/usr/bin/env python3
"""抓取 GitHub Trending 周榜（star 涨得最快的项目），打分标注，输出 JSON。

用法:
    python3 fetch_trending.py [--since weekly|daily|monthly] [--language python] > /tmp/github_trending.json

- 纯标准库，零 token 消耗，进度日志走 stderr，JSON 结果走 stdout。
- 自动处理 SSL 拦截环境：先走验证连接，失败再退回不验证的 context。
- 用共享配置里的关键词给每个项目打分并标注是否与研究方向相关（不丢弃非相关项）。
"""

import argparse
import html as ihtml
import json
import re
import ssl
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

# 复用 _shared 里的配置加载器
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
try:
    from user_config import daily_papers_config
except Exception:  # pragma: no cover - 配置缺失时的兜底
    daily_papers_config = None


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fetch_html(url: str, timeout: int = 30) -> str:
    """抓取 HTML，兼容 SSL 被中间人拦截的环境。"""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 github-trending-bot/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (ssl.SSLError, URLError) as exc:
        # SSL 拦截环境下证书验证会失败（可能被包成 URLError），退回不验证证书重试
        reason = getattr(exc, "reason", exc)
        if not isinstance(exc, ssl.SSLError) and not isinstance(reason, ssl.SSLError):
            raise
        log(f"⚠️  SSL 验证失败({reason})，退回不验证证书重试")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="replace")


def strip_tags(fragment: str) -> str:
    return ihtml.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_trending(html_text: str, period: str) -> list[dict]:
    period_word = {"daily": "today", "weekly": "this week", "monthly": "this month"}[period]
    rows = re.split(r'<article class="Box-row">', html_text)[1:]
    repos: list[dict] = []
    for block in rows:
        m = re.search(r'<h2[^>]*>\s*<a\b[^>]*\shref="/([^"]+)"', block)
        if not m:
            continue
        full = m.group(1).strip().strip("/")
        if full.count("/") != 1:
            continue
        owner, name = full.split("/", 1)

        desc_m = re.search(r'<p class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', block, re.S)
        description = strip_tags(desc_m.group(1)) if desc_m else ""

        lang_m = re.search(r'itemprop="programmingLanguage">\s*([^<]+?)\s*</span>', block)
        language = lang_m.group(1).strip() if lang_m else ""

        totals = re.findall(r"Link--muted[^>]*>\s*<svg[\s\S]*?</svg>\s*([\d,]+)", block)

        def to_int(x: str) -> int:
            return int(x.replace(",", "")) if x else 0

        stars_total = to_int(totals[0]) if len(totals) >= 1 else 0
        forks_total = to_int(totals[1]) if len(totals) >= 2 else 0

        wk_m = re.search(rf"([\d,]+)\s+stars\s+{re.escape(period_word)}", block)
        stars_period = to_int(wk_m.group(1)) if wk_m else 0

        repos.append(
            {
                "repo": full,
                "owner": owner,
                "name": name,
                "url": f"https://github.com/{full}",
                "description": description,
                "language": language,
                "stars_total": stars_total,
                "forks_total": forks_total,
                "stars_period": stars_period,
                "period": period,
            }
        )
    return repos


def load_keywords():
    if daily_papers_config is None:
        return [], [], []
    cfg = daily_papers_config()
    return (
        [k.lower() for k in cfg.get("keywords", [])],
        [k.lower() for k in cfg.get("negative_keywords", [])],
        [k.lower() for k in cfg.get("domain_boost_keywords", [])],
    )


def score_repo(repo: dict, keywords, negatives, boosts) -> None:
    text = f"{repo['repo']} {repo['description']} {repo['language']}".lower()
    matched = [k for k in keywords if k in text]
    boosted = [k for k in boosts if k in text]
    negatived = [k for k in negatives if k in text]
    score = 2 * len(matched) + len(boosted) - 3 * len(negatived)
    repo["score"] = score
    repo["matched_keywords"] = sorted(set(matched + boosted))
    # 与研究方向相关：命中正向/领域词且未被强负向词压过
    repo["relevant"] = bool(matched or boosted) and score >= 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="weekly", choices=["daily", "weekly", "monthly"])
    ap.add_argument("--language", default="", help="按语言过滤，如 python / rust；留空为全部")
    args = ap.parse_args()

    url = f"https://github.com/trending?since={args.since}"
    if args.language:
        url += f"&l={args.language}"

    log(f"🐙 抓取 GitHub Trending: {url}")
    html_text = fetch_html(url)
    repos = parse_trending(html_text, args.since)
    log(f"   解析到 {len(repos)} 个项目")

    keywords, negatives, boosts = load_keywords()
    for r in repos:
        score_repo(r, keywords, negatives, boosts)

    repos.sort(key=lambda r: r["stars_period"], reverse=True)
    for i, r in enumerate(repos, 1):
        r["rank"] = i

    relevant_n = sum(1 for r in repos if r["relevant"])
    log(f"   其中与研究方向相关: {relevant_n} 个")

    json.dump(repos, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
