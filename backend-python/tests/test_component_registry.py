import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from domains.component_registry import (  # noqa: E402
    find_english_component_heading,
    normalize_component_label,
)


class ComponentRegistryTests(unittest.TestCase):
    def test_normalizes_known_aliases_without_touching_unknown_semantics(self):
        self.assertEqual("Control Unit", normalize_component_label("Control Units"))
        self.assertEqual("Safety Integrated", normalize_component_label("SI P1"))
        self.assertEqual(
            "new interface module",
            normalize_component_label("new interface module"),
        )

    def test_normalizes_title_components(self):
        self.assertEqual(
            "Control system (internal software)",
            find_english_component_heading("F01000 Internal software error"),
        )
        self.assertEqual(
            "SI Motion",
            find_english_component_heading("A01706 SI Motion P1: SAM/SBR limit exceeded"),
        )


if __name__ == "__main__":
    unittest.main()
