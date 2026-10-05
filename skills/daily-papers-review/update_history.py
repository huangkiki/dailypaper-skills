#!/usr/bin/env python3
"""
update_history.py - Update the recommendation history file.

This script is part of daily-papers-review (Phase 6).

Usage:
    python3 update_history.py --arxiv-ids ID1 ID2 ... --date YYYY-MM-DD
    python3 update_history.py --from-enriched /tmp/daily_papers_enriched.json --date YYYY-MM-DD
    python3 update_history.py --from-recommendation YYYY-MM-DD-论文推荐.md --date YYYY-MM-DD

    # Cross-platform (auto-detect paths)
    python3 update_history.py --date 2026-03-17

The script:
1. Reads existing history from {vault}/DailyPapers/.history.json
2. Adds new entries for papers not already in history
3. Preserves the earliest date for papers that are re-recommended
4. Removes entries older than 30 days
5. Writes back to .history.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from user_config import obsidian_vault_path, temp_file_path

HISTORY_FILE = obsidian_vault_path() / "DailyPapers" / ".history.json"
DAYS_TO_KEEP = 30


def load_history() -> list:
    """Load existing history or return empty list."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_history(history: list):
    """Save history to file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def extract_arxiv_id_from_url(url: str) -> str:
    """Extract arXiv ID from URL."""
    m = re.search(r'arxiv\.org/abs/(\d+\.\d+)', url)
    return m.group(1) if m else ""


def load_from_enriched(path: str) -> list:
    """Load papers from enriched JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        papers = json.load(f)

    entries = []
    for p in papers:
        arxiv_id = p.get('arxiv_id', '')
        if not arxiv_id:
            url = p.get('url', '')
            arxiv_id = extract_arxiv_id_from_url(url)

        if arxiv_id:
            entries.append({
                'id': arxiv_id,
                'title': p.get('title', '')[:200],
                'score': p.get('score', 0),
            })
    return entries


def load_from_recommendation(path: str) -> list:
    """Load papers from recommendation markdown file."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract arXiv IDs from links
    arxiv_ids = re.findall(r'arxiv\.org/abs/(\d+\.\d+)', content)

    # Extract paper titles (### N. Title pattern)
    titles = {}
    for m in re.finditer(r'^### \d+\. (.+)$', content, re.MULTILINE):
        title = m.group(1).strip()
        # Extract arXiv ID from nearby lines
        idx = len(titles)
        titles[idx] = title

    entries = []
    for arxiv_id in arxiv_ids:
        entries.append({
            'id': arxiv_id,
            'title': '',  # Would need more complex parsing to match
        })
    return entries


def update_history(entries: list, date: str, preserve_earliest: bool = True):
    """Update history with new entries."""
    history = load_history()

    # Build index of existing IDs
    existing_ids = {h.get('id') for h in history if h.get('id')}

    # Add new entries
    added = 0
    for entry in entries:
        arxiv_id = entry.get('id', '')
        if not arxiv_id:
            continue

        if arxiv_id not in existing_ids:
            history.append({
                'id': arxiv_id,
                'date': date,
                'title': entry.get('title', ''),
            })
            existing_ids.add(arxiv_id)
            added += 1
        elif preserve_earliest:
            # Update to preserve earliest date
            for h in history:
                if h.get('id') == arxiv_id:
                    if h.get('date', '') > date:
                        h['date'] = date
                    break

    # Remove old entries (older than 30 days)
    cutoff_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=DAYS_TO_KEEP)).strftime('%Y-%m-%d')
    history = [h for h in history if h.get('date', '') >= cutoff_date]

    save_history(history)
    return added


def main():
    parser = argparse.ArgumentParser(description='Update recommendation history')
    parser.add_argument('--arxiv-ids', nargs='+', help='arXiv IDs to add')
    parser.add_argument('--from-enriched', help='Path to enriched JSON file')
    parser.add_argument('--from-recommendation', help='Path to recommendation markdown file')
    parser.add_argument('--date', required=True, help='Date (YYYY-MM-DD)')

    args = parser.parse_args()

    entries = []

    if args.arxiv_ids:
        entries = [{'id': aid, 'title': ''} for aid in args.arxiv_ids]
    elif args.from_enriched:
        entries = load_from_enriched(args.from_enriched)
    elif args.from_recommendation:
        entries = load_from_recommendation(args.from_recommendation)
    else:
        # Auto-detect: try to load from default temp path
        auto_enriched = temp_file_path('daily_papers_enriched.json')
        if auto_enriched.exists():
            print(f"[update_history] Auto-detected input: {auto_enriched}", file=sys.stderr)
            entries = load_from_enriched(str(auto_enriched))
        else:
            print("Error: Must specify --arxiv-ids, --from-enriched, or --from-recommendation", file=sys.stderr)
            print(f"  Or ensure {temp_file_path('daily_papers_enriched.json')} exists", file=sys.stderr)
            sys.exit(1)

    added = update_history(entries, args.date)
    print(f"Added {added} new entries to history")


if __name__ == '__main__':
    main()
