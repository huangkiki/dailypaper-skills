#!/usr/bin/env python3

import argparse
import copy
import json
import os
import sys
from functools import lru_cache
from pathlib import Path


def get_temp_dir() -> Path:
    """Get platform-appropriate temp directory for daily papers data.

    On Windows: ~/tmp/ (e.g., C:/Users/username/tmp/)
    On Linux/Mac: /tmp/
    DAILYPAPER_TEMP_DIR overrides both defaults for isolated runs.
    """
    if os.environ.get("DAILYPAPER_TEMP_DIR"):
        tmp_dir = Path(os.environ["DAILYPAPER_TEMP_DIR"]).expanduser()
    elif sys.platform == 'win32':
        # Windows: use user's home directory under ~/tmp
        tmp_dir = Path.home() / 'tmp'
    else:
        # Linux/Mac: use /tmp
        tmp_dir = Path('/tmp')

    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


DEFAULT_CONFIG = {
    "paths": {
        "obsidian_vault": "~/ObsidianVault",
        "paper_notes_folder": "论文笔记",
        "daily_papers_folder": "DailyPapers",
        "github_trending_folder": "GitHubTrending",
        "concepts_folder": "_概念",
        "zotero_db": "~/Zotero/zotero.sqlite",
        "zotero_storage": "~/Zotero/storage"
    },
    "daily_papers": {
        "keywords": [
            "reinforcement learning",
            "rlhf",
            "rlvr",
            "grpo",
            "rl infrastructure",
            "rl infra",
            "distributed rollout",
            "policy optimization",
            "verl",
            "slime",
            "areal",
            "world model",
            "jepa",
            "joint embedding predictive",
            "latent dynamics",
            "dexterous",
            "in-hand manipulation",
            "multi-finger",
            "robot hand",
            "hand simulation",
            "contact-rich",
            "differentiable simulation",
            "gpu simulation",
            "batched simulation",
            "superdex",
            "mjlab",
            "unlib",
            "unilab",
            "unisim",
            "mjbatch",
            "mujoco",
            "physics engine",
            "physics simulator",
            "robotics simulation",
            "simulation framework",
            "simulation engine",
            "rigid body",
            "soft body",
            "deformable simulation",
            "contact solver",
            "gpu physics",
            "parallel simulation",
            "newton",
            "isaac sim",
            "isaacsim",
            "physx",
            "genesis"
        ],
        "negative_keywords": [
            "medical imaging",
            "weather forecast",
            "climate prediction",
            "protein folding",
            "drug discovery",
            "speech synthesis",
            "music generation"
        ],
        "domain_boost_keywords": [
            "rollout",
            "post-training",
            "reasoning",
            "contact dynamics",
            "sim-to-real",
            "sim2real",
            "physics simulation",
            "manipulation",
            "grasping"
        ],
        "arxiv_categories": [
            "cs.RO",
            "cs.LG",
            "cs.AI",
            "cs.CL",
            "cs.DC",
            "cs.CV"
        ],
        "min_score": 2,
        "top_n": 10,
        "research_interests": [
            "Reinforcement learning for large language models: RLHF, RLVR, GRPO, policy optimization, reasoning and agent training.",
            "RL infrastructure: distributed training, rollout generation, inference/training scheduling, scalable RL systems such as verl, slime and AReaL.",
            "World models, especially the JEPA family: I-JEPA, V-JEPA, V-JEPA 2, joint-embedding predictive architectures and action-conditioned latent prediction.",
            "Dexterous manipulation tasks: multi-finger hand control, in-hand manipulation, grasping, contact-rich tasks and robot learning.",
            "Dexterous-hand physics simulation and sim-to-real: contact dynamics, differentiable simulation, GPU parallel environments and batched simulation.",
            "Physics simulation engines and emerging simulation infrastructure for robotics and embodied AI: rigid/soft-body dynamics, contact solvers, GPU parallel simulation, differentiable simulation and sim-to-real. Examples include MuJoCo, Newton, Isaac Sim, PhysX, Genesis, SuperDex, mjlab, unlib, UniLab and mjbatch. These are examples, not a whitelist: discover relevant new projects and ecosystem advances too."
        ],
        "candidate_pool_size": 30,
        "ranking": {
            "backend": "jev",
            "model": "jev-1.13.0",
            "batch_size": 30,
            "min_score": 2.0
        },
        "project_queries": [
            "\"physics simulation\" in:name,description",
            "\"physics engine\" in:name,description",
            "\"robot simulation\" in:name,description",
            "\"differentiable simulation\" in:name,description"
        ]
    },
    "automation": {
        "auto_refresh_indexes": True,
        "git_commit": False,
        "git_push": False
    }
}

def _deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def shared_config_path() -> Path:
    """One optional personal configuration, independent of the agent installation."""
    root = Path(os.environ.get("XDG_CONFIG_HOME") or "~/.config").expanduser()
    return root / "dailypaper-skills" / "user-config.json"


@lru_cache(maxsize=1)
def load_user_config(config_dir: Path | None = None) -> dict:
    config = copy.deepcopy(DEFAULT_CONFIG)
    config_dir = Path(config_dir) if config_dir is not None else Path(__file__).resolve().parent
    config_paths = [config_dir / name for name in ("user-config.json", "user-config.local.json")]
    config_paths.append(shared_config_path())
    explicit = os.environ.get("DAILYPAPER_CONFIG")
    if explicit:
        explicit_path = Path(explicit).expanduser()
        if not explicit_path.is_file():
            raise FileNotFoundError(f"DAILYPAPER_CONFIG does not point to a file: {explicit_path}")
        config_paths.append(explicit_path)

    for config_path in config_paths:
        if not config_path.exists():
            continue
        with config_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError(f"Configuration must be a JSON object: {config_path}")
        for section in ("paths", "daily_papers", "automation"):
            if section in loaded and not isinstance(loaded[section], dict):
                raise ValueError(f"{section} must be a JSON object: {config_path}")
        _deep_merge(config, loaded)

    if os.environ.get("OBSIDIAN_VAULT_PATH"):
        config["paths"]["obsidian_vault"] = os.environ["OBSIDIAN_VAULT_PATH"]

    return config


def _expand(path_value: str) -> Path:
    return Path(path_value).expanduser()


def paths_config() -> dict:
    return load_user_config()["paths"]


def daily_papers_config() -> dict:
    return load_user_config()["daily_papers"]


def automation_config() -> dict:
    config = load_user_config()["automation"]
    if config.get("git_push") and not config.get("git_commit"):
        config = copy.deepcopy(config)
        config["git_push"] = False
    return config


def obsidian_vault_path() -> Path:
    return _expand(paths_config()["obsidian_vault"])


def paper_notes_dir() -> Path:
    return obsidian_vault_path() / paths_config()["paper_notes_folder"]


def daily_papers_dir() -> Path:
    return obsidian_vault_path() / paths_config()["daily_papers_folder"]


def concepts_dir() -> Path:
    return paper_notes_dir() / paths_config()["concepts_folder"]


def zotero_db_path() -> Path:
    return _expand(paths_config()["zotero_db"])


def zotero_storage_dir() -> Path:
    return _expand(paths_config()["zotero_storage"])


def auto_refresh_indexes_enabled() -> bool:
    return bool(automation_config()["auto_refresh_indexes"])


def git_commit_enabled() -> bool:
    return bool(automation_config()["git_commit"])


def git_push_enabled() -> bool:
    return bool(automation_config()["git_push"])


# ── Temp directory for intermediate data (Windows/Linux compatible) ──────────

def temp_dir() -> Path:
    """Get platform-appropriate temp directory.

    Windows: ~/tmp/
    Linux/Mac: /tmp/
    """
    return get_temp_dir()


def temp_file_path(filename: str) -> Path:
    """Get full path for a temp file.

    Usage:
        top30_path = temp_file_path('daily_papers_top30.json')
        enriched_path = temp_file_path('daily_papers_enriched.json')
    """
    return temp_dir() / filename


def main() -> None:
    parser = argparse.ArgumentParser(description="Print effective configuration and resolved runtime paths.")
    parser.add_argument("--init", action="store_true", help="Create shared personal config if absent; never overwrite it")
    args = parser.parse_args()
    config = copy.deepcopy(load_user_config())
    if args.init:
        path = shared_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as stream:
                json.dump(config, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        except FileExistsError:
            print(f"Existing configuration preserved: {path}")
        else:
            print(f"Created personal configuration: {path}")
        return
    config["automation"] = automation_config()
    for key in ("obsidian_vault", "zotero_db", "zotero_storage"):
        config["paths"][key] = str(_expand(config["paths"][key]))
    config["runtime"] = {
        "python": sys.executable,
        "temp_dir": str(temp_dir()),
        "shared_config": str(shared_config_path()),
    }
    print(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
