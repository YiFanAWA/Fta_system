from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "evaluation/quality_eval/runs/siemens_s120_s150_gate_node_ai_role_review_pilot_v1_2026-09-27.json"
CORPUS = ROOT / "evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.jsonl"
MANIFEST = ROOT / "evaluation/quality_eval/datasets/siemens_s120_s150_2023_public_fault_corpus_holdout_v2.manifest.json"
BUNDLE = ROOT / "evaluation/quality_eval/runs/siemens_s120_s150_gate_review_candidate_bundle_v2_2026-09-27.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_records() -> dict[str, dict]:
    return {
        row["sample_id"]: row
        for row in (
            json.loads(line)
            for line in CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


class TestS120S150AiRoleGateReviewPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.sources = _source_records()

    def test_review_is_provisional_and_not_a_calibration_or_production_claim(self) -> None:
        artifact = self.artifact
        self.assertFalse(artifact["reviewer_is_human_expert"])
        self.assertFalse(artifact["formal_gold"])
        self.assertFalse(artifact["database_written"])
        self.assertFalse(artifact["fta_ready"])
        self.assertFalse(artifact["production_ready"])
        self.assertFalse(artifact["model_inference_run"])
        self.assertFalse(artifact["threshold_selected"])
        self.assertFalse(artifact["probability_calibrated"])
        self.assertEqual(artifact["summary"]["independent_source_cluster_count"], 1)
        self.assertEqual(artifact["summary"]["gate_node_count"], 5)

    def test_source_hashes_match_the_exact_corpus_manifest_and_candidate_bundle(self) -> None:
        artifact = self.artifact
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(
            _sha256(CORPUS.read_bytes()),
            artifact["input_artifacts"]["source_corpus_sha256"],
        )
        self.assertEqual(
            manifest["source_pdf_sha256"], artifact["input_artifacts"]["source_pdf_sha256"]
        )
        self.assertEqual(
            _sha256(BUNDLE.read_bytes()), artifact["input_artifacts"]["candidate_bundle_sha256"]
        )

    def test_every_gate_node_id_and_evidence_span_recomputes_exactly(self) -> None:
        nodes = self.artifact["gate_nodes"]
        node_ids = {node["gate_node_id"] for node in nodes}
        self.assertEqual(len(node_ids), len(nodes))
        for node in nodes:
            source = self.sources[node["sample_id"]]
            text = source["input_text"]
            source_digest = _sha256(text.encode("utf-8"))
            self.assertEqual(node["source_sha256"], source_digest)
            self.assertEqual(source["provenance"]["record_text_sha256"], source_digest)
            anchor = node["scope_anchor"]
            self.assertEqual(text[anchor["start"] : anchor["end"]], anchor["quote"])
            identity = (
                f"{node['fault_code']}|{source_digest}|{node['scope_type']}|"
                f"{anchor['start']}|{anchor['end']}"
            )
            expected_id = f"gate:{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]}"
            self.assertEqual(node["gate_node_id"], expected_id)
            for evidence in [*node["gate_evidence"], *(
                span
                for child in node["children"]
                for span in child["evidence"]
            )]:
                self.assertEqual(text[evidence["start"] : evidence["end"]], evidence["quote"])
                self.assertEqual(text.count(evidence["quote"]), 1)
                self.assertLessEqual(anchor["start"], evidence["start"])
                self.assertLessEqual(evidence["end"], anchor["end"])

    def test_nested_or_link_is_preserved_instead_of_flattened(self) -> None:
        nodes = {node["gate_node_id"]: node for node in self.artifact["gate_nodes"]}
        roots = [node for node in nodes.values() if node["fault_code"] == "F06000" and not node.get("parent_gate_node_id")]
        self.assertEqual(len(roots), 1)
        root = roots[0]
        nested_id = next(
            child["child_gate_node_id"]
            for child in root["children"]
            if child.get("child_gate_node_id")
        )
        nested = nodes[nested_id]
        self.assertEqual(nested["parent_gate_node_id"], root["gate_node_id"])
        self.assertEqual(nested["gate_label"], "OR")
        self.assertEqual(len(root["children"]), 10)
        self.assertEqual(len(nested["children"]), 2)


if __name__ == "__main__":
    unittest.main()
