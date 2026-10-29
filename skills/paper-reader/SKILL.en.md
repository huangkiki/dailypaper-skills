# Paper reader

Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md), then load effective configuration, including Zotero paths and automation switches. Use English for progress, analysis, new notes, concept explanations, and captions. Keep original titles, identifiers, equations, and existing link targets.

## Default reading and saving contract

- A standalone arXiv paper URL (`/abs/`, `/pdf/`, or `/html/`, including versioned IDs and a `.pdf` suffix) requests full reading and automatic note saving. No extra "read" or "save" instruction is needed. A link used only as a citation, example, or background for another task follows that task.
- Ordinary "read/analyze this paper", "读一下", and "帮我读" requests run through full-text retrieval, structured reading with an independent critical verdict, note writing in the configured Obsidian/Markdown library, concept maintenance, enabled index refresh, and a final verdict with the saved path. Do not stop at a chat summary, a plan, or a question about saving.
- Explicit quick-summary, critique, or equation-extraction requests retain that depth and save a corresponding note by default. Explicit chat-only, no-save, or alternative-destination instructions take precedence; do not also archive them in Obsidian.
- Resolve a title-only request from context, Zotero, or title search. Ask only about an ambiguous paper identity or a missing/nonexistent/uninitialized/unwritable library destination. Do not silently create a guessed vault or claim an unwritten note was saved.

## Obtain the paper and select a mode

Accept local PDFs, arXiv/DOI links, Zotero searches, or collections. For a collection without a clear batch request, list candidates for selection. For a Zotero item without an attachment, run `python3 assets/zotero_helper.py info ITEM_ID`, then try arXiv HTML, arXiv PDF, DOI, and title search, in that order. Skip only unavailable or non-paper items, reporting why. See [Zotero operations](references/zotero-guide.md) as needed.

| Request | Output |
| --- | --- |
| “Quick summary” / “quickly read” | 3–5 sentences about the core contribution |
| Bare arXiv URL / “Read/analyze this paper” / default | Full structured note with an independent critical verdict, saved automatically |
| “Critique this paper” | Method and evidence assessment centered on an independent critical verdict |
| “Extract equations/technical details” | Equations and algorithm pseudocode |

Full notes use [the English paper template](assets/paper-note-template.en.md). Explicit quick summaries, critiques, and extraction requests save mode-appropriate notes with the title, source URL, date, reading mode, and actual source coverage; they do not require a full-note expansion. Git synchronization follows configuration and existing user authorization separately from saving.

Normalize the supplied arXiv URL to its ID and requested version, removing query parameters and any `.pdf` suffix. Retrieve HTML first, then PDF, preserving a specified version across fallbacks. Record the source URL/version actually read. Match existing notes by arXiv identity and title before writing; update the original note while preserving user annotations instead of creating duplicates for different URL forms; a quick summary must not replace an existing full note. If full text is unavailable, label any saved partial reading and missing coverage explicitly; an abstract-only note is not a completed full reading.

## Full-note quality

- Account for every figure, equation, and table in the source. Preserve complete table rows/columns and exact reported numbers. Compare source counts with the final note; mark inaccessible content explicitly instead of inventing it.
- Link technical concepts at first mention with `[[concept]]` or an alias of an existing target. Use structured Markdown and math for architecture descriptions, not ASCII diagrams.
- For each equation, provide a linked name, LaTeX block, meaning, and all symbol definitions. Keep blank lines around `$$`; split long expressions with `aligned`. Verify bound/free variables, notation consistency, limits, stop-gradient and other operators against the paper.
- Use `### Figure N: Original English caption` and an English explanation. Do not add a Chinese caption simply because the Chinese reference uses bilingual titles.
- Read [quality standards](references/quality-standards.md) for detailed checks; its Chinese labels map to the English template. Source-faithfulness and coverage are unchanged.

## Independent critical verdict

Full readings and critiques include a separate **Critical verdict** in the note and a concise verdict in the final chat response. This does not depend on running `daily-papers-review` first. An abstract recap, a list of pros and cons, or a saved-path report alone is insufficient.

- **Actual novelty**: Compare with specific prior work and identify the new mechanism, combination, data, scale, or engineering tradeoff. Bound novelty claims when the prior work could not be verified.
- **Strongest evidence**: Identify the most convincing result, its comparison conditions, and the precise claim it supports instead of merely praising performance.
- **Key gap or boundary**: Examine the confound, ablation, baseline fairness, cost, or generalization limit that most affects the conclusion. Insufficient evidence is different from evidence of failure. If no reliable flaw is established, state the validated scope rather than manufacturing a criticism.
- **Clear verdict**: Decide whether the paper merits close reading, offers a useful idea needing more evidence, adds limited value, or is not currently recommended. Explain what is worth learning and whether reproduction is worthwhile. Labels such as 🔥 / 👀 / ⚠️ / 🫠 are optional and never replace reasons.

Be direct and opinionated about methods and evidence. Anchor material judgments to sections, figures, tables, equations, or inspected code locations; distinguish author claims, reported evidence, and your inference. Before alleging a missing ablation, real-world experiment, or baseline, check the relevant sections and available supplements; unread material is unverified, not absent. Distinguish static code inspection from actual execution and reproduction.

Quick summaries, equation extraction, and explicit requests to summarize without evaluation do not require the full verdict. A no-save request changes persistence, not depth: a full chat-only reading still includes the verdict. If full text is unavailable, limit any provisional judgment to the material read and list what remains unverified; do not treat inaccessible experiments as missing.

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

For a bare arXiv link, PDF, or title without a Zotero collection, inspect the existing topic categories and select the closest match; use the unfiled folder only when uncertain (create that subfolder inside the confirmed library if needed). Missing Zotero metadata is not a reason to skip saving. Record the actual relative category in `zotero_collection`.

Write the note and read it back to confirm the title, source, and new content before reporting success. Explicit chat-only/no-save requests skip note and persistent-asset writes, concept-library writes, index refresh, and Git. For an alternative destination, write only the requested artifacts there and leave the configured Obsidian library unchanged. The concept maintenance below applies only to notes saved in that library.

Keep the template's schema keys (`title`, `method_name`, `authors`, `year`, `venue`, `tags`, `zotero_collection`, `image_source`, `created`) and add `language: en`. Use 3–8 lowercase hyphenated topic tags; preserve verifiable publication status.

Scan every concept link, check all existing categories and aliases, and create missing notes using [the English concept template](assets/concept-note-template.en.md). Reuse [the category rules](references/concept-categories.md) and actual folder names; link this paper as a representative work.

When index refresh is enabled for a saved library note:

```bash
python3 ../_shared/generate_concept_mocs.py --output-language en
python3 ../_shared/generate_paper_mocs.py --output-language en
```

After concept maintenance and checks, Git follows effective configuration and existing authorization; explicit standing or current user instructions take precedence without another confirmation. Detect the repository with `git -C "{VAULT_PATH}" rev-parse --show-toplevel` (including worktrees). Stage only this task's notes, required assets, concepts, and indexes; inspect staged changes and preserve unrelated work. Push only when enabled/authorized and a remote exists, without publishing unrelated local commits or force-pushing.

## Final checks and response

Review coverage appropriate to the selected mode, figure accessibility, inline links, and concept-note existence. For full readings and critiques, unless the user explicitly declined evaluation, verify that both the note and final response contain actual novelty, strongest evidence, a key gap or boundary, and a clear verdict; for no-save requests, check the chat response. Check source anchors and keep inferences and unverified items distinct from established flaws.

Finish saving and enabled post-processing before responding. For full readings and critiques, lead with the core conclusion and a separate concise critical verdict: the decision, key evidence, and boundary that most affects it. Then report the actual note path, new concept count, and unresolved reading/saving/synchronization gaps. A verdict in the saved file does not replace the chat verdict; do not defer it as an optional follow-up. Other modes and explicit no-evaluation requests retain their requested scope. Report saving, index refresh, commit, and push outcomes separately; a local commit is not a successful push. Do not ask whether to save after the analysis.

## Batches

For an explicitly requested Zotero collection batch, include subcollections by default, deduplicate items, check existing notes for quality, process remaining papers, and summarize completed and outstanding work. Preserve `OUTPUT_LANGUAGE` across every invocation. Follow-up explanations and comparisons use the same language unless the user changes it.
