"""四维信任分模型（0–100）：功能 35 / 可靠 25 / 安全 25 / 兼容 15。"""
from __future__ import annotations

from .models import DimensionScore, Finding, grade_of

WEIGHTS = {
    "functionality": 0.35,
    "reliability": 0.25,
    "security": 0.25,
    "compatibility": 0.15,
}


def total_score(dimensions: dict[str, DimensionScore]) -> tuple[float, str]:
    total = sum(dimensions[k].value * w for k, w in WEIGHTS.items() if k in dimensions)
    return round(total, 1), grade_of(total)


def functionality_score(handshake_ok: bool, tools_total: int, tools_callable: int,
                        schema_findings: list[Finding]) -> DimensionScore:
    if not handshake_ok:
        return DimensionScore(0.0, [Finding("critical", "FUNC-HANDSHAKE", "协议握手失败")])
    if tools_total == 0:
        return DimensionScore(20.0, schema_findings, {"tools_total": 0})
    callable_ratio = tools_callable / tools_total
    base = 40 + 60 * callable_ratio
    deductions = 5 * sum(1 for f in schema_findings if f.severity == "warning")
    value = max(0.0, min(100.0, base - deductions))
    return DimensionScore(round(value, 1), schema_findings,
                          {"tools_total": tools_total, "tools_callable": tools_callable})


def reliability_score(latencies: list[float], failures: int, attempts: int) -> DimensionScore:
    if attempts == 0:
        return DimensionScore(0.0, [Finding("warning", "REL-NONE", "无可测调用")])
    findings: list[Finding] = []
    failure_rate = failures / attempts
    avg = sum(latencies) / len(latencies) if latencies else float("inf")
    # 延迟分：<=0.5s 满分，>=5s 零分，线性衰减
    latency_score = max(0.0, min(100.0, 100 * (1 - (avg - 0.5) / 4.5))) if latencies else 0.0
    stability_score = 100 * (1 - failure_rate)
    value = round(0.6 * stability_score + 0.4 * latency_score, 1)
    if failure_rate > 0:
        findings.append(Finding("warning", "REL-FAIL", f"调用失败率 {failure_rate:.0%}"))
    return DimensionScore(value, findings, {"avg_latency_s": round(avg, 3) if latencies else None,
                                            "failure_rate": failure_rate, "attempts": attempts})


def security_score(security_findings: list[Finding]) -> DimensionScore:
    critical = sum(1 for f in security_findings if f.severity == "critical")
    warnings = sum(1 for f in security_findings if f.severity == "warning")
    value = max(0.0, 100.0 - 30 * critical - 5 * warnings)
    return DimensionScore(round(value, 1), security_findings, {"critical": critical})


def compatibility_score(verdicts: list[tuple[str, str, bool]]) -> DimensionScore:
    """verdicts: [(model, tool, success)]，按整体成功率计分。"""
    if not verdicts:
        return DimensionScore(0.0, [Finding("info", "COMPAT-NONE", "未执行跨模型评估")])
    success = sum(1 for _, _, ok in verdicts if ok)
    ratio = success / len(verdicts)
    models = sorted({m for m, _, _ in verdicts})
    return DimensionScore(round(100 * ratio, 1), [],
                          {"success_rate": round(ratio, 3), "models": models,
                           "verdicts": len(verdicts)})
