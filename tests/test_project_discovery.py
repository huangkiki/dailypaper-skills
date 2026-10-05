from datetime import date
import unittest
from unittest.mock import patch

from test_portability import ROOT, load_module

discovery = load_module("project_discovery", ROOT / "skills/github-trending/discover_projects.py")
writer = load_module("project_note_writer", ROOT / "skills/github-trending/write_trending_note.py")


def repo(name, created):
    return {"full_name": name, "html_url": f"https://github.com/{name}", "description": "A new physics simulator",
            "stargazers_count": 1, "created_at": created + "T00:00:00Z", "pushed_at": "2026-10-04T00:00:00Z"}


class DiscoveryTests(unittest.TestCase):
    def test_unknown_project_names_are_discovered_and_duplicates_removed(self):
        result = {"items": [repo("new/unknown-engine", "2026-10-03"), repo("old/classic", "2020-01-01")],
                  "total_count": 2, "incomplete_results": False}
        with patch.object(discovery, "search_repositories", return_value=result):
            report = discovery.discover(['"physics simulation" in:description'], 7, date(2026, 10, 4))
        self.assertEqual([r["repo"] for r in report["new_projects"]], ["new/unknown-engine"])
        self.assertEqual([r["repo"] for r in report["recently_updated"]], ["old/classic"])
        self.assertEqual(len(report["new_projects"][0]["matched_queries"]), 2)
        note = writer.build_markdown([], "weekly", date(2026, 10, 4), report)
        self.assertIn("new/unknown-engine", note)
        self.assertIn("代码推送不等于新版本发布", note)

    def test_failed_search_cannot_be_reported_as_no_new_projects(self):
        with patch.object(discovery, "search_repositories", side_effect=RuntimeError("GitHub search HTTP 403")):
            report = discovery.discover(["physics"], 7, date(2026, 10, 4))
        self.assertEqual(report["status"], "partial")
        self.assertIn("部分检索失败", writer.build_markdown([], "weekly", date(2026, 10, 4), report))


if __name__ == "__main__":
    unittest.main()
