"""评测引擎：对一个能力单元执行完整评测，产出 ServerReport。"""
from __future__ import annotations

import re

from . import checks, score
from .llm import ToolUseProvider, default_providers
from .models import ServerReport, ToolInfo
from .protocol import McpStdioClient, ProtocolError

MAX_TOOLS_TO_CALL = 5
CALLS_PER_TOOL = 2
# 连续 N 次协议超时即判定该服务器对真实调用不可用，跳过剩余探针。
# 否则病理服务器每台可烧 calls×timeout（如 10×90s）的墙钟，拉爆 CI。
MAX_CONSECUTIVE_TIMEOUTS = 2


def _dummy_arguments(schema: dict) -> dict:
    """按 inputSchema 生成最小合法参数。"""
    args: dict = {}
    props = (schema or {}).get("properties", {})
    required = (schema or {}).get("required", [])
    for name in required:
        ptype = (props.get(name) or {}).get("type", "string")
        args[name] = {"string": "trustlens-probe", "integer": 1, "number": 1,
                      "boolean": True, "array": [], "object": {}}.get(ptype, "trustlens-probe")
    return args


def _finalize_failure(report: ServerReport, error: str) -> ServerReport:
    """启动/握手失败的统一收尾：四个维度按失败计分。"""
    report.error = error
    report.dimensions = {
        "functionality": score.functionality_score(False, 0, 0, []),
        "reliability": score.reliability_score([], 0, 0),
        "security": score.security_score([]),
        "compatibility": score.compatibility_score([]),
    }
    report.total_score, report.grade = score.total_score(report.dimensions)
    return report


def evaluate_server(name: str, command: list[str], server_type: str = "mcp-server",
                    source: str = "", providers: list[ToolUseProvider] | None = None,
                    timeout: float = 15.0, quick: bool = False) -> ServerReport:
    """完整评测一个服务器：握手 → 列工具 → 静态检查 → 试调用 → 跨模型评估 → 计分。

    quick=True：减探针量（2 工具 × 1 次），用于每周快速复检（够判断是否退化）。
    """
    max_tools = 2 if quick else MAX_TOOLS_TO_CALL
    calls_per_tool = 1 if quick else CALLS_PER_TOOL
    report = ServerReport(name=name, server_type=server_type, source=source)
    providers = providers if providers is not None else default_providers()

    try:
        client = McpStdioClient(command, timeout=timeout, hard_timeout=max(300.0, timeout * 3))
    except OSError as e:
        return _finalize_failure(report, f"无法启动服务器进程: {e}")

    with client:
        try:
            client.initialize()
            raw_tools = client.list_tools()
        except ProtocolError as e:
            return _finalize_failure(report, str(e))

        tools = [ToolInfo(
            name=t.get("name", ""),
            description=t.get("description", "") or "",
            schema=t.get("inputSchema", {}) or {},
        ) for t in raw_tools]
        report.tools = tools

        # 静态检查
        sec_findings = checks.security_scan(tools)
        schema_findings = checks.schema_check(tools)

        # 试调用（功能性 + 可靠性）
        latencies: list[float] = []
        callable_tools = 0
        attempts = failures = 0
        consecutive_timeouts = 0
        for tool in tools[:max_tools]:
            if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
                break
            tool_ok = False
            for _ in range(calls_per_tool):
                if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
                    break
                attempts += 1
                try:
                    result, latency = client.call_tool(tool.name, _dummy_arguments(tool.schema))
                    latencies.append(latency)
                    consecutive_timeouts = 0
                    # MCP 语义错误（isError: true）计为失败：工具被调用但未正确履职
                    if result.get("isError"):
                        failures += 1
                    else:
                        tool_ok = True
                except ProtocolError:
                    failures += 1
                    consecutive_timeouts += 1
            if tool_ok:
                callable_tools += 1

        # 跨模型兼容性
        verdicts: list[tuple[str, str, bool]] = []
        for tool in tools:
            for provider in providers:
                v = provider.judge(tool)
                verdicts.append((v.model, tool.name, v.success))

        report.dimensions = {
            "functionality": score.functionality_score(True, len(tools), callable_tools, schema_findings),
            "reliability": score.reliability_score(latencies, failures, attempts),
            "security": score.security_score(sec_findings),
            "compatibility": score.compatibility_score(verdicts),
        }
        report.total_score, report.grade = score.total_score(report.dimensions)
        report.ok = True
        return report


def apply_compatibility(report: ServerReport, providers: list[ToolUseProvider]) -> ServerReport:
    """只更新跨模型兼容维度（不重跑服务器）——用真实模型评测已存结果的工具清单。"""
    verdicts: list[tuple[str, str, bool]] = []
    for tool in report.tools:
        for provider in providers:
            v = provider.judge(tool)
            verdicts.append((v.model, tool.name, v.success))
    report.dimensions["compatibility"] = score.compatibility_score(verdicts)
    report.total_score, report.grade = score.total_score(report.dimensions)
    return report


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9\-]", "-", name.lower()).strip("-") or "unnamed"
