"""静态检查：schema 规范性与安全扫描（工具描述投毒、凭证泄露等）。"""
from __future__ import annotations

import re

from .models import Finding, ToolInfo

# 工具描述投毒 / 提示注入模式（对齐公开研究中的 MCP tool poisoning 特征）
INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "SEC-INJECTION-001", "试图让模型忽略先前指令"),
    (r"disregard\s+(all\s+)?(prior|previous)", "SEC-INJECTION-002", "试图让模型无视先前上下文"),
    (r"do\s+not\s+(tell|inform|show)\s+(the\s+)?user", "SEC-INJECTION-003", "试图对用户隐瞒行为"),
    (r"<\s*(IMPORTANT|SYSTEM|HIDDEN)\s*>", "SEC-INJECTION-004", "描述中夹带伪系统标签"),
    (r"(send|exfiltrate|upload|post).{0,40}(to\s+)?https?://", "SEC-EXFIL-001", "疑似将数据外发到远程地址"),
    (r"(read|cat|open).{0,30}(~?/\.ssh|\.env|id_rsa|credentials)", "SEC-EXFIL-002", "疑似读取本机敏感文件"),
]

# 硬编码凭证模式
CREDENTIAL_PATTERNS: list[tuple[str, str, str]] = [
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}", "SEC-CRED-001", "疑似硬编码凭证"),
    (r"-----BEGIN\s+(RSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----", "SEC-CRED-002", "包含私钥材料"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "SEC-CRED-003", "包含 GitHub 个人令牌"),
    (r"sk-[A-Za-z0-9]{20,}", "SEC-CRED-004", "包含疑似 OpenAI 密钥"),
]


def security_scan(tools: list[ToolInfo]) -> list[Finding]:
    """对工具名称 + 描述 + schema 文本做静态安全扫描。"""
    findings: list[Finding] = []
    for tool in tools:
        haystack = f"{tool.name}\n{tool.description}\n{tool.schema}"
        for pattern, code, message in INJECTION_PATTERNS:
            if re.search(pattern, haystack, re.IGNORECASE):
                findings.append(Finding("critical", code, f"工具 {tool.name}: {message}"))
        for pattern, code, message in CREDENTIAL_PATTERNS:
            if re.search(pattern, haystack):
                findings.append(Finding("critical", code, f"工具 {tool.name}: {message}"))
    return findings


def schema_check(tools: list[ToolInfo]) -> list[Finding]:
    """工具定义规范性检查。"""
    findings: list[Finding] = []
    if not tools:
        findings.append(Finding("warning", "SCHEMA-EMPTY", "服务器未声明任何工具"))
        return findings
    seen: set[str] = set()
    for tool in tools:
        if not tool.name or not re.fullmatch(r"[a-zA-Z0-9_\-]{1,128}", tool.name):
            findings.append(Finding("warning", "SCHEMA-NAME", f"工具名不规范: {tool.name!r}"))
        if tool.name in seen:
            findings.append(Finding("warning", "SCHEMA-DUP", f"工具名重复: {tool.name}"))
        seen.add(tool.name)
        if not tool.description:
            findings.append(Finding("info", "SCHEMA-NODESC", f"工具 {tool.name} 缺少描述（影响模型选择准确率）"))
        elif len(tool.description) > 2000:
            findings.append(Finding("warning", "SCHEMA-BLOAT", f"工具 {tool.name} 描述过长（{len(tool.description)} 字符，加剧上下文膨胀）"))
        schema = tool.schema or {}
        if schema and schema.get("type") not in (None, "object"):
            findings.append(Finding("warning", "SCHEMA-TYPE", f"工具 {tool.name} 的 inputSchema 顶层类型应为 object"))
    return findings
