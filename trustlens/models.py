"""数据模型：评测报告与各维度得分。所有模型可序列化为 JSON（数据即审计日志）。"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Finding:
    """一条检查发现（问题或警告）。"""
    severity: str  # "critical" | "warning" | "info"
    code: str      # 如 "SEC-INJECTION-001"
    message: str


@dataclass
class ToolInfo:
    name: str
    description: str = ""
    schema: dict = field(default_factory=dict)


@dataclass
class DimensionScore:
    """单个维度得分，0–100。"""
    value: float
    findings: list[Finding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServerReport:
    """一份完整评测报告。"""
    name: str
    server_type: str
    source: str
    evaluated_at: float = field(default_factory=time.time)
    engine_version: str = "0.1.0"
    ok: bool = False  # 是否完成评测（False 表示无法启动/握手失败）
    error: str = ""
    total_score: float = 0.0
    grade: str = "F"
    dimensions: dict[str, DimensionScore] = field(default_factory=dict)
    tools: list[ToolInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ServerReport":
        dims = {
            k: DimensionScore(
                value=v["value"],
                findings=[Finding(**f) for f in v.get("findings", [])],
                details=v.get("details", {}),
            )
            for k, v in d.get("dimensions", {}).items()
        }
        return cls(
            name=d["name"],
            server_type=d.get("server_type", "mcp-server"),
            source=d.get("source", ""),
            evaluated_at=d.get("evaluated_at", 0.0),
            engine_version=d.get("engine_version", "0.1.0"),
            ok=d.get("ok", False),
            error=d.get("error", ""),
            total_score=d.get("total_score", 0.0),
            grade=d.get("grade", "F"),
            dimensions=dims,
            tools=[ToolInfo(**t) for t in d.get("tools", [])],
        )


def grade_of(score: float) -> str:
    """分数 → 等级。"""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"
