# Review and save recommendations

Stage 2. Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md), load effective configuration, and announce the date in English. Require `{TEMP_DIR}/daily_papers_enriched.json`; if missing, explain that fetching must run first.

## Scan existing knowledge

Scan `NOTES_PATH` and concept subdirectories. Skip internal underscore folders except the existing unfiled paper folder. Match enriched method names and title acronyms to note filenames case-insensitively; also check existing aliases before creating a translated concept. Record `has_existing_note` and the actual `existing_note_name` without `.md`.

## Review with evidence

The host agent writes the commentary. Be a sharp, well-informed research colleague: specific praise, specific criticism, clear priorities, no hype. Use effective `daily_papers.research_interests`; default topic examples are not a whitelist.

Review only selected, enriched papers. Skip a paper unrelated to every configured interest and list its title and reason at the end. Do not exclude a paper just because it concerns LLMs, NLP, or agents. Do not pad the recommendation count.

Preserve each paper's source and upvotes: `hf-daily` → `📰 HF Daily, ⬆️ N`; `hf-trending` → `🔥 HF Trending, ⬆️ N`; `arxiv` → `📄 arXiv keyword search` with no invented upvotes.

Ground claims in abstracts and enriched evidence. If `has_real_world` is true, acknowledge real-world experiments. Do not invent missing ablations/baselines, claim a paper is simulation-only without evidence, or call it a copy without concrete methodological overlap. Say “not mentioned in the abstract” or “requires checking the full paper” when appropriate. Distinguish compared baselines from methods the work builds on. Agent/Jev relevance scores are not research-quality verdicts. Jev confidence is not a correctness probability; do not invent Jev metadata for host-agent scores.

Discuss assumptions, evaluation coverage, compute/data needs, engineering cost, and what the paper enables for the user's research. Even for a strong paper, identify a worthwhile question, explicitly marking uncertainty. End each critique with one verdict emoji: 🔥 strong, 👀 interesting, ⚠️ concerns, 🫠 incremental, 💀 little value, 🤡 overstated, or 💤 irrelevant.

## Recommendation format

Start with `# 🔪 Today's research take`: 2–3 direct sentences about the day's quality and trends, including overlap with existing notes when relevant. Immediately follow with:

```markdown
## Reading priorities

| Priority | Papers |
| --- | --- |
| 🔥 Must read | [[MethodA]] (specific reason) · [[MethodB]] (specific reason) |
| 👀 Worth a look | [[MethodC]] (specific reason) |
| 💤 Skip | [[MethodD]] (specific reason) |
```

Use method/model names as link targets, not full titles. Group the detailed reviews by research topic. For papers without an existing note:

```markdown
### 1. Original paper title
- **Authors**: Full available author list
- **Affiliations**: All sourced affiliations, or Unknown
- **Links**: [arXiv](verified-url) | [PDF](verified-url)
- **Source**: Source label and actual upvotes where applicable

> ⏪ **Previously recommended**: YYYY-MM-DD

![Figure 1](verified-figure-url)

- **Core method**: 3–5 sentences explaining inputs, outputs, architecture/loss/training, and the main difference from prior work. Link technical terms on first use.
- **Baselines and foundations**: Actual compared methods versus methods built upon, with [[links]].
- **Relevance**: Concrete usefulness for a configured research interest.
- **Critique**: Evidence-based judgment and limitations, ending with a verdict emoji.
- **Related notes**: Existing [[notes]] and how they relate, if any.
- 💡 **Read in depth**: `Read this paper: title`
```

Include the repeat reminder only for `is_re_recommend=true`, the image only when `figure_url` exists, and the final reading prompt only for “Worth a look.” Must-read notes are generated automatically. Do not invent URLs.

For papers with existing notes, keep title, links, source, an applicable repeat reminder, and `- 📒 **Existing note**: [[actual-note-name]]`. Avoid repeating the full introduction. End the page with exclusions, if any, and one concise trend judgment; do not repeat the priority table.

## Save and record history

Save to the authorized destination using `YYYY-MM-DD-paper-recommendations.md`. Add frontmatter with `date`, the actual relevant configured `keywords`, `tags: [daily-papers, auto-generated]`, and `language: en`. Pass the exact saved path to the notes stage.

Update `.history.json` with every recommended arXiv ID, date, and title. Preserve the earliest date for existing IDs; retain only the last 30 days. Verify that today's new entries plus earlier entries appearing in this recommendation cover all `### N.` paper sections. The history format is language-independent.

Git automation stays off unless enabled and authorized as described in the runtime. Report total and per-priority counts. Continue to notes when called by the pipeline; otherwise suggest `Generate notes for the must-read papers`. Do not generate full notes or concepts in this stage.
