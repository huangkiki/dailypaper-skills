# Daily papers

English workflow for [daily-papers](SKILL.md). Read the [runtime](../_shared/agent-runtime.en.md) and resolve [language](../_shared/language.md) before running commands.

One request runs the complete pipeline:

- `Recommend today's papers` → today.
- `Recommend papers from the past three days` / `last 3 days` → 3 days.
- `What papers should I read from the past week?` / `this week's papers` → 7 days.
- `Papers from the past two weeks` → 14 days.

1. Resolve the requested time range. If unspecified, use today.
2. Invoke [daily-papers-fetch](../daily-papers-fetch/SKILL.md), passing the range and `OUTPUT_LANGUAGE`.
3. When fresh enriched JSON is verified, invoke [daily-papers-review](../daily-papers-review/SKILL.md), preserving configuration and `TEMP_DIR`.
4. Pass the actual recommendation file path and language to [daily-papers-notes](../daily-papers-notes/SKILL.md).
5. Report the recommendation path, completed paper-note count, and whether indexes were refreshed, in English.

Only advance after the preceding stage's expected artifacts exist and validate. On failure, preserve completed work and report the failed stage. Do not ask the user to manually invoke all three stages. If only one stage is requested, run that stage alone.

This skill does not schedule itself. If scheduling is requested, use the host's supported scheduler and this whole-pipeline entry point, with the requested language and scope preserved.
