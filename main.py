from ai_module import (
	analyze_fault_tree_report,
	generate_failure_events,
	review_fault_tree_draft,
)
from kg_builder import create_failure_nodes
from kg_reasoner import get_failure_paths
from fta_generator import build_fault_tree
from xml_exporter import export_xml
from visualizer import export_visuals
from utils import log, save_json, save_text


def _parse_manual_failures(text):
	items = [part.strip() for part in text.split(",") if part.strip()]
	failures = []

	for item in items:
		if ":" in item:
			name, prob_text = item.split(":", 1)
			name = name.strip()
			prob_text = prob_text.strip()
			try:
				probability = float(prob_text)
			except ValueError:
				probability = None
		else:
			name = item
			probability = None

		if not name:
			continue

		failures.append(
			{
				"name": name,
				"probability": probability,
				"gate": "OR",
				"causes": []
			}
		)

	return failures


def _collect_user_inputs():
	system = input("请输入系统名称 [Drone]: ").strip() or "Drone"
	top_event = input("请输入顶事件 [Drone Crash]: ").strip() or "Drone Crash"
	mode = input("故障来源: 1-AI生成 2-手动输入 [1]: ").strip() or "1"
	return system, top_event, mode


def _save_analysis_report(report):
	save_json(report, "fta_analysis_report.json")

	lines = [
		"# FTA 分析报告",
		"",
		f"顶事件分析: {report.get('top_event_analysis', '')}",
		"",
		"## 关键路径",
	]

	for item in report.get("key_paths", []):
		lines.append(
			f"- {item.get('path', '')} | 风险: {item.get('risk_level', '')} | 原因: {item.get('reason', '')}"
		)

	lines.append("")
	lines.append("## 薄弱环节")
	for item in report.get("weak_links", []):
		lines.append(
			f"- {item.get('component', '')} | 严重度: {item.get('severity', '')} | 原因: {item.get('reason', '')}"
		)

	lines.append("")
	lines.append("## 改进建议")
	for item in report.get("recommended_actions", []):
		lines.append(
			f"- {item.get('priority', '')}: {item.get('action', '')} | 预期效果: {item.get('expected_effect', '')}"
		)

	lines.append("")
	lines.append("## 验证计划")
	for item in report.get("verification_plan", []):
		lines.append(
			f"- 任务: {item.get('task', '')} | 方法: {item.get('method', '')} | 通过标准: {item.get('pass_criteria', '')}"
		)

	save_text("\n".join(lines), "fta_analysis_report.txt")


def _save_draft_review(review):
	save_json(review, "fta_draft_review.json")

	lines = [
		"# FTA 初稿检验报告",
		"",
		f"总体评分: {review.get('overall_score', '')}",
		f"总结: {review.get('summary', '')}",
		"",
		"## 不足项",
	]

	for item in review.get("deficiencies", []):
		lines.append(
			f"- [{item.get('id', '')}] {item.get('title', '')} | 严重度: {item.get('severity', '')} | 位置: {item.get('location', '')}"
		)
		lines.append(
			f"  问题: {item.get('issue', '')} | 影响: {item.get('impact', '')} | 建议: {item.get('suggestion', '')}"
		)

	lines.append("")
	lines.append("## 建议补充事件")
	for event in review.get("missing_events", []):
		lines.append(f"- {event}")

	lines.append("")
	lines.append("## 门逻辑调整建议")
	for item in review.get("gate_adjustments", []):
		lines.append(
			f"- 节点: {item.get('node', '')} | 当前: {item.get('current_gate', '')} -> 建议: {item.get('recommended_gate', '')} | 理由: {item.get('reason', '')}"
		)

	lines.append("")
	lines.append("## 概率问题说明")
	for item in review.get("probability_notes", []):
		lines.append(
			f"- 节点: {item.get('node', '')} | 问题: {item.get('problem', '')} | 建议: {item.get('suggestion', '')}"
		)

	lines.append("")
	lines.append("## 下一步工作")
	for item in review.get("next_steps", []):
		lines.append(
			f"- {item.get('priority', '')}: {item.get('task', '')} | 产出: {item.get('output', '')}"
		)

	save_text("\n".join(lines), "fta_draft_review.txt")


def main():
	system, top_event, mode = _collect_user_inputs()

	if mode == "2":
		manual_text = input(
			"请输入故障列表(逗号分隔，支持 名称:概率，例如 电机失效:0.12, 电池异常:0.09): "
		).strip()
		failures = _parse_manual_failures(manual_text)
		if not failures:
			log("手动输入故障为空或格式无效")
			return
		log(f"手动输入顶层故障数: {len(failures)}")
	else:
		try:
			log("AI分析系统...")
			failures = generate_failure_events(system)
			log(f"AI返回顶层故障数: {len(failures)}")
		except Exception as exc:
			log(f"AI分析失败: {exc}")
			return

	try:
		log("构建知识图谱(含层级关系)...")
		create_failure_nodes(system, failures)
	except Exception as exc:
		log(f"知识图谱构建失败: {exc}")
		return

	try:
		log("图谱推理(读取故障及子故障)...")
		events = get_failure_paths(system)
		log(f"图谱推理返回顶层事件数: {len(events)}")
	except Exception as exc:
		log(f"图谱推理失败: {exc}")
		return

	try:
		log("生成多层故障树...")
		tree = build_fault_tree(top_event, events)
		export_xml(tree)
		visuals = export_visuals(tree)
	except Exception as exc:
		log(f"故障树导出失败: {exc}")
		return

	log("FTA XML 已生成: fault_tree.xml")
	log(f"FTA DOT 已生成: {visuals['dot']}")
	if visuals["png"]:
		log(f"FTA PNG 已生成: {visuals['png']}")
	else:
		log("未检测到Graphviz(dot)，已跳过PNG生成")

	try:
		log("AI生成故障树分项分析与后续工作建议...")
		report = analyze_fault_tree_report(system, top_event, tree)
		_save_analysis_report(report)
		log("分析报告已生成: fta_analysis_report.json / fta_analysis_report.txt")
	except Exception as exc:
		log(f"分析报告生成失败: {exc}")

	try:
		log("AI检验初稿故障树并输出不足项...")
		review = review_fault_tree_draft(system, top_event, tree)
		_save_draft_review(review)
		log("初稿检验报告已生成: fta_draft_review.json / fta_draft_review.txt")
	except Exception as exc:
		log(f"初稿检验失败: {exc}")


if __name__ == "__main__":
    main()