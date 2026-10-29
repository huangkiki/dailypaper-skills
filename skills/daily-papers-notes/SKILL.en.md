# Concepts, paper notes, and links

Stage 3. Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md), load effective configuration, and announce the date in English.

Require fresh enriched data at `{TEMP_DIR}/daily_papers_enriched.json` and the actual recommendation path passed by review. For a standalone/resumed run, locate the date's recommendation in the selected destination; accept both filename suffixes from the language rules. If both exist and the request does not identify one, resolve which run is intended before writing. Missing prerequisites must be reported, not silently skipped.

## Maintain concepts

Extract wikilinks from the recommendation and names from enriched `method_names`. Deduplicate and retain specific methods, models, datasets, simulators/frameworks, and technical concepts. Exclude generic words, this paper's own name, people, and companies.

Search all concept subdirectories and aliases before creating a missing concept. Reuse existing filenames and categories regardless of their language. Follow [concept categories](../paper-reader/references/concept-categories.md) for classification and the [English concept template](../paper-reader/assets/concept-note-template.en.md) for new prose. Avoid putting everything in the unclassified folder.

## Read must-read papers

Read the recommendation's priority table, accepting `Must read` and `必读`. Generate full notes for every must-read paper; “Worth a look” and “Skip” do not receive automatic full notes.

Check existing notes rather than merely checking existence. Accept corresponding headings in either language: Key equations/关键公式, Figures and tables/关键图表, and Experiments/实验/实验结果. The existing workflow uses 100 lines as a skeleton warning, and checks newly generated full notes for at least 120 lines, two math expressions, and one image reference. These are screening checks, not permission to pad a note, fabricate formulas, or add nonexistent figures. Compare against the source's actual equations, figures, tables, and results; explain a source with no applicable item. Preserve existing useful content while repairing incomplete notes.

Before skipping an existing note and after generating a new one, check for an evidence-based independent critical verdict: actual novelty, strongest evidence, a key gap or boundary, and a clear decision with source anchors. Equivalent content under another heading is acceptable; a heading alone or generic pros and cons are not. Repair a missing verdict in the original note while preserving valid content and user annotations. The recommendation page's short review does not replace a judgment based on full reading.

Invoke [paper-reader](../paper-reader/SKILL.md) for each paper with its arXiv/PDF source and `OUTPUT_LANGUAGE=en`. Let it choose the method-based filename and collection path; record the actual path after generation. Use the full template, including the independent critical verdict, and verify source coverage immediately. Do not replace the workflow with a short summary or omit papers because there are many. Paper-reader maintains concepts too; avoid duplicate creation.

## Backfill and finish

Scan paper notes excluding the configured concept directory. Match method/model names case-insensitively and use enriched method names when needed. The helper supports both recommendation languages:

```bash
python3 backfill_links.py --recommendation "{RECOMMENDATION_PATH}" --notes-dir "{NOTES_PATH}"
```

Verify its results; manually resolve unmatched names using actual generated paths. Insert `- 📒 **Note**: [[actual-note-name]]` after `**Source**` in an English page, or the corresponding Chinese line in a Chinese page. Do not duplicate “Note” or “Existing note” links. Fix priority-table and detail-section links to use the real filename. Preserve the rest of the recommendation.

If `AUTO_REFRESH_INDEXES=true`:

```bash
python3 ../_shared/generate_concept_mocs.py --output-language en
python3 ../_shared/generate_paper_mocs.py --output-language en
```

Git requires the runtime's configuration and authorization checks. Report new concepts, completed paper notes, backfilled links, and index status. If interrupted, preserve completed artifacts and explicitly list remaining papers; report completion only when all required papers are handled.
