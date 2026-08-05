"""跨模型兼容性评估：provider 接口与离线 mock 实现。

真实 provider（openai / anthropic / qwen / deepseek）后续在此扩展：
实现 ToolUseProvider 接口并从环境变量读取 API key。
MVP 与 CI 默认使用 MockProvider——确定性、零成本、可复现。
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import ToolInfo


@dataclass
class ModelVerdict:
    model: str
    success: bool
    note: str = ""


class ToolUseProvider:
    """评估"给定模型能否正确选择并调用某工具"的接口。"""

    name = "base"

    def judge(self, tool: ToolInfo) -> ModelVerdict:
        raise NotImplementedError


class MockProvider(ToolUseProvider):
    """离线确定性 provider：用可解释的启发式规则模拟模型表现。

    规则（与真实失败模式同构）：
    - 无描述 → 模型难以判断何时调用 → 失败
    - schema 非法 → 参数构造失败 → 失败
    - 描述超长 → 注意力稀释 → 失败
    """

    def __init__(self, model: str = "mock-model"):
        self.name = model

    def judge(self, tool: ToolInfo) -> ModelVerdict:
        if not tool.description:
            return ModelVerdict(self.name, False, "缺少描述，模型无法判断调用时机")
        if len(tool.description) > 2000:
            return ModelVerdict(self.name, False, "描述过长，注意力被稀释")
        schema = tool.schema or {}
        if schema and schema.get("type") not in (None, "object"):
            return ModelVerdict(self.name, False, "inputSchema 顶层类型非法")
        return ModelVerdict(self.name, True, "成功选择并构造调用")


def default_providers() -> list[ToolUseProvider]:
    """MVP 默认评测阵容（模拟四个真实模型维度，后续替换为真实 provider）。"""
    return [MockProvider(m) for m in ("gpt", "claude", "qwen", "deepseek")]
