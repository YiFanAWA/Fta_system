from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

from pypdf import PdfReader


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATASET = ROOT / "evaluation" / "quality_eval" / "datasets" / "fta_gate_diagram_development_v1.json"
sys.path.insert(0, str(HERE))
from fta_gate_external_probe_core import build_prompt  # noqa: E402


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _load_fixture() -> dict:
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    if payload.get("artifact_type") != "external_diagram_gate_classification_fixture":
        raise ValueError("unexpected dataset artifact type")
    return payload


class FtaGateDiagramDevelopmentFixtureTests(unittest.TestCase):
    def test_fixture_is_development_only_and_cluster_complete(self) -> None:
        fixture = _load_fixture()
        self.assertEqual("development_only", fixture["dataset_role"])
        self.assertFalse(fixture["formal_gold"])
        self.assertFalse(fixture["in_project_gold"])
        self.assertEqual("not_created", fixture["partition_policy"]["independent_final_validation_status"])
        self.assertFalse(fixture["partition_policy"]["source_cluster_splitting_allowed"])

        sources = fixture["sources"]
        rows = fixture["gate_nodes"]
        self.assertEqual(3, fixture["source_document_count"])
        self.assertEqual(3, fixture["source_cluster_count"])
        self.assertEqual(11, len(rows))
        self.assertEqual({"AND": 5, "OR": 6}, {
            gate: sum(row["expected_gate"] == gate for row in rows)
            for gate in ("AND", "OR")
        })
        self.assertEqual(
            {source["source_cluster_id"] for source in sources},
            {row["source_cluster_id"] for row in rows},
        )
        self.assertEqual(len(rows), len({row["gate_node_id"] for row in rows}))

    def test_new_development_sources_do_not_overlap_seen_regression_clusters(self) -> None:
        fixture = _load_fixture()
        manifest = json.loads((ROOT / "evaluation" / "quality_eval" / "fta_baseline_manifest_v15.json").read_text(encoding="utf-8"))
        seen_clusters = {row["source_cluster_id"] for row in manifest["seen_case_regression_suite"]["source_clusters"]}
        development_clusters = {row["source_cluster_id"] for row in fixture["sources"]}
        self.assertTrue(development_clusters.isdisjoint(seen_clusters))

    def test_source_hashes_and_evidence_quotes_match_pinned_pdfs(self) -> None:
        fixture = _load_fixture()
        source_map = {source["source_id"]: source for source in fixture["sources"]}
        pdf_readers: dict[str, PdfReader] = {}
        for source in fixture["sources"]:
            path = (ROOT / source["source_pdf_path"]).resolve(strict=True)
            self.assertTrue(path.is_relative_to(ROOT.resolve()))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(source["source_pdf_sha256"], digest, source["source_id"])
            pdf_readers[source["source_id"]] = PdfReader(str(path))

        for row in fixture["gate_nodes"]:
            source = source_map[row["source_id"]]
            self.assertEqual(source["source_cluster_id"], row["source_cluster_id"])
            evidence = row["label_evidence"]
            quote_page = evidence.get("supporting_text_pdf_page") or evidence.get("symbol_table_pdf_page") or evidence["figure_pdf_page"]
            source_text = pdf_readers[row["source_id"]].pages[quote_page - 1].extract_text() or ""
            self.assertIn(_normalize_text(evidence["quote"]), _normalize_text(source_text), row["gate_node_id"])

    def test_inference_prompt_contains_only_parent_and_direct_children(self) -> None:
        fixture = _load_fixture()
        for row in fixture["gate_nodes"]:
            prompt = build_prompt(row)
            payload = json.loads(prompt[prompt.rfind("{") : prompt.rfind("}") + 1])
            self.assertEqual({"parent_event", "direct_child_events"}, set(payload))
            self.assertNotIn(row["gate_node_id"], prompt)
            self.assertNotIn(row["source_id"], prompt)
            self.assertNotIn(row["figure_id"], prompt)
            self.assertNotIn(row["label_evidence"]["quote"], prompt)
            self.assertGreaterEqual(len(payload["direct_child_events"]), 2)


if __name__ == "__main__":
    unittest.main()
