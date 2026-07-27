# 图片获取排错指南

## ar5iv 图片 URL 的坑

ar5iv 的 asset 编号（x1.png, x2.png...）**不一定对应论文的 Figure 编号**！

常见问题：
- 小 icon/箭头/符号图片也占编号，容易下载到错误图片
- 同一 Figure 的子图（a/b/c）可能用不连续的编号
- 某些 Figure 是由多个小图拼成的

**解决方法**:
1. 用 WebFetch 获取页面时，提取每个 Figure 标题和对应的 img src
2. 下载后**必须验证** — Read 每张图片确认内容正确
3. 文件 < 10KB 时必须重新检查

## 多源 fallback 策略

当 arXiv HTML 获取失败或图片不完整时，按顺序尝试：

### 来源 A: arXiv HTML（首选）
- WebFetch `https://arxiv.org/html/{arxiv_id}` → 提取 `<figure>` 的 img src
- 先统计论文 Figure 总数，确保提取完整

### 来源 B: 项目主页（补充）
- 从论文摘要/HTML 中查找项目主页（关键词：`project page`、`github.io`、`our website`）
- WebFetch 项目主页，提取展示图片（teaser / demo 图）
- 适合获取 arXiv HTML 中缺失的方法概览图

### 来源 C: PDF 提取（最终 fallback）
```bash
wget -O /tmp/paper.pdf "https://arxiv.org/pdf/{arxiv_id}.pdf"
mkdir -p {笔记所在目录}/assets/
pdfimages -png /tmp/paper.pdf {笔记所在目录}/assets/{方法名}_fig
```
提取后验证：文件 >10KB、Read 确认内容正确。

## 选择性本地化（解决外链不可达）

arXiv 外链在某些网络环境下不稳定。笔记保存后自动运行可达性检查：

```bash
python3 ../daily-papers/download_note_images.py "{笔记路径}"
```

脚本行为：
- 并发检查所有外链图片的 HTTP 可达性（10s 超时）
- **可达** → 保持外链不动
- **不可达** → 下载到 `assets/{方法名}_fig{N}.{ext}`，替换为 `![[...]]` wikilink
- 下载也失败时，尝试从 PDF 提取对应 figure
- 有本地化操作时，自动更新 frontmatter `image_source: online` → `mixed`

## ⚠️ 图片 URL 规范化（防止路径重复）— 高频 Bug

> **这是已反复出现的 bug，务必严格执行。**

arXiv HTML 中图片的 `src` 属性是相对路径，且**已包含版本目录前缀**：
```html
<img src="2607.04988v1/x1.png">        <!-- 常见格式 -->
<img src="2607.04988v1/figures/fig1.png"> <!-- 子目录格式 -->
```

### 绝对 URL 构建规则

| src 值 | 正确拼接 | 错误拼接 |
|--------|----------|----------|
| `2607.04988v1/x1.png` | `https://arxiv.org/html/` + src | `https://arxiv.org/html/2607.04988v1/` + src |
| `figures/fig1.png` | `https://arxiv.org/html/2607.04988v1/` + src | — |

**铁律**:
1. 如果 src 以 `2` 开头（含 arxiv_id 前缀），base = `https://arxiv.org/html/`
2. 如果 src 不含 arxiv_id 前缀（如 `figures/`），base = `https://arxiv.org/html/{arxiv_id}v1/`
3. **写入前必须验证**：URL 中不得出现连续两段相同的 arxiv_id（如 `2607.04988v1/2607.04988v1/`）

```
✗ https://arxiv.org/html/2607.04988v1/2607.04988v1/x1.png  ← 路径重复，404
✓ https://arxiv.org/html/2607.04988v1/x1.png               ← 正确
```

## 笔记中的图片引用格式

**外链**（默认）:
```markdown
![Figure 1](https://arxiv.org/html/xxxx/x1.png)
```

**本地**（外链不可用时的备选）:
```markdown
![[{方法名}_fig1_overview.png]]
![[{方法名}_fig1_overview.png|600]]  <!-- 指定宽度 -->
```

## frontmatter 中记录图片来源

```yaml
---
image_source: online  # 默认 online；部分图片用本地时填 mixed
arxiv_id: "2501.12345"
---
```
