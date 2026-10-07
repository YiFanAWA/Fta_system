from __future__ import annotations

import json
import sys
import unittest
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from contracts.candidate_fta_contract import CandidateFtaStatus
from contracts.evidence_locator_review_contract import (
    EvidenceLocatorSpan,
    EvidenceLocatorTargetField,
    EvidenceOccurrenceLocatorReview,
)
from contracts.extraction_contract import (
    EvidenceField,
    EvidenceSpan,
    ExtractionResult,
    ExtractionStatus,
    FaultRecord,
)
from fta.candidate_fta_extraction_service import CandidateFtaExtractionService
from fta.cause_disposition_service import CauseDispositionService
from fta.evidence_locator_review_service import (
    EvidenceLocatorReviewResolver,
    EvidenceLocatorReviewValidationError,
)


class StaticClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self.responses)


class EvidenceLocatorReviewTests(unittest.TestCase):
    SOURCE = (
        "F30021 Drive: ground fault\n"
        "Possible causes:\n"
        "- short-circuit at the braking resistor.\n"
        "Fault value (r0949):\n"
        "0:\n"
        "- short-circuit at the braking resistor."
    )
    DESCRIPTION = "ground fault"
    CAUSE = "short-circuit at the braking resistor"

    def setUp(self) -> None:
        self.record = FaultRecord(
            fault_code="F30021",
            description=self.DESCRIPTION,
            causes=(self.CAUSE,),
        )
        description_start = self.SOURCE.index(self.DESCRIPTION)
        cause_starts = [
            index
            for index in range(len(self.SOURCE))
            if self.SOURCE.startswith(self.CAUSE, index)
        ]
        self.extraction = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            records=(self.record,),
            evidence_spans=(
                EvidenceSpan(
                    record_id=self.record.record_id,
                    field=EvidenceField.DESCRIPTION,
                    source_id="input_text",
                    quote=self.DESCRIPTION,
                    start=description_start,
                    end=description_start + len(self.DESCRIPTION),
                ),
                *(
                    EvidenceSpan(
                        record_id=self.record.record_id,
                        field=EvidenceField.CAUSE,
                        source_id="input_text",
                        quote=self.CAUSE,
                        start=start,
                        end=start + len(self.CAUSE),
                        value_index=0,
                    )
                    for start in cause_starts
                ),
            ),
        )
        self.cause_review = self._review(
            "cause-review",
            EvidenceLocatorTargetField.CAUSE,
            0,
            self._line_span(self.CAUSE, first=True),
            self._scope_span("Possible causes:", "Fault value"),
        )
        self.description_review = self._review(
            "description-review",
            EvidenceLocatorTargetField.DESCRIPTION,
            None,
            self._exact_span(self.DESCRIPTION, first=True),
            self._line_span("F30021 Drive: ground fault", first=True),
        )

    def test_locator_contract_preserves_provenance_without_promoting_gold(self) -> None:
        payload = self.cause_review.to_payload()

        self.assertEqual("locator_confirmed", payload["review_status"])
        self.assertFalse(payload["reviewer_is_human_expert"])
        self.assertFalse(payload["formal_gold"])
        self.assertEqual("user_authorized_ai_locator_review", payload["reviewer_provenance"])

    def test_resolver_selects_only_the_reviewed_occurrence_inside_scope(self) -> None:
        resolver = EvidenceLocatorReviewResolver(
            self.extraction,
            self.record.record_id,
            self.SOURCE,
            (self.cause_review,),
        )

        selected = resolver.selected_span(EvidenceLocatorTargetField.CAUSE, 0)
        self.assertIsNotNone(selected)
        self.assertEqual(self.cause_review.selected_occurrence.start + 2, selected.start)
        self.assertEqual(self.CAUSE, selected.quote)
        self.assertEqual(
            (selected.start, selected.end),
            resolver.bind_model_quote(
                self.CAUSE, EvidenceLocatorTargetField.CAUSE, 0
            ),
        )

    def test_duplicate_quote_inside_review_scope_is_rejected(self) -> None:
        ambiguous_scope = EvidenceLocatorSpan(
            self.SOURCE[
                self.SOURCE.index("Possible causes:") :
                len(self.SOURCE)
            ],
            self.SOURCE.index("Possible causes:"),
            len(self.SOURCE),
        )
        ambiguous_review = self._review(
            "ambiguous-cause-review",
            EvidenceLocatorTargetField.CAUSE,
            0,
            self._exact_span(self.CAUSE, first=True),
            ambiguous_scope,
        )

        with self.assertRaisesRegex(
            EvidenceLocatorReviewValidationError,
            "unique occurrence within its scope",
        ):
            EvidenceLocatorReviewResolver(
                self.extraction,
                self.record.record_id,
                self.SOURCE,
                (ambiguous_review,),
            )

    def test_stale_source_offsets_and_duplicate_review_targets_fail_closed(self) -> None:
        stale = EvidenceOccurrenceLocatorReview(
            **{
                **self.cause_review.__dict__,
                "source_text_sha256": "0" * 64,
            }
        )
        with self.assertRaises(EvidenceLocatorReviewValidationError):
            EvidenceLocatorReviewResolver(
                self.extraction, self.record.record_id, self.SOURCE, (stale,)
            )

        bad_offset = EvidenceOccurrenceLocatorReview(
            **{
                **self.cause_review.__dict__,
                "selected_occurrence": EvidenceLocatorSpan(
                    quote="X" * len(self.cause_review.selected_occurrence.quote),
                    start=self.cause_review.selected_occurrence.start,
                    end=self.cause_review.selected_occurrence.end,
                ),
            }
        )
        with self.assertRaises(EvidenceLocatorReviewValidationError):
            EvidenceLocatorReviewResolver(
                self.extraction, self.record.record_id, self.SOURCE, (bad_offset,)
            )

        duplicate = EvidenceOccurrenceLocatorReview(
            **{**self.cause_review.__dict__, "review_id": "cause-review-2"}
        )
        with self.assertRaisesRegex(
            EvidenceLocatorReviewValidationError, "multiple locator reviews"
        ):
            EvidenceLocatorReviewResolver(
                self.extraction,
                self.record.record_id,
                self.SOURCE,
                (self.cause_review, duplicate),
            )

    def test_cause_disposition_needs_explicit_locator_and_exact_model_quote(self) -> None:
        response = self._cause_response(self.CAUSE)
        without_review = CauseDispositionService(StaticClient([response])).propose(
            self.extraction, self.record.record_id, self.SOURCE
        )
        self.assertEqual("unresolved", without_review.dispositions[0].disposition.value)
        self.assertEqual("evidence_missing_or_ambiguous", without_review.dispositions[0].reason_code.value)

        client = StaticClient([response])
        with_review = CauseDispositionService(client).propose(
            self.extraction,
            self.record.record_id,
            self.SOURCE,
            (self.cause_review,),
        )
        item = with_review.dispositions[0]
        self.assertEqual("fta_event_candidate", item.disposition.value)
        self.assertEqual(self.cause_review.selected_occurrence.start + 2, item.evidence[0].start)
        self.assertEqual((self.cause_review,), with_review.locator_reviews)
        self.assertEqual(
            "user_authorized_ai_locator_review",
            with_review.to_payload()["locator_reviews"][0]["reviewer_provenance"],
        )
        self.assertIn("reviewed_locator_decisions", client.prompts[0])
        self.assertIn("selected_extraction_evidence", client.prompts[0])

        bad_quote = self._cause_response(
            "- short-circuit at the braking resistor.\nFault value"
        )
        rejected = CauseDispositionService(StaticClient([bad_quote])).propose(
            self.extraction,
            self.record.record_id,
            self.SOURCE,
            (self.cause_review,),
        )
        self.assertEqual("unresolved", rejected.dispositions[0].disposition.value)
        self.assertEqual("evidence_missing_or_ambiguous", rejected.dispositions[0].reason_code.value)

    def test_candidate_preview_uses_locator_for_top_event_and_cause_but_not_gate(self) -> None:
        responses = [
            self._cause_response(self.CAUSE),
            json.dumps(
                {
                    "structure_status": "complete",
                    "nodes": [
                        {
                            "node_id": "braking-resistor-short-circuit",
                            "node_type": "cause_candidate",
                            "text": self.CAUSE,
                            "source_cause_indices": [0],
                            "evidence_quote": self.CAUSE,
                        }
                    ],
                    "gate_scopes": [
                        {
                            "gate_id": "single-child-scope",
                            "output_node_id": "__top_event__",
                            "child_node_ids": ["braking-resistor-short-circuit"],
                            "scope_type": "single_complete_cause",
                            "scope_quote": self.SOURCE,
                            "cause_set_complete": True,
                            "cause_set_leaf_normalized": True,
                            "reason": "One reviewed child is present in this synthetic contract fixture.",
                        }
                    ],
                    "unresolved_cause_indices": [],
                    "reason": "Offline contract fixture only.",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "gate_assessments": [
                        {
                            "gate_id": "single-child-scope",
                            "gate_evidence_quote": "",
                            "reason": "A single complete child has no Boolean gate.",
                        }
                    ],
                    "relations": [],
                    "reason": "No gate or relation claim in this fixture.",
                },
                ensure_ascii=False,
            ),
        ]
        client = StaticClient(responses)
        tree = CandidateFtaExtractionService(client).propose(
            self.extraction,
            self.record.record_id,
            self.SOURCE,
            (self.cause_review, self.description_review),
        )

        self.assertNotIn("top_event_evidence_ambiguous", tree.blockers)
        self.assertNotIn("cause_disposition_unresolved:0", tree.blockers)
        cause_node = next(node for node in tree.nodes if node.source_cause_indices == (0,))
        self.assertEqual(self.cause_review.selected_occurrence.start + 2, cause_node.evidence[0].start)
        self.assertEqual(self.description_review.selected_occurrence.start, tree.nodes[0].evidence[0].start)
        self.assertEqual((self.cause_review, self.description_review), tree.locator_reviews)
        locator_payloads = tree.to_payload()["locator_reviews"]
        self.assertEqual(2, len(locator_payloads))
        self.assertFalse(any(item["formal_gold"] for item in locator_payloads))
        self.assertFalse(any(item["reviewer_is_human_expert"] for item in locator_payloads))
        self.assertEqual("v7", tree.to_payload()["artifact_version"])
        self.assertIn("reviewed_locator_decisions", client.prompts[1])
        self.assertFalse(tree.fta_ready)

    def _review(
        self,
        review_id: str,
        field: EvidenceLocatorTargetField,
        value_index: int | None,
        selected: EvidenceLocatorSpan,
        scope: EvidenceLocatorSpan,
    ) -> EvidenceOccurrenceLocatorReview:
        return EvidenceOccurrenceLocatorReview(
            review_id=review_id,
            extraction_result_id=self.extraction.result_id,
            record_id=self.record.record_id,
            source_text_sha256=sha256(self.SOURCE.encode("utf-8")).hexdigest(),
            target_field=field,
            value_index=value_index,
            selected_occurrence=selected,
            scope=scope,
            reviewer_provenance="user_authorized_ai_locator_review",
            reviewer_is_human_expert=False,
            rationale="The selected exact occurrence is inside the reviewed field scope.",
        )

    def _exact_span(self, quote: str, *, first: bool) -> EvidenceLocatorSpan:
        start = self.SOURCE.index(quote) if first else self.SOURCE.rindex(quote)
        return EvidenceLocatorSpan(quote, start, start + len(quote))

    def _line_span(self, quote: str, *, first: bool) -> EvidenceLocatorSpan:
        exact = self._exact_span(quote, first=first)
        start = self.SOURCE.rfind("\n", 0, exact.start) + 1
        end = self.SOURCE.find("\n", exact.end)
        if end < 0:
            end = len(self.SOURCE)
        return EvidenceLocatorSpan(self.SOURCE[start:end], start, end)

    def _scope_span(self, start_marker: str, end_marker: str) -> EvidenceLocatorSpan:
        start = self.SOURCE.index(start_marker)
        end = self.SOURCE.index(end_marker, start)
        return EvidenceLocatorSpan(self.SOURCE[start:end], start, end)

    def _cause_response(self, evidence_quote: str) -> str:
        return json.dumps(
            {
                "cause_dispositions": [
                    {
                        "source_cause_index": 0,
                        "semantic_role": "causal_condition",
                        "fta_disposition": "fta_event_candidate",
                        "evidence_quote": evidence_quote,
                        "reason_code": "direct_causal_or_condition_statement",
                        "rationale": "The source labels this as a possible cause.",
                    }
                ]
            },
            ensure_ascii=False,
        )


if __name__ == "__main__":
    unittest.main()
