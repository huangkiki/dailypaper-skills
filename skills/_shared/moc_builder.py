#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class MOCSummary:
    root_dir: Path
    total_directories: int = 0
    created_files: int = 0
    updated_files: int = 0
    unchanged_files: int = 0
    indexed_notes: int = 0

    def to_dict(self) -> dict:
        return {
            "root_dir": str(self.root_dir),
            "total_directories": self.total_directories,
            "created_files": self.created_files,
            "updated_files": self.updated_files,
            "unchanged_files": self.unchanged_files,
            "indexed_notes": self.indexed_notes,
        }


def build_tree_mocs(
    *,
    vault_root: Path,
    root_dir: Path,
    title_prefix: str,
    intro: str,
    exclude_dir_names: Iterable[str] = (),
) -> MOCSummary:
    root_dir.mkdir(parents=True, exist_ok=True)
    summary = MOCSummary(root_dir=root_dir)
    excluded = set(exclude_dir_names)

    directories = [root_dir]
    directories.extend(_iter_child_dirs(root_dir, excluded))

    for directory in directories:
        summary.total_directories += 1
        notes = _note_files(directory)
        summary.indexed_notes += len(notes)
        content = _build_moc_content(
            vault_root=vault_root,
            root_dir=root_dir,
            directory=directory,
            title_prefix=title_prefix,
            intro=intro,
            exclude_dir_names=excluded,
        )
        moc_path = directory / f"{directory.name}.md"
        if not moc_path.exists():
            moc_path.write_text(content, encoding="utf-8")
            summary.created_files += 1
            continue
        previous = moc_path.read_text(encoding="utf-8")
        if previous == content:
            summary.unchanged_files += 1
            continue
        moc_path.write_text(content, encoding="utf-8")
        summary.updated_files += 1

    return summary


def _iter_child_dirs(root_dir: Path, exclude_dir_names: set[str]) -> list[Path]:
    result = []
    queue = [root_dir]

    while queue:
        current = queue.pop(0)
        for path in sorted(current.iterdir(), key=lambda child: child.name):
            if not path.is_dir() or path.name.startswith(".") or path.name in exclude_dir_names:
                continue
            result.append(path)
            queue.append(path)

    return result


def _subdirs(directory: Path, exclude_dir_names: set[str]) -> list[Path]:
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_dir() and not path.name.startswith(".") and path.name not in exclude_dir_names
        ),
        key=lambda path: path.name,
    )


def _note_files(directory: Path) -> list[Path]:
    moc_name = f"{directory.name}.md"
    return sorted(
        (
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix == ".md"
            and not path.name.startswith(".")
            and path.name != moc_name
        ),
        key=lambda path: path.name,
    )


def _build_moc_content(
    *,
    vault_root: Path,
    root_dir: Path,
    directory: Path,
    title_prefix: str,
    intro: str,
    exclude_dir_names: set[str],
) -> str:
    relative_dir = directory.relative_to(root_dir)
    display_name = _display_name(root_dir, directory)

    frontmatter = "\n".join(
        [
            "---",
            "tags: [MOC, auto-generated]",
            "generated_by: dailypaper-skills",
            "---",
            "",
        ]
    )

    lines = [
        f"# {title_prefix}：{display_name}",
        "",
        intro,
        "",
    ]

    if directory == root_dir:
        lines.append(f"- 根目录：`{root_dir}`")
    else:
        lines.append(f"- 当前目录：`{relative_dir.as_posix()}`")
    lines.append("")

    subdirs = _subdirs(directory, exclude_dir_names)
    notes = _note_files(directory)

    if subdirs:
        lines.extend(["## 子目录", ""])
        for subdir in subdirs:
            note_count = len(_note_files(subdir))
            child_count = len(_subdirs(subdir, exclude_dir_names))
            lines.append(
                f"- [[{_wikilink(subdir / f'{subdir.name}.md', vault_root)}|{subdir.name}]]"
                f" · {note_count} 篇笔记 · {child_count} 个子目录"
            )
        lines.append("")

    if notes:
        lines.extend(["## 当前目录笔记", ""])
        for note in notes:
            lines.append(f"- [[{_wikilink(note, vault_root)}|{note.stem}]]")
        lines.append("")

    if not subdirs and not notes:
        lines.extend(["## 当前目录笔记", "", "- 暂无内容", ""])

    lines.extend(
        [
            "## 说明",
            "",
            "- 这个目录页由脚本自动生成。",
            "- 你手动新增、移动或重命名笔记后，可以再运行一次“更新索引”。",
            "",
        ]
    )

    return frontmatter + "\n".join(lines)


def _display_name(root_dir: Path, directory: Path) -> str:
    if directory == root_dir and directory.name.startswith("_"):
        return directory.name.lstrip("_") or directory.name
    return directory.name


def _wikilink(path: Path, vault_root: Path) -> str:
    return path.relative_to(vault_root).with_suffix("").as_posix()
