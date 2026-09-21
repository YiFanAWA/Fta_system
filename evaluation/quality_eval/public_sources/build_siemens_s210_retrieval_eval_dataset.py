"""Build a stratified Chinese retrieval evaluation set from the frozen S210 Gold.

The query set is intentionally independent from the Gold records.  It derives
relevance labels from fault codes already present in Gold, but does not modify
Gold content or claim human query annotation.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


QUERY_SPECS: tuple[dict[str, Any], ...] = (
    # Exact fault-code queries.
    {"query_id": "Q001", "query": "A01006 是什么故障？", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["A01006"], "ambiguity": "none"},
    {"query_id": "Q002", "query": "请查询故障码 F01033。", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["F01033"], "ambiguity": "none"},
    {"query_id": "Q003", "query": "F07412 对应什么故障？", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},
    {"query_id": "Q004", "query": "A01784 的故障信息是什么？", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["A01784"], "ambiguity": "none"},
    {"query_id": "Q005", "query": "查一下 F30002。", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["F30002"], "ambiguity": "none"},
    {"query_id": "Q006", "query": "F01630 是制动相关的哪类故障？", "query_type": "fault_code", "difficulty": "easy", "relevant_fault_codes": ["F01630"], "ambiguity": "none"},

    # Symptom/title queries, including deliberately duplicated descriptions.
    {"query_id": "Q007", "query": "控制单元温度过高是什么报警？", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["A05003", "A30034", "F30036"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q008", "query": "直流母线过压有哪些故障？", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["A30502", "F30002"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q009", "query": "系统报制动控制错误。", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["F01630", "F07930", "F30630"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q010", "query": "出现安全限速超限，应该查哪些故障？", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["A01714", "A30714"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q011", "query": "循环数据传输错误对应哪些故障码？", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["F31835", "F31845", "F31885"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q012", "query": "驱动器提示 STO 已启动。", "query_type": "symptom", "difficulty": "medium", "relevant_fault_codes": ["F01600", "F01700", "F30600", "F30700"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q013", "query": "故障现象是监控通道故障。", "query_type": "symptom", "difficulty": "hard", "relevant_fault_codes": ["A01711", "A30711", "F01611", "F30611"], "ambiguity": "insufficient_query_context"},
    {"query_id": "Q014", "query": "控制系统出现内部软件错误。", "query_type": "symptom", "difficulty": "hard", "relevant_fault_codes": ["F01000", "F01002", "F01015", "F01649", "F30649", "F30950", "F31950", "N01004"], "ambiguity": "insufficient_query_context"},
    {"query_id": "Q015", "query": "电机换向角不正确，可能是哪条故障？", "query_type": "symptom", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},

    # Cause/context queries.
    {"query_id": "Q016", "query": "风扇使用寿命到期会触发什么报警？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["A30042"], "ambiguity": "none"},
    {"query_id": "Q017", "query": "固件文件校验和错误或文件缺失对应什么故障？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["A01016"], "ambiguity": "none"},
    {"query_id": "Q018", "query": "参考参数等于 0 会导致哪个单位换算故障？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["F01033"], "ambiguity": "none"},
    {"query_id": "Q019", "query": "电机抱闸不存在但 SBC 被启用，会出现什么报警？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["A01631"], "ambiguity": "none"},
    {"query_id": "Q020", "query": "两个安全监控通道的参数不一致会对应什么故障？", "query_type": "cause", "difficulty": "medium", "relevant_fault_codes": ["A01711", "A30711", "F01611", "F30611"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q021", "query": "如果电机编码器损坏，应该检索哪类换向角故障？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},
    {"query_id": "Q022", "query": "没有选择安全功能却执行 SI 参数复制，会导致什么故障？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["F01663"], "ambiguity": "none"},
    {"query_id": "Q023", "query": "驱动对象之间的交叉比较数据不一致，可能是哪类安全故障？", "query_type": "cause", "difficulty": "medium", "relevant_fault_codes": ["F01600", "F01611", "F30600", "F30611"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q024", "query": "电机相序错误或编码器磁极位置调整不正确，会触发什么故障？", "query_type": "cause", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},

    # Remedy/action queries.  These are intentionally not treated as causes.
    {"query_id": "Q025", "query": "需要升级 DRIVE-CLiQ 组件固件，应该查看哪些故障？", "query_type": "remedy", "difficulty": "medium", "relevant_fault_codes": ["A01006", "A01304"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q026", "query": "更换风扇后要处理寿命计数器，相关报警是什么？", "query_type": "remedy", "difficulty": "easy", "relevant_fault_codes": ["A30042"], "ambiguity": "none"},
    {"query_id": "Q027", "query": "把单位换算的参考参数设置为非零，解决的是哪个故障？", "query_type": "remedy", "difficulty": "easy", "relevant_fault_codes": ["F01033"], "ambiguity": "none"},
    {"query_id": "Q028", "query": "检查电机相序并重新调整编码器，适用于哪条故障？", "query_type": "remedy", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},
    {"query_id": "Q029", "query": "检查 p9501 和 p9601 后重新执行安全参数复制，针对什么故障？", "query_type": "remedy", "difficulty": "easy", "relevant_fault_codes": ["F01663"], "ambiguity": "none"},

    # Component/context queries.
    {"query_id": "Q030", "query": "控制单元和液压模块相关的 STO 监控通道故障有哪些？", "query_type": "component", "difficulty": "medium", "relevant_fault_codes": ["F01611", "F30611"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q031", "query": "电机模块和制动组件的 SBC 配置故障是什么？", "query_type": "component", "difficulty": "easy", "relevant_fault_codes": ["A01631"], "ambiguity": "none"},
    {"query_id": "Q032", "query": "编码器相关的电机换向角故障是什么？", "query_type": "component", "difficulty": "easy", "relevant_fault_codes": ["F07412"], "ambiguity": "none"},
    {"query_id": "Q033", "query": "DRIVE-CLiQ 组件固件需要升级的报警有哪些？", "query_type": "component", "difficulty": "medium", "relevant_fault_codes": ["A01006", "A01304"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q034", "query": "控制单元内部软件错误有哪些可能的故障码？", "query_type": "component", "difficulty": "hard", "relevant_fault_codes": ["F01000", "F01002", "F01015", "F01649", "F30649", "F30950", "F31950", "N01004"], "ambiguity": "insufficient_query_context"},

    # Exact parameter / diagnostic identifier queries.
    {"query_id": "Q035", "query": "p7829 是哪个固件更新报警的参数？", "query_type": "parameter", "difficulty": "easy", "relevant_fault_codes": ["A01006", "A01304"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q036", "query": "p9542 与哪条安全监控报警有关？", "query_type": "parameter", "difficulty": "easy", "relevant_fault_codes": ["A01711"], "ambiguity": "none"},
    {"query_id": "Q037", "query": "p2000 相关的单位换算故障有哪些？", "query_type": "parameter", "difficulty": "medium", "relevant_fault_codes": ["F01033", "F01034"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q038", "query": "p1215 涉及哪些抱闸或制动控制故障？", "query_type": "parameter", "difficulty": "hard", "relevant_fault_codes": ["A01631", "F01630", "F07930", "F07935"], "ambiguity": "ambiguous_description"},
    {"query_id": "Q039", "query": "p9602 是哪些安全功能故障的关联参数？", "query_type": "parameter", "difficulty": "hard", "relevant_fault_codes": ["A01631", "A01785", "F01611", "F30611"], "ambiguity": "ambiguous_description"},

    # Hard ambiguity / insufficient-context cases.
    {"query_id": "Q040", "query": "监控通道异常，能不能直接确定唯一故障码？", "query_type": "ambiguous_description", "difficulty": "hard", "relevant_fault_codes": ["A01711", "A30711", "F01611", "F30611"], "ambiguity": "insufficient_query_context"},
    {"query_id": "Q041", "query": "内部软件错误，应该返回哪一个故障？", "query_type": "ambiguous_description", "difficulty": "hard", "relevant_fault_codes": ["F01000", "F01002", "F01015", "F01649", "F30649", "F30950", "F31950", "N01004"], "ambiguity": "insufficient_query_context"},
    {"query_id": "Q042", "query": "制动控制错误但没有更多上下文，候选故障有哪些？", "query_type": "ambiguous_description", "difficulty": "hard", "relevant_fault_codes": ["F01630", "F07930", "F30630"], "ambiguity": "insufficient_query_context"},
)


def build(gold: dict[str, Any]) -> dict[str, Any]:
    records = [record for sample in gold.get("samples", []) for record in sample.get("gold_records", [])]
    available = {str(record.get("fault_code")) for record in records if record.get("fault_code")}
    if len(available) != len(records):
        raise ValueError("Gold must have one unique fault_code per record")

    queries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for raw in QUERY_SPECS:
        query = dict(raw)
        query_id = str(query["query_id"])
        if query_id in seen_ids:
            raise ValueError(f"duplicate query_id: {query_id}")
        seen_ids.add(query_id)
        relevant = [str(code) for code in query["relevant_fault_codes"]]
        if not relevant or not set(relevant).issubset(available):
            missing = sorted(set(relevant) - available)
            raise ValueError(f"{query_id} has unavailable fault codes: {missing}")
        query["relevance_policy"] = "any_relevant_in_top_k"
        query["gold_source"] = "frozen_siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20"
        queries.append(query)

    counts = Counter(query["query_type"] for query in queries)
    difficulty = Counter(query["difficulty"] for query in queries)
    ambiguity = Counter(query["ambiguity"] for query in queries)
    return {
        "dataset_info": {
            "name": "siemens_s210_retrieval_evaluation_v1",
            "version": "2026-09-21",
            "source_gold": "evaluation/quality_eval/datasets/siemens_s210_public_fault_final_gold_ai_assisted_2026-09-20.json",
            "gold_sample_count": len(records),
            "query_count": len(queries),
            "label_status": "ai_assisted_benchmark_derived_from_frozen_gold",
            "annotation_authority": "derived_relevance_labels; not human_query_annotation",
            "ranking_unit": "fault_code",
            "multi_answer_policy": "a query is a hit when any relevant_fault_codes item appears in top_k",
            "metrics": ["Recall@1", "Recall@3", "Recall@5", "MRR"],
            "query_types": dict(counts),
            "difficulty_counts": dict(difficulty),
            "ambiguity_counts": dict(ambiguity),
            "stages": [
                "query_normalization",
                "exact_fault_code_and_parameter_retrieval",
                "description_and_cause_vector_retrieval",
                "candidate_fusion",
                "fault_code_aggregation",
                "reranking",
            ],
            "notes": [
                "This benchmark freezes Gold and must not be used to rewrite Gold labels.",
                "Ambiguous queries intentionally allow multiple relevant fault codes.",
                "Retrieval errors must be classified as ambiguity or insufficient_query_context before changing embeddings.",
            ],
        },
        "queries": queries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    result = build(gold)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["dataset_info"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
