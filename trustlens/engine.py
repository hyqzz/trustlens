"""评测引擎：对一个能力单元执行完整评测，产出 ServerReport。"""
from __future__ import annotations

import re

from . import checks, score
from .llm import ToolUseProvider, default_providers
from .models import ServerReport, ToolInfo
from .protocol import McpStdioClient, ProtocolError

MAX_TOOLS_TO_CALL = 5
CALLS_PER_TOOL = 2


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


def evaluate_server(name: str, command: list[str], server_type: str = "mcp-server",
                    source: str = "", providers: list[ToolUseProvider] | None = None,
                    timeout: float = 15.0) -> ServerReport:
    """完整评测一个服务器：握手 → 列工具 → 静态检查 → 试调用 → 跨模型评估 → 计分。"""
    report = ServerReport(name=name, server_type=server_type, source=source)
    providers = providers if providers is not None else default_providers()

    with McpStdioClient(command, timeout=timeout) as client:
        try:
            client.initialize()
            raw_tools = client.list_tools()
        except ProtocolError as e:
            report.error = str(e)
            report.dimensions = {
                "functionality": score.functionality_score(False, 0, 0, []),
                "reliability": score.reliability_score([], 0, 0),
                "security": score.security_score([]),
                "compatibility": score.compatibility_score([]),
            }
            report.total_score, report.grade = score.total_score(report.dimensions)
            return report

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
        for tool in tools[:MAX_TOOLS_TO_CALL]:
            tool_ok = False
            for _ in range(CALLS_PER_TOOL):
                attempts += 1
                try:
                    _, latency = client.call_tool(tool.name, _dummy_arguments(tool.schema))
                    latencies.append(latency)
                    tool_ok = True
                except ProtocolError:
                    failures += 1
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


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9\-]", "-", name.lower()).strip("-") or "unnamed"
