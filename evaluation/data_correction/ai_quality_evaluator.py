import argparse
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import openai


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend-python"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS


NOISE_CAUSE_RE = re.compile(r"^(?:[:：%\s].*|.*bin[\"'”’)]?.*|检查.*|重新.*|请.*|见.*)$", re.IGNORECASE)
TOKEN_RE = re.compile(r"[A-Za-z0-9\u4e00-\u9fff]+")


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _extract_json_object(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty LLM response")

    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")

    payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("JSON is not object")
    return payload


def _is_noise_cause(text: str) -> bool:
    val = _safe_text(text)
    if len(val) < 2:
        return True
    if NOISE_CAUSE_RE.match(val):
        return True
    if not TOKEN_RE.search(val):
        return True
    return False


def _load_records(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("records", [])
    elif isinstance(payload, list):
        records = payload
    else:
        records = []

    return [x for x in records if isinstance(x, dict)]


def _rule_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    if total == 0:
        return {
            "record_count": 0,
            "completeness_rate": 0.0,
            "records_with_causes_rate": 0.0,
            "avg_causes_per_record": 0.0,
            "avg_parameters_per_record": 0.0,
            "noise_cause_rate": 0.0,
            "fault_code_format_rate": 0.0,
        }

    required_ok = 0
    with_causes = 0
    cause_count = 0
    param_count = 0
    noise_count = 0
    fault_code_ok = 0

    for rec in records:
        code = _safe_text(rec.get("fault_code"))
        comp = _safe_text(rec.get("component"))
        desc = _safe_text(rec.get("description"))
        causes = rec.get("causes", []) if isinstance(rec.get("causes"), list) else []
        params = rec.get("parameters", []) if isinstance(rec.get("parameters"), list) else []

        if code and comp and desc:
            required_ok += 1

        if re.fullmatch(r"[A-Z]\d{5}", code or ""):
            fault_code_ok += 1

        if causes:
            with_causes += 1

        cause_count += len(causes)
        param_count += len(params)

        for c in causes:
            if _is_noise_cause(str(c)):
                noise_count += 1

    return {
        "record_count": total,
        "completeness_rate": round(required_ok / total, 4),
        "records_with_causes_rate": round(with_causes / total, 4),
        "avg_causes_per_record": round(cause_count / total, 4),
        "avg_parameters_per_record": round(param_count / total, 4),
        "noise_cause_rate": round((noise_count / cause_count) if cause_count else 0.0, 4),
        "fault_code_format_rate": round(fault_code_ok / total, 4),
    }


def _build_sample(records: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if len(records) <= limit:
        return records
    random.seed(42)
    return random.sample(records, limit)


def _call_llm(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY / QWEN_API_KEY 未配置")

    kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_API_BASE:
        kwargs["base_url"] = OPENAI_API_BASE

    if hasattr(openai, "OpenAI"):
        client = openai.OpenAI(**kwargs)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=OPENAI_TIMEOUT_SECONDS,
        )
        return (response.choices[0].message.content if response.choices else "") or ""

    openai.api_key = OPENAI_API_KEY
    if OPENAI_API_BASE:
        openai.api_base = OPENAI_API_BASE
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        request_timeout=OPENAI_TIMEOUT_SECONDS,
    )
    return response["choices"][0]["message"]["content"]


def _ai_assess(records: List[Dict[str, Any]], metrics: Dict[str, Any], sample_limit: int) -> Dict[str, Any]:
    sample = _build_sample(records, sample_limit)
    prompt = (
        "你是工业故障知识库质量评审员。请根据给定样本和规则指标进行数据质量评估，"
        "只输出一个JSON对象，不要输出解释文本。\n\n"
        "输出格式:\n"
        "{\n"
        "  \"overall_score\": 0-100整数,\n"
        "  \"dimension_scores\": {\"completeness\":0-100,\"consistency\":0-100,\"noise\":0-100,\"usability\":0-100},\n"
        "  \"key_issues\": [{\"severity\":\"high|medium|low\",\"issue\":\"...\",\"evidence\":\"...\",\"suggestion\":\"...\"}],\n"
        "  \"high_value_corrections\": [{\"fault_code\":\"...\",\"action\":\"...\",\"reason\":\"...\"}],\n"
        "  \"summary\": \"一句话总结\"\n"
        "}\n\n"
        f"规则指标:\n{json.dumps(metrics, ensure_ascii=False)}\n\n"
        f"样本数据:\n{json.dumps(sample, ensure_ascii=False)}\n"
    )

    raw = _call_llm(prompt)
    return _extract_json_object(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-assisted quality evaluation for corrected KB data")
    parser.add_argument("--input", required=True, help="Path to KB json")
    parser.add_argument("--output", required=True, help="Path to output quality report json")
    parser.add_argument("--sample-limit", type=int, default=20, help="How many records to send to AI")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    records = _load_records(in_path)
    metrics = _rule_metrics(records)

    ai_result: Dict[str, Any]
    ai_error = ""
    try:
        ai_result = _ai_assess(records, metrics, args.sample_limit)
    except Exception as exc:
        ai_result = {}
        ai_error = str(exc)

    report = {
        "input": str(in_path),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "model": OPENAI_MODEL,
        "base_url": OPENAI_API_BASE,
        "rule_metrics": metrics,
        "ai_assessment": ai_result,
        "ai_error": ai_error,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"records={len(records)}")
    print(f"output={out_path}")
    print(f"ai_ok={bool(ai_result)}")


if __name__ == "__main__":
    main()
