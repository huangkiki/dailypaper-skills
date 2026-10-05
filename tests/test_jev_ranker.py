"""Contract tests for ranking, usage accounting and the actual fetch entry point."""

import copy
import json
import os
import sys
import unittest
from unittest.mock import patch

from test_portability import IsolatedWorkspace, ROOT, load_module
import jev_ranker as ranker
import user_config


def paper(index, score=3):
    return {"url": f"https://arxiv.org/abs/2601.{index:05}",
            "title": f"Paper {index}", "abstract": "A study of dexterous manipulation.",
            "score": score}


def response_for(payload, scores=None):
    scores = scores or [3] * len(payload["questions"])
    return {
        "model": payload["model"],
        "answers": {key: {
            "type": "score", "score": score, "confidence": 1.0,
            "probabilities": {str(level): float(level == score) for level in range(5)},
        } for key, score in zip(payload["questions"], scores)},
        "usage": {"input_tokens": 123, "output_tokens": 7},
    }


class JevRankingTests(IsolatedWorkspace):
    def setUp(self):
        super().setUp()
        self.config = copy.deepcopy(user_config.DEFAULT_CONFIG["daily_papers"])
        self.config["ranking"]["batch_size"] = 2
        os.environ["TYPESAFE_API_KEY"] = "test-secret-not-a-real-key"

    def test_rank_threshold_ties_batches_and_usage(self):
        papers = [paper(4, 2), paper(3, 4), paper(2, 4), paper(1, 9)]
        untouched = copy.deepcopy(papers)
        calls = []

        def respond(payload, key):
            calls.append(payload)
            return response_for(payload, [3, 3] if len(calls) == 1 else [3, 1])

        with patch.object(ranker, "request_scores", side_effect=respond):
            selected, report = ranker.rank_papers(papers, self.config, 10)
        self.assertEqual([p["url"] for p in selected], [papers[i]["url"] for i in (2, 1, 0)])
        self.assertEqual(selected[0]["score"], 75)
        self.assertEqual(papers, untouched)
        self.assertEqual(report["usage"], {"input_tokens": 246, "output_tokens": 14})
        self.assertTrue(report["usage_complete"])
        self.assertEqual(calls[0]["questions"]["paper_1"]["instructions"]["paper"]["title"], "Paper 3")
        self.assertNotIn("papers", calls[0]["state"])
        self.assertNotIn(os.environ["TYPESAFE_API_KEY"], json.dumps(report))

    def test_partial_failure_preserves_billed_usage_and_never_returns_shortlist(self):
        def respond(payload, key):
            if payload["questions"]["paper_0"]["instructions"]["paper"]["title"] == "Paper 2":
                raise RuntimeError("TypeSafe returned HTTP 429")
            return response_for(payload)

        with patch.object(ranker, "request_scores", side_effect=respond), \
                self.assertRaises(ranker.RankingError) as failure:
            ranker.rank_papers([paper(i) for i in range(4)], self.config, 10)
        report = failure.exception.report
        self.assertEqual(report["usage"]["input_tokens"], 123)
        self.assertFalse(report["usage_complete"])
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(len(report["calls"]), 2)
        self.assertNotIn("selected_urls", report)

    def test_invalid_answers_still_record_reported_usage(self):
        def respond(payload, key):
            response = response_for(payload)
            response["answers"] = {}
            return response

        with patch.object(ranker, "request_scores", side_effect=respond), \
                self.assertRaises(ranker.RankingError) as failure:
            ranker.rank_papers([paper(1)], self.config, 10)
        self.assertEqual(failure.exception.report["usage"]["input_tokens"], 123)

    def test_malformed_responses_are_rejected(self):
        payload = ranker.build_request([paper(1)], self.config["research_interests"], ranker.DEFAULT_MODEL)
        valid = response_for(payload)
        broken = [None, {**valid, "model": "jev-other"}, {**valid, "answers": {}},
                  {**valid, "usage": {}}, {**valid, "usage": {"input_tokens": True, "output_tokens": 0}}]
        for field, value in [("score", float("nan")), ("score", 5), ("confidence", -1),
                             ("probabilities", {"0": 1}), ("probabilities", {str(i): 1 for i in range(5)})]:
            response = copy.deepcopy(valid)
            response["answers"]["paper_0"][field] = value
            broken.append(response)
        for response in broken:
            with self.subTest(response=response), self.assertRaises(ValueError):
                ranker.validate_response(payload, response)

    def test_missing_key_fails_without_api_or_implicit_keyword_fallback(self):
        os.environ.pop("TYPESAFE_API_KEY")
        with patch.object(ranker, "request_scores") as call, self.assertRaises(ranker.RankingError):
            ranker.rank_papers([paper(1)], self.config, 10)
        call.assert_not_called()

    def test_empty_candidates_do_not_call_api(self):
        with patch.object(ranker, "request_scores") as call:
            selected, report = ranker.rank_papers([], self.config, 10)
        call.assert_not_called()
        self.assertEqual(selected, [])
        self.assertTrue(report["usage_complete"])

    def test_fetch_default_actually_uses_jev_and_caps_at_ten(self):
        fetch = load_module("jev_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        output, usage = self.root / "selected.json", self.root / "usage.json"
        candidates = [paper(i) for i in range(30)]
        with patch.object(sys, "argv", ["fetch", "--output", str(output), "--usage-output", str(usage)]), \
                patch.object(fetch, "fetch_hf_papers", return_value=[]), \
                patch.object(fetch, "fetch_arxiv_papers", return_value=[]), \
                patch.object(fetch, "merge_and_dedup", return_value=candidates), \
                patch.object(ranker, "request_scores", side_effect=lambda payload, key: response_for(payload)):
            fetch.main()
        self.assertEqual(len(json.loads(output.read_text())), 10)
        self.assertEqual(json.loads(usage.read_text())["candidate_count"], 30)

    def test_new_topics_survive_recall_without_substring_false_positives(self):
        fetch = load_module("topic_fetch", ROOT / "skills/daily-papers/fetch_and_score.py")
        for topic in ("RLHF", "GRPO", "RL infra", "V-JEPA", "SuperDex", "mjlab", "unlib", "mjbatch"):
            with self.subTest(topic=topic):
                self.assertGreaterEqual(fetch.score_paper({"title": topic, "abstract": ""}), fetch.MIN_SCORE)
        self.assertFalse(fetch.keyword_matches("areal", "arealistic model"))
        self.assertFalse(fetch.keyword_matches("verl", "overlap"))


if __name__ == "__main__":
    unittest.main()
