"""Exercise the no-extra-key handoff, its validation, and explicit backend choices."""

import copy
import json
import os
import sys
from unittest.mock import patch

from test_portability import IsolatedWorkspace, ROOT, installer, load_module
from test_jev_ranker import paper
import agent_ranker
import user_config


class AgentRankingTests(IsolatedWorkspace):
    def setUp(self):
        super().setUp()
        os.environ.pop("TYPESAFE_API_KEY", None)
        self.config = copy.deepcopy(user_config.DEFAULT_CONFIG["daily_papers"])

    def scores(self, request, values):
        return {"run_id": request["run_id"], "scores": [
            {"id": index, "score": value, "reason": f"Evidence for candidate {index}"}
            for index, value in enumerate(values)
        ]}

    def test_default_prepares_full_pool_without_key_or_api_calls(self):
        fetch = load_module("agent_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        candidates = [paper(i) for i in range(30)]
        output, report = self.root / "candidates.json", self.root / "report.json"
        self.assertEqual(fetch._CONFIG["ranking"]["backend"], "agent")
        for key in ("", "present-but-not-selected"):
            with self.subTest(key_present=bool(key)), \
                    patch.dict(os.environ, {"TYPESAFE_API_KEY": key}), \
                    patch.object(sys, "argv", ["fetch", "--output", str(output), "--usage-output", str(report)]), \
                    patch.object(fetch, "fetch_hf_papers", return_value=[]), \
                    patch.object(fetch, "fetch_arxiv_papers", return_value=[]), \
                    patch.object(fetch, "merge_and_dedup", return_value=candidates), \
                    patch.object(fetch, "rank_papers") as jev:
                fetch.main()
                jev.assert_not_called()
                request = json.loads(output.read_text())
                self.assertEqual(request["status"], "awaiting_agent")
                self.assertEqual(request["candidates"], candidates)
                self.assertEqual(request["requested_top_n"], 10)
                self.assertEqual(request["research_interests"], self.config["research_interests"])
                pending = json.loads(report.read_text())
                self.assertEqual(pending["run_id"], request["run_id"])
                self.assertIsNone(pending["selected_count"])
                self.assertIsNone(pending["usage"])

    def test_semantic_scores_control_selection_and_keep_source_metadata(self):
        candidates = [{**paper(4, 2), "source": "hf-daily", "hf_upvotes": 8},
                      paper(3, 4), paper(2, 4), paper(1, 99)]
        original = copy.deepcopy(candidates)
        request = agent_ranker.prepare_request(candidates, self.config, 2)
        response = self.scores(request, [4, 3, 3, 1])
        response["scores"].reverse()  # Judge row order must not decide the ranking.
        selected, report = agent_ranker.apply_scores(request, response)
        self.assertEqual([p["url"] for p in selected], [candidates[i]["url"] for i in (0, 2)])
        self.assertEqual(selected[0]["source"], "hf-daily")
        self.assertEqual(selected[0]["hf_upvotes"], 8)
        self.assertEqual(selected[0]["keyword_score"], 2)
        self.assertEqual(selected[0]["score"], 100)
        self.assertEqual(selected[0]["agent"]["reason"], "Evidence for candidate 0")
        self.assertNotIn("jev", selected[0])
        self.assertEqual(candidates, original)
        self.assertIsNone(report["usage"])
        self.assertFalse(report["usage_complete"])
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["candidate_count"], 4)

    def test_sparse_and_empty_pools_are_not_padded(self):
        for candidates, values in (([], []), ([paper(1), paper(2)], [1, 0]),
                                   ([paper(1), paper(2)], [3, 0])):
            with self.subTest(values=values):
                request = agent_ranker.prepare_request(candidates, self.config, 10)
                selected, report = agent_ranker.apply_scores(request, self.scores(request, values))
                self.assertEqual(len(selected), sum(score >= 2 for score in values))
                self.assertEqual(report["selected_count"], len(selected))

    def test_stale_run_is_rejected_even_with_identical_candidates(self):
        request = agent_ranker.prepare_request([paper(1)], self.config, 10)
        next_run = agent_ranker.prepare_request([paper(1)], self.config, 10)
        with self.assertRaisesRegex(ValueError, "run_id"):
            agent_ranker.apply_scores(next_run, self.scores(request, [3]))

    def test_incomplete_duplicate_unknown_and_invalid_scores_are_rejected(self):
        request = agent_ranker.prepare_request([paper(1), paper(2)], self.config, 10)
        valid = self.scores(request, [3, 2])
        broken = [None, [], {**valid, "scores": None}, {**valid, "scores": []},
                  {**valid, "scores": valid["scores"][:1]},
                  {**valid, "scores": [valid["scores"][0], valid["scores"][0]]},
                  {**valid, "scores": [None, valid["scores"][1]]}]
        for field, value in (("id", -1), ("id", 2), ("id", True), ("score", True),
                             ("score", float("nan")), ("score", float("inf")), ("score", 5),
                             ("score", -1), ("score", "3"), ("reason", " "), ("reason", None)):
            invalid = copy.deepcopy(valid)
            invalid["scores"][0][field] = value
            broken.append(invalid)
        for response in broken:
            with self.subTest(response=response), self.assertRaises(ValueError):
                agent_ranker.apply_scores(request, response)

    def test_multiday_request_scales_pool_and_selection_limit(self):
        fetch = load_module("multiday_agent_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        output, report = self.root / "candidates.json", self.root / "report.json"
        with patch.object(sys, "argv", ["fetch", "--days", "3", "--output", str(output),
                                         "--usage-output", str(report)]), \
                patch.object(fetch, "fetch_hf_papers", return_value=[]), \
                patch.object(fetch, "fetch_arxiv_papers", return_value=[]), \
                patch.object(fetch, "merge_and_dedup", return_value=[]) as merge:
            fetch.main()
        self.assertEqual(merge.call_args.kwargs["top_n"], 90)
        request = json.loads(output.read_text())
        self.assertEqual(request["requested_top_n"], 30)
        self.assertEqual(request["days"], 3)

    def test_explicit_jev_without_key_fails_before_network_access(self):
        fetch = load_module("explicit_jev_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        with patch.object(sys, "argv", ["fetch", "--ranker", "jev"]), \
                patch.object(fetch, "fetch_hf_papers") as source, \
                self.assertRaises(SystemExit) as failure:
            fetch.main()
        self.assertNotEqual(failure.exception.code, 0)
        source.assert_not_called()

    def test_installed_finalizer_roundtrip_and_failed_retry_preserves_artifacts(self):
        bundle = self.root / "installed skills"
        installer.install([bundle])
        request = agent_ranker.prepare_request([paper(1), paper(2)], self.config, 1)
        candidates = self.write_json(self.root / "候选 request.json", request)
        scores = self.write_json(self.root / "agent scores.json", self.scores(request, [1, 4]))
        selected, report = self.root / "selected.json", self.root / "ranking.json"
        command = (bundle / "_shared/agent_ranker.py", candidates, scores,
                   "--output", selected, "--usage-output", report)
        result = self.run_python(*command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(selected.read_text())[0]["url"], paper(2)["url"])
        self.assertEqual(json.loads(report.read_text())["request"], request)
        previous = (selected.read_bytes(), report.read_bytes())
        self.write_json(scores, {"run_id": "old", "scores": []})
        failed = self.run_python(*command)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual((selected.read_bytes(), report.read_bytes()), previous)

    def test_finalizer_rejects_overwriting_its_input(self):
        request = agent_ranker.prepare_request([paper(1)], self.config, 1)
        candidates = self.write_json(self.root / "request.json", request)
        scores = self.write_json(self.root / "scores.json", self.scores(request, [3]))
        original = candidates.read_bytes()
        result = self.run_python(ROOT / "skills/_shared/agent_ranker.py", candidates, scores,
                                 "--output", candidates, "--usage-output", self.root / "report.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(candidates.read_bytes(), original)

    def test_upgrading_preserves_explicit_jev_personal_config(self):
        bundle = self.root / "installed skills"
        installer.install([bundle])
        config_path = bundle / "_shared/user-config.json"
        config = json.loads(config_path.read_text())
        config["daily_papers"]["ranking"]["backend"] = "jev"
        self.write_json(config_path, config)
        installer.install([bundle], update=True)
        config_result = self.run_python(bundle / "_shared/user_config.py")
        self.assertEqual(config_result.returncode, 0, config_result.stderr)
        self.assertEqual(json.loads(config_result.stdout)["daily_papers"]["ranking"]["backend"], "jev")
