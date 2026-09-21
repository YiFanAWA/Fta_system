import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from render_online_review_checklist import build_bundle, render_html  # noqa: E402


class OnlineReviewChecklistTests(unittest.TestCase):
    def test_pairs_latest_output_and_audits_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            old = {
                "records": [{"record_id": "old", "fault_code": "F-1"}],
                "evidence_spans": [],
                "status": "success",
            }
            newest = {
                "records": [{"record_id": "new", "fault_code": "F-1", "description": "故障"}],
                "evidence_spans": [
                    {"record_id": "new", "field": "fault_code", "quote": "F-1", "start": 0, "end": 3}
                ],
                "status": "success",
            }
            old_path = output_dir / "old_extracted_faults.json"
            newest_path = output_dir / "new_extracted_faults.json"
            old_path.write_text(json.dumps(old), encoding="utf-8")
            newest_path.write_text(json.dumps(newest), encoding="utf-8")
            os.utime(old_path, (100, 100))
            os.utime(newest_path, (200, 200))
            dataset = {
                "dataset_info": {"name": "test"},
                "samples": [
                    {
                        "sample_id": "S-1",
                        "input_text": "F-1 原文",
                        "gold_records": [{"fault_code": "F-1", "description": "候选"}],
                        "source": {},
                        "annotation": {},
                    }
                ],
            }
            report = {"summary": {}, "details": [{"sample_id": "S-1", "hallucinated_fields": 0}]}
            bundle = build_bundle(dataset, report, output_dir)
            sample = bundle["samples"][0]
            self.assertEqual("matched_latest_of_multiple", sample["pairing"]["status"])
            self.assertEqual("new_extracted_faults.json", sample["pairing"]["selected_file"])
            self.assertEqual(1, sample["evidence_audit"]["valid"])
            self.assertFalse(sample["evidence_audit"]["issues"])

    def test_unmatched_sample_is_explicit_and_html_is_reviewable(self):
        dataset = {
            "samples": [
                {
                    "sample_id": "S-2",
                    "input_text": "没有输出",
                    "gold_records": [{"fault_code": "F-2"}],
                    "source": {},
                    "annotation": {},
                }
            ]
        }
        bundle = build_bundle(dataset, {"summary": {}, "details": []}, Path(tempfile.mkdtemp()))
        self.assertEqual("unmatched", bundle["samples"][0]["pairing"]["status"])
        self.assertTrue(bundle["warnings"])
        html = render_html(bundle)
        self.assertIn("FTA 在线抽取结果审核清单", html)
        self.assertIn("未配对", html)
        self.assertIn("不是专家金标", html)

    def test_initial_decisions_are_embedded_without_overwriting_saved_state_contract(self):
        bundle = build_bundle(
            {"samples": []}, {"summary": {}, "details": []}, Path(tempfile.mkdtemp())
        )
        html = render_html(bundle, {"S-1": {"status": "审核通过（证据级）", "note": "证据明确"}})
        self.assertIn('审核通过（证据级）', html)
        self.assertIn('证据明确', html)
        self.assertIn('const savedState = JSON.parse', html)


if __name__ == "__main__":
    unittest.main()
