import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from domains.aerospace_adapter import FaaSdrAerospaceAdapter  # noqa: E402


SAMPLE = ROOT / "evaluation/quality_eval/datasets/aerospace_faa_sdr_public_sample_v1_2026-09-21.json"


class AerospaceAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
        cls.adapter = FaaSdrAerospaceAdapter()
        cls.entities = cls.adapter.parse_source(cls.payload)

    def test_sample_maps_to_unique_parent_entities(self):
        self.assertEqual(40, len(self.entities))
        self.assertEqual(40, len({entity.entity_id for entity in self.entities}))
        self.assertEqual(40, len({entity.fault_code for entity in self.entities}))

    def test_raw_source_and_character_evidence_are_preserved(self):
        for entity in self.entities:
            self.assertTrue(entity.raw_text)
            self.assertIn("raw_record", entity.domain_specific)
            self.assertTrue(entity.evidence)
            for evidence in entity.evidence:
                self.assertEqual(entity.raw_text[evidence.start : evidence.end], evidence.quote)

    def test_chunks_keep_parent_identity_and_roles(self):
        chunks = self.adapter.build_retrieval_chunks(self.entities)
        self.assertGreaterEqual(len(chunks), 40)
        self.assertEqual({entity.entity_id for entity in self.entities}, {chunk.entity_id for chunk in chunks})
        self.assertIn("description", {chunk.kind for chunk in chunks})

    def test_jasc_and_part_number_are_exact_retrieval_inputs(self):
        entity = next(entity for entity in self.entities if entity.parameters)
        jasc = entity.domain_specific["jasc_code"]
        part_number = entity.parameters[0]
        matches = self.adapter.extract_exact_fields(f"JASC {jasc} part {part_number}")
        self.assertIn(jasc.upper(), matches.fault_codes)
        self.assertIn(part_number.upper(), matches.parameters)

    def test_native_fault_code_gap_is_explicit(self):
        self.assertTrue(all(entity.domain_specific["native_fault_code_present"] is False for entity in self.entities))
        self.assertTrue(all(entity.domain_specific["identifier_kind"] == "operator_control_number" for entity in self.entities))


if __name__ == "__main__":
    unittest.main()
