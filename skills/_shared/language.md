# Language selection

Resolve `OUTPUT_LANGUAGE` (`en` or `zh`) before starting any skill:

1. Follow an explicit output-language request, including a request to change language during a run.
2. An internally invoked stage inherits the parent's `OUTPUT_LANGUAGE`. Do not detect language again from a translated handoff, paper abstract, or tool output.
3. Otherwise use the language of the user's own request: English prose selects `en`; Chinese prose selects `zh`. Ignore quoted material, paper titles, URLs, paths, code, and skill names when deciding. For mixed prose, use the main instruction's language.
4. For a bare URL, skill name, or an ambiguous continuation, retain the conversation's established language; without that context, use `zh` for backward compatibility.

For `en`, read the skill's `SKILL.en.md` and the [English runtime](agent-runtime.en.md); do not also execute the Chinese workflow. For `zh`, use `SKILL.md` and [Chinese runtime](agent-runtime.md). Both versions implement the same workflow and quality requirements.

Carry `OUTPUT_LANGUAGE`, the effective configuration, `TEMP_DIR`, and the actual recommendation path into each downstream stage and any permitted paper-reader subagent. A separately requested stage follows the new user request; do not infer its output language from cached paper data. On resume, locate the actual recommendation file (either language) and preserve its path; do not silently create a second copy or rewrite existing prose merely to change language.

## Output contract

- Progress messages, recommendations, critiques, paper/concept notes, captions, generated index text, and final summaries use the selected language.
- Keep original paper titles, author names, method identifiers, citations, URLs, formulas, JSON/YAML keys, and source enum values. Quoted source material can remain in its original language.
- Do not rename configured folders, Zotero collections, existing note files, or wikilink targets when switching language. Reuse a concept's existing note, including aliases; an English display alias such as `[[现有概念|English term]]` is fine. New prose uses the selected language; existing notes need no translation unless requested.
- Pass `--output-language en` to the index generators and GitHub note writer for English runs (`zh` is their CLI default). This is distinct from `fetch_trending.py --language python`, which filters programming languages.
- New recommendation files are `YYYY-MM-DD-paper-recommendations.md` for English and `YYYY-MM-DD-论文推荐.md` for Chinese. Add `language: en` or `language: zh` to their frontmatter. Temporary JSON filenames, schemas, and `.history.json` stay unchanged.

| Chinese | English |
| --- | --- |
| `## 分流表` | `## Reading priorities` |
| `🔥 必读` | `🔥 Must read` |
| `👀 值得看` | `👀 Worth a look` |
| `💤 可跳过` | `💤 Skip` |
| `**来源**` | `**Source**` |
| `**笔记**` / `**已有笔记**` | `**Note**` / `**Existing note**` |
| `## 关键公式` | `## Key equations` |
| `## 关键图表` | `## Figures and tables` |
| `## 实验结果` / `## 实验` | `## Experiments` |

When inspecting or backfilling existing artifacts, accept both sets of labels. Preserve the artifact's label language when inserting links. English template headings are presentation text, not changes to the underlying data schema.

Examples: `Recommend papers from the past three days` → English, 3 days; `过去三天论文推荐，please` → Chinese, 3 days; `今日论文推荐，用英文输出` → English; `Read this paper, but write the notes in Chinese` → Chinese.
