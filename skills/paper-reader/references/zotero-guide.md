# Zotero 集成指南

## 查询分类下的论文（支持递归子分类）

```bash
# 使用辅助脚本
python3 assets/zotero_helper.py collections         # 列出所有分类
python3 assets/zotero_helper.py papers 1            # 列出分类ID=1的论文
python3 assets/zotero_helper.py papers 1 --recursive # 递归包含子分类
python3 assets/zotero_helper.py pdf 12345           # 获取论文PDF路径
```

**递归查询原理**：
1. 先获取目标分类的所有子分类 ID（递归遍历 parentCollectionID）
2. 用 `WHERE ci.collectionID IN (id1, id2, ...)` 查询所有论文
3. 去重（同一论文可能在多个分类中）

## 获取论文 PDF 路径

```sql
SELECT ia.path, items.key
FROM itemAttachments ia
JOIN items ON ia.itemID = items.itemID
WHERE ia.parentItemID = {item_id} AND ia.contentType = 'application/pdf';
-- 完整路径: {ZOTERO_STORAGE}/{key}/{filename}
```

## 获取 Zotero 分类路径

```python
def get_collection_path(collection_id):
    """返回完整路径如 '3-Robotics/1-VLX/VLA'"""
    cursor.execute("SELECT collectionID, collectionName, parentCollectionID FROM collections")
    collections = {row[0]: {'name': row[1], 'parent': row[2]} for row in cursor.fetchall()}
    path_parts = []
    current = collection_id
    while current:
        if current in collections:
            path_parts.insert(0, collections[current]['name'])
            current = collections[current]['parent']
        else:
            break
    return '/'.join(path_parts)
```

## 智能分类判断

**不要依赖关键词匹配！** 必须理解论文核心贡献后判断。

### 判断流程

1. **理解论文核心贡献** — 解决什么问题？核心方法？目标应用？
2. **查看现有分类**：`python3 assets/zotero_helper.py collections`
3. **选最合适的** — 问自己：找这篇论文会去哪个分类？按**主要贡献**分类，而非使用的技术
4. **交叉学科** — 可添加到多个分类，选最核心的作为主分类

### 分类判断示例

| 论文 | 错误分类 | 正确分类 | 理由 |
|------|----------|----------|------|
| 用 Flow Matching 做 VLA | Flow Matching | VLA | 核心是机器人策略 |
| 用 3DGS 做 SLAM | 3DGS | SLAM | 目标是定位建图 |
| DepthAnything | Deep Learning | Depth Estimation | 具体任务 |

## Zotero 分类操作

```bash
# 查看论文当前分类
python3 assets/zotero_helper.py info {item_id}
# 查找目标分类 ID
python3 assets/zotero_helper.py find-collection "VLA"
# 移动论文
python3 assets/zotero_helper.py move {item_id} {new_collection_id} --from {old_collection_id}
# 添加到多个分类
python3 assets/zotero_helper.py add-to-collection {item_id} {collection_id}
```

### 何时移动分类

| 当前分类 | 处理方式 |
|----------|----------|
| "2025"、"杂项"、"feifeili" 等临时分类 | **必须移动** |
| 分类与论文内容不符 | 移动到正确分类 |
| 基本正确但可更精确 | 可选：移动到子分类 |
| 完全正确 | 保持不变 |
