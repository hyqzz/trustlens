"""跨模型兼容性评估：provider 接口、离线 mock 实现、真实模型实现。

真实 provider 走 OpenAI 兼容接口（GPT / DeepSeek / Qwen 均支持），
API key 从环境变量读取，绝不写入代码或数据文件。
默认（含 CI）使用 MockProvider——确定性、零成本、可复现；
设置 TRUSTLENS_REAL_PROVIDERS=1 并配置对应 key 后启用真实评测。
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass

from .models import ToolInfo

# 智能探针把"看起来危险/内网/凭证形状"的参数改写到这里：
# 文件类工具的真实可用性靠这个预置文件验证（引擎启动时尽力创建）。
PROBE_TMP_FILE = "/tmp/trustlens_probe.txt"


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

    def probe_args(self, tool: ToolInfo) -> tuple[dict | None, str]:
        """离线 mock 不支持智能探针（返回 None → 引擎回退 dummy 参数）。"""
        return None, "mock provider 不支持智能探针生成"


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


SMART_PROBE_PROMPT = """你是 MCP 工具评测中的"智能探针参数生成器"。评测引擎会对每个工具做一次真实调用，
验证该工具是否真的可用。你的任务：根据工具元数据，生成一组最像真实用户会传的调用参数。

工具名称: {name}
工具描述: {description}
参数 schema: {schema}

要求：
1. 参数必须贴合工具的真实业务（文件工具给文件路径、HTTP 工具给 https://example.com/、搜索工具给常见关键词等）；
2. 全部使用零凭证、公开、安全的资源；即使某个属性未被 required 标出，也应尽量补一个最合理的值；
3. 严禁生成：任何 shell 命令或注入串（`、$(、;、&&、||）；rm/shutdown/mkfs/dd 等破坏性操作；
   任何 API key/密码/令牌；内网或本机地址（127.0.0.1、localhost、169.254.169.254、10.x、192.168.x、
   172.16-31.x、*.local、*.internal）；/etc、/home、/root、/usr、/boot 等敏感路径；路径穿越（../）；
   任何会产生真实扣费、外发数据或修改生产数据的操作；
4. 若该工具本质上必须使用凭证或执行命令，无法构造安全且合理的参数，只输出 {{"__skip__": true}}。

只输出一个 JSON 对象作为调用参数，不要输出任何其他文字。"""


# ---- 智能探针参数安全护栏 ----
# 工具元数据来自不可信第三方（可能投毒 prompt），模型输出仅用作调用参数；
# 无论模型被如何诱导，以下模式都是硬性拦截——正则兜底，不依赖模型自觉。
# 返回值若为 _DANGEROUS 哨兵，则该工具整体跳过（不计入探测基数，不奖不罚）。
_DANGEROUS = object()

# 破坏性/危险命令（值本身就是要执行的破坏行为）
_DESTRUCTIVE = re.compile(
    r"(?i)\brm\s+-rf\b|--no-preserve-root|\bshutdown\b|\breboot\b|\bmkfs\b|\bfdisk\b|"
    r"\bdd\s+if=|\bkillall\b|\bkill\s+-9\b|\bmv\s+/|/dev/sd[a-z]\b|:\(\)\s*\{|fork\s*bomb|"
    r"\bgit\s+push\b|\bgit\s+reset\s+--hard\b|drop\s+table")
# 命令执行形状（值以命令开头，或显式 -c / cmd /c）
_SHELL_EXEC = re.compile(
    r"(?i)^\s*(curl|wget|nc|telnet|bash|sh|zsh|python|python3|perl|ruby|node|powershell|"
    r"cmd\.exe|sudo|chmod|chown)\b|\b(?:cmd\s*/c|powershell\s*-\w|sh\s+-c|bash\s+-c)\b")
# 注入定界符（URL 的 & 是合法查询分隔，故不拦单 &，拦这些即可）
_SHELL_INJECTION = re.compile(r"[`]|\$\(|;|&&|\|\||[\n\r]")
# 路径穿越
_PATH_TRAVERSAL = re.compile(r"(?:\.\./|\.\.\\)")
# 凭证形状 → 改写为 <redacted>
_CRED_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9]{16,}|ghp_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|"
    r"AKIA[0-9a-z]{16}|Bearer\s+[a-z0-9._-]{16,}|xox[bap]-[a-z0-9-]{10,}|"
    r"(?:api[_-]?key|password|passwd|secret|token|access[_-]?key|client[_-]?secret)"
    r"\s*[:=]\s*[^\s\"'{{}}]{6,})")
# 内网/本机/私网目标 → 改写为 example.com（防 SSRF 到元数据等内网服务）
_PRIVATE_TARGET = re.compile(
    r"(?i)(localhost|\b127\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|0\.0\.0\.0|"
    r"169\.254\.\d{1,3}\.\d{1,3}|\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b|"
    r"\b192\.168\.\d{1,3}\.\d{1,3}\b|\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b|"
    r"\b(?:fe80|fd[0-9a-f]{2}):|\.internal\b|\.local\b)")
# 敏感路径段 → 改写为预置探针文件（防读 /etc/passwd 等）
_SENSITIVE_PATH = re.compile(
    r"(?i)(^|[/\\])(etc|home|root|boot|proc|sys|dev|usr|windows|system32|users|secrets?)([/\\]|$)")


def _sanitize_value(v):
    """递归清洗单个参数值；危险 → 返回 _DANGEROUS（整工具跳过）。"""
    if isinstance(v, str):
        if (_DESTRUCTIVE.search(v) or _SHELL_EXEC.search(v)
                or _SHELL_INJECTION.search(v) or _PATH_TRAVERSAL.search(v)):
            return _DANGEROUS
        if _CRED_PATTERN.search(v):
            return _CRED_PATTERN.sub("<redacted>", v)
        if _PRIVATE_TARGET.search(v):
            return "https://example.com/"
        if _SENSITIVE_PATH.search(v):
            return PROBE_TMP_FILE
        # /tmp 下的具体路径（如 /tmp/example.txt）评测环境里并不存在 →
        # 统一改写为引擎会预置的探针文件，文件类工具才能被真实测到。
        if v.startswith("/tmp/") or v.startswith("\\tmp\\") or v == "/tmp":
            return PROBE_TMP_FILE
        return v
    if isinstance(v, list):
        out = []
        for item in v:
            sv = _sanitize_value(item)
            if sv is _DANGEROUS:
                return _DANGEROUS
            out.append(sv)
        return out
    if isinstance(v, dict):
        out = {}
        for k, item in v.items():
            sv = _sanitize_value(item)
            if sv is _DANGEROUS:
                return _DANGEROUS
            out[k] = sv
        return out
    return v  # 数字 / 布尔安全


def _sanitize_args(args: dict) -> tuple[dict | None, bool]:
    """清洗整组参数。(None, False) 表示含危险值 → 该工具跳过。"""
    out: dict = {}
    for k, v in args.items():
        sv = _sanitize_value(v)
        if sv is _DANGEROUS:
            return None, False
        out[k] = sv
    return out, True


def _extract_json(text: str) -> dict | None:
    """解析模型输出（容忍 ```json 代码围栏）。"""
    t = text.strip()
    if t.startswith("```"):
        if "\n" in t:
            t = t.split("\n", 1)[-1]
        else:
            t = t[3:]
        t = t.rstrip("`").strip()
    try:
        parsed = json.loads(t)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


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
            # 推理型模型先耗尽"推理 token"再输出内容；预算太小会 content 为空 → 误判。
            # 实测 300 时约 18% 解析失败、1500 时 <3%。
            "max_tokens": 1500,
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

    def probe_args(self, tool: ToolInfo) -> tuple[dict | None, str]:
        """为工具生成一组真实、安全的探针参数。

        返回 (args, "") 用该参数实测；返回 (None, "") 表示安全探针不可构造，跳过该工具；
        返回 (None, err) 表示 API 失败，调用方应回退 dummy 参数。
        工具元数据可能投毒 prompt，输出一律经 _sanitize_args 清洗后才可用。
        """
        prompt = SMART_PROBE_PROMPT.format(
            name=tool.name,
            description=(tool.description or "(无描述)")[:800],
            schema=json.dumps(tool.schema or {}, ensure_ascii=False)[:1200],
        )
        content, err = self.complete(prompt, max_tokens=2000)
        if err:
            return None, f"API 调用失败: {err}"
        parsed = _extract_json(content)
        if parsed is None:
            return None, "模型输出非合法 JSON"
        if parsed.get("__skip__"):
            return None, ""
        safe, ok = _sanitize_args(parsed)
        if not ok:
            return None, ""  # 危险参数 → 该工具跳过
        return safe, ""


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
