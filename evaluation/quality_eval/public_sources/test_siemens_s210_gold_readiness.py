import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from audit_siemens_s210_gold_readiness import audit_readiness  # noqa: E402


class SiemensS210GoldReadinessTests(unittest.TestCase):
    def test_component_canonicalization_and_semantic_policy_block_official_f1(self):
        gold = {
            "dataset_info": {
                "name": "demo",
                "version": "v1",
                "stats": {"split": {"test": 1}},
                "review": {"field_values_confirmed": True, "evidence_confirmed": True},
            },
            "gold_status": {
                "f1_ready": False,
                "independent_expert_reviewed": True,
                "reviewer_identity_verified": True,
            },
            "samples": [{"gold_records": [{"fault_code": "F01000", "component": "功率单元（Power unit）", "causes": ["Possible causes: overcurrent"]}]}],
        }
        report = audit_readiness(gold)
        self.assertEqual("not_ready_for_official_f1", report["readiness"])
        blocker_ids = {item["id"] for item in report["blockers"]}
        self.assertIn("component_canonicalization", blocker_ids)
        self.assertIn("semantic_match_policy", blocker_ids)
        self.assertEqual("blocked_until_canonicalized", report["field_assessment"]["component"]["status"])

    def test_explicit_relation_projection_is_ready_for_policy_diagnostic(self):
        gold = {
            "dataset_info": {"name": "demo", "version": "v2", "stats": {"split": {"test": 1}}},
            "gold_status": {"f1_ready": False},
            "samples": [{"gold_records": [{"fault_code": "F01357", "related_components": ["Control Unit"]}]}],
            "related_component_policy_projection": {
                "policy": "explicit_relation_only",
                "source_version": "v1",
                "preserves_original_values": True,
                "changed_record_count": 0,
                "changes": [],
            },
        }
        report = audit_readiness(gold)
        self.assertEqual("ready_for_policy_diagnostic_f1", report["field_assessment"]["related_components"]["status"])
        self.assertEqual("explicit_relation_only", report["related_component_policy_projection"]["policy"])


if __name__ == "__main__":
    unittest.main()
