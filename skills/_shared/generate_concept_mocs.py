#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_SHARED_DIR = Path(__file__).resolve().parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from moc_builder import build_tree_mocs
from user_config import concepts_dir, obsidian_vault_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate concept indexes")
    parser.add_argument("--output-language", choices=("zh", "en"), default="zh")
    args = parser.parse_args()
    english = args.output_language == "en"
    summary = build_tree_mocs(
        vault_root=obsidian_vault_path(),
        root_dir=concepts_dir(),
        title_prefix="Concept index" if english else "概念目录页",
        intro="Browse concept notes and their categories." if english else "用于浏览概念笔记和对应分类入口。",
        output_language=args.output_language,
    )
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
