# Refresh paper and concept indexes

Read the [runtime](../_shared/agent-runtime.en.md) and [language rules](../_shared/language.md). Run `python3 ../_shared/user_config.py` to resolve the actual library paths and automation settings.

```bash
python3 ../_shared/generate_concept_mocs.py --output-language en
python3 ../_shared/generate_paper_mocs.py --output-language en
```

The scripts generate English navigation text while keeping folder names, existing note names, wikilink targets, and index paths unchanged. Use these bundled scripts, not scripts assumed to exist in the user's library.

Report scanned directories, created/updated/unchanged index counts, and output locations. Repeating a run with the same language and unchanged library must be idempotent. An explicit refresh request runs even if automatic index refresh is disabled.

Git commit/push defaults to off; follow the runtime's configuration and authorization checks before any Git action.
