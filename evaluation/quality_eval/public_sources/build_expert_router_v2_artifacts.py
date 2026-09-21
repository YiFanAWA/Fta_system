"""Build expert-derived Router v2 artifacts without changing production config.

The input is a completed manual-review bundle. Only fields explicitly filled by
the reviewer are promoted into evaluation Gold or the experiment registry. The
generated registry is intentionally separate from backend/config so it cannot
silently change the production Router.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {
    "scope_industrial_drive",
    "scope_aerospace",
    "cross_domain",
    "clarify_first",
}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_ref(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _reviewed_queries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in bundle.get("cross_domain_review", []):
        action = row.get("final_action")
        domain = row.get("human_domain_conclusion")
        sufficiency = row.get("human_sufficiency")
        if not domain or not sufficiency or action not in ALLOWED_ACTIONS:
            continue
        rows.append(
            {
                "query_id": row["query_id"],
                "query": row["query"],
                "query_type": row.get("query_type"),
                "gold_domain": domain,
                "gold_sufficiency": sufficiency,
                "gold_action": action,
                "relevant_entity_ids": row.get("relevant_entity_ids", []),
                "relevant_entity_evidence": row.get("relevant_entity_evidence", []),
                "machine_router_decision": row.get("router_machine_decision"),
                "machine_sufficiency_decision": row.get("sufficiency_machine_decision"),
                "machine_taxonomy_decision": row.get("taxonomy_machine_decision"),
                "review_notes": row.get("human_notes"),
            }
        )
    if not rows:
        raise ValueError("no human-reviewed query labels were found")
    return rows


def _build_gold(bundle: dict[str, Any], review_path: Path, root: Path) -> dict[str, Any]:
    rows = _reviewed_queries(bundle)
    all_queries = bundle.get("all_query_review", [])
    return {
        "dataset_info": {
            "name": "query_sufficiency_gold_v1",
            "version": date.today().isoformat(),
            "purpose": "human-reviewed query domain/sufficiency/action evaluation Gold",
            "review_authority": bundle.get("expert_review", {}),
            "source_review_file": _source_ref(review_path, root),
            "source_review_sha256": _sha256(review_path),
            "reviewed_query_count": len(rows),
            "mixed_domain_query_count": len(all_queries),
            "unreviewed_query_count": max(0, len(all_queries) - len(rows)),
            "gold_coverage": len(rows) / len(all_queries) if all_queries else 0.0,
            "production_use": False,
            "promotion_rule": "Only rows with explicit reviewer domain/sufficiency/action labels are Gold; the remaining benchmark rows stay unreviewed.",
        },
        "label_schema": {
            "gold_domain": ["industrial_drive", "aerospace", "both_or_ambiguous", "cannot_determine"],
            "gold_sufficiency": ["sufficient", "partially_sufficient", "insufficient", "cannot_determine"],
            "gold_action": sorted(ALLOWED_ACTIONS),
            "evidence_requirement": "Each Gold row retains relevant entity evidence and the original machine decisions.",
        },
        "queries": rows,
    }


def _build_registry(bundle: dict[str, Any], review_path: Path, root: Path) -> dict[str, Any]:
    scopes: dict[str, dict[str, Any]] = {}
    reviewed_signal_count = 0
    for row in bundle.get("signal_review", []):
        role = str(row.get("approved_router_role") or "").strip()
        if role not in {"high_signal", "medium_signal"}:
            continue
        scope_id = str(row["scope_id"])
        scope = scopes.setdefault(
            scope_id,
            {
                "domain": row.get("domain", ""),
                "manufacturer": row.get("manufacturer", ""),
                "system": row.get("system", ""),
                "high_signal": [],
                "medium_signal": [],
                "excluded_signal": [],
                "signal_evidence": {},
            },
        )
        term = str(row["term"])
        scope[role].append(term)
        scope["signal_evidence"][term] = {
            "reviewer_judgement": row.get("human_judgement"),
            "approved_router_role": role,
            "notes": row.get("human_notes"),
            "positive_presence_evidence": row.get("positive_presence_evidence", []),
            "registry_status_before_review": row.get("registry_status"),
        }
        reviewed_signal_count += 1

    # Preserve explicit reviewer exclusions as an auditable non-signal list.
    exclusions: dict[str, list[str]] = {}
    for row in bundle.get("signal_review", []):
        role = str(row.get("approved_router_role") or "").strip()
        if role != "不加入":
            continue
        scope_id = str(row["scope_id"])
        exclusions.setdefault(scope_id, []).append(str(row["term"]))
    for scope_id, terms in exclusions.items():
        scopes.setdefault(scope_id, {}).setdefault("excluded_signal", []).extend(terms)

    # These patterns are inherited from the v1 contract; the expert review did
    # not alter identifier syntax, so they remain experiment metadata only.
    for scope_id, scope in scopes.items():
        scope["high_signal"] = sorted(set(scope.get("high_signal", [])), key=str.casefold)
        scope["medium_signal"] = sorted(set(scope.get("medium_signal", [])), key=str.casefold)
        scope["excluded_signal"] = sorted(set(scope.get("excluded_signal", [])), key=str.casefold)
        scope["identifier_patterns"] = [r"\b[AFN]\d{5}\b", r"\b[pr]\d{4,5}\b"]
        if scope_id == "faa_sdr":
            scope["identifier_patterns"].append(r"\bjasc\s*\d{4}\b")

    if reviewed_signal_count == 0:
        raise ValueError("no expert-approved signal entries were found")
    return {
        "registry_info": {
            "name": "domain_signal_registry_v1",
            "version": date.today().isoformat(),
            "status": "expert_review_derived_experiment_only",
            "authority": bundle.get("expert_review", {}),
            "source_review_file": _source_ref(review_path, root),
            "source_review_sha256": _sha256(review_path),
            "reviewed_signal_count": reviewed_signal_count,
            "production_enabled": False,
            "promotion_rule": "Do not replace backend/config/domain_evidence_registry_v1.json until the three-way experiment and regression review pass.",
            "medium_signal_rule": "A medium signal alone does not scope a query; it needs same-scope high signal, an explicit identifier/system match, or human-approved scope evidence.",
            "collision_rule": "Signals from multiple scopes keep the query cross_domain until a higher-confidence disambiguator exists.",
        },
        "scopes": scopes,
    }


def _build_policy(gold: dict[str, Any], registry: dict[str, Any], review_path: Path, root: Path) -> str:
    info = gold["dataset_info"]
    lines = [
        "# Domain Router v2 Policy（专家审核派生，实验版）",
        "",
        "> 本策略仅用于 No Router / Rule Router v1 / Expert Router v2 对比，不直接替换生产 Router。",
        "> 只有刘武在审核文件中明确确认的信号和查询标签进入本版本；未审核查询不作为 Gold。",
        "",
        "## 输入依据",
        "",
        f"- 审核文件：`{_source_ref(review_path, root)}`。",
        f"- 审核信号：{registry['registry_info']['reviewed_signal_count']} 个。",
        f"- 查询 Gold：{info['reviewed_query_count']} / {info['mixed_domain_query_count']} 条，覆盖率 `{info['gold_coverage']:.4f}`。",
        f"- 审核者：{gold['dataset_info']['review_authority'].get('expert_name', '未提供')}。",
        "- 证据要求：每条 Gold 查询保留相关故障实体的原始记录证据；领域词保留原文出现证据或明确标记无直接证据。",
        "",
        "## 信号分类",
        "",
        "| 信号级别 | 路由含义 | 约束 |",
        "|---|---|---|",
        "| high_signal | 强领域/系统信号 | 单一领域命中且无冲突时可缩小 scope |",
        "| medium_signal | 条件领域信号 | 单独出现不能缩小 scope，需同域 high signal 或明确系统/标识符支持 |",
        "| excluded_signal | 专家明确不加入 | 不参与 Router 打分 |",
        "",
        "## 路由决策",
        "",
        "1. 先解析显式故障码、参数、JASC/部件号等 identifier；identifier 命中某一 scope 时，可作为强证据。",
        "2. 统计每个 scope 的 high/medium 信号；只命中一个 scope 的 high signal，且没有跨域冲突时，输出 `scope_<domain>`。",
        "3. 只有 medium signal 时，保持 `cross_domain`，除非同时存在同域 high signal 或明确 system/manufacturer/identifier。",
        "4. 多个 scope 同时出现 high signal 时，输出 `cross_domain`，不得猜测。",
        "5. Router 不修改检索实体、Gold、embedding、RRF、reranker 或前端/API。",
        "",
        "## Query Sufficiency",
        "",
        "- `sufficient`：可以直接检索。",
        "- `partially_sufficient`：可以谨慎检索，但是否先澄清由专家 Gold 的 `gold_action` 决定。",
        "- `insufficient`：原则上输出 `clarify_first`，不强行确定领域。",
        "- `cannot_determine`：保持跨域并记录无法判断原因。",
        "- `clarification precision` 只在专家明确标注的查询 Gold 子集上计算；全量查询的 clarification rate 只是行为统计，不是准确率。",
        "",
        "## 三组实验定义",
        "",
        "| 方案 | 领域处理 | 澄清判断 |",
        "|---|---|---|",
        "| No Router | 321 个实体混合检索 | 不主动澄清 |",
        "| Rule Router v1 | 使用当前 backend v1 已确认注册表 | 使用当前机器 sufficiency evaluator |",
        "| Expert Router v2 | 使用本策略派生 registry；未命中强条件时保持 cross_domain | 使用同一 sufficiency evaluator；Gold 仅用于评估 |",
        "",
        "## 验收指标",
        "",
        "- `WrongDomain@1`：Top1 是否出现错误领域实体。",
        "- `Candidate Recall@20`：正确实体是否进入 Top20 候选池。",
        "- `Clarification Precision`：在专家 Gold 子集上，要求澄清的查询中实际应澄清的比例。",
        "- `Clarification Rate`：所有查询中系统要求补充信息的比例。",
        "- 同时保留 `R@1/R@3/R@5/R@10/R@20/MRR`，防止 Router 降低召回。",
        "",
        "## 禁止事项",
        "",
        "- 不把这份 registry 自动复制到 `backend-python/config`。",
        "- 不把 57 条未审核查询补成 Gold。",
        "- 不用实验结果反向修改 Gold。",
        "- 不因 Router 指标变化直接修改 Generic Retrieval Pipeline。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--gold-output", type=Path, required=True)
    parser.add_argument("--registry-output", type=Path, required=True)
    parser.add_argument("--policy-output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    bundle = _read(args.review)
    gold = _build_gold(bundle, args.review, root)
    registry = _build_registry(bundle, args.review, root)
    policy = _build_policy(gold, registry, args.review, root)
    for path in (args.gold_output, args.registry_output, args.policy_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.gold_output.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.registry_output.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.policy_output.write_text(policy, encoding="utf-8")
    print(json.dumps({
        "reviewed_queries": gold["dataset_info"]["reviewed_query_count"],
        "all_queries": gold["dataset_info"]["mixed_domain_query_count"],
        "reviewed_signals": registry["registry_info"]["reviewed_signal_count"],
        "gold_output": str(args.gold_output),
        "registry_output": str(args.registry_output),
        "policy_output": str(args.policy_output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
