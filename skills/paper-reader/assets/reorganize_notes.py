#!/usr/bin/env python3
"""
论文笔记自动分类工具
根据论文 tags 和内容自动分类到对应目录，并同步更新 Zotero 分类
"""

import os
import csv
import re
import sys
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Optional, Dict, List

_SHARED_DIR = Path(__file__).resolve().parents[2] / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from user_config import paper_notes_dir, zotero_db_path

# 配置
PAPER_NOTES_ROOT = paper_notes_dir()
ZOTERO_DB = zotero_db_path()

# 新的分类结构（与概念分类对应）
# 优先级从上到下，越靠前越优先
CATEGORY_RULES = {
    # (目录名, 匹配规则 - tags 关键词)
    # 具体任务优先
    "4-足式运动": ["legged-locomotion", "quadruped", "bipedal", "locomotion", "parkour", "walking", "humanoid-locomotion", "足式", "腿式"],
    "3-机器人策略": ["VLA", "imitation-learning", "manipulation", "grasping", "bi-manual", "teleoperation", "action-prediction", "embodied", "机器人策略", "移动操作", "mobile-manipulation"],
    "5-导航与定位": ["VLN", "navigation", "SLAM", "localization", "mapping", "path-planning", "visual-navigation", "导航", "定位"],
    "6-3D视觉": ["3DGS", "NeRF", "depth", "3D-vision", "reconstruction", "gaussian-splatting", "point-cloud", "mesh", "3D-generation", "novel-view", "depth-estimation", "PBD", "world-model"],
    "7-无人机": ["drone", "UAV", "quadrotor", "aerial", "MAV", "无人机", "飞行器"],
    "8-仿真器": ["simulation", "sim2real", "simulator", "synthetic-data", "domain-randomization", "仿真"],
    "9-规划与控制": ["planning", "control", "MPC", "trajectory", "motion-planning", "规划", "控制"],
    # 通用方法
    "2-强化学习": ["reinforcement-learning", "RL", "PPO", "SAC", "reward", "policy-gradient", "强化学习", "GRPO"],
    "1-生成模型": ["diffusion", "flow-matching", "generative", "GAN", "VAE", "autoregressive", "video-generation", "生成模型"],
    "10-深度学习基础": ["transformer", "CNN", "attention", "backbone", "pre-training", "VLM", "LLM", "foundation-model", "深度学习"],
    "11-物理仿真": ["physics", "dynamics", "contact", "friction", "deformable", "物理"],
    "12-Survey": ["survey", "review", "benchmark", "tutorial", "综述"],
}

# Zotero 分类 ID 映射（需要根据实际情况更新）
ZOTERO_COLLECTION_MAP = {
    "1-生成模型": None,  # 需要在 Zotero 中创建
    "2-强化学习": 31,    # 2-DRL
    "3-机器人策略": 36,  # VLA
    "4-足式运动": 26,    # Locomotion
    "5-导航与定位": 43,  # VLN
    "6-3D视觉": 13,      # 3-3D Vision
    "7-无人机": None,
    "8-仿真器": 32,      # 0-Simulation
    "9-规划与控制": None,
    "10-深度学习基础": 2, # 1-Deep Learning
    "11-物理仿真": 37,   # Physical Simulation
    "12-Survey": None,
}


def parse_frontmatter(filepath: Path) -> Optional[Dict]:
    """解析 Markdown 文件的 YAML frontmatter"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return None

        # 找到第二个 ---
        end_idx = content.find('---', 3)
        if end_idx == -1:
            return None

        yaml_str = content[3:end_idx].strip()
        return parse_simple_frontmatter(yaml_str)
    except Exception as e:
        print(f"  解析失败: {e}")
        return None


def parse_simple_frontmatter(frontmatter: str) -> Dict[str, Any]:
    """解析本项目使用的简单 YAML frontmatter（仅支持顶层键值和列表）。"""
    parsed: Dict[str, Any] = {}
    current_list_key: Optional[str] = None

    for raw_line in frontmatter.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith('#'):
            continue

        if raw_line.startswith((' ', '\t')):
            stripped = raw_line.strip()
            if current_list_key and stripped.startswith('- '):
                parsed[current_list_key].append(parse_frontmatter_value(stripped[2:].strip()))
            continue

        current_list_key = None
        if ':' not in raw_line:
            continue

        key, raw_value = raw_line.split(':', 1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            continue

        if not value:
            parsed[key] = []
            current_list_key = key
            continue

        parsed[key] = parse_frontmatter_value(value)

    return parsed


def parse_frontmatter_value(raw_value: str) -> Any:
    value = strip_inline_comment(raw_value).strip()
    if not value:
        return ""

    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = next(csv.reader([inner], skipinitialspace=True))
        return [parse_frontmatter_scalar(item) for item in items if item.strip()]

    return parse_frontmatter_scalar(value)


def parse_frontmatter_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""

    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False

    if re.fullmatch(r'-?\d+', value):
        return int(value)
    if re.fullmatch(r'-?\d+\.\d+', value):
        return float(value)

    return value


def strip_inline_comment(raw_value: str) -> str:
    in_single_quote = False
    in_double_quote = False

    for idx, char in enumerate(raw_value):
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == '#' and not in_single_quote and not in_double_quote:
            return raw_value[:idx].rstrip()

    return raw_value.rstrip()


def determine_category(tags: List[str], title: str = "") -> str:
    """根据 tags 判断论文应该属于哪个分类"""
    if not tags:
        return "_待整理"

    # 确保所有 tags 都是字符串
    tags_lower = [str(t).lower() for t in tags]
    title_lower = title.lower()

    # 计算每个分类的匹配分数，同时考虑优先级
    scores = {}
    priority_bonus = len(CATEGORY_RULES)  # 优先级奖励基数

    for idx, (category, keywords) in enumerate(CATEGORY_RULES.items()):
        score = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # 检查 tags
            for tag in tags_lower:
                if keyword_lower in tag or tag in keyword_lower:
                    score += 2
            # 检查标题
            if keyword_lower in title_lower:
                score += 1

        # 添加优先级奖励（越靠前的分类，同分时越优先）
        if score > 0:
            score = score * 100 + (priority_bonus - idx)

        scores[category] = score

    # 返回得分最高的分类
    best_category = max(scores, key=scores.get)
    if scores[best_category] > 0:
        return best_category
    return "_待整理"


def get_all_notes() -> List[Path]:
    """获取所有论文笔记"""
    notes = []
    for root, dirs, files in os.walk(PAPER_NOTES_ROOT):
        # 跳过概念目录
        if '_概念' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                notes.append(Path(root) / f)
    return notes


def reorganize_notes(dry_run: bool = True):
    """重新组织论文笔记"""
    notes = get_all_notes()
    print(f"找到 {len(notes)} 篇论文笔记\n")

    moves = []  # (原路径, 新路径, 分类, zotero_item_id, 当前 Zotero 分类)

    for note in notes:
        fm = parse_frontmatter(note)
        if not fm:
            print(f"跳过 (无frontmatter): {note.name}")
            continue

        tags = fm.get('tags', [])
        title = fm.get('title', note.stem)
        zotero_item_id = fm.get('zotero_item_id')
        current_collection = fm.get('zotero_collection', '')

        # 判断新分类
        new_category = determine_category(tags, title)

        # 当前目录
        current_rel = note.relative_to(PAPER_NOTES_ROOT)
        current_dir = str(current_rel.parent)

        # 如果已经在正确分类，跳过
        if current_dir.startswith(new_category):
            print(f"✓ 已正确分类: {note.name} -> {new_category}")
            continue

        # 新路径
        new_path = PAPER_NOTES_ROOT / new_category / note.name

        moves.append((note, new_path, new_category, zotero_item_id, current_collection))
        print(f"→ 需移动: {note.name}")
        print(f"  从: {current_dir}")
        print(f"  到: {new_category}")
        print(f"  tags: {tags[:5]}...")
        print()

    print(f"\n总计需要移动 {len(moves)} 篇笔记")

    if dry_run:
        print("\n[DRY RUN] 未实际执行移动，添加 --execute 参数执行")
        return moves

    # 执行移动
    for old_path, new_path, category, zotero_id, current_collection in moves:
        # 创建目标目录
        new_path.parent.mkdir(parents=True, exist_ok=True)

        # 移动文件
        shutil.move(str(old_path), str(new_path))
        print(f"✓ 已移动: {old_path.name} -> {category}/")

        # 更新 Zotero 分类
        zotero_collection_value = category
        if zotero_id:
            synced_collection = update_zotero_collection(zotero_id, category, current_collection)
            if synced_collection:
                zotero_collection_value = synced_collection

        # 更新 frontmatter 中的 zotero_collection
        update_frontmatter_collection(new_path, zotero_collection_value)

    return moves


def update_frontmatter_collection(filepath: Path, new_collection: str):
    """更新笔记的 zotero_collection 字段"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换 zotero_collection
        if 'zotero_collection:' in content:
            content = re.sub(
                r'^zotero_collection:.*$',
                f'zotero_collection: {new_collection}',
                content,
                flags=re.MULTILINE,
            )
        elif content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx != -1:
                content = content[:end_idx] + f"zotero_collection: {new_collection}\n" + content[end_idx:]

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"  更新 frontmatter 失败: {e}")


def get_collection_path(collections: Dict[int, Dict[str, Optional[int]]], collection_id: int) -> str:
    """获取分类完整路径，如 3-Robotics/1-VLX/VLA"""
    path_parts = []
    current = collection_id
    while current:
        info = collections.get(current)
        if not info:
            break
        path_parts.insert(0, info['name'])
        current = info['parent']
    return '/'.join(path_parts)


def resolve_collection_id(
    collection_ref: str,
    collections: Dict[int, Dict[str, Optional[int]]],
    path_to_id: Dict[str, int],
    name_to_ids: Dict[str, List[int]],
) -> Optional[int]:
    """按完整路径、ID 或唯一末级分类名解析 collection ID。"""
    if not collection_ref:
        return None

    ref = str(collection_ref).strip()
    if not ref:
        return None

    if ref.isdigit():
        cid = int(ref)
        return cid if cid in collections else None

    if ref in path_to_id:
        return path_to_id[ref]

    leaf_name = ref.split('/')[-1]
    matched_ids = name_to_ids.get(leaf_name, [])
    if len(matched_ids) == 1:
        return matched_ids[0]

    return None


def update_zotero_collection(item_id: int, new_category: str, current_collection: str = "") -> Optional[str]:
    """更新 Zotero 中论文的分类"""
    collection_id = ZOTERO_COLLECTION_MAP.get(new_category)
    if not collection_id:
        print(f"  Zotero 分类未配置: {new_category}")
        return None

    if not ZOTERO_DB.exists():
        print(f"  Zotero 数据库不存在: {ZOTERO_DB}")
        return None

    conn = None
    try:
        conn = sqlite3.connect(ZOTERO_DB, timeout=10)
        cursor = conn.cursor()

        cursor.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections")
        collections = {
            row[0]: {'name': row[1], 'parent': row[2]}
            for row in cursor.fetchall()
        }
        path_to_id = {get_collection_path(collections, cid): cid for cid in collections}
        name_to_ids: Dict[str, List[int]] = {}
        for cid, info in collections.items():
            name_to_ids.setdefault(info['name'], []).append(cid)

        target_path = get_collection_path(collections, collection_id)
        previous_collection_id = resolve_collection_id(current_collection, collections, path_to_id, name_to_ids)

        cursor.execute(
            """
            SELECT 1 FROM collectionItems
            WHERE collectionID = ? AND itemID = ?
            """,
            (collection_id, item_id),
        )
        already_in_target = cursor.fetchone() is not None
        if not already_in_target:
            cursor.execute(
                """
                INSERT INTO collectionItems (collectionID, itemID, orderIndex)
                VALUES (?, ?, 0)
                """,
                (collection_id, item_id),
            )
            print(f"  已将 Zotero item {item_id} 添加到分类 {target_path}")
        else:
            print(f"  Zotero item {item_id} 已在分类 {target_path} 中")

        if previous_collection_id and previous_collection_id != collection_id:
            cursor.execute(
                """
                DELETE FROM collectionItems
                WHERE collectionID = ? AND itemID = ?
                """,
                (previous_collection_id, item_id),
            )
            if cursor.rowcount > 0:
                print(f"  已从原分类 {get_collection_path(collections, previous_collection_id)} 移除 Zotero item {item_id}")

        conn.commit()
        return target_path
    except Exception as e:
        if conn is not None:
            conn.rollback()
        print(f"  更新 Zotero 失败: {e}")
        return None
    finally:
        if conn is not None:
            conn.close()


def analyze_current_distribution():
    """分析当前笔记分布"""
    notes = get_all_notes()

    category_count = {}
    for note in notes:
        fm = parse_frontmatter(note)
        if not fm:
            continue

        tags = fm.get('tags', [])
        title = fm.get('title', note.stem)
        category = determine_category(tags, title)

        category_count[category] = category_count.get(category, 0) + 1

    print("=== 按新分类统计 ===")
    for cat, count in sorted(category_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} 篇")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--analyze":
        analyze_current_distribution()
    elif len(sys.argv) > 1 and sys.argv[1] == "--execute":
        reorganize_notes(dry_run=False)
    else:
        reorganize_notes(dry_run=True)
