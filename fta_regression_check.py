from __future__ import annotations

from typing import Dict, List

from fta_dot_builder import build_fta


def _check_case(name: str, text: str, top_event: str) -> Dict[str, object]:
    fta = build_fta([{"text": text, "description": text, "top_event": top_event}])

    top = str(fta.get("top") or "")
    fault = str(fta.get("fault") or "")
    causes = fta.get("causes") if isinstance(fta.get("causes"), list) else []

    ok = True
    reasons: List[str] = []

    if not top or top == "系统级故障":
        ok = False
        reasons.append("top invalid")

    if not fault or fault == "未命名故障":
        ok = False
        reasons.append("fault invalid")

    if len(causes) < 2:
        ok = False
        reasons.append("cause count < 2")

    low_causes = [str(c).strip().lower() for c in causes]
    if any(not c for c in low_causes):
        ok = False
        reasons.append("empty cause")

    top_norm = "".join(top.lower().split())
    fault_norm = "".join(fault.lower().split())
    for c in low_causes:
        c_norm = "".join(c.split())
        if c_norm == top_norm or c_norm == fault_norm:
            ok = False
            reasons.append("cause polluted by top/fault")
            break

    return {
        "name": name,
        "ok": ok,
        "reasons": reasons,
        "fta": fta,
    }


def run_regression() -> int:
    cases = [
        {
            "name": "AOCS",
            "top": "卫星姿态失控导致通信天线偏离目标区域超过0.5度",
            "text": "故障报告编号：INC-20260319-AOCS-04。星敏感器输出无效数据，反作用轮转速饱和，姿态发散漂移。",
        },
        {
            "name": "Hydraulic",
            "top": "液压系统关键回路失效",
            "text": "P-204 主油路压力过低报警。主油泵密封件老化破裂，液压油滤芯堵塞，压力传感器零点漂移。",
        },
        {
            "name": "E-Drive",
            "top": "电驱系统硬件故障",
            "text": "驱动系统发生过流告警，电机绝缘老化导致相间击穿，连接器密封不良引起进水腐蚀。",
        },
        {
            "name": "Narrative",
            "top": "关键任务链路中断",
            "text": "系统在轨运行期间出现遥测异常，业务中断，需进行故障树分析。",
        },
    ]

    results = [_check_case(c["name"], c["text"], c["top"]) for c in cases]

    failed = 0
    for r in results:
        if r["ok"]:
            print(f"[PASS] {r['name']}")
        else:
            failed += 1
            print(f"[FAIL] {r['name']} -> {', '.join(r['reasons'])}")
        print(r["fta"])

    print(f"Summary: total={len(results)}, failed={failed}")
    return failed


if __name__ == "__main__":
    raise SystemExit(run_regression())
