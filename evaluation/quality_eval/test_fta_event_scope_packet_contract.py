from __future__ import annotations

import copy
import hashlib
import json
import unittest

from evaluation.quality_eval.fta_event_scope_packet_contract import (
    ScopePacketValidationError,
    model_input_payload,
    validate_input_packet,
    validate_reference_gold,
)


def valid_packet() -> dict:
    return {
        "packet_schema": "fta_event_scope_input_packet_v1",
        "packet_id": "case-001",
        "source_provenance": {
            "document_id": "synthetic-doc",
            "source_cluster_id": "synthetic-cluster",
            "official_record_url": "https://example.org/report",
            "document_sha256": "a" * 64,
            "page_count": 3,
            "rights_status": "public_use_permitted",
            "exposure_status": "unseen_candidate",
        },
        "model_input": {
            "event_scope_id": "scope-opaque-001",
            "top_event": {
                "text": "Engine shutdown",
                "evidence": {"segment_id": "p1-s1", "quote": "Engine shutdown"},
            },
            "source_segments": [
                {
                    "segment_id": "p1-s1",
                    "page_number": 1,
                    "section_locator": "§ 2.1",
                    "text": "Engine shutdown occurs when both Valve A and Valve B are closed.",
                }
            ],
        },
    }


def valid_gold() -> dict:
    model_input = valid_packet()["model_input"]
    canonical = json.dumps(model_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "gold_schema": "fta_event_scope_reference_gold_v1",
        "packet_id": "case-001",
        "model_input_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "source_cluster_id": "synthetic-cluster",
        "source_document_id": "synthetic-doc",
        "source_document_sha256": "a" * 64,
        "root_node_id": "event-root",
        "nodes": [
            {"node_id": "event-root", "text": "Engine shutdown", "node_type": "top_event", "page_number": 2, "figure_id": "Fig. 1"},
            {"node_id": "cause-a", "text": "Valve A closed", "node_type": "basic_event", "page_number": 2, "figure_id": "Fig. 1"},
            {"node_id": "cause-b", "text": "Valve B closed", "node_type": "basic_event", "page_number": 2, "figure_id": "Fig. 1"},
        ],
        "diagram_gates": [
            {
                "scope_id": "gate-root",
                "output_node_id": "event-root",
                "child_node_ids": ["cause-a", "cause-b"],
                "diagram_reference_gate": "AND",
                "page_number": 2,
                "figure_id": "Fig. 1",
            }
        ],
        "text_gate_reviews": [
            {
                "scope_id": "gate-root",
                "text_authorized_gate": "AND",
                "unknown_reason": None,
                "evidence": {"segment_id": "p1-s1", "quote": "both Valve A and Valve B are closed"},
                "review_provenance": {
                    "reviewer_role": "ai_role_review",
                    "reviewer_id": "review-agent-1",
                    "review_status": "reviewed",
                    "reviewed_at": "2026-09-29",
                },
            }
        ],
    }


class TestFtaEventScopePacketContract(unittest.TestCase):
    def test_model_payload_projects_only_validated_model_input(self) -> None:
        packet = valid_packet()
        payload = model_input_payload(packet)
        self.assertEqual({"event_scope_id", "top_event", "source_segments"}, set(payload))
        self.assertNotIn("source_provenance", payload)
        self.assertNotIn("diagram_reference_gate", str(payload))
        self.assertEqual(packet["model_input"], payload)

    def test_input_rejects_gate_labels_and_extra_fields(self) -> None:
        packet = valid_packet()
        packet["model_input"]["diagram_reference_gate"] = "AND"
        with self.assertRaisesRegex(ScopePacketValidationError, "keys mismatch"):
            validate_input_packet(packet)

    def test_input_rejects_non_unique_top_event_quote(self) -> None:
        packet = valid_packet()
        packet["model_input"]["source_segments"][0]["text"] += " Engine shutdown."
        with self.assertRaisesRegex(ScopePacketValidationError, "exactly once"):
            validate_input_packet(packet)

    def test_input_rejects_source_page_out_of_range(self) -> None:
        packet = valid_packet()
        packet["model_input"]["source_segments"][0]["page_number"] = 4
        with self.assertRaisesRegex(ScopePacketValidationError, "outside source"):
            validate_input_packet(packet)

    def test_reference_gold_keeps_diagram_gate_and_text_authorization_distinct(self) -> None:
        self.assertEqual(valid_gold(), validate_reference_gold(valid_packet(), valid_gold()))

    def test_unknown_text_gate_requires_reason_and_cannot_carry_decisive_quote(self) -> None:
        gold = valid_gold()
        review = gold["text_gate_reviews"][0]
        review["text_authorized_gate"] = "unknown"
        review["unknown_reason"] = "no_direct_logic_evidence"
        review["evidence"] = None
        validate_reference_gold(valid_packet(), gold)

        invalid = copy.deepcopy(gold)
        invalid["text_gate_reviews"][0]["evidence"] = {"segment_id": "p1-s1", "quote": "both Valve A and Valve B are closed"}
        with self.assertRaisesRegex(ScopePacketValidationError, "unknown gate requires"):
            validate_reference_gold(valid_packet(), invalid)

    def test_known_text_gate_requires_unique_direct_quote_in_model_input(self) -> None:
        gold = valid_gold()
        gold["text_gate_reviews"][0]["evidence"]["quote"] = "not present"
        with self.assertRaisesRegex(ScopePacketValidationError, "must be unique"):
            validate_reference_gold(valid_packet(), gold)

    def test_gold_must_match_packet_source_cluster(self) -> None:
        gold = valid_gold()
        gold["source_cluster_id"] = "other-source"
        with self.assertRaisesRegex(ScopePacketValidationError, "source_cluster_id does not match"):
            validate_reference_gold(valid_packet(), gold)

    def test_gold_must_match_exact_document_identity_and_hash(self) -> None:
        gold = valid_gold()
        gold["source_document_sha256"] = "b" * 64
        with self.assertRaisesRegex(ScopePacketValidationError, "identity/hash"):
            validate_reference_gold(valid_packet(), gold)

    def test_gold_must_pin_exact_model_visible_packet_bytes(self) -> None:
        packet = valid_packet()
        packet["model_input"]["source_segments"][0]["text"] += " Additional context."
        with self.assertRaisesRegex(ScopePacketValidationError, "exact model-visible packet"):
            validate_reference_gold(packet, valid_gold())

    def test_gold_graph_rejects_disconnected_node(self) -> None:
        gold = valid_gold()
        gold["nodes"].append({"node_id": "orphan", "text": "Orphan", "node_type": "basic_event", "page_number": 2, "figure_id": "Fig. 1"})
        with self.assertRaisesRegex(ScopePacketValidationError, "disconnected"):
            validate_reference_gold(valid_packet(), gold)

    def test_review_provenance_rejects_untyped_reviewer_identity(self) -> None:
        gold = valid_gold()
        gold["text_gate_reviews"][0]["review_provenance"]["reviewer_id"] = []
        with self.assertRaisesRegex(ScopePacketValidationError, "reviewer_id must be"):
            validate_reference_gold(valid_packet(), gold)


if __name__ == "__main__":
    unittest.main()
