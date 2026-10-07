import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.fta_graph_contract import validate_fta_preview  # noqa: E402


class FtaGraphContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = json.loads(
            (
                ROOT
                / "evaluation"
                / "quality_eval"
                / "datasets"
                / "siemens_s210_fta_preview_v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_expert_bound_preview_is_valid(self):
        self.assertEqual([], validate_fta_preview(self.preview))

    def test_preview_cannot_be_marked_production_ready(self):
        payload = json.loads(json.dumps(self.preview))
        payload["dataset_info"]["production_ready"] = True
        errors = validate_fta_preview(payload)
        self.assertIn("dataset_info.production_ready must be false", errors)

    def test_preview_cannot_be_marked_fta_ready(self):
        payload = json.loads(json.dumps(self.preview))
        payload["dataset_info"]["fta_ready"] = True
        errors = validate_fta_preview(payload)
        self.assertIn("dataset_info.fta_ready must be false", errors)

    def test_preview_requires_evidence_for_each_child(self):
        payload = json.loads(json.dumps(self.preview))
        payload["trees"][0]["children"][0]["evidence"] = []
        errors = validate_fta_preview(payload)
        self.assertTrue(any("evidence must be non-empty" in error for error in errors))

    def test_unknown_event_is_not_in_preview(self):
        faults = {
            tree["top_event"]["fault_code"] for tree in self.preview["trees"]
        }
        self.assertNotIn("F01611", faults)
        self.assertEqual(1, len(self.preview["excluded_events"]))

    @staticmethod
    def _recursive_preview():
        def citation(citation_id, quote, start):
            return {
                "citation_id": citation_id,
                "source_id": "sample-1",
                "start": start,
                "end": start + len(quote),
                "quote": quote,
            }

        path_quote = "trigger one and trigger two"
        first = {
            "relation_id": "rel-root-path-1",
            "relation_type": "causes",
            "direction": "source_to_target",
            "evidence": [citation("cite-path-1", path_quote, 0)],
            "node": {
                "node_id": "path-1",
                "node_type": "trigger_path",
                "identity_status": "preview_local_derived_not_gold",
                "text": "documented trigger path one",
                "gate": "AND",
                "gate_provenance": {
                    "review_status": "ai_authorized_reviewed",
                    "evidence_support": "supported",
                },
                "gate_evidence": [citation("cite-and-1", path_quote, 0)],
                "children": [
                    {
                        "relation_id": "rel-path-1-a",
                        "relation_type": "causes",
                        "direction": "source_to_target",
                        "evidence": [citation("cite-leaf-1", "trigger one", 0)],
                        "node": {
                            "node_id": "condition-1",
                            "node_type": "trigger_condition",
                            "identity_status": "preview_local_derived_not_gold",
                            "text": "trigger one",
                        },
                    },
                    {
                        "relation_id": "rel-path-1-b",
                        "relation_type": "causes",
                        "direction": "source_to_target",
                        "evidence": [citation("cite-leaf-2", "trigger two", 16)],
                        "node": {
                            "node_id": "condition-2",
                            "node_type": "trigger_condition",
                            "identity_status": "preview_local_derived_not_gold",
                            "text": "trigger two",
                        },
                    },
                ],
            },
        }
        second = {
            "relation_id": "rel-root-path-2",
            "relation_type": "causes",
            "direction": "source_to_target",
            "evidence": [citation("cite-path-2", "alternate trigger", 40)],
            "node": {
                "node_id": "path-2",
                "node_type": "trigger_condition",
                "identity_status": "preview_local_derived_not_gold",
                "text": "alternate trigger",
            },
        }
        return {
            "artifact_type": "test_recursive_preview",
            "artifact_version": "v2",
            "dataset_info": {
                "status": "preview_only",
                "production_ready": False,
                "fta_ready": False,
                "automatic_causal_inference": False,
                "evidence_required": True,
                "tree_count": 1,
                "excluded_event_count": 0,
            },
            "trees": [
                {
                    "preview_tree_id": "preview-1",
                    "top_event": {"fault_code": "F00001", "description": "test event"},
                    "gate": "OR",
                    "gate_provenance": {
                        "review_status": "ai_authorized_reviewed",
                        "evidence_support": "supported",
                    },
                    "gate_evidence": [citation("cite-root", "either path", 70)],
                    "children": [first, second],
                    "status": "preview_only",
                }
            ],
            "excluded_events": [],
        }

    def test_recursive_evidence_bound_preview_v2_is_valid(self):
        self.assertEqual([], validate_fta_preview(self._recursive_preview()))

    def test_recursive_preview_requires_nested_gate_evidence(self):
        payload = self._recursive_preview()
        del payload["trees"][0]["children"][0]["node"]["gate_evidence"]
        errors = validate_fta_preview(payload)
        self.assertTrue(any("node.gate_evidence must be a non-empty list" in error for error in errors))

    def test_recursive_preview_rejects_invalid_span_and_duplicate_ids(self):
        payload = self._recursive_preview()
        first = payload["trees"][0]["children"][0]
        first["node"]["children"][0]["evidence"][0]["end"] = 0
        first["node"]["children"][1]["node"]["node_id"] = "condition-1"
        errors = validate_fta_preview(payload)
        self.assertTrue(any("end must be an integer greater than start" in error for error in errors))
        self.assertTrue(any("node.node_id must be unique within a tree" in error for error in errors))

    def test_recursive_contract_reports_malformed_types_without_raising(self):
        payload = self._recursive_preview()
        payload["trees"][0]["children"][0]["node"]["children"][0]["relation_type"] = {}
        payload["trees"][0]["children"][0]["node"]["gate"] = []
        errors = validate_fta_preview(payload)
        self.assertTrue(any("relation_type must be causes" in error for error in errors))
        self.assertTrue(any("node.gate must be AND or OR" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
