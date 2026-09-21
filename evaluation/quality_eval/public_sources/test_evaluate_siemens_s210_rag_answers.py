import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_siemens_s210_rag_answers import (  # noqa: E402
    evaluate_dataset,
    evaluate_response,
)


def _query():
    return {
        "query_id": "RA001",
        "expected_fault_codes": ["A01009"],
        "required_evidence_fields": ["fault_code", "description", "cause", "remedy"],
    }


def _response():
    evidence = [
        {"citation_id": "A01009:E1", "field": "fault_code"},
        {"citation_id": "A01009:E2", "field": "description"},
        {"citation_id": "A01009:E3", "field": "cause"},
        {"citation_id": "A01009:E4", "field": "remedy"},
    ]
    return {
        "query_id": "RA001",
        "answer": {
            "text": "A01009 表示控制单元过热。[A01009:E1]",
            "citations": [
                "A01009:E1",
                "A01009:E2",
                "A01009:E3",
                "A01009:E4",
            ],
        },
        "contexts": [{"fault_code": "A01009", "evidence": evidence}],
    }


class RagAnswerEvaluationTests(unittest.TestCase):
    def test_contract_passes_when_code_and_required_evidence_are_present(self):
        result = evaluate_response(_query(), _response())
        self.assertTrue(result["fault_code_hit"])
        self.assertTrue(result["citations_valid"])
        self.assertTrue(result["citations_aligned"])
        self.assertTrue(result["answer_contract_pass"])

    def test_wrong_fault_citation_fails_alignment(self):
        response = _response()
        response["answer"]["citations"] = ["F30002:E1"]
        response["contexts"].append(
            {
                "fault_code": "F30002",
                "evidence": [{"citation_id": "F30002:E1", "field": "cause"}],
            }
        )
        result = evaluate_response(_query(), response)
        self.assertFalse(result["citations_aligned"])
        self.assertFalse(result["answer_contract_pass"])

    def test_dataset_reports_missing_responses(self):
        dataset = {"dataset_info": {"name": "test"}, "queries": [_query()]}
        report = evaluate_dataset(dataset, [])
        self.assertEqual(1, report["query_count"])
        self.assertEqual(0, report["response_count"])
        self.assertEqual(["RA001"], report["missing_response_ids"])


if __name__ == "__main__":
    unittest.main()
