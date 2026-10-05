import importlib.util
import pathlib
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "web-viewer" / "app.py"
SPEC = importlib.util.spec_from_file_location("web_viewer_app", APP_PATH)
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)


class PaperNoteDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = pathlib.Path(self.temp_dir.name)
        self.notes_root = self.vault / "论文笔记"
        self.concepts_dir = self.notes_root / "_概念"
        self.inbox_dir = self.notes_root / "_待整理"

        self._originals = {
            name: getattr(viewer, name)
            for name in (
                "VAULT_PATH",
                "DAILY_DIR",
                "TRENDING_DIR",
                "_NOTES_ROOT",
                "NOTES_DIR",
                "CONCEPTS_DIR",
                "WIKILINK_INDEX",
            )
        }
        viewer.VAULT_PATH = str(self.vault)
        viewer.DAILY_DIR = str(self.vault / "DailyPapers")
        viewer.TRENDING_DIR = str(self.vault / "GitHubTrending")
        viewer._NOTES_ROOT = str(self.notes_root)
        viewer.NOTES_DIR = str(self.inbox_dir)
        viewer.CONCEPTS_DIR = str(self.concepts_dir)

        self._write(self.inbox_dir / "InboxMethod.md", "Inbox paper")
        self._write(
            self.notes_root / "3-机器人策略" / "CategorizedMethod.md",
            "---\ntitle: Categorized paper\n---\nCategorized body",
        )
        self._write(self.notes_root / "3-机器人策略" / "3-机器人策略.md", "MOC")
        self._write(self.concepts_dir / "1-基础" / "Concept.md", "Concept")
        self._write(self.notes_root / ".hidden" / "Hidden.md", "Hidden")
        self._write(self.notes_root / "A" / "SameName.md", "First")
        self._write(self.notes_root / "B" / "SameName.md", "Second")

    def tearDown(self):
        for name, value in self._originals.items():
            setattr(viewer, name, value)
        self.temp_dir.cleanup()

    @staticmethod
    def _write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_discovers_inbox_and_categorized_notes_only(self):
        notes = viewer.discover_paper_notes()
        ids = {note["id"] for note in notes}

        self.assertEqual(
            ids,
            {
                "_待整理/InboxMethod",
                "3-机器人策略/CategorizedMethod",
                "A/SameName",
                "B/SameName",
            },
        )
        categorized = next(note for note in notes if note["filename"] == "CategorizedMethod")
        self.assertEqual(categorized["category"], "3-机器人策略")

    def test_list_and_detail_use_stable_note_id(self):
        listed = viewer.list_paper_notes()
        categorized = next(note for note in listed if note["filename"] == "CategorizedMethod")

        self.assertEqual(categorized["id"], "3-机器人策略/CategorizedMethod")
        self.assertEqual(categorized["title"], "Categorized paper")
        detail = viewer.get_paper_note(categorized["id"])
        self.assertIn("Categorized body", detail["content"])
        self.assertIn("Categorized body", viewer.get_paper_note("CategorizedMethod")["content"])

    def test_detail_rejects_paths_outside_discovered_notes(self):
        self._write(self.vault / "outside.md", "Outside")

        self.assertEqual(viewer.get_paper_note("../outside"), {"error": "not found"})
        self.assertEqual(viewer.get_paper_note("_概念/1-基础/Concept"), {"error": "not found"})
        self.assertEqual(viewer.get_paper_note("SameName"), {"error": "not found"})

    def test_discovery_ignores_symlinks_outside_notes_root(self):
        outside = self.vault / "outside.md"
        self._write(outside, "Outside")
        link = self.inbox_dir / "LinkedOutside.md"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks are not supported")

        self.assertNotIn(
            "_待整理/LinkedOutside",
            {note["id"] for note in viewer.discover_paper_notes()},
        )

    def test_wikilink_index_avoids_ambiguous_basenames(self):
        viewer.build_wikilink_index()

        self.assertIn("A/SameName", viewer.WIKILINK_INDEX)
        self.assertIn("B/SameName", viewer.WIKILINK_INDEX)
        self.assertNotIn("SameName", viewer.WIKILINK_INDEX)
        self.assertEqual(
            viewer.WIKILINK_INDEX["CategorizedMethod"]["path"],
            "3-机器人策略/CategorizedMethod",
        )

    def test_search_returns_categorized_note_id(self):
        result = next(item for item in viewer.search(q="Categorized") if item["type"] == "note")

        self.assertEqual(result["id"], "3-机器人策略/CategorizedMethod")


if __name__ == "__main__":
    unittest.main()
