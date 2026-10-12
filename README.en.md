# dailypaper-skills 🗞️

**English** | [简体中文](README.md)

**Turn your agent into a research reading workflow: discover relevant papers, decide what deserves your attention, and build notes you can use again.**

Keeping up with research takes more than collecting links. dailypaper-skills finds papers that match your interests, critiques their methods and evidence, and reads the most useful ones in depth. You get connected Markdown notes with equations, figures, tables, and technical concepts.

Ask your agent:

```text
Recommend today's papers.
```

You get **up to 10 recommendations per day, clear reading priorities, and full notes for must-read papers**. Recommendation pages link to paper notes, which link to reusable concept notes.

Built for **AI and robotics researchers, graduate students, and engineers following research**. Install it for Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode, or OpenClaw. Other agents can use the bundle if they can read instructions, run Python, access the web, and write files.

[What you get](#-what-you-get) · [Skills](#-skills) · [Get started](#-get-started) · [Language selection](#-english-and-chinese) · [Usage guide (Chinese)](docs/usage.md) · [Video demo (Chinese)](http://xhslink.com/o/1dhQCn40EWY)

## 🎁 What you get

### 🔎 A reading list shaped by your research

Discover papers from Hugging Face Daily/Trending and arXiv, filter by your configured interests, and avoid repeats using recommendation history. Catch up on three days or a whole week in one request. If too few relevant papers are available, the workflow does not pad the list.

Each recommendation explains what the method does, why it matters to your work, what you can reuse, and what needs closer scrutiny. Original sources and existing notes remain linked.

### 🎯 Clear, evidence-based priorities

| Priority | What happens next |
| --- | --- |
| 🔥 Must read | Read the full paper and generate structured notes |
| 👀 Worth a look | Understand the contribution; request a deeper reading if useful |
| 💤 Skip | See why the relevance or contribution is limited |

The commentary is deliberately candid: specific about assumptions, experiment coverage, engineering cost, and the limits of the evidence. Missing information is marked as needing a full-text check. **By default, your current agent scores relevance and evaluates research value. Jev is an optional relevance-scoring backend.**

### 📝 Research notes that remain useful

Full notes cover the problem, method, equations, figures, tables, experiments, and critical assessment. Technical terms link to concept notes; the workflow backfills links into the recommendation page and refreshes navigation indexes.

| Artifact | Contents |
| --- | --- |
| Recommendation page | Research take, reading priorities, individual reviews, source and note links |
| Paper notes | Method analysis, equations, figures, experiments, and limitations |
| Concept notes and indexes | Definitions, related methods, and navigation through your research library |

See the [English paper-note template](skills/paper-reader/assets/paper-note-template.en.md). Files are ordinary Markdown in your chosen local directory. Obsidian is useful for linked reading, but a Markdown editor or the optional Web Viewer also works.

## 🧩 Skills

| What you want | Ask your agent | Skill |
| --- | --- | --- |
| Today's research and priority notes | `Recommend today's papers` | [daily-papers](skills/daily-papers/SKILL.md) |
| Catch up | `Recommend papers from the past week` | daily-papers |
| Read a paper | `Read this paper: <arXiv link or PDF path>` | [paper-reader](skills/paper-reader/SKILL.md) |
| Read your collection | `Read Diffusion Policy from my Zotero library` | paper-reader |
| Get the gist | `Quickly summarize this paper: <PDF path>` | paper-reader |
| Discover open-source projects | `Show me weekly GitHub trending` | [github-trending](skills/github-trending/SKILL.md) |
| Refresh navigation | `Refresh paper and concept indexes` | [generate-mocs](skills/generate-mocs/SKILL.md) |

The daily pipeline connects [fetch](skills/daily-papers-fetch/SKILL.md), [review](skills/daily-papers-review/SKILL.md), and [notes](skills/daily-papers-notes/SKILL.md). You can also ask to “fetch papers,” “review fetched papers,” or “generate paper notes” to rerun one stage.

GitHub discovery combines Trending with topic searches for new simulation projects and recent updates. Daily, weekly, and monthly periods are supported. Default interests include LLM reinforcement learning, RL infrastructure, world models/JEPA, dexterous manipulation, and physics simulation. These are configurable; known engine names are examples, not a whitelist.

## 🌐 English and Chinese

**Ask in English to get the English workflow and output. Ask in Chinese to get Chinese.** No separate installation or language toggle is needed.

| Request | Result |
| --- | --- |
| `Recommend papers from the past three days` | English, three-day window |
| `过去三天论文推荐` | Chinese, three-day window |
| `今日论文推荐，用英文输出` | English, today |
| `Read this paper, but write the notes in Chinese` | Chinese notes |

An explicit language request takes priority. All pipeline stages inherit the selected language. Paper titles, URLs, code, and quoted source text do not determine it. Ambiguous follow-ups retain the conversation's language; without context, the original Chinese default remains.

New recommendations, paper/concept notes, generated index text, and summaries follow that language. Existing folders, note names, citations, and link targets are preserved. Original paper metadata and repository descriptions remain source text. This supports English skill workflows; it does not translate the optional Web Viewer UI or Claude daemon interface.

For direct script use, the index generators and GitHub note writer accept `--output-language en` (default `zh`). GitHub's separate `--language python` flag filters programming languages. See the [shared language contract](skills/_shared/language.md).

## 🚀 Get started

You need an agent with file, command, and web access; **Python 3.10+, Git, and curl**; and **Poppler** for PDF text/image extraction. Install Poppler with `brew install poppler` on macOS or `sudo apt install poppler-utils` on Ubuntu/Debian. On Windows, make `pdftotext` and `pdfimages` available on `PATH`. Obsidian and Zotero are optional.

### 1. Install the complete bundle

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills
python3 install.py --agent codex
```

Replace `codex` with `claude`, `cursor`, `copilot`, `gemini`, `opencode`, or `openclaw`. Use `py -3` instead of `python3` on Windows if needed. The installer copies all seven skills, both workflow languages, templates, and `_shared` dependencies. Do not copy a single skill file on its own.

```bash
# Multiple agents or a project-local destination:
python3 install.py --agent claude codex
python3 install.py --target "/path/to/project/.agents/skills"

# Preview without writing:
python3 install.py --agent codex --dry-run
```

### 2. Set your interests and output directory

```bash
python3 skills/_shared/user_config.py --init
```

This prints the shared configuration path, normally `~/.config/dailypaper-skills/user-config.json` (respecting `XDG_CONFIG_HOME`). Existing personal configuration is preserved. Ask your agent:

```text
Configure dailypaper-skills using the shared configuration.
Save Markdown to /path/to/my-research-notes.
I work on robot learning, VLA, diffusion policies, and physics simulation.
Recommend at most 10 papers per day.
```

**No extra API key is needed by default.** Your current agent reads candidate abstracts, scores relevance, then reviews and reads the selected papers using its existing model/session allowance.

Choose `daily_papers.ranking.backend`:

| Mode | How papers are selected | Extra key |
| --- | --- | --- |
| `agent` (default) | Semantic scores from your current agent, validated before selection | None |
| `jev` | TypeSafe Jev semantic scoring | `TYPESAFE_API_KEY` |
| `keyword` | Keyword scores only | None |

For optional Jev mode, set the key in the environment that starts your agent, never in a committed config file. Explicit Jev failures stop that mode instead of silently switching backends. Upgrades preserve personal configuration: if an older config says `jev`, change it to `agent` to use the new default without an extra key.

Use `python3 skills/_shared/user_config.py` to inspect effective settings. Important fields include `paths.obsidian_vault` (any Markdown output directory), folder names, `daily_papers.research_interests`, keywords, `top_n`, and `ranking`. Zotero paths are needed only for Zotero access. English folder names can be configured explicitly; language switching never renames an existing library.

Configuration precedence is built-in defaults → bundled config → local config → shared personal config → `DAILYPAPER_CONFIG`; `OBSIDIAN_VAULT_PATH` overrides the output root last. Use a distinct `DAILYPAPER_TEMP_DIR` for concurrent runs.

### 3. Ask for papers

Restart or refresh your agent session and ask `Recommend today's papers`. The agent filters, reviews, reads priority papers, and returns the artifact locations. These are conversation prompts, not terminal commands.

To upgrade later, pull repository updates and rerun `python3 install.py --agent codex --update`. Personal configuration is preserved; refresh the agent session to load the updated skills.

## ⚡ Optional: Jev for ranking

You can enable Jev to delegate repeated relevance scoring to a dedicated API, while keeping research commentary and full reading in the host agent. In the repository's **single 2026-10-05 scoring comparison**, both models received the same 30 candidates and selected 10:

| Scoring stage | GPT-6 Astra | Jev 1.13.0 |
| --- | ---: | ---: |
| Cost at recorded standard API list prices | $0.109264 | $0.000576408 |
| API elapsed time | 10.35 s | 0.52 s |
| Total tokens | 11,932 | 14,198 |

That run had **99.47% lower estimated scoring cost**, about **20× lower API latency**, and **9/10 selection overlap**. Jev used more tokens but had a lower unit price. These are historical scoring-stage measurements including the host model's reported cache usage, not current pricing, a full-workflow cost, an account bill, or a human quality evaluation. [Recorded evidence and reproduction (Chinese)](docs/jev-benchmark.md)

## 📚 Fit it into your reading workflow

- **Obsidian**: Browse linked recommendations, paper notes, concepts, and indexes.
- **Zotero**: Find papers by title or process requested collections using existing attachments.
- **Browser**: Browse the same notes in the optional Web Viewer.
- **Multiple agents**: Share research interests and output settings. Installation/script checks do not imply every host has passed end-to-end testing. [Compatibility details (Chinese)](docs/agents.md)

[Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar) complements this workflow with questions, translation, and follow-ups while reading PDFs.

## 💬 FAQ

**Do I need Obsidian?** No. A local Markdown directory is enough. Zotero is only needed when reading your Zotero library.

**Does installation schedule daily runs or publish my notes?** No. Runs start when requested; scheduling uses your host's facilities. Automatic Git commit and push are disabled by default. Saving or synchronizing to Obsidian follows your explicit destination and authorization.

**Can a chat-only client run this?** The full local pipeline requires commands and filesystem access. Cloud/sandbox agents also need dependencies and access to the output directory in their actual execution environment.

**Can I keep using Chinese?** Yes. Chinese prompts retain the Chinese workflow. Explicit language preferences override automatic selection.

## 🛠️ Development

[Architecture (Chinese)](ARCHITECTURE.md) · [Usage (Chinese)](docs/usage.md) · [Language rules](skills/_shared/language.md)

```bash
python3 -m pip install -r web-viewer/requirements.txt
python3 -m unittest discover -s tests -v
```

For issues, include your agent/OS version, failing stage, and sanitized logs. Contributions and adaptation feedback are welcome.

[![Star History Chart](https://star-history.dera.page/svg?repos=huangkiki/dailypaper-skills&type=Date)](https://star-history.dera.page/#huangkiki/dailypaper-skills&Date)

## 📄 License

Apache-2.0. See [LICENSE](LICENSE).
