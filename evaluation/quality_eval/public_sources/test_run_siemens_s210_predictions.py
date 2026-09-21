import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SOURCES = ROOT / "evaluation" / "quality_eval" / "public_sources"
sys.path.insert(0, str(PUBLIC_SOURCES))

from run_siemens_s210_predictions import _build_request_payload  # noqa: E402


class SiemensS210PredictionRunnerTests(unittest.TestCase):
    def test_generate_endpoint_payload_uses_raw_text_contract(self):
        payload = _build_request_payload(
            {"sample_id": "sample-1", "input_text": "F01000 fault text"}
        )
        self.assertEqual("text", payload["source"])
        self.assertEqual("F01000 fault text", payload["raw_text"])
        self.assertNotIn("text", payload)


if __name__ == "__main__":
    unittest.main()
