import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import api_server  # noqa: E402
from rag_contract import (  # noqa: E402
    EvidenceCitation,
    FaultContext,
    GeneratedAnswer,
    RagResponse,
    RetrievedFault,
)


class FakeRagService:
    def answer(self, question, *, top_k):
        evidence = EvidenceCitation(
            citation_id="A01009:E1",
            field="cause",
            quote="Control Unit temperature exceeded the limit.",
            source_id="input_text",
            source_file="S210_Manual_Test.pdf",
            start=70,
            end=113,
        )
        context = FaultContext(
            fault_code="A01009",
            description="Control module overtemperature",
            component="CU",
            causes=("Control Unit temperature exceeded the limit.",),
            parameters=("r0037[0]",),
            evidence=(evidence,),
            source_file="S210_Manual_Test.pdf",
            raw_text="private source text",
        )
        return RagResponse(
            question=question,
            answer=GeneratedAnswer(
                text="A01009 表示控制单元过热。[A01009:E1]",
                citations=("A01009:E1",),
                model="fake",
            ),
            retrieved=(
                RetrievedFault(
                    fault_code="A01009",
                    score=0.91,
                    rank=1,
                    signals={"d2_rank": 1, "alarm_rank": 4},
                ),
            ),
            contexts=(context,),
            evidence_status="cited",
        )


class RagApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_service = api_server.app.state.s210_rag_service
        api_server.app.state.s210_rag_service = FakeRagService()

    def tearDown(self):
        api_server.app.state.s210_rag_service = self.previous_service

    def test_query_hides_internal_fields_without_debug(self):
        response = api_server.query_s210_rag(
            api_server.RagQueryRequest(question="控制单元温度过高怎么办？")
        )

        self.assertEqual("A01009", response["retrieved"][0]["fault_code"])
        self.assertEqual("cited", response["pipeline"]["evidence_status"])
        self.assertNotIn("raw_text", response["contexts"][0])
        self.assertNotIn("signals", response["retrieved"][0])

    def test_query_exposes_debug_signals_only_when_requested(self):
        response = api_server.query_s210_rag(
            api_server.RagQueryRequest(
                question="控制单元温度过高怎么办？",
                debug=True,
            )
        )

        self.assertEqual("private source text", response["contexts"][0]["raw_text"])
        self.assertEqual(1, response["retrieved"][0]["signals"]["d2_rank"])
        self.assertIn("BAAI/bge-m3", response["pipeline"]["retriever"])


if __name__ == "__main__":
    unittest.main()
