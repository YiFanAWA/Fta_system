"""Mark a finalized dataset with the authorized AI-assisted review authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def mark(dataset: dict[str, Any], decisions: dict[str, Any]) -> dict[str, Any]:
    result = dict(dataset)
    info = dict(result.get("dataset_info") or {})
    if info.get("import_ready") is not True:
        raise ValueError("dataset must pass finalizer before AI-assisted marking")
    info["label_status"] = "ai_assisted_expert_reviewed"
    info["review_authority"] = "user_authorized_ai_assisted_expert_review"
    info["reviewer_identity_policy"] = (
        "审核由多个AI子agent完成，用户已明确授权按本项目审核专家处理；不等同于真人领域专家审核。"
    )
    info["review_rounds"] = decisions.get("review_rounds") or []
    info["merge_summary"] = decisions.get("merge_summary") or {}
    result["dataset_info"] = info
    result["review_authority"] = info["review_authority"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-json", required=True, type=Path)
    parser.add_argument("--decisions-json", required=True, type=Path)
    args = parser.parse_args()
    dataset = json.loads(args.dataset_json.read_text(encoding="utf-8"))
    decisions = json.loads(args.decisions_json.read_text(encoding="utf-8"))
    result = mark(dataset, decisions)
    args.dataset_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["dataset_info"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
