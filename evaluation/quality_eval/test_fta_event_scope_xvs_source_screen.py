from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "evaluation" / "quality_eval" / "runs" / "fta_event_scope_xvs_source_screen_v1_2026-09-29.json"


class TestXvsSourceScreen(unittest.TestCase):
    def test_report_keeps_seen_source_out_of_final_and_gold(self) -> None:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual("fta_event_scope_source_screen_v1", payload["audit_schema"])
        self.assertEqual("seen_development_only_not_final", payload["evaluation_suitability"]["status"])
        self.assertFalse(payload["evaluation_suitability"]["eligible_for_independent_final"])
        self.assertFalse(payload["evaluation_suitability"]["input_packet_created"])
        self.assertFalse(payload["evaluation_suitability"]["reference_gold_created"])
        self.assertFalse(payload["evaluation_suitability"]["model_inference_run"])
        self.assertFalse(payload["readiness"]["fta_ready"])
        self.assertFalse(payload["readiness"]["production_ready"])

    def test_report_pins_document_and_all_eight_figure_scopes(self) -> None:
        payload = json.loads(REPORT.read_text(encoding="utf-8"))
        source = payload["source_document"]
        self.assertRegex(source["downloaded_pdf_sha256"], re.compile(r"^[0-9a-f]{64}$"))
        self.assertEqual(40, source["page_count"])
        self.assertEqual(list(range(29, 37)), payload["content_screen"]["fault_tree_appendix"]["tree_pdf_pages"])
        self.assertEqual([f"D-{index}" for index in range(1, 9)], payload["content_screen"]["fault_tree_appendix"]["figure_ids"])
        self.assertFalse(payload["document_family_and_overlap"]["semantic_overlap_audit_complete"])
        self.assertFalse(payload["rights_review"]["redistribution_authorized_by_this_audit"])


if __name__ == "__main__":
    unittest.main()
