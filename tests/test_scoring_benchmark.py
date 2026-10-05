import copy
import json
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_portability import ROOT, load_module
from test_jev_ranker import paper, response_for
import jev_ranker
import user_config

benchmark = load_module("scoring_benchmark", ROOT / "scripts/benchmark_scoring.py")


class BenchmarkTests(unittest.TestCase):
    def test_stream_reads_final_usage_and_rejects_incomplete_output(self):
        content = '{"scores":[{"id":0,"score":4}]}'
        events = [
            {"model": "test-model", "choices": [{"index": 0, "delta": {"content": content}}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}},
        ]
        raw = ''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode()
        response = benchmark.read_chat_stream(io.BytesIO(raw+b'data: [DONE]\n\n'))
        selected, usage = benchmark.read_llm_response(response, [paper(1)], user_config.DEFAULT_CONFIG['daily_papers'])
        self.assertEqual(selected, [paper(1)['url']])
        self.assertEqual(usage['total_tokens'], 120)
        partial = benchmark.read_chat_stream(io.BytesIO(raw))
        self.assertEqual(partial['usage']['total_tokens'], 120)
        with self.assertRaisesRegex(ValueError, 'without DONE'):
            benchmark.read_llm_response(partial, [paper(1)], user_config.DEFAULT_CONFIG['daily_papers'])

    def test_reuse_checks_inputs_and_usage_against_raw_calls(self):
        config = user_config.DEFAULT_CONFIG["daily_papers"]
        papers = [paper(1), paper(2)]
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "fake-test-key"}), \
                patch.object(jev_ranker, "request_scores", side_effect=lambda payload, key: response_for(payload)):
            _, report = jev_ranker.rank_papers(papers, config, 10)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            benchmark.reuse_jev_report(path, papers, config)
            changed_papers = [{**papers[0], "abstract": "Different experiment"}, papers[1]]
            with self.assertRaisesRegex(ValueError, "differs"):
                benchmark.reuse_jev_report(path, changed_papers, config)
            report["usage"]["input_tokens"] = 1
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "summary differs"):
                benchmark.reuse_jev_report(path, papers, config)

    def test_response_requires_complete_ids_and_real_usage(self):
        config = user_config.DEFAULT_CONFIG["daily_papers"]
        papers = [paper(1), paper(2)]
        response = {"usage": {"prompt_tokens": 90, "completion_tokens": 10, "total_tokens": 100},
                    "choices": [{"finish_reason": "stop", "message": {
                        "content": '{"scores":[{"id":0,"score":1},{"id":1,"score":4}]}'}}]}
        selected, usage = benchmark.read_llm_response(response, papers, config)
        self.assertEqual(selected, [papers[1]["url"]])
        self.assertEqual(usage["total_tokens"], 100)
        bad = copy.deepcopy(response)
        bad["choices"][0]["message"]["content"] = '{"scores":[{"id":0,"score":4},{"id":0,"score":4}]}'
        with self.assertRaises(ValueError):
            benchmark.read_llm_response(bad, papers, config)
        for change in ({"usage": {}}, {"choices": [{"finish_reason": "length"}]}):
            with self.assertRaises(ValueError):
                benchmark.read_llm_response({**response, **change}, papers, config)

    def test_negative_savings_are_reported_as_negative(self):
        baseline = {"usage": {"total_tokens": 100}, "selected_urls": ["a", "b"]}
        jev = {"usage": {"input_tokens": 150, "output_tokens": 10}, "selected_urls": ["b", "c"]}
        result = benchmark.comparison(baseline, jev)
        self.assertEqual(result["cross_tokenizer_count_delta"], -60)
        self.assertEqual(result["cross_tokenizer_count_reduction_percent"], -60)
        self.assertEqual(result["selected_overlap"], 1)
        self.assertTrue(result["equal_selection_count"])


if __name__ == "__main__":
    unittest.main()
