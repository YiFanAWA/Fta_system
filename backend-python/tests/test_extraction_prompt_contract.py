import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from core.prompt_templates import build_text_extraction_prompt  # noqa: E402


class ExtractionPromptContractTests(unittest.TestCase):
    def test_prompt_accepts_project_fault_codes_and_parameters(self):
        prompt = build_text_extraction_prompt("故障码A01032，参数r2124。", 1, 1)

        self.assertIn("A\\d+", prompt)
        self.assertIn("文本行首直接出现故障编号", prompt)
        self.assertIn("N\\d+", prompt)
        self.assertIn("r2124", prompt)
        self.assertIn("related_components", prompt)

    def test_prompt_keeps_related_components_in_one_record(self):
        prompt = build_text_extraction_prompt(
            "F01651关联控制单元及电机模块。",
            1,
            1,
        )

        self.assertIn("一个明确的“故障码 + 故障现象”只输出一个 item", prompt)
        self.assertNotIn("必须拆分为多个 item", prompt)

    def test_prompt_requires_explicit_english_relation_for_related_components(self):
        prompt = build_text_extraction_prompt(
            "F30075 Drive fault. The power unit is mentioned in the cause.",
            1,
            1,
        )

        self.assertIn("associated with、related to、connected to/with、linked to", prompt)
        self.assertIn("普通正文、故障原因或处理建议中单独提到的组件", prompt)

    def test_prompt_separates_cause_scenarios_from_repair_actions(self):
        prompt = build_text_extraction_prompt(
            "故障值20表示制动绕组短路，需检查参数并升级固件。",
            1,
            1,
        )

        self.assertIn("故障值20表示制动绕组短路", prompt)
        self.assertIn("原因、触发条件或明确故障场景", prompt)
        self.assertIn("仅用于定位的诊断索引不能单独作为候选原因", prompt)
        self.assertIn("missing_reason_evidence", prompt)
        self.assertIn("处理动作不是 causes", prompt)
        self.assertIn("同一原因只保留一次", prompt)


if __name__ == "__main__":
    unittest.main()
