# GitHub trending and project discovery

Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md). Announce today's date and period in English. Load configuration with `python3 ../_shared/user_config.py`.

Use `paths.github_trending_folder`, the configured research keywords/boosts/negative keywords, and `daily_papers.project_queries`. Project names are examples, not a discovery whitelist.

## Resolve period and filters

- `weekly`, `past week`, or no period → `--since weekly`, discovery `--days 7`.
- `daily`, `today` → `--since daily`, discovery `--days 1`.
- `monthly`, `this month` → `--since monthly`, discovery `--days 30`.

GitHub Trending supports only these three periods. A request such as “Python repositories” adds `--language python` to the fetch command. That flag selects a programming language; it does **not** select the output language.

## Fetch, discover, and write

Run with the resolved period and optional programming-language filter:

```bash
python3 fetch_trending.py --since weekly --output "{TEMP_DIR}/github_trending.json"
python3 discover_projects.py --days 7 --output "{TEMP_DIR}/github_projects.json"
python3 write_trending_note.py "{TEMP_DIR}/github_trending.json" --projects "{TEMP_DIR}/github_projects.json" --period weekly --output-language en
```

The fetcher parses repository descriptions, languages, star/fork counts, period star growth, and keyword relevance. It retains unrelated entries and sorts by period star growth. Verify the JSON and inspect stderr if it is empty.

Discovery searches configured topics separately by creation and push dates, up to 10 results per query. It may read `GITHUB_TOKEN` / `GH_TOKEN`; do not print or save credentials. A recently pushed repository is not evidence of a release. Read original README/Releases when needed to verify claims. `status=partial` and empty results must not be reported as proof that no new projects exist. Pass partial results to the writer so their limitations remain visible.

The writer saves English Markdown under the configured folder and prints the actual path. Weekly filenames use ISO weeks, e.g. `2026-W28 GitHub Weekly.md`; daily/monthly filenames use dates. It includes a summary, relevant repositories, discovered projects/updates, and the full ranking. Original repository descriptions and configured keywords remain source text; translate them in the final user-facing explanation if helpful, preserving names and links.

Report trending/relevant counts, new/updated project counts, search completeness, and the saved note path. The scripts do not need an LLM or subagents. Do not perform Git actions. On network failure, inspect the host's actual network/proxy settings without assuming a port.
