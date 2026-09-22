"""Run the deterministic boundary layer against named-expert Gold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend-python"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag.response_policy import ResponsePolicyLayer  # noqa: E402
from validate_rag_boundary_expert_gold import load, score_policy, validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    gold = load(Path(args.gold))
    errors = validate(gold)
    if errors:
        raise SystemExit("expert Gold is not valid: " + "; ".join(errors))

    layer = ResponsePolicyLayer()
    actual_rows: list[dict[str, Any]] = []
    for row in gold["rows"]:
        decision = layer.assess_boundary(question=str(row["question"]), contexts=[object()])
        actual_rows.append(
            {
                "query_id": row["query_id"],
                "actual_knowledge_status": decision.knowledge_status,
                "decision": decision.to_dict(),
            }
        )

    metrics = score_policy(gold, actual_rows)
    report = {
        "dataset": gold["dataset_info"].get("name"),
        "status": "engineering_boundary_policy_against_expert_gold",
        "expert_validated": True,
        "query_count": len(actual_rows),
        "metrics": metrics,
        "results": actual_rows,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"query_count": report["query_count"], "metrics": metrics}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
