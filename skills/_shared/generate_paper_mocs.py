#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path


_SHARED_DIR = Path(__file__).resolve().parent
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from moc_builder import build_tree_mocs
from user_config import obsidian_vault_path, paper_notes_dir, paths_config


def main() -> int:
    summary = build_tree_mocs(
        vault_root=obsidian_vault_path(),
        root_dir=paper_notes_dir(),
        title_prefix="论文目录页",
        intro="用于浏览论文笔记、分类目录和子主题入口。",
        exclude_dir_names={paths_config()["concepts_folder"]},
    )
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
