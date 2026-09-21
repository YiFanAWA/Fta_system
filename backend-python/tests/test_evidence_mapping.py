import sys
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from contracts.extraction_contract import EvidenceField  # noqa: E402
from core.model_client import CallableModelClient  # noqa: E402
from extraction.text_extraction_adapter import TextExtractionAdapter  # noqa: E402
from workflows.ai_module import _evidence_span_to_legacy_dict  # noqa: E402


class EvidenceMappingTests(unittest.TestCase):
    def _adapter(self, response: str) -> TextExtractionAdapter:
        return TextExtractionAdapter(
            CallableModelClient(lambda prompt: response),
            lambda text, index, total: text,
        )

    def test_binds_literal_record_fields_to_source_offsets(self):
        response = (
            '{"items":[{"fault_code":"F01630",'
            '"description":"制动控制出错","component":"电机模块",'
            '"causes":["制动绕组短路"],"parameters":["p1278"]}]}'
        )
        source = "故障代码F01630。故障现象：制动控制出错。组件：电机模块。参数：p1278。故障值20：制动绕组短路。"

        result = self._adapter(response).extract(source)

        self.assertEqual("success", result.status.value)
        self.assertEqual(5, len(result.evidence_spans))
        self.assertTrue(all(span.matches(source) for span in result.evidence_spans))
        self.assertEqual(
            {
                EvidenceField.FAULT_CODE,
                EvidenceField.DESCRIPTION,
                EvidenceField.PRIMARY_COMPONENT,
                EvidenceField.CAUSE,
                EvidenceField.PARAMETER,
            },
            {span.field for span in result.evidence_spans},
        )

    def test_whitespace_normalized_model_value_uses_original_quote(self):
        response = '{"items":[{"description":"SI P1（CU）：制动控制出错"}]}'
        source = "故障现象为SI P1（CU）：\n制动控制出错。"

        result = self._adapter(response).extract(source)

        self.assertEqual(1, len(result.evidence_spans))
        span = result.evidence_spans[0]
        self.assertEqual("SI P1（CU）：\n制动控制出错", span.quote)
        self.assertTrue(span.matches(source))

    def test_description_uses_explicit_chinese_phenomenon_boundary(self):
        response = (
            '{"items":[{"fault_code":"A01013",'
            '"description":"控制单元：达到或超过风扇的使用寿命",'
            '"component":"控制单元（CU）","causes":[],"parameters":[]}]} '
        )
        source = "故障代码A01013。组件为控制单元（CU）。故障现象为控制单元：达到或超过风扇的使用寿命。"

        result = self._adapter(response).extract(source)

        self.assertEqual("达到或超过风扇的使用寿命", result.records[0].description)
        self.assertTrue(
            any(
                span.field is EvidenceField.DESCRIPTION
                and span.quote == "达到或超过风扇的使用寿命"
                for span in result.evidence_spans
            )
        )

    def test_description_uses_english_title_before_cause_section(self):
        response = (
            '{"items":[{"fault_code":"F30655",'
            '"description":"SI P2: Align monitoring functions; an error occurred",'
            '"component":"Safety Integrated","causes":[],"parameters":[]}]} '
        )
        source = (
            "F30655 SI P2: Align monitoring functions\n"
            "Reaction: OFF2\n"
            "Cause: An error occurred when aligning the Safety Integrated monitoring functions."
        )

        result = self._adapter(response).extract(source)

        self.assertEqual("Align monitoring functions", result.records[0].description)

    def test_plain_encoder_heading_is_normalized_to_primary_component(self):
        response = (
            '{"items":[{"fault_code":"F31120","description":"Sign-of-life missing",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = "F31120 Encoder 1: Sign-of-life missing\nCause: Encoder communication failed"

        result = self._adapter(response).extract(source)

        self.assertEqual("Encoder 1", result.records[0].component)

    def test_description_embedded_cause_is_not_kept_as_duplicate(self):
        response = (
            '{"items":[{"fault_code":"F01640","description":"识别出组件更换",'
            '"component":"控制单元","causes":["控制单元更换","识别出组件更换"]}]}'
        )
        source = (
            "故障代码F01640。组件为控制单元。故障现象为识别出组件更换。"
            "可能原因：控制单元更换。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("控制单元更换",), result.records[0].causes)

    def test_explicit_cause_section_is_recovered_when_model_returns_none(self):
        response = (
            '{"items":[{"fault_code":"F40000","description":"驱动对象故障",'
            '"component":"","causes":[],"parameters":[]}]}'
        )
        source = (
            "F40000 Fault at the drive object at the DRIVE-CLiQ socket X100\n"
            "Cause: A fault has occurred at the drive object at the DRIVE-CLiQ socket X100.\n"
            "Remedy: Cycle power"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(
            ("A fault has occurred at the drive object at the DRIVE-CLiQ socket X100.",),
            result.records[0].causes,
        )
        self.assertTrue(
            any(
                span.field is EvidenceField.CAUSE
                and span.quote.startswith("A fault has occurred")
                for span in result.evidence_spans
            )
        )

    def test_unknown_fields_do_not_create_synthetic_evidence(self):
        response = '{"items":[{"fault_code":null,"description":"写RAM失败","causes":[]}]}'
        source = "故障现象为写RAM失败。"

        result = self._adapter(response).extract(source)

        self.assertEqual(1, len(result.evidence_spans))
        self.assertEqual(EvidenceField.DESCRIPTION, result.evidence_spans[0].field)

    def test_same_fault_record_with_multiple_components_is_grouped(self):
        response = (
            '{"items":['
            '{"fault_code":"F01651","description":"安全时间片同步失败",'
            '"component":"控制单元","causes":["热启动导致"],"parameters":["r0949"]},'
            '{"fault_code":"F01651","description":"安全时间片同步失败",'
            '"component":"电机模块","causes":["PROFIBUS主站同步故障"],"parameters":["p9510"]}'
            ']}'
        )
        source = (
            "故障码F01651。组件为无（关联控制单元及电机模块）。"
            "故障现象为安全时间片同步失败。"
            "可能原因：热启动导致、PROFIBUS主站同步故障。"
            "参数：r0949、p9510。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual("success", result.status.value)
        self.assertEqual(1, len(result.records))
        record = result.records[0]
        self.assertIsNone(record.component)
        self.assertEqual(("控制单元", "电机模块"), record.related_components)
        self.assertEqual(("热启动导致", "PROFIBUS主站同步故障"), record.causes)
        self.assertEqual(("r0949", "p9510"), record.parameters)
        self.assertEqual(
            2,
            sum(
                span.field is EvidenceField.RELATED_COMPONENT
                for span in result.evidence_spans
            ),
        )
        self.assertTrue(
            any(
                span.field is EvidenceField.COMPONENT_DECLARATION
                and span.quote == "组件为无"
                for span in result.evidence_spans
            )
        )

    def test_related_components_do_not_promote_to_primary_component(self):
        response = (
            '{"items":[{"fault_code":"F01600","description":"STOP A被触发",'
            '"component":"","related_components":["控制单元","电机模块"]}]}'
        )
        source = "故障码F01600。组件为无（关联控制单元及电机模块）。故障现象为STOP A被触发。"

        result = self._adapter(response).extract(source)

        record = result.records[0]
        self.assertIsNone(record.component)
        self.assertEqual(("控制单元", "电机模块"), record.related_components)

    def test_primary_component_is_not_duplicated_as_related_component(self):
        response = (
            '{"items":[{"fault_code":"F01009","description":"控制单元过热",'
            '"component":"控制单元","related_components":["控制单元","编码器"]}]}'
        )
        source = "故障码F01009。组件为控制单元。故障现象为控制单元过热，间接影响编码器信号处理。"

        result = self._adapter(response).extract(source)

        self.assertEqual("控制单元", result.records[0].component)
        self.assertEqual((), result.records[0].related_components)
        fields = {span.field for span in result.evidence_spans}
        self.assertIn(EvidenceField.PRIMARY_COMPONENT, fields)
        self.assertNotIn(EvidenceField.RELATED_COMPONENT, fields)

    def test_recovers_single_bare_header_fault_code_and_binds_evidence(self):
        response = (
            '{"items":[{"fault_code":null,"description":"Firmware update",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = "A01006 Firmware update for DRIVE-CLiQ component required\nCause: no firmware"

        result = self._adapter(response).extract(source)

        self.assertEqual("A01006", result.records[0].fault_code)
        code_spans = [
            span for span in result.evidence_spans if span.field is EvidenceField.FAULT_CODE
        ]
        self.assertEqual(["A01006"], [span.quote for span in code_spans])

    def test_does_not_recover_inline_message_code_as_record_header(self):
        response = (
            '{"items":[{"fault_code":null,"description":"SAM/SBR limit exceeded",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = "A01706 SAM/SBR limit exceeded. The drive is stopped by message F01700."

        result = self._adapter(response).extract(source)

        self.assertEqual("A01706", result.records[0].fault_code)

    def test_recovers_explicit_english_component_heading(self):
        response = (
            '{"items":[{"fault_code":"A02007","description":"Drive not SERVO",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = "A02007 Function generator: Drive not SERVO / VECTOR / DC_CTRL"

        result = self._adapter(response).extract(source)

        self.assertEqual("Function generator", result.records[0].component)
        self.assertTrue(
            any(
                span.field is EvidenceField.PRIMARY_COMPONENT
                and span.quote == "Function generator"
                for span in result.evidence_spans
            )
        )

    def test_normalizes_siemens_title_component_variants(self):
        cases = (
            (
                "A01706 SI Motion P1: SAM/SBR limit exceeded",
                "SI Motion P1",
                "SI Motion",
            ),
            (
                "A01788 SI: Automatic test stop waits for STO deselection",
                "SI P1",
                "Safety Integrated",
            ),
            (
                "F01000 Internal software error",
                "",
                "Control system (internal software)",
            ),
            (
                "F01023 Software timeout (internal)",
                "",
                "Control system (internal software)",
            ),
            (
                "F01042 Parameter error during project download",
                "",
                "Parameter configuration system",
            ),
            (
                "F01357 Topology: Two Control Units identified on the DRIVE-CLiQ line",
                "",
                "DRIVE-CLiQ line",
            ),
            (
                "F31851 Encoder 1 DRIVE-CLiQ (CU): Sign-of-life missing",
                "Encoder 1 DRIVE-CLiQ (CU)",
                "Encoder 1 (DRIVE-CLiQ)",
            ),
        )
        for source, model_component, expected in cases:
            with self.subTest(source=source):
                response = (
                    '{"items":[{"fault_code":null,"description":"fault",'
                    f'"component":"{model_component}","related_components":[],'
                    '"causes":[],"parameters":[]}]}'
                )
                result = self._adapter(response).extract(source)
                self.assertEqual(expected, result.records[0].component)
                self.assertTrue(
                    any(
                        span.field is EvidenceField.PRIMARY_COMPONENT
                        for span in result.evidence_spans
                    )
                )

    def test_does_not_infer_component_from_plain_english_body_mention(self):
        response = (
            '{"items":[{"fault_code":"A02007","description":"Drive not SERVO",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = "A02007 Drive not SERVO / VECTOR / DC_CTRL. Check the power unit."

        result = self._adapter(response).extract(source)

        self.assertIsNone(result.records[0].component)

    def test_does_not_infer_plain_english_component_mention_as_related(self):
        response = (
            '{"items":[{"fault_code":"F07801","description":"Motor overcurrent",'
            '"component":"Drive","related_components":["Motor"],"causes":[],"parameters":[]}]}'
        )
        source = "F07801 Drive: Motor overcurrent. The motor current exceeded the limit."

        result = self._adapter(response).extract(source)

        self.assertEqual("Drive", result.records[0].component)
        self.assertEqual((), result.records[0].related_components)

    def test_keeps_english_related_component_with_explicit_relation(self):
        response = (
            '{"items":[{"fault_code":"F07801","description":"Drive fault",'
            '"component":"Drive","related_components":["Motor"],"causes":[],"parameters":[]}]}'
        )
        source = "F07801 Drive fault associated with the Motor."

        result = self._adapter(response).extract(source)

        self.assertEqual(("Motor",), result.records[0].related_components)

    def test_recovers_omitted_english_related_component_from_explicit_relation(self):
        response = (
            '{"items":[{"fault_code":"F01357","description":"Topology fault",'
            '"component":"","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = (
            "F01357 Topology fault. Two Control Units are connected with one another "
            "through DRIVE-CLiQ."
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("Control Unit",), result.records[0].related_components)
        self.assertTrue(
            any(
                span.field is EvidenceField.RELATED_COMPONENT
                and span.quote == "Control Unit"
                for span in result.evidence_spans
            )
        )

    def test_normalizes_plural_explicit_english_related_component(self):
        response = (
            '{"items":[{"fault_code":"F01357","description":"Topology fault",'
            '"component":"DRIVE-CLiQ line","related_components":["Control Units"],'
            '"causes":[],"parameters":[]}]}'
        )
        source = (
            "F01357 Topology fault. Two Control Units are connected with one another "
            "through DRIVE-CLiQ."
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("Control Unit",), result.records[0].related_components)

    def test_does_not_recover_english_component_from_non_relation_phrase(self):
        response = (
            '{"items":[{"fault_code":"F30075","description":"Configuration fault",'
            '"component":"Power unit","related_components":[],"causes":[],"parameters":[]}]}'
        )
        source = (
            "F30075 Configuration fault. A communication error occurred while configuring "
            "the power unit using the Control Unit."
        )

        result = self._adapter(response).extract(source)

        self.assertEqual((), result.records[0].related_components)

    def test_does_not_duplicate_plural_primary_component_as_related(self):
        response = (
            '{"items":[{"fault_code":"F01357","description":"Topology fault",'
            '"component":"Control Units","related_components":["Control Unit"],'
            '"causes":[],"parameters":[]}]}'
        )
        source = (
            "F01357 Topology fault. Two Control Units are connected with one another "
            "through DRIVE-CLiQ."
        )

        result = self._adapter(response).extract(source)

        self.assertEqual((), result.records[0].related_components)

    def test_does_not_infer_chinese_body_mention_as_related(self):
        response = (
            '{"items":[{"fault_code":"F07802","description":"过热",'
            '"component":"控制单元","related_components":["编码器"],"causes":[],"parameters":[]}]}'
        )
        source = "故障码F07802。故障现象为控制单元过热，间接影响编码器信号处理。"

        result = self._adapter(response).extract(source)

        self.assertEqual((), result.records[0].related_components)

    def test_parameter_value_cause_is_normalized_to_natural_language(self):
        response = (
            '{"items":[{"fault_code":"F01630","description":"制动控制出错",'
            '"causes":["10、11表示打开制动过程出错",'
            '"故障值为20（制动绕组短路）"]}]}'
        )
        source = (
            "故障码F01630。故障现象为制动控制出错。"
            "10、11表示打开制动过程出错；故障值为20（制动绕组短路）。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("打开制动过程出错", "制动绕组短路"), result.records[0].causes)
        cause_quotes = [
            span.quote
            for span in result.evidence_spans
            if span.field is EvidenceField.CAUSE
        ]
        self.assertEqual(["打开制动过程出错", "制动绕组短路"], cause_quotes)

    def test_diagnostic_index_is_not_a_candidate_cause(self):
        response = (
            '{"items":[{"fault_code":"F01600","description":"监控通道故障",'
            '"causes":["1~999表示交叉比较数据编号"]}]}'
        )
        source = (
            "故障代码F01600。故障现象为监控通道故障。"
            "关联故障值r0949（1~999表示交叉比较数据编号）。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual((), result.records[0].causes)
        cause_spans = [
            span for span in result.evidence_spans if span.field is EvidenceField.CAUSE
        ]
        self.assertEqual([], cause_spans)

    def test_conditional_causes_are_readable_and_shared_evidence_is_deduplicated(self):
        response = (
            '{"items":[{"fault_code":"A01631","description":"制动配置无意义",'
            '"causes":["不存在电机抱闸且SBC使能",'
            '"电机抱闸控制，B且SBC使能"]}]}'
        )
        source = (
            "故障代码A01631。故障现象为制动配置无意义。"
            "若p1215=0（不存在电机抱闸）且p9602=1（SBC使能），"
            "若p1215=3（电机抱闸控制，B）且p9602=1。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(
            ("不存在电机抱闸且SBC使能", "电机抱闸控制，B且SBC使能"),
            result.records[0].causes,
        )
        cause_spans = [
            span for span in result.evidence_spans if span.field is EvidenceField.CAUSE
        ]
        self.assertEqual(
            ["不存在电机抱闸", "SBC使能", "电机抱闸控制，B"],
            [span.quote for span in cause_spans],
        )

    def test_explicit_component_declarations_recover_missing_related_components(self):
        response = (
            '{"items":[{"fault_code":"A01016","description":"固件被修改",'
            '"component":"","related_components":[]}]}'
        )
        source = "故障代码A01016：组件为无（关联控制单元存储器）。故障现象为固件被修改。"

        result = self._adapter(response).extract(source)

        self.assertIsNone(result.records[0].component)
        self.assertEqual(("控制单元存储器",), result.records[0].related_components)
        self.assertTrue(
            any(
                span.field is EvidenceField.RELATED_COMPONENT
                and span.quote == "控制单元存储器"
                for span in result.evidence_spans
            )
        )

    def test_driver_object_declaration_does_not_become_component(self):
        response = (
            '{"items":[{"fault_code":"A01006",'
            '"description":"DRIVE-CLiQ组件的固件需要升级",'
            '"component":"DRIVE-CLiQ组件","related_components":[]}]}'
        )
        source = (
            "故障代码A01006：驱动对象为无（关联DRIVE-CLiQ组件及编码器模块）。"
            "故障现象为DRIVE-CLiQ组件的固件需要升级。"
        )

        result = self._adapter(response).extract(source)

        self.assertIsNone(result.records[0].component)
        self.assertEqual(
            ("DRIVE-CLiQ组件", "编码器模块"),
            result.records[0].related_components,
        )
        self.assertTrue(
            any(
                span.field is EvidenceField.DRIVER_OBJECT_DECLARATION
                and span.quote == "驱动对象为无"
                for span in result.evidence_spans
            )
        )

    def test_whitespace_normalized_component_uses_earliest_declaration(self):
        response = (
            '{"items":[{"fault_code":"A01006",'
            '"description":"DRIVE-CLiQ组件的固件需要升级（含编码器模块）",'
            '"component":"","related_components":["DRIVE-CLiQ组件","编码器模块"]}]}'
        )
        source = (
            "故障代码A01006：驱动对象为无（关联DRIVE-CLiQ组件及编码\n"
            "器模块）。故障现象为DRIVE-CLiQ组件的固件需要升级（含编码器模块）。"
        )

        result = self._adapter(response).extract(source)

        related_quotes = [
            span.quote
            for span in result.evidence_spans
            if span.field is EvidenceField.RELATED_COMPONENT
        ]
        self.assertEqual(["DRIVE-CLiQ组件", "编码\n器模块"], related_quotes)

    def test_compact_conditional_cause_keeps_multiple_literal_evidence_parts(self):
        response = (
            '{"items":[{"fault_code":"A01631","description":"制动配置无意义",'
            '"causes":["不存在电机抱闸且SBC使能"]}]}'
        )
        source = (
            "故障代码A01631：故障现象为制动配置无意义。"
            "若p1215=0（不存在电机抱闸）且p9602=1（SBC使能）。"
        )

        result = self._adapter(response).extract(source)

        cause_quotes = [
            span.quote
            for span in result.evidence_spans
            if span.field is EvidenceField.CAUSE
        ]
        self.assertEqual(["不存在电机抱闸", "SBC使能"], cause_quotes)

    def test_explicit_causal_phrase_is_augmented_and_grounded(self):
        response = (
            '{"items":[{"fault_code":"A01013","description":"风扇寿命到期",'
            '"component":"控制单元","causes":[]}]}'
        )
        source = (
            "故障代码A01013。组件为控制单元。故障现象为风扇寿命到期。"
            "处理建议：更换风扇，避免因散热不良导致二次故障。"
        )

        result = self._adapter(response).extract(source)

        record = result.records[0]
        self.assertEqual((), record.causes)
        cause_spans = [span for span in result.evidence_spans if span.field is EvidenceField.CAUSE]
        self.assertEqual([], cause_spans)

    def test_preventive_environment_condition_can_remain_a_current_fault_scenario(self):
        response = (
            '{"items":[{"fault_code":"F01009","description":"控制单元过热",'
            '"component":"控制单元","causes":[],"parameters":[]}]} '
        )
        source = (
            "故障代码F01009。故障现象为控制单元过热。"
            "处理建议：避免环境温度过高导致控制单元过热。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("环境温度过高",), result.records[0].causes)

    def test_explicit_cause_augmentation_stays_with_the_matching_fault_code(self):
        response = (
            '{"items":['
            '{"fault_code":"F01001","description":"故障一","causes":[]},'
            '{"fault_code":"F01002","description":"故障二","causes":[]}'
            ']}'
        )
        source = (
            "故障代码F01001。故障现象为故障一。因温度过高导致故障一。"
            "故障代码F01002。故障现象为故障二。因通讯中断导致故障二。"
        )

        result = self._adapter(response).extract(source)

        self.assertEqual(("温度过高",), result.records[0].causes)
        self.assertEqual(("通讯中断",), result.records[1].causes)

    def test_legacy_projection_preserves_evidence_span_fields(self):
        response = '{"items":[{"description":"pump stopped"}]}'
        source = "Problem: pump stopped"
        result = self._adapter(response).extract(source)

        projected = _evidence_span_to_legacy_dict(result.evidence_spans[0])

        self.assertEqual(projected["field"], "description")
        self.assertEqual(projected["quote"], "pump stopped")
        self.assertEqual(source[projected["start"] : projected["end"]], projected["quote"])


if __name__ == "__main__":
    unittest.main()
