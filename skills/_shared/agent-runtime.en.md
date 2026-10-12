# Running on different agents

The bundle needs file access, Python/command execution, web access, and Markdown output. Use the host's actual tools; no particular agent brand or model is required. Resolve [output language](language.md) first.

## Paths and configuration

- Resolve script and resource paths relative to the current skill directory, not the user's working directory. Set the working directory or use absolute paths; quote paths containing spaces.
- Install the whole bundle: each skill and `_shared` must be siblings.
- Run `python3 ../_shared/user_config.py` using Python 3.10+. On Windows, use `py -3` or `python` if appropriate. Read the effective JSON, including `runtime.temp_dir`.
- Configuration merges in this order: built-in defaults → `_shared/user-config.json` → `_shared/user-config.local.json` → `~/.config/dailypaper-skills/user-config.json` (respecting `XDG_CONFIG_HOME`) → the file in `DAILYPAPER_CONFIG`. `OBSIDIAN_VAULT_PATH` overrides the vault path last. Arrays are replaced, not appended.
- Set `TEMP_DIR` from `runtime.temp_dir`. Replace `{TEMP_DIR}` in examples with that absolute path. Every stage uses the same directory. For concurrent runs, set a different `DAILYPAPER_TEMP_DIR` for each run and propagate it.
- Derive `VAULT_PATH`, `NOTES_PATH`, `CONCEPTS_PATH`, and `DAILY_PAPERS_PATH` from `paths.obsidian_vault`, `paper_notes_folder`, `concepts_folder`, and `daily_papers_folder`. Do not translate these configured paths.

## Invocation and tools

- Use native skill invocation when available. Otherwise read the target `SKILL.md`, select its language version, and execute its instructions. Run fetch → review → notes sequentially, checking each stage's actual output before continuing.
- Names such as Bash, Read, Write, Glob, WebFetch, and WebSearch describe capabilities, not required tool names. Without a PDF reader, use `pdftotext` and `pdfimages`.
- Only if the host supports and permits subagents, a paper-reader invocation may run in a separate context. Pass the skill path, paper source, effective configuration, `TEMP_DIR`, and `OUTPUT_LANGUAGE`. Otherwise read papers sequentially in the current session.
- Report missing capabilities and completed stages accurately. A stale file does not prove a failed command succeeded.

## Delivery and optional integrations

Follow the user's chosen destination and the host's permissions. A configured vault is an available destination, not permission to archive there when the user requests chat or project-local output. Never infer Obsidian synchronization from language selection.

Read `automation.auto_refresh_indexes`, `git_commit`, and `git_push`. Index refresh defaults to enabled; Git actions default to disabled. Git additionally requires existing user authorization, a repository, and actual staged changes. Stage only task files, preserve unrelated changes, and push only when both Git switches permit it and a remote exists.

The optional `paper_daemon.py` and Web Viewer's Claude chat button still require Claude CLI. The browser UI and daemon are separate entry points; this language routing applies to skill requests, not to the Web Viewer's interface.
