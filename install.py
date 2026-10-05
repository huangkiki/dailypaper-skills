#!/usr/bin/env python3
"""Install the complete skill bundle without dropping its shared dependencies."""

import argparse
import os
import shutil
from collections.abc import Iterator, Sequence
from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "skills"
AGENT_DIRS = {
    "agents": ".agents/skills",
    "claude": ".claude/skills",
    "codex": ".agents/skills",
    "cursor": ".cursor/skills",
    "copilot": ".copilot/skills",
    "gemini": ".gemini/skills",
    "opencode": ".config/opencode/skills",
    "openclaw": ".openclaw/skills",
}
PERSONAL_FILES = {"user-config.local.json", "collection_mapping.json"}


def bundle_files() -> Iterator[Path]:
    """Ship skills and _shared, excluding machine-local data and Python caches."""
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(SOURCE)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        if path.suffix == ".pyc" or path.name in PERSONAL_FILES:
            continue
        yield relative


def install(targets: Sequence[Path], *, update: bool = False, dry_run: bool = False) -> int:
    files = list(bundle_files())
    copies = []
    # Preflight every target before writing anything, including on multi-agent installs.
    for target in targets:
        resolved = target.resolve()
        if resolved == SOURCE or SOURCE in resolved.parents or resolved in SOURCE.parents:
            raise ValueError(f"Target overlaps the source bundle: {target}")
        for relative in files:
            destination = target / relative
            for path in (destination, *destination.parents):
                if path == target.parent:
                    break
                if path.is_symlink():
                    raise ValueError(f"Refusing to overwrite a symlink: {path}")
                if path != destination and path.exists() and not path.is_dir():
                    raise ValueError(f"Expected a directory: {path}")
            if destination.exists():
                if not destination.is_file():
                    raise ValueError(f"Expected a file: {destination}")
                if relative == Path("_shared/user-config.json"):
                    continue  # Preserve older installations' personal configuration.
                if destination.read_bytes() == (SOURCE / relative).read_bytes():
                    continue
                if not update:
                    raise ValueError(f"Existing file differs: {destination}. Use --update to replace bundle files.")
            copies.append((SOURCE / relative, destination))

    for source, destination in copies:
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return len(copies)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--agent", nargs="+", choices=AGENT_DIRS,
                             help="Agent(s) to install for; agents uses the shared .agents/skills directory")
    destination.add_argument("--target", type=Path, help="Custom skill root, including project-local directories")
    parser.add_argument("--update", action="store_true", help="Replace changed bundle files; keep user configuration")
    parser.add_argument("--dry-run", action="store_true", help="Check the install and print destinations without writing")
    args = parser.parse_args()
    if args.target is not None:
        targets = [args.target.expanduser().absolute()]
    else:
        targets = []
        for agent in args.agent:
            path = Path.home() / AGENT_DIRS[agent]
            if agent == "opencode" and os.environ.get("XDG_CONFIG_HOME"):
                path = Path(os.environ["XDG_CONFIG_HOME"]).expanduser() / "opencode/skills"
            targets.append(path.absolute())
    targets = list(dict.fromkeys(targets))
    try:
        count = install(targets, update=args.update, dry_run=args.dry_run)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Install failed: {exc}\n")
    for target in targets:
        print(f"{'Would install' if args.dry_run else 'Installed'} bundle: {target}")
    print(f"{'Planned' if args.dry_run else 'Copied'} {count} files; existing personal configuration preserved.")
    print("Restart/reload your agent to discover the skills. See README.md for shared configuration.")


if __name__ == "__main__":
    main()
