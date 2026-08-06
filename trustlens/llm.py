"""跨模型兼容性评估：provider 接口、离线 mock 实现、真实模型实现。

真实 provider 走 OpenAI 兼容接口（GPT / DeepSeek / Qwen 均支持），
API key 从环境变量读取，绝不写入代码或数据文件。
默认（含 CI）使用 MockProvider——确定性、零成本、可复现；
设置 TRUSTLENS_REAL_PROVIDERS=1 并配置对应 key 后启用真实评测。
"""
from __future__ import annotations

import json
import os
import urllib.request
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


# 真实模型配置：OpenAI 兼容端点（OpenCode Go）。
# 当前策略：全程只用 DeepSeek-V4 Flash（$0.14/$0.28，最便宜档）。key 走环境变量，禁止硬编码。
REAL_MODELS: dict[str, dict] = {
    "deepseek": {"base_url": "https://opencode.ai/zen/go/v1", "model": "deepseek-v4-flash",
                 "key_env": "OPENCODE_API_KEY"},
    # 备选（需切换时启用，当前策略不使用）：
    # "gpt": {"base_url": "https://opencode.ai/zen/go/v1", "model": "gpt-5.6-luna",
    #         "key_env": "OPENCODE_API_KEY"},
    # "qwen": {"base_url": "https://opencode.ai/zen/go/v1", "model": "qwen3.7-plus",
    #          "key_env": "OPENCODE_API_KEY"},
}

JUDGE_PROMPT = """你是一个工具调用评估任务中的 Agent。用户目标：{goal}

可用工具：
名称: {name}
描述: {description}
参数schema: {schema}

如果你会调用此工具完成目标，只输出一个 JSON 对象作为调用参数（不含任何其他文字）；
如果你不会调用，只输出 {{"__skip__": true}}。"""


class OpenAICompatProvider(ToolUseProvider):
    """通过 OpenAI 兼容 chat/completions 接口评估模型的工具调用能力。"""

    _UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

    def __init__(self, name: str, base_url: str, model: str, api_key: str, timeout: float = 40.0):
        self.name = name
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    def complete(self, prompt: str, max_tokens: int = 500) -> tuple[str, str]:
        """原始补全：返回 (content, error)。供 Skills 质量评分等直接读文本的场景用。"""
        body = json.dumps({"model": self._model,
                           "messages": [{"role": "user", "content": prompt}],
                           "temperature": 0, "max_tokens": max_tokens}).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json",
                     "User-Agent": self._UA})
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip(), ""
        except Exception as e:
            return "", str(e)

    def judge(self, tool: ToolInfo) -> ModelVerdict:
        prompt = JUDGE_PROMPT.format(
            goal=f"需要使用 {tool.name} 所提供的能力完成一个常见任务",
            name=tool.name,
            description=tool.description or "(无描述)",
            schema=json.dumps(tool.schema or {}, ensure_ascii=False)[:1500],
        )
        body = json.dumps({
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 300,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions", data=body,
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json",
                     "User-Agent": self._UA})  # 部分网关拦截 urllib 默认 UA（403）
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return ModelVerdict(self.name, False, f"API 调用失败: {e}")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return ModelVerdict(self.name, False, "模型输出非合法 JSON")
        if parsed.get("__skip__"):
            return ModelVerdict(self.name, False, "模型放弃调用该工具")
        if isinstance(parsed, dict):
            return ModelVerdict(self.name, True, "成功构造调用参数")
        return ModelVerdict(self.name, False, "模型输出不是参数对象")


def default_providers(use_real: bool | None = None) -> list[ToolUseProvider]:
    """默认评测阵容。use_real=None 时读 TRUSTLENS_REAL_PROVIDERS 环境变量。

    真实模式只启用配置了 API key 且为 OpenAI 兼容端点的模型；
    一个真实模型都不可用则回退到全 mock（保证 CI 与离线可复现）。
    """
    if use_real is None:
        use_real = os.environ.get("TRUSTLENS_REAL_PROVIDERS") == "1"
    if use_real:
        providers: list[ToolUseProvider] = []
        for name, cfg in REAL_MODELS.items():
            key = os.environ.get(cfg["key_env"], "")
            if key and cfg["base_url"]:
                providers.append(OpenAICompatProvider(name, cfg["base_url"], cfg["model"], key))
        if providers:
            return providers
    return [MockProvider(m) for m in ("gpt", "qwen", "deepseek")]
