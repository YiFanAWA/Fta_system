import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from rag.fault_relation_expansion import FaultRelationRegistry  # noqa: E402
from contracts.rag_contract import EvidenceCitation, FaultContext, RetrievedFault  # noqa: E402
from rag.rag_service import FaultRagService  # noqa: E402


def _context(code: str, description: str, evidence_id: str, field: str) -> FaultContext:
    return FaultContext(
        fault_code=code,
        description=description,
        evidence=(
            EvidenceCitation(
                citation_id=evidence_id,
                field=field,
                quote=f"evidence for {code}",
                source_id="input_text",
                source_file="test.pdf",
            ),
        ),
    )


class RelationRegistryTests(unittest.TestCase):
    def test_relation_requires_query_trigger_and_resolves_evidence(self):
        registry = FaultRelationRegistry.from_payload(
            {
                "relations": [
                    {
                        "relation_id": "REL-1",
                        "fault_codes": ["A00001", "F00001"],
                        "relation_type": "shared_parameter",
                        "query_triggers": ["p9506"],
                        "relation_note": "shared parameter",
                        "evidence": [
                            {"fault_code": "A00001", "citation_id": "A00001:E1", "field": "parameter"},
                            {"fault_code": "F00001", "citation_id": "F00001:E1", "field": "parameter"},
                        ],
                        "review_status": "reviewed",
                    }
                ]
            }
        )
        contexts = (
            _context("A00001", "message", "A00001:E1", "parameter"),
            _context("F00001", "fault", "F00001:E1", "parameter"),
        )
        self.assertEqual(("A00001",), registry.triggered_related_codes("p9506 关联故障", "F00001"))
        relations = registry.expand("p9506 关联故障", "F00001", contexts)
        self.assertEqual(1, len(relations))
        self.assertEqual("A00001", relations[0].related_fault_code)
        self.assertEqual("F00001:E1", relations[0].evidence[1].citation_id)
        self.assertEqual((), registry.expand("普通故障查询", "F00001", contexts))


class RelationAwareServiceTests(unittest.TestCase):
    def test_service_adds_relation_context_without_changing_retrieval_candidates(self):
        class Retriever:
            def retrieve(self, question, *, limit):
                return [RetrievedFault("F00001", score=0.9, rank=1)]

        class Loader:
            def __init__(self, contexts):
                self.contexts = {context.fault_code: context for context in contexts}

            def load(self, fault_codes):
                return [self.contexts[code] for code in fault_codes]

        class Generator:
            def __init__(self):
                self.contexts = ()

            def generate(self, question, contexts):
                self.contexts = tuple(contexts)
                return type("Answer", (), {"text": "回答", "citations": (), "model": "test"})()

        primary = _context("F00001", "fault", "F00001:E1", "parameter")
        related = _context("A00001", "message", "A00001:E1", "parameter")
        generator = Generator()
        registry = FaultRelationRegistry.from_payload(
            {
                "relations": [
                    {
                        "relation_id": "REL-1",
                        "fault_codes": ["A00001", "F00001"],
                        "relation_type": "shared_parameter",
                        "query_triggers": ["p9506"],
                        "relation_note": "shared parameter",
                        "evidence": [
                            {"fault_code": "A00001", "citation_id": "A00001:E1", "field": "parameter"},
                            {"fault_code": "F00001", "citation_id": "F00001:E1", "field": "parameter"},
                        ],
                        "review_status": "reviewed",
                    }
                ]
            }
        )
        response = FaultRagService(
            Retriever(),
            Loader([primary, related]),
            generator,
            relation_registry=registry,
        ).answer("p9506 关联故障", top_k=1)
        self.assertEqual(["F00001"], [item.fault_code for item in response.retrieved])
        self.assertEqual(["A00001"], [item.related_fault_code for item in response.relations])
        self.assertEqual(["F00001", "A00001"], [context.fault_code for context in generator.contexts])
        self.assertEqual(["F00001", "A00001"], [context.fault_code for context in response.contexts])


if __name__ == "__main__":
    unittest.main()
