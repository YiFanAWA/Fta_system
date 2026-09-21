import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from contracts.common_fault_schema import build_fault_entity_id  # noqa: E402
from domains.siemens_s210_adapter import SiemensS210Adapter  # noqa: E402


GOLD = ROOT / "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json"


class CommonFaultSchemaTests(unittest.TestCase):
    def test_entity_id_is_scoped_by_domain_manufacturer_system_and_code(self):
        self.assertEqual(
            "industrial-drive:siemens:s210:A01006",
            build_fault_entity_id(
                domain="industrial_drive",
                manufacturer="Siemens",
                system="S210",
                fault_code="a01006",
            ),
        )

    def test_s210_full_gold_maps_without_loss_of_core_fields(self):
        adapter = SiemensS210Adapter()
        entities = adapter.parse_file(GOLD)
        payload = json.loads(GOLD.read_text(encoding="utf-8"))
        expected = [
            record
            for sample in payload["samples"]
            for record in sample.get("gold_records", [])
        ]
        self.assertEqual(281, len(entities))
        self.assertEqual(281, len({entity.entity_id for entity in entities}))
        self.assertEqual(281, len({entity.fault_code for entity in entities}))
        by_code = {entity.fault_code: entity for entity in entities}
        for record in expected:
            entity = by_code[record["fault_code"]]
            self.assertEqual(record["description"], entity.description)
            self.assertEqual(tuple(record.get("causes", [])), entity.causes)
            self.assertEqual(tuple(record.get("parameters", [])), entity.parameters)
            self.assertEqual(record.get("component") or "", entity.domain_specific["primary_component"])
            self.assertTrue(entity.raw_text)
            self.assertGreater(len(entity.evidence), 0)

    def test_s210_adapter_builds_parent_scoped_chunks_and_exact_fields(self):
        adapter = SiemensS210Adapter()
        entities = adapter.parse_file(GOLD)
        chunks = adapter.build_retrieval_chunks(entities[:1])
        self.assertTrue(chunks)
        self.assertEqual({entities[0].entity_id}, {chunk.entity_id for chunk in chunks})
        self.assertEqual(
            {"A01006"},
            set(adapter.extract_exact_fields("请查询 A01006 的 p7829 参数").fault_codes),
        )
        self.assertEqual(
            {"P7829"},
            set(adapter.extract_exact_fields("请查询 A01006 的 p7829 参数").parameters),
        )


if __name__ == "__main__":
    unittest.main()
