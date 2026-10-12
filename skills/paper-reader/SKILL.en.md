# Paper reader

Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md), then load effective configuration, including Zotero paths and automation switches. Use English for progress, analysis, new notes, concept explanations, and captions. Keep original titles, identifiers, equations, and existing link targets.

## Obtain the paper and select a mode

Accept local PDFs, arXiv/DOI links, Zotero searches, or collections. For a collection without a clear batch request, list candidates for selection. For a Zotero item without an attachment, run `python3 assets/zotero_helper.py info ITEM_ID`, then try arXiv HTML, arXiv PDF, DOI, and title search, in that order. Skip only unavailable or non-paper items, reporting why. See [Zotero operations](references/zotero-guide.md) as needed.

| Request | Output |
| --- | --- |
| “Quick summary” / “quickly read” | 3–5 sentences about the core contribution |
| “Read/analyze this paper” / default | Full structured analysis using the template |
| “Critique this paper” | Methodological strengths, limitations, and evidence |
| “Extract equations/technical details” | Equations and algorithm pseudocode |

Respect the requested delivery destination. Full saved notes use [the English paper template](assets/paper-note-template.en.md). Quick summaries do not require a full note. A request for analysis alone does not imply Obsidian archival or Git synchronization.

## Full-note quality

- Account for every figure, equation, and table in the source. Preserve complete table rows/columns and exact reported numbers. Compare source counts with the final note; mark inaccessible content explicitly instead of inventing it.
- Link technical concepts at first mention with `[[concept]]` or an alias of an existing target. Use structured Markdown and math for architecture descriptions, not ASCII diagrams.
- For each equation, provide a linked name, LaTeX block, meaning, and all symbol definitions. Keep blank lines around `$$`; split long expressions with `aligned`. Verify bound/free variables, notation consistency, limits, stop-gradient and other operators against the paper.
- Use `### Figure N: Original English caption` and an English explanation. Do not add a Chinese caption simply because the Chinese reference uses bilingual titles.
- Read [quality standards](references/quality-standards.md) for detailed checks; its Chinese labels map to the English template. Source-faithfulness and coverage are unchanged.

## Obtain and verify figures

1. Determine the correct arXiv ID and source figure count.
2. Prefer `https://arxiv.org/html/ID`: extract figure captions and actual image URLs.
3. If unavailable or incomplete, inspect the paper's linked project page for the corresponding figures.
4. Fall back to PDF extraction with `pdfimages -png`; inspect extracted images and confirm they depict the correct figures. The existing workflow's >10 KB filter is a heuristic, not proof of correctness.
5. Embed verified remote URLs with `![Figure N](url)` or local assets with `![[filename.png]]`. Inspect that links/files work.
6. Avoid duplicating the arXiv ID when resolving relative URLs: an image `src` may already include `IDv1/`. Use URL resolution rather than appending the ID twice. See [image troubleshooting](references/image-troubleshooting.md) for ar5iv numbering and PDF fallbacks.

After saving a full note, run:

```bash
python3 ../daily-papers/download_note_images.py "{NOTE_PATH}"
```

The helper retains reachable external images and attempts local fallbacks for unreachable ones, updating `image_source` when applicable. Check its results; unavailable figures remain an explicit gap.

## Save and maintain concepts

Use the method/model name as the filename, e.g. `Pi05.md`, without a year prefix. Infer it from the title or “we propose” statement; transliterate Greek letters to ASCII. Keep existing collection/category names. In the configured library, save under `NOTES_PATH/{zotero_collection_path}/{MethodName}.md`, or the existing unfiled folder when classification is uncertain. Do not translate folder names automatically.

Keep the template's schema keys (`title`, `method_name`, `authors`, `year`, `venue`, `tags`, `zotero_collection`, `image_source`, `created`) and add `language: en`. Use 3–8 lowercase hyphenated topic tags; preserve verifiable publication status.

Scan every concept link, check all existing categories and aliases, and create missing notes using [the English concept template](assets/concept-note-template.en.md). Reuse [the category rules](references/concept-categories.md) and actual folder names; link this paper as a representative work.

When index refresh is enabled for a saved library note:

```bash
python3 ../_shared/generate_concept_mocs.py --output-language en
python3 ../_shared/generate_paper_mocs.py --output-language en
```

Git follows the runtime's enabled-and-authorized checks. Review the final source coverage, equations, tables, figure accessibility, inline concept links, and concept-note existence. Report the actual note path and new concept count, plus any unresolved gaps.

## Batches

For an explicitly requested Zotero collection batch, include subcollections by default, deduplicate items, check existing notes for quality, process remaining papers, and summarize completed and outstanding work. Preserve `OUTPUT_LANGUAGE` across every invocation. Follow-up explanations and comparisons use the same language unless the user changes it.
