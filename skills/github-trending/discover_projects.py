#!/usr/bin/env python3
"""Discover new simulation projects and recent ecosystem activity beyond Trending."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from user_config import daily_papers_config


def search_repositories(query: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "dailypaper-skills",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = "https://api.github.com/search/repositories?" + urlencode(
        {"q": query, "sort": "stars", "order": "desc", "per_page": 10})
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub search HTTP {error.code}") from None
    except (URLError, OSError):
        raise RuntimeError("GitHub search connection failed") from None


def discover(queries: list[str], days: int, today: date) -> dict:
    start = (today - timedelta(days=days - 1)).isoformat()
    end = today.isoformat()
    report = {"status": "complete", "start_date": start, "end_date": end,
              "searches": [], "new_projects": [], "recently_updated": []}
    repos = {}
    for field in ("created", "pushed"):
        for topic in queries:
            query = f"{topic} {field}:{start}..{end} fork:false archived:false"
            print(f"  Searching {query}", file=sys.stderr, flush=True)
            record = {"query": query, "status": "incomplete"}
            report["searches"].append(record)
            try:
                response = search_repositories(query)
                if not isinstance(response.get("items"), list):
                    raise ValueError("GitHub returned no items array")
                record.update(status="complete", total_count=response["total_count"],
                              incomplete_results=response.get("incomplete_results", False))
                if record["incomplete_results"]:
                    report["status"] = "partial"
                for item in response["items"]:
                    if item.get("fork") or item.get("archived"):
                        continue
                    name = item["full_name"]
                    if name not in repos:
                        repos[name] = {"repo": name, "url": item["html_url"],
                                       "description": item.get("description") or "",
                                       "stars": item["stargazers_count"],
                                       "created_at": item["created_at"], "pushed_at": item["pushed_at"],
                                       "matched_queries": []}
                    repos[name]["matched_queries"].append(query)
            except (RuntimeError, ValueError, KeyError, TypeError) as error:
                record["error"] = str(error)
                report["status"] = "partial"
    for item in sorted(repos.values(), key=lambda r: (-r["stars"], r["repo"])):
        if start <= item["created_at"][:10] <= end:
            report["new_projects"].append(item)
        elif start <= item["pushed_at"][:10] <= end:
            report["recently_updated"].append(item)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")
    queries = daily_papers_config()["project_queries"]
    if not queries or not all(isinstance(q, str) and q.strip() for q in queries):
        parser.error("daily_papers.project_queries must contain search queries")
    report = discover(queries, args.days, args.date)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(report['new_projects'])} new; {len(report['recently_updated'])} recently updated; {report['status']}", file=sys.stderr)
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
