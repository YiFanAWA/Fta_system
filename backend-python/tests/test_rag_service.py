import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from rag_contract import FaultContext, GeneratedAnswer, RetrievedFault  # noqa: E402
from rag_service import (  # noqa: E402
    EvidenceBoundPromptBuilder,
    FaultRagService,
    GoldFaultContextStore,
    PromptAnswerGenerator,
    RagServiceError,
)


def _gold_payload():
    return {
        "samples": [
            {
                "sample_id": "TEST_A01009",
                "source_file": "S210_Manual_Test.pdf",
                "input_text": (
                    "A01009 Control module overtemperature\n"
                    "Cause: Control Unit temperature exceeded the limit.\n"
                    "Alarm value (r0037):\nTemperature value.\n"
                    "Remedy: Check cooling and ambient temperature."
                ),
                "gold_records": [
                    {
                        "fault_code": "A01009",
                        "component": "CU",
                        "related_components": [],
                        "description": "Control module overtemperature",
                        "causes": ["Control Unit temperature exceeded the limit."],
                        "parameters": ["r0037[0]"],
                        "gate_type": None,
                    }
                ],
                "evidence_spans": [
                    {
                        "field": "fault_code",
                        "source_id": "input_text",
                        "quote": "A01009",
                        "start": 0,
                        "end": 6,
                    },
                    {
                        "field": "cause",
                        "source_id": "input_text",
                        "quote": "Control Unit temperature exceeded the limit.",
                        "start": 70,
                        "end": 113,
                    },
                ],
            }
        ]
    }


class FakeRetriever:
    def __init__(self):
        self.calls = 0

    def retrieve(self, question, *, limit):
        self.calls += 1
        return [
            RetrievedFault("A01009", score=0.91, rank=1, signals={"source": "fake"}),
            RetrievedFault("A01009", score=0.90, rank=2, signals={"source": "duplicate"}),
        ][:limit]


class FakeGenerator:
    def __init__(self):
        self.contexts = None

    def generate(self, question, contexts):
        self.contexts = tuple(contexts)
        return GeneratedAnswer(
            text="A01009 表示控制单元过热。[A01009:E1]",
            citations=("A01009:E1",),
            model="fake",
        )


class MultiRetriever:
    def __init__(self, candidates):
        self.candidates = candidates

    def retrieve(self, question, *, limit):
        return self.candidates[:limit]


class FixedContextLoader:
    def __init__(self, contexts):
        self.contexts = {context.fault_code: context for context in contexts}

    def load(self, fault_codes):
        return [self.contexts[code] for code in fault_codes]


class RecordingGenerator:
    def __init__(self):
        self.contexts = ()

    def generate(self, question, contexts):
        self.contexts = tuple(contexts)
        return GeneratedAnswer(text="回答", citations=())


def _context(code, description):
    return FaultContext(
        fault_code=code,
        description=description,
        evidence=(),
    )


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.prompt = ""

    def complete(self, prompt):
        self.prompt = prompt
        return self.response


class RagServiceTests(unittest.TestCase):
    def test_gold_context_loads_alarm_remedy_and_evidence(self):
        store = GoldFaultContextStore.from_payload(_gold_payload())
        context = store.load(["a01009"])[0]
        self.assertIn("Alarm value", context.alarm_value)
        self.assertIn("Remedy", context.remedy)
        self.assertEqual("A01009:E1", context.evidence[0].citation_id)
        self.assertEqual("S210_Manual_Test.pdf", context.evidence[0].source_file)

        evidence_by_field = {item.field: item for item in context.evidence}
        self.assertIn("alarm_value", evidence_by_field)
        self.assertIn("remedy", evidence_by_field)
        self.assertEqual(
            "Alarm value (r0037):\nTemperature value.",
            evidence_by_field["alarm_value"].quote,
        )
        self.assertEqual(
            "Remedy: Check cooling and ambient temperature.",
            evidence_by_field["remedy"].quote,
        )

    def test_prompt_contains_all_context_planes_and_evidence_rule(self):
        store = GoldFaultContextStore.from_payload(_gold_payload())
        context = store.load(["A01009"])[0]
        prompt = EvidenceBoundPromptBuilder().build("控制单元温度过高怎么办？", [context])
        self.assertIn("Alarm value section:", prompt)
        self.assertIn("Remedy section:", prompt)
        self.assertIn("[A01009:E1]", prompt)
        self.assertIn("不得补造参数、原因或维修结论", prompt)
        self.assertIn("结论第一行必须同时引用故障码和故障现象的证据", prompt)

    def test_service_deduplicates_faults_and_returns_evidence_status(self):
        generator = FakeGenerator()
        service = FaultRagService(
            FakeRetriever(),
            GoldFaultContextStore.from_payload(_gold_payload()),
            generator,
        )
        response = service.answer("控制单元温度过高怎么办？", top_k=3)
        self.assertEqual("cited", response.evidence_status)
        self.assertEqual(["A01009"], [item.fault_code for item in response.retrieved])
        self.assertEqual("A01009", response.contexts[0].fault_code)
        self.assertIsNotNone(generator.contexts)

    def test_service_does_not_generate_for_out_of_domain_query(self):
        generator = FakeGenerator()
        retriever = FakeRetriever()
        service = FaultRagService(
            retriever,
            GoldFaultContextStore.from_payload(_gold_payload()),
            generator,
        )
        response = service.answer("今天天气怎么样？", top_k=3)
        self.assertEqual("out_of_domain", response.boundary.knowledge_status)
        self.assertFalse(response.boundary.answer_allowed)
        self.assertEqual("not_answered", response.evidence_status)
        self.assertEqual("boundary-policy", response.answer.model)
        self.assertIsNone(generator.contexts)
        self.assertEqual(0, retriever.calls)

    def test_service_does_not_generate_for_low_information_query(self):
        generator = FakeGenerator()
        service = FaultRagService(
            FakeRetriever(),
            GoldFaultContextStore.from_payload(_gold_payload()),
            generator,
        )
        response = service.answer("设备坏了。", top_k=3)
        self.assertEqual("insufficient_evidence", response.boundary.knowledge_status)
        self.assertFalse(response.boundary.answer_allowed)
        self.assertIn("信息不足", response.answer.text)

    def test_service_scopes_generation_to_primary_fault_by_default(self):
        contexts = [
            _context("A01009", "Control module overtemperature"),
            _context("A30034", "Internal overtemperature"),
        ]
        generator = RecordingGenerator()
        service = FaultRagService(
            MultiRetriever(
                [
                    RetrievedFault("A01009", score=0.95, rank=1),
                    RetrievedFault("A30034", score=0.70, rank=2),
                ]
            ),
            FixedContextLoader(contexts),
            generator,
        )
        service.answer("控制单元温度过高是什么报警？", top_k=2)
        self.assertEqual(["A01009"], [item.fault_code for item in generator.contexts])

    def test_service_keeps_close_duplicate_descriptions_for_multi_fault_query(self):
        contexts = [
            _context("F01611", "Defect in a monitoring channel"),
            _context("F30611", "Defect in a monitoring channel"),
        ]
        generator = RecordingGenerator()
        service = FaultRagService(
            MultiRetriever(
                [
                    RetrievedFault("F01611", score=0.94, rank=1),
                    RetrievedFault("F30611", score=0.92, rank=2),
                ]
            ),
            FixedContextLoader(contexts),
            generator,
        )
        service.answer("STO 两个监控通道状态不一致可能对应哪些故障？", top_k=2)
        self.assertEqual(
            ["F01611", "F30611"],
            [item.fault_code for item in generator.contexts],
        )

    def test_prompt_generator_rejects_answer_without_citation(self):
        client = FakeClient("A01009 表示控制单元过热。")
        context = GoldFaultContextStore.from_payload(_gold_payload()).load(["A01009"])
        with self.assertRaises(RagServiceError) as raised:
            PromptAnswerGenerator(client).generate("问题", context)
        self.assertEqual("answer_missing_evidence_citation", raised.exception.code)

    def test_prompt_generator_rejects_unknown_citation(self):
        client = FakeClient("结论。[A01009:E99]")
        context = GoldFaultContextStore.from_payload(_gold_payload()).load(["A01009"])
        with self.assertRaises(RagServiceError) as raised:
            PromptAnswerGenerator(client).generate("问题", context)
        self.assertEqual("answer_unknown_evidence", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
