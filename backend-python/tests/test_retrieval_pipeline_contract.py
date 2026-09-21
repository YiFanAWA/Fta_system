import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))

from retrieval_pipeline_contract import CandidateHit, CandidateUnion  # noqa: E402


class CandidateUnionTests(unittest.TestCase):
    def test_child_hits_are_deduplicated_by_entity_and_keep_channel_signals(self):
        candidates = CandidateUnion().merge(
            {
                "description": [
                    CandidateHit("siemens:siemens:s210:A01006", "A01006:description", "description", 0.92, 1),
                ],
                "cause": [
                    CandidateHit("siemens:siemens:s210:A01006", "A01006:cause", "cause", 0.91, 1),
                    CandidateHit("siemens:siemens:s210:F01005", "F01005:cause", "cause", 0.80, 2),
                ],
            },
            per_channel_limit={"description": 20, "cause": 10},
        )
        self.assertEqual(2, len(candidates))
        self.assertEqual("siemens:siemens:s210:A01006", candidates[0].entity_id)
        self.assertEqual(("description", "cause"), candidates[0].channels)
        self.assertEqual(2, candidates[0].signals["hit_count"])
        self.assertEqual(
            {"description": 0.92, "cause": 0.91},
            candidates[0].signals["scores_by_channel"],
        )

    def test_per_channel_limit_is_applied_before_union(self):
        candidates = CandidateUnion().merge(
            {
                "alarm": [
                    CandidateHit("E1", "E1:alarm", "alarm", 0.9, 1),
                    CandidateHit("E2", "E2:alarm", "alarm", 0.8, 2),
                ]
            },
            per_channel_limit=1,
        )
        self.assertEqual(["E1"], [candidate.entity_id for candidate in candidates])


if __name__ == "__main__":
    unittest.main()
