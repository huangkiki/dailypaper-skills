---
name: paper-reader
description: |
  Read academic papers from a bare arXiv abs/pdf/html URL, a PDF, a paper title,
  or Zotero. Use for "read this paper", "analyze this paper", "读一下 XXX",
  "读一下这篇", "帮我读", "看一下这篇论文", "论文笔记", quick summaries,
  critiques, and Zotero collection reading. A standalone arXiv link or ordinary
  reading request defaults to full reading and automatic note saving in the
  configured Obsidian/Markdown library. Honor explicit depth, destination, and
  no-save requests; a citation used for another task does not trigger reading.
---

## Language / 语言

First resolve `OUTPUT_LANGUAGE` using [language selection](../_shared/language.md).
For an English request (or an explicit request for English), read and follow
[the English workflow](SKILL.en.md) instead of the Chinese body below.
中文请求继续执行下文；用户明确指定的语言优先。内部阶段继承语言，不从论文或工具输出重新判断。

## 执行环境

开始前读取 [Agent 运行约定](../_shared/agent-runtime.md)，解析当前 Skill 目录、有效配置和 `TEMP_DIR`，再执行下文。

> **开始前**: 先跟用户打个招呼 🐕

# 学术论文阅读助手 (Paper Reader)

专注 CV/DL 领域，支持 Zotero 集成和 Obsidian 笔记保存。

## 默认执行约定

- 单独发送 arXiv 论文链接（`/abs/`、`/pdf/`、`/html/`，含版本号或 `.pdf` 后缀）就是完整阅读请求，无需补说“读一下”或“保存”。链接仅作为其他任务的引用、示例或背景时，按该任务处理。
- “读一下 XXX”“读一下这篇”“帮我读”“看一下这篇论文”“分析这篇论文”默认执行：获取全文 → 完整解析与独立锐评 → 生成正式笔记 → 写入配置的 Obsidian/Markdown 库 → 补概念与按配置刷新索引 → 反馈核心判断与实际笔记路径。不要停在聊天摘要、计划或“要不要保存”的询问。
- 用户明确要求快速摘要、批判分析或公式提取时，保留该阅读深度，并默认保存相应模式的笔记；“只在聊天里回答”“不要保存”或指定其他输出位置优先，不额外归档到 Obsidian。
- 仅有论文名时先用当前上下文、Zotero 或标题检索定位来源；同名论文无法确定时只澄清论文身份。笔记库配置缺失、根目录不存在、仍是未初始化的示例路径或不可写时，只询问/报告实际缺失项，不假装已保存，也不擅自另建一个笔记库。

## Step 0: 读取共享配置

运行 `python3 ../_shared/user_config.py`，使用其输出的合并配置（含个人配置和环境变量覆盖）。

显式生成并在后续统一使用这些变量：

- `VAULT_PATH`
- `NOTES_PATH`
- `CONCEPTS_PATH`
- `ZOTERO_DB`
- `ZOTERO_STORAGE`
- `AUTO_REFRESH_INDEXES`
- `GIT_COMMIT_ENABLED`
- `GIT_PUSH_ENABLED`

其中：

- `NOTES_PATH = {VAULT_PATH}/{paper_notes_folder}`
- `CONCEPTS_PATH = {NOTES_PATH}/{concepts_folder}`
- `GIT_PUSH_ENABLED` 只有在 `GIT_COMMIT_ENABLED=true` 时才可能为真

后续统一使用上面的变量。

## 1. 接收论文

| 输入方式 | 示例 | 处理方法 |
|----------|------|----------|
| PDF 路径 | `/path/to/paper.pdf` | 直接 Read |
| arXiv 链接（可单独发送） | `https://arxiv.org/abs/xxxx`、`/pdf/xxxx`、`/html/xxxx` | 解析 ID/版本 → 优先获取 HTML 全文，失败回退 PDF → 完整阅读并保存 |
| Zotero 分类 | "VLA 分类的论文" | 查询数据库 → 列出 → 用户选择 |
| Zotero 搜索 | "Zotero 里的 π0.5" | 搜索标题 → 找到 PDF |
| 无 PDF | Zotero 条目无附件 | 从网上获取（见下方） |

从 arXiv 链接保留论文 ID 与用户指定的版本，去掉查询参数或 `.pdf` 后缀后定位同一篇论文；HTML 和 PDF 回退不能偷偷换版本。笔记记录实际阅读的来源链接与版本。先检查已有笔记中的来源 ID/标题，命中同一论文时优先补充原文件并保留用户批注，不因链接形式不同重复建档；快速模式不得用短摘要覆盖已有完整笔记。全文无法获取时明确标记阅读范围和缺失部分，不把仅摘要笔记报告为完整精读。

### 无 PDF 时的获取流程

1. `python3 assets/zotero_helper.py info {item_id}` 获取论文信息
2. 按优先级获取：arXiv HTML > arXiv PDF > DOI > WebSearch 标题
3. 判断 arXiv ID：从 URL / Zotero extra 字段 / 标题搜索
4. 推荐直接 WebFetch `https://arxiv.org/html/{arxiv_id}`，无需下载
5. 跳过条件：既无 PDF 也无在线来源 / 非论文内容

> Zotero 详细操作见 `references/zotero-guide.md`

## 2. 阅读模式

| 模式 | 触发词 | 输出 |
|------|--------|------|
| **快速摘要** | "快速看一下"、"quick" | 3-5 句核心贡献 |
| **完整解析** | 裸 arXiv 链接、“读一下”“帮我读”、“详细分析”、默认 | 完整结构化笔记（用模板）+ 独立锐评，自动保存 |
| **批判分析** | "批判性分析"、"critique" | 以独立锐评为主体的方法与证据评估 |
| **知识提取** | "提取公式"、"技术细节" | 公式 + 算法伪代码 |

## 3. 笔记生成

完整解析使用 `assets/paper-note-template.md`，不可自行降级为摘要。下方完整覆盖要求适用于完整解析；明确要求快速摘要、批判分析或知识提取时，按对应模式组织笔记，保留标题、来源链接、日期、阅读模式与实际阅读范围，不强行扩展为完整精读。所有模式默认保存，除非用户明确要求不保存。

### 核心质量规则

1. **零遗漏**: 论文中所有 Figure、所有公式、所有 Table 必须全部出现在笔记中
2. **内联概念链接**: 正文中首次出现的技术术语必须用 `[[概念]]` 链接，不仅仅是结尾
3. **严禁 ASCII 流程图**: 用结构化 Markdown 列表 + `$数学符号$` 描述架构
4. **公式完整性**: 每个公式必须有名称（`[[概念|名称]]`）、LaTeX 公式、含义、符号说明
5. **图片外链优先**: arXiv HTML / 项目主页 / GitHub，找不到再本地下载

> 公式/图片/表格的详细质量规范见 `references/quality-standards.md`

### 独立锐评（完整解析与批判分析默认包含）

单篇阅读也要给出自己的研究判断，不依赖 `daily-papers-review` 先跑过。笔记的独立“锐评”紧接标题，作为正文第一节，先给判决，再给依据；元信息、摘要、方法和实验放在其后，YAML frontmatter 仍保留在文件最顶部。最终聊天答复同样以简短锐评开头；复述摘要、罗列优缺点或只报告存档状态都不能替代它。

这是展示顺序：先完成阅读和证据核对，再形成并前置判断。更新已有笔记时，将原有完整锐评移到标题后，保留来源与用户批注，不仅在开头复制一句判决而把实质锐评留在文末。用户明确指定其他顺序时遵循其要求。

- **真正的新意**：对照具体前作，说明新增的是机制、组合、数据、规模还是工程取舍；无法核实前作时标明新颖性判断的范围。
- **最强证据**：指出最有说服力的结果及比较条件，解释它实际支持哪条主张，不能只说“效果好”。
- **关键缺口或边界**：检查最影响结论的混杂因素、消融、基线公平性、成本或泛化范围。区分“证据不足以支持”与“已经证明无效”；没有发现可靠缺陷时说明已验证的适用边界，不为显得尖锐编造问题。
- **明确判决**：给出值得精读、值得借鉴但需补证、增量有限或暂不推荐等判断，并解释最值得学什么、是否值得复现及原因。可用 🔥 / 👀 / ⚠️ / 🫠 等标签，但标签不能替代理由。

语气直接、有态度，夸与质疑都落在方法和证据上。关键判断就近指向章节、图表、公式或已核查的代码位置；区分作者主张、论文证据与自己的推断。指责“没有消融/真实实验/基线”前先核对相应章节和可得补充材料；未读到应写“尚未核实”。涉及代码时注明静态审查或实际运行范围，不能把代码存在当作复现成功。

快速摘要、公式提取和明确“只总结、不评价”的请求不强制增加完整锐评。仅“不要保存”不改变阅读深度，完整解析仍在聊天里给出锐评。全文不可得时给出限定于已读材料的暂定判断，列明待核实项，不把未获取的实验当作缺失。

### 图片获取流程（多源 fallback）

**目标**: 确保笔记中包含论文的**所有 Figure**，先统计论文 Figure 总数再逐一获取。

1. WebSearch `"{论文标题} arxiv"` 获取 arXiv ID
2. **来源 A — arXiv HTML**（首选）：
   - WebFetch `https://arxiv.org/html/{arxiv_id}` 提取所有 `<figure>` 的标题与 img src URL
   - 统计论文 Figure 总数，确认提取数量是否完整
3. **来源 B — 项目主页**（HTML 404 或图片不全时）：
   - 从摘要/HTML 中查找项目主页 URL（常见模式：`project page`、`github.io`、`our website`）
   - WebFetch 项目主页，提取展示图片（通常包含 teaser / demo 图）
4. **来源 C — PDF 提取**（前两者都失败时）：
   - `pdfimages -png` 从 PDF 中提取，筛选 >10KB 的有效图片
5. 笔记中用 `![Figure X](url)` 外链嵌入
6. 验证：外链可加载 / 本地文件 >10KB
7. **URL 去重（必做）**：写入前检查每个 URL，如果 `https://arxiv.org/html/` 后出现了连续两段相同的 arxiv_id（如 `2607.04988v1/2607.04988v1/`），删除重复段。这是高频 bug，详见 `references/image-troubleshooting.md`
   - 原因：arXiv HTML 中 img src 已含 `{id}v1/` 前缀，拼接时不要再加一次
   - 正确：`https://arxiv.org/html/` + src（如 `https://arxiv.org/html/2607.04988v1/x1.png`）
   - 错误：`https://arxiv.org/html/2607.04988v1/` + src（导致路径重复，返回 404）

> ar5iv 编号不一定对应 Figure 编号，排错见 `references/image-troubleshooting.md`

### 图片可靠性保障（生成后自动执行）

笔记保存后，运行图片可达性检查脚本，自动将不可访问的外链图片下载到本地：
```bash
python3 ../daily-papers/download_note_images.py "{笔记完整路径}"
```
- 可达的外链保持不动，不可达的自动下载到 `assets/` 并替换为 Obsidian wikilink
- 如有本地化操作，frontmatter `image_source` 自动更新为 `mixed`

### 公式格式

每个公式必须包含：名称（`[[概念|名称]]`）、LaTeX `$$` 块（前后留空行）、含义、符号列表。
`$$` 块前后**必须有空行**否则 Obsidian 不渲染。超长公式用 `aligned` 拆分。

## 4. Obsidian 保存

将笔记实际写入文件，并读回确认标题、来源和本次内容。未写入成功不能报告“已保存”。默认保存不需要再次征求确认；用户明确选择其他目录或不保存时遵循该选择，明确不保存时跳过笔记与持久附件写入、概念库写入、索引和 Git；输出到其他目录时只写该目标所需产物，不修改配置的 Obsidian 库。第 5 节概念维护仅适用于保存到该库的笔记。

### 文件命名

只用**方法名/模型名**：`{方法名}.md`（如 `Pi05.md`，不加年份前缀）。
方法名判断：标题冒号前 / Abstract 中 "We propose XXX" / 希腊字母转 ASCII。
不确定时保存到 `_待整理/`。

### 保存路径

优先按 Zotero 分类层级：`{NOTES_PATH}/{zotero_collection_path}/{方法名}.md`。

裸 arXiv / PDF / 论文名没有 Zotero 分类时，扫描 `{NOTES_PATH}` 的现有分类，按论文主题选择最匹配目录；无法可靠分类时使用 `_待整理/`（已确认的库内缺少该子目录时可创建），不因缺少 Zotero 分类而停止保存。保持已有文件名和内部链接，`zotero_collection` 记录实际相对目录。

### YAML frontmatter

```yaml
---
title: "论文标题"
method_name: "MethodName"
authors: [Author1, Author2]
year: 2025
venue: arXiv
tags: [tag1, tag2]  # 小写连字符，3-8 个
zotero_collection: 3-Robotics/1-VLX/VLA
image_source: online
created: YYYY-MM-DD
---
```

Tags 判断：看 Related Work 小标题 + Abstract 关键词。第一个 tag 是最核心主题。

### 概念补齐后自动执行

先完成第 5 节概念维护和笔记/图片检查，再处理索引与 Git：

1. 只有在 `AUTO_REFRESH_INDEXES=true` 时刷新目录页：
   ```bash
   python3 ../_shared/generate_concept_mocs.py
   python3 ../_shared/generate_paper_mocs.py
   ```
2. Git 按有效配置和用户已有授权执行；明确的长期或当次授权优先，不重复询问。没有已有授权时不把自动保存等同于自动发布。使用 `git -C "{VAULT_PATH}" rev-parse --show-toplevel` 确认仓库（兼容 worktree）。
3. 仅暂存本次新增/修改的笔记、必要附件、概念和索引，先检查暂存差异；不得使用整个论文目录的 `git add` 混入其他任务变更。存在本次变更时再 commit；push 还需要启用/已授权、已配置远端，且不会带入无关本地提交。遇到分叉或其他改动时按已有工作流隔离整合，不强推。
4. 分别报告保存、索引、commit、push 的实际结果；同步失败不能把本地 commit 报告为 push 成功。

## 5. 概念库维护（保存到笔记库时执行）

概念库位置：`{CONCEPTS_PATH}`

### 流程

1. **扫描**论文笔记中所有 `[[概念]]` 链接
2. **检查**每个链接对应的概念笔记是否存在（`ls` + `find`）
3. **创建**不存在的概念（不可跳过），自动归类到对应子目录

> 分类规则和模板见 `references/concept-categories.md`

### 自检

- [ ] 笔记中所有 `[[概念]]` 链接的概念笔记都存在？
- [ ] 概念笔记包含本论文作为"代表工作"？

## 6. 完成后自检（合并 checklist）

- [ ] 已按请求模式写入并读回实际笔记文件（明确不保存除外），来源链接和阅读范围准确？
- [ ] 完整解析时：所有 Figure 都在笔记中（数量与论文一致）？
- [ ] 完整解析时：所有公式都在笔记中（变量一致、无冲突）？
- [ ] 完整解析时：所有 Table 完整保留（所有行列）？
- [ ] 完整解析/批判分析时（用户明确不评价除外）：笔记标题后第一节和最终答复开头是否为独立锐评，说明新意、最强证据、关键缺口或边界与明确判决？不保存时检查聊天答复；用户指定其他顺序时按其要求。
- [ ] 锐评的关键判断有来源定位，作者主张与自己的推断分开，未核实内容没有写成已证实缺陷？
- [ ] 正文中技术术语有 `[[概念]]` 内联链接？
- [ ] 概念库已更新（缺失的概念已创建）？
- [ ] 图片可用（外链可加载 / 本地 >10KB）？

## 7. 完成后反馈

先完成阅读、保存和配置启用的后处理。完整解析与批判分析的最终答复以独立的简短锐评开头：明确判决、关键依据及最影响结论的边界；随后按需解释核心方法，最后报告笔记实际路径、新增概念数量及未解决的阅读/保存/同步问题。不能用“已读完/已保存”开场替代锐评，不能因为完整锐评已写入笔记就从聊天答复中省略，也不能把锐评留成“需要的话下次补充”。其他模式及用户明确不评价或指定顺序的请求按其要求反馈；不要再询问是否保存，也不要用后续建议代替本次交付。

## 8. 批量处理

支持 Zotero 分类批量处理（默认递归子分类）。流程：递归获取论文 → 去重 → 检查已有笔记的覆盖与锐评，补齐缺项并保留用户批注 → 依次处理剩余论文 → 汇总。

## 参考文件（按需查阅）

- **`references/zotero-guide.md`** — Zotero 查询、分类、PDF 路径获取、智能分类判断
- **`references/image-troubleshooting.md`** — ar5iv 图片编号对应、PDF 提取备选
- **`references/concept-categories.md`** — 概念自动归类的 16 个子目录规则 + 模板
- **`references/quality-standards.md`** — 公式/图片/表格的详细质量规范 + 自检清单
