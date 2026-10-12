#!/usr/bin/env python3
"""
backfill_links.py - Backfill paper note links to recommendation file.

This script is part of daily-papers-notes (Step 3).

Usage:
    python3 backfill_links.py --recommendation YYYY-MM-DD-论文推荐.md
    python3 backfill_links.py --recommendation YYYY-MM-DD-论文推荐.md --notes-dir 论文笔记

The script:
1. Scans the notes directory for existing paper notes
2. Matches papers in the recommendation file with existing notes
3. Inserts note links after the "来源" / "Source" line for each matched paper
4. Updates "分流表" / "Reading priorities" to use the actual note filenames
"""

import argparse
import re
import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from user_config import paper_notes_dir, paths_config


def scan_notes(notes_dir: Path | None = None) -> dict:
    """Scan notes directory and build index of {method_name: note_path}."""
    notes_index = {}
    notes_dir = notes_dir if notes_dir is not None else paper_notes_dir()
    concepts_path = notes_dir / paths_config()["concepts_folder"]

    if not notes_dir.exists():
        return notes_index

    # Scan all subdirectories (exclude _concept folder)
    for md_file in notes_dir.rglob('*.md'):
        # Skip concept notes
        if md_file.is_relative_to(concepts_path) or md_file.stem == md_file.parent.name:
            continue

        # Use filename (without .md) as method name
        method_name = md_file.stem
        notes_index[method_name.lower()] = {
            'name': method_name,
            'path': md_file.relative_to(notes_dir.parent),
        }

    return notes_index


def extract_method_name_from_title(title: str) -> str:
    """Extract method name from paper title.

    Examples:
        "NavThinker: Action-Conditioned..." -> "NavThinker"
        "HapticVLA: Contact-Rich..." -> "HapticVLA"
        "ForceVLA2: Unleashing..." -> "ForceVLA2"
    """
    # Try to find text before colon
    if ':' in title:
        method_name = title.split(':')[0].strip()
        # Clean up common patterns
        method_name = re.sub(r'^\d+\.\s*', '', method_name)  # Remove "1. " prefix
        return method_name
    return title.split()[0] if title else ""


def match_papers_with_notes(content: str, notes_index: dict) -> list:
    """Match papers in recommendation with existing notes.

    Returns list of dicts with paper_title, method_name, note_name, section_start, source_line_end
    """
    matches = []

    # Find all paper sections (### N. Title pattern)
    for m in re.finditer(r'^### \d+\. (.+)$', content, re.MULTILINE):
        paper_title = m.group(1).strip()
        section_start = m.start()

        # Find the next section end
        next_section = re.search(r'^#{1,3} ', content[m.end():], re.MULTILINE)
        section_end = m.end() + next_section.start() if next_section else len(content)

        section_content = content[section_start:section_end]

        # Extract method name from title
        method_name = extract_method_name_from_title(paper_title)

        # Look for "来源" line
        source_match = re.search(r'^- \*\*(来源|Source)\*\*:.*$', section_content, re.MULTILINE)
        if not source_match:
            continue

        source_line_end = source_match.end()

        # Check if note link already exists
        if re.search(r'- 📒 \*\*(?:笔记|已有笔记|Note|Existing note)\*\*:', section_content):
            continue  # Already has note link

        # Try to match with existing notes
        method_lower = method_name.lower()
        if method_lower in notes_index:
            matches.append({
                'paper_title': paper_title,
                'method_name': method_name,
                'note_name': notes_index[method_lower]['name'],
                'note_label': 'Note' if source_match.group(1) == 'Source' else '笔记',
                'section_start': section_start,
                'source_line_end': section_start + source_line_end,
            })

    return matches


def backfill_links(recommendation_path: Path, notes_index: dict) -> int:
    """Backfill note links to recommendation file."""
    with open(recommendation_path, 'r', encoding='utf-8') as f:
        content = f.read()

    matches = match_papers_with_notes(content, notes_index)

    if not matches:
        print("No papers matched with existing notes")
        return 0

    # Insert note links (in reverse order to preserve positions)
    for match in reversed(matches):
        insert_text = f'\n- 📒 **{match["note_label"]}**: [[{match["note_name"]}]]'
        content = (
            content[:match['source_line_end']] +
            insert_text +
            content[match['source_line_end']:]
        )

    with open(recommendation_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Update 分流表 wikilinks
    update_diversion_table(recommendation_path, notes_index, matches)

    return len(matches)


def update_diversion_table(recommendation_path: Path, notes_index: dict, matches: list):
    """Update the 分流表 section to use correct wikilink names."""
    with open(recommendation_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find 分流表 section
    table_match = re.search(r'^## (?:分流表|Reading priorities)$.+?(?=^##|\Z)', content, re.MULTILINE | re.DOTALL)
    if not table_match:
        return

    table_start = table_match.start()
    table_end = table_match.end()
    table_content = content[table_start:table_end]

    # Update wikilinks for papers that have notes
    for match in matches:
        if match['method_name'] != match['note_name']:
            # Update the wikilink but keep the description
            table_content = re.sub(
                rf'\[\[{re.escape(match["method_name"])}\]\]',
                f'[[{match["note_name"]}]]',
                table_content,
                flags=re.IGNORECASE
            )

    # Replace the table in content
    content = content[:table_start] + table_content + content[table_end:]

    with open(recommendation_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description='Backfill paper note links')
    parser.add_argument('--recommendation', required=True, help='Path to recommendation file')
    parser.add_argument('--notes-dir', help='Path to notes directory (default: from config)')

    args = parser.parse_args()

    recommendation_path = Path(args.recommendation)
    if not recommendation_path.exists():
        print(f"Error: Recommendation file not found: {recommendation_path}", file=sys.stderr)
        sys.exit(1)

    # Scan notes
    notes_index = scan_notes(Path(args.notes_dir) if args.notes_dir else None)
    print(f"Found {len(notes_index)} paper notes")

    # Backfill links
    count = backfill_links(recommendation_path, notes_index)
    print(f"Added {count} note links to recommendation file")


if __name__ == '__main__':
    main()
