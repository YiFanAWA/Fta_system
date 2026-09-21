import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from build_siemens_s210_fault_corpus import build_corpus  # noqa: E402


class SiemensS210FaultCorpusTests(unittest.TestCase):
    def test_public_manual_records_are_unlabeled_and_provenance_preserving(self):
        pdf_path = ROOT / "tmp/pdfs/S210_Manual_2019.pdf"
        if not pdf_path.exists() or pdf_path.stat().st_size < 100000:
            self.skipTest("downloaded public PDF is not available")
        manifest, records = build_corpus(pdf_path, retrieved_date="2026-09-19")
        self.assertGreaterEqual(len(records), 250)
        self.assertEqual("unlabeled_public_corpus", manifest["label_status"])
        self.assertFalse(manifest["human_expert_reviewed"])
        f01003 = next(item for item in records if item["sample_id"].endswith("_F01003"))
        self.assertIn("Acknowledgment delay", f01003["input_text"])
        self.assertEqual("F01003", f01003["weak_record"]["fault_code"])
        self.assertIn("r0949", f01003["weak_record"]["parameters"])
        self.assertTrue(f01003["provenance"]["source_sha256"])


if __name__ == "__main__":
    unittest.main()
