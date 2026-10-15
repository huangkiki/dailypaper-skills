# dailypaper-skills 🗞️

**English** | [简体中文](README.md)

**One daily prompt to find relevant papers, get candid reviews, and turn the best ones into research notes.**

These are the Agent skills I use to keep up with research. They find papers on Hugging Face and arXiv, select them around your interests, and read priority papers in depth, saving Markdown notes with equations, figures, and links to technical concepts.

```text
Recommend today's papers.
```

One request runs **discovery → selection → review → priority paper notes**. You can also start with a paper you already want to read.

[🎬 Demo](#-see-it-in-use) · [🧭 Prompts](#-everyday-prompts) · [🚀 Get started](#-get-started) · [📖 Detailed guide (Chinese)](docs/usage.md)

## 🎬 See it in use

> ### [▶ My paper-reading workflow with Claude Code｜Xiaohongshu video](http://xhslink.com/o/1dhQCn40EWY)
>
> A recording of how I use the skills, in Chinese.
>
> The video shows the earlier Claude Code workflow. The current bundle also provides installation targets for Codex, Cursor, and other agents; follow the setup below for the current version.
>
> The original share link may show an unavailable-note message. The output structure and note template below provide another way to see what the workflow produces.

A run produces three connected kinds of content:

| Output | What you use it for |
| --- | --- |
| 🗞️ **Daily recommendations** | Choose what to read from “must read / worth a look / skip”; up to 10 recommendations per day by default |
| 📝 **Priority paper notes** | Work through the research question, method, equations, figures, experiments, and limitations |
| 🔗 **Concept notes and indexes** | Follow unfamiliar terms and reconnect new methods with previous reading |

**The commentary is a core part of the workflow.** Each recommendation explains what the method does, why it relates to your work, what you can reuse, and which claims deserve scrutiny. Criticism needs evidence; anything the abstract leaves unclear is marked for a full-text check.

Recommendations link to paper notes, which link to `[[concepts]]`. This illustrates the output structure with the default folder names; paper names and categories depend on the actual run:

```text
your-notes/
├── DailyPapers/
│   └── YYYY-MM-DD-paper-recommendations.md
└── 论文笔记/
    ├── category/MethodName.md
    └── _概念/topic/Concept.md
```

Existing folder names are preserved when you switch languages; you can configure your own. See the [English paper-note template](skills/paper-reader/assets/paper-note-template.en.md). Read the files in Obsidian, a Markdown editor, or the optional [Web Viewer (setup in Chinese)](docs/usage.md#可选在浏览器里看笔记).

## 🧭 Everyday prompts

After installation, ask your agent what you want to do:

| Situation | Ask your agent |
| --- | --- |
| Find today's reading | `Recommend today's papers` |
| Catch up | `Recommend papers from the past three days` or `Recommend papers from the past week` |
| Read a specific paper | `Read this paper: <arXiv link or PDF path>` |
| Get the core contribution | `Quickly summarize this paper: <PDF path>` |
| Examine the limitations | `Critically analyze this paper: <PDF path>` |
| Read your collection | `Read Diffusion Policy from my Zotero library` |
| Follow open-source projects | `Show me weekly GitHub trending` |
| Refresh navigation after moving notes | `Refresh paper and concept indexes` |

**You choose the research interests.** Defaults cover LLM reinforcement learning, RL infrastructure, world models/JEPA, dexterous manipulation, and physics simulation. Recommendations use history to avoid repeats and do not pad a sparse list. Must-read papers continue to full notes; existing notes are matched and linked.

**English and Chinese follow your prompt.** Ask in English for English recommendations and notes, or explicitly request a language: `Read this paper, but write in Chinese`. Switching languages preserves existing folders, note names, and link targets. [Language rules](skills/_shared/language.md)

## 🚀 Get started

You need an agent with file, command, and web access, plus **Python 3.10+, Git, and curl**. Full PDF reading needs **Poppler**: `brew install poppler` on macOS, `sudo apt install poppler-utils` on Ubuntu/Debian, or `pdftotext` and `pdfimages` on `PATH` on Windows. Obsidian and Zotero are optional.

### 1. Install the complete bundle

```bash
git clone https://github.com/huangkiki/dailypaper-skills.git
cd dailypaper-skills
python3 install.py --agent codex
```

Replace `codex` with `claude`, `cursor`, `copilot`, `gemini`, `opencode`, or `openclaw`. On Windows, use `py -3` if needed. The installer copies all seven skills, both workflow languages, templates, and shared dependencies together.

### 2. Set your interests and output directory

Create the shared personal configuration; an existing configuration is preserved:

```bash
python3 skills/_shared/user_config.py --init
```

Restart or refresh your agent session, then send this prompt with your own directory and interests:

```text
Configure dailypaper-skills using the shared configuration.
Save Markdown to /path/to/my-research-notes.
I work on robot learning, VLA, world models, and physics simulation.
Recommend at most 10 papers per day.
```

**No extra API key is needed by default.** Selection, reviews, and full reading use your current agent's model allowance. Save to an ordinary local directory or an Obsidian vault you choose.

### 3. Run your first recommendation

```text
Recommend today's papers.
```

The agent selects papers, writes reviews and priority notes, and returns their locations. To try a single paper first, ask `Read this paper: <link or PDF path>`. These are conversation prompts.

To upgrade, pull repository updates and rerun `python3 install.py --agent codex --update`, then refresh your session. For multiple agents or custom installation directories, see the [usage guide (Chinese)](docs/usage.md).

## 🧩 Included skills

Use `daily-papers` to follow new research and `paper-reader` for a specific paper. Fetching, review, and note generation connect automatically; each stage can also be rerun separately.

| Skill | Role |
| --- | --- |
| [daily-papers](skills/daily-papers/SKILL.en.md) | Run the complete daily paper workflow |
| [paper-reader](skills/paper-reader/SKILL.en.md) | Full reading, quick summaries, and critical analysis of arXiv papers, local PDFs, or Zotero items |
| [daily-papers-fetch](skills/daily-papers-fetch/SKILL.en.md) | Discover, select, and enrich papers from Hugging Face Daily/Trending and arXiv |
| [daily-papers-review](skills/daily-papers-review/SKILL.en.md) | Write candid reviews, reading priorities, and recommendation pages |
| [daily-papers-notes](skills/daily-papers-notes/SKILL.en.md) | Generate priority notes, add concepts, and backfill links |
| [generate-mocs](skills/generate-mocs/SKILL.en.md) | Refresh paper and concept indexes |
| [github-trending](skills/github-trending/SKILL.en.md) | Daily, weekly, and monthly project lists, plus simulation topic searches |

I also use [Zotero AI Sidebar](https://github.com/huangkiki/zotero-ai-sidebar): these skills handle discovery and research notes, while Sidebar supports questions, translation, and follow-ups inside the PDF reader.

## 💬 FAQ

**Do I need Obsidian?** No. A local Markdown directory is enough. Zotero is only needed when reading your Zotero library.

**Does it run every day or upload my notes automatically?** Runs start when requested. Installation creates no scheduled tasks, and automatic Git commit and push are disabled by default. Scheduling uses your host or system tools; archiving and synchronization follow your chosen destination and authorization.

**Has every agent been tested end to end?** The installer supports multiple targets, but the full workflow needs file, command, and web access. Installation and script checks do not establish end-to-end validation for every client. [Compatibility details (Chinese)](docs/agents.md)

**Can I change how papers are selected?** Set `daily_papers.ranking.backend` to `agent` (default), `keyword`, or `jev`. Only Jev needs an extra `TYPESAFE_API_KEY`. Upgrades preserve personal configuration; existing Jev users can switch the effective setting to `agent`. [Configuration and migration (Chinese)](docs/usage.md#3-配置并开始使用)

<details>
<summary>⚡ Optional Jev: recorded scoring cost and latency</summary>

In a single comparison on 2026-10-05, both models received the same 30 candidates and selected 10. GPT-6 Astra scoring took **$0.109264 / 10.35 s**, versus **$0.000576408 / 0.52 s** for Jev 1.13.0, with **9/10 selection overlap**. At the recorded standard API list prices, estimated scoring cost was **99.47% lower** and the call was about **20× faster**.

These are historical **scoring-stage measurements** including the host model's reported cache usage, not a full-workflow cost or an account bill. Selection overlap is not a human quality evaluation. [Recorded evidence and reproduction (Chinese)](docs/jev-benchmark.md)

</details>

## 🛠️ Development

[Architecture (Chinese)](ARCHITECTURE.md) · [Agent integration (Chinese)](docs/agents.md) · [Usage (Chinese)](docs/usage.md)

```bash
python3 -m pip install -r web-viewer/requirements.txt
python3 -m unittest discover -s tests -v
```

Usage examples, adaptation feedback, issues, and pull requests are welcome. For bugs, include your agent/OS version, failing stage, and sanitized logs.

[![Star History Chart](https://star-history.dera.page/svg?repos=huangkiki/dailypaper-skills&type=Date)](https://star-history.dera.page/#huangkiki/dailypaper-skills&Date)

## 📄 License

Apache-2.0. See [LICENSE](LICENSE).
