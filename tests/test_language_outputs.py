"""Exercise bilingual artifacts through the installed bundle without network calls."""

from datetime import date, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_portability import IsolatedWorkspace, ROOT, installer, load_module


writer = load_module("language_trending_writer", ROOT / "skills/github-trending/write_trending_note.py")
backfill = load_module("language_backfill", ROOT / "skills/daily-papers-notes/backfill_links.py")


class LanguageOutputTests(IsolatedWorkspace):
    def setUp(self):
        super().setUp()
        self.bundle = self.root / "installed skills"
        installer.install([self.bundle])
        self.vault = self.root / "Research notes"
        self.write_json(self.root / "config.json", {"paths": {
            "obsidian_vault": str(self.vault),
            "paper_notes_folder": "Papers",
            "concepts_folder": "Concepts",
            "github_trending_folder": "Projects",
        }})
        os.environ["DAILYPAPER_CONFIG"] = str(self.root / "config.json")

    def test_indexes_switch_language_without_renaming_or_changing_targets(self):
        paper = self.vault / "Papers/机器人/Method.md"
        concept = self.vault / "Papers/Concepts/Control/MPC.md"
        for path in (paper, concept):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Source note\n", encoding="utf-8")
        (paper.parent / "Empty").mkdir()

        for kind in ("paper", "concept"):
            command = self.bundle / f"_shared/generate_{kind}_mocs.py"
            with self.subTest(kind=kind):
                english = self.run_python(command, "--output-language", "en")
                self.assertEqual(english.returncode, 0, english.stderr)
                summary = json.loads(english.stdout)
                self.assertEqual(summary["indexed_notes"], 1)
                repeated = self.run_python(command, "--output-language", "en")
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                self.assertEqual(json.loads(repeated.stdout)["unchanged_files"], summary["total_directories"])

        moc = paper.parent / "机器人.md"
        english_text = moc.read_text(encoding="utf-8")
        self.assertIn("## Notes in this directory", english_text)
        self.assertIn("[[Papers/机器人/Method|Method]]", english_text)
        self.assertIn("No content yet", (paper.parent / "Empty/Empty.md").read_text(encoding="utf-8"))
        english_paths = set(self.vault.rglob("*.md"))
        chinese = self.run_python(self.bundle / "_shared/generate_paper_mocs.py")
        self.assertEqual(chinese.returncode, 0, chinese.stderr)
        self.assertEqual(set(self.vault.rglob("*.md")), english_paths)
        self.assertIn("## 当前目录笔记", moc.read_text(encoding="utf-8"))
        self.assertIn("[[Papers/机器人/Method|Method]]", moc.read_text(encoding="utf-8"))
        self.assertEqual(paper.read_text(encoding="utf-8"), "# Source note\n")

    def test_english_trending_cli_preserves_source_data_and_partial_warning(self):
        data = [{"repo": "lab/robot", "url": "https://github.com/lab/robot", "rank": 1,
                 "description": "机器人 | simulator", "language": "Python", "relevant": True,
                 "matched_keywords": ["simulation"], "stars_period": 7, "stars_total": 42,
                 "period": "weekly"}]
        source = self.write_json(self.root / "trending.json", data)
        discovery = self.write_json(self.root / "projects.json", {
            "start_date": "2026-10-01", "end_date": "2026-10-07", "status": "partial",
            "new_projects": [], "recently_updated": [],
        })
        result = self.run_python(self.bundle / "github-trending/write_trending_note.py",
                                 source, "--projects", discovery, "--output-language", "en")
        self.assertEqual(result.returncode, 0, result.stderr)
        note = Path(result.stdout.strip())
        self.assertEqual(note.parent, self.vault / "Projects")
        self.assertTrue(note.name.endswith(" GitHub Weekly.md"))
        text = note.read_text(encoding="utf-8")
        self.assertIn("Relevant to your research", text)
        self.assertIn("Some searches failed", text)
        self.assertIn("A code push is not a release", text)
        self.assertIn("机器人 \\| simulator", text)
        self.assertIn("| +7 | 42 | Python | ✅ |", text)
        self.assertIn("https://github.com/lab/robot", text)

    def test_trending_filenames_keep_iso_week_and_chinese_default(self):
        day = date(2021, 1, 1)
        self.assertEqual(writer.note_filename("weekly", day), "2020-W53 GitHub周榜.md")
        self.assertEqual(writer.note_filename("weekly", day, "en"), "2020-W53 GitHub Weekly.md")
        self.assertEqual(writer.note_filename("daily", day, "en"), "2021-01-01 GitHub Daily.md")
        self.assertEqual(writer.note_filename("monthly", day, "en"), "2021-01-01 GitHub Monthly.md")

    def test_discovery_only_english_note_retains_project_evidence(self):
        report = {"start_date": "2026-10-01", "end_date": "2026-10-07", "status": "complete",
                  "new_projects": [{"repo": "new/engine", "url": "https://github.com/new/engine",
                                    "description": "A physics engine", "stars": 3,
                                    "created_at": "2026-10-02", "pushed_at": "2026-10-05"}],
                  "recently_updated": []}
        text = writer.build_markdown([], "daily", date(2026, 10, 7), report, "en")
        self.assertIn("new/engine", text)
        self.assertIn("created 2026-10-02; pushed 2026-10-05", text)
        self.assertNotIn("Some searches failed", text)

    def test_backfill_both_languages_is_idempotent_and_preserves_existing_notes(self):
        note_dir = self.root / "custom note folder"
        note_dir.mkdir()
        for name in ("MethodA", "MethodB", "MethodC"):
            (note_dir / f"{name}.md").write_text("# Existing content\n", encoding="utf-8")
        for source, label, existing, heading in (
            ("Source", "Note", "Existing note", "Reading priorities"),
            ("来源", "笔记", "已有笔记", "分流表"),
        ):
            with self.subTest(language=source):
                recommendation = self.root / f"{source}.md"
                original = (f"## {heading}\n\n| Priority | Papers |\n| --- | --- |\n"
                            "| 🔥 | [[methoda]] · [[MethodB]] · [[MethodC]] |\n\n"
                            f"## Robotics\n\n### 1. methoda: A method\n- **{source}**: arXiv\n\n"
                            f"### 2. MethodB: Another method\n- **{source}**: HF Daily\n"
                            f"- 📒 **{existing}**: [[MethodB]]\n\n"
                            f"### 3. MethodC: Last method\n- **{source}**: arXiv\n\n"
                            "## Closing\n\nPreserve this paragraph.\n")
                recommendation.write_text(original, encoding="utf-8")
                command = (self.bundle / "daily-papers-notes/backfill_links.py",
                           "--recommendation", recommendation, "--notes-dir", note_dir)
                result = self.run_python(*command)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = recommendation.read_text(encoding="utf-8")
                self.assertIn(f"- 📒 **{label}**: [[MethodA]]", output)
                self.assertIn(f"- 📒 **{label}**: [[MethodC]]", output)
                self.assertEqual(output.count(f"- 📒 **{existing}**: [[MethodB]]"), 1)
                self.assertNotIn(f"- 📒 **{label}**: [[MethodB]]", output)
                self.assertIn("| 🔥 | [[MethodA]] · [[MethodB]] · [[MethodC]] |", output)
                self.assertTrue(output.endswith("Preserve this paragraph.\n"))
                self.assertEqual(self.run_python(*command).returncode, 0)
                self.assertEqual(recommendation.read_text(encoding="utf-8"), output)

    def test_backfill_excludes_configured_concepts_and_navigation_notes(self):
        notes = self.vault / "Papers"
        for relative in ("Robotics/Method.md", "Concepts/Control/Method.md", "Robotics/Robotics.md"):
            path = notes / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Note\n", encoding="utf-8")
        index = backfill.scan_notes(notes)
        self.assertEqual(set(index), {"method"})
        self.assertEqual(index["method"]["path"], Path("Papers/Robotics/Method.md"))

    def test_invalid_output_language_fails_without_writing_notes(self):
        result = self.run_python(self.bundle / "_shared/generate_paper_mocs.py",
                                 "--output-language", "fr")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.vault.exists())

    def test_fallback_history_reads_both_recommendation_languages(self):
        fetch = load_module("bilingual_history_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        daily = self.root / "DailyPapers"
        daily.mkdir()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        for suffix, arxiv_id in (("论文推荐", "2601.00001"), ("paper-recommendations", "2601.00002")):
            (daily / f"{yesterday}-{suffix}.md").write_text(
                f"[arXiv](https://arxiv.org/abs/{arxiv_id})\n", encoding="utf-8")
        with patch.object(fetch, "DAILYPAPERS_DIR", daily):
            self.assertEqual(fetch.load_fallback_ids(1), {"2601.00001", "2601.00002"})
