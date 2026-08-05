"""MCP stdio 协议客户端（JSON-RPC 2.0 over stdio，换行分隔 JSON）。

用后台线程 + 队列实现跨平台带超时的读取（Windows 管道不支持 select）。
"""
from __future__ import annotations

import collections
import json
import os
import queue
import subprocess
import sys
import threading
import time
from typing import Any

PROTOCOL_VERSION = "2025-06-18"


def resolve_command(command: list[str]) -> list[str]:
    """Windows 下 CreateProcess 不做 PATHEXT 查找，npx/uvx 等 .cmd 脚本
    必须用 shutil.which 解析为带扩展名的完整路径。"""
    if sys.platform == "win32" and command:
        import shutil
        resolved = shutil.which(command[0])
        if resolved:
            command = [resolved, *command[1:]]
    return command


def _safe_env() -> dict:
    """子进程的最小环境：剥离一切可能的密钥，仅保留运行必需项。

    Windows 下进程启动要求 SystemRoot 存在（否则 WinError 87）；
    PATH 用于定位 npx/uvx 与解释器依赖，本身不含敏感信息，两个平台都保留。
    """
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    if sys.platform == "win32":
        # USERPROFILE/LOCALAPPDATA 等是 uv/npm 缓存目录的定位依赖，非敏感信息
        for key in ("SystemRoot", "COMSPEC", "PATHEXT", "TEMP", "TMP",
                    "USERPROFILE", "LOCALAPPDATA", "APPDATA", "HOME"):
            if key in os.environ:
                env[key] = os.environ[key]
    else:
        if "HOME" in os.environ:
            env["HOME"] = os.environ["HOME"]
    return env


class ProtocolError(Exception):
    pass


class McpStdioClient:
    """与一个 MCP Server 子进程通信。环境变量默认剥离（防密钥泄露给不可信代码）。"""

    def __init__(self, command: list[str], env: dict | None = None, timeout: float = 15.0):
        self._timeout = timeout
        safe_env = env if env is not None else _safe_env()
        self._proc = subprocess.Popen(
            resolve_command(command),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=safe_env,
        )
        self._lines: queue.Queue[str] = queue.Queue()
        self._stderr_tail: collections.deque[str] = collections.deque(maxlen=10)
        self._id = 0
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._err_reader = threading.Thread(target=self._err_loop, daemon=True)
        self._err_reader.start()

    def _read_loop(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            self._lines.put(line)

    def _err_loop(self) -> None:
        assert self._proc.stderr is not None
        for line in self._proc.stderr:
            self._stderr_tail.append(line.rstrip())

    @property
    def stderr_tail(self) -> str:
        """进程最近的 stderr 输出（诊断启动失败原因用）。"""
        return "\n".join(self._stderr_tail)

    def _fail(self, msg: str) -> ProtocolError:
        """构造带诊断上下文的协议错误。"""
        if self._proc.poll() is not None:
            msg += f"（进程已退出，退出码 {self._proc.returncode}）"
        tail = self.stderr_tail
        if tail:
            msg += f" | stderr: {tail[-400:]}"
        return ProtocolError(msg)

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _request(self, method: str, params: dict | None = None, timeout: float | None = None) -> dict:
        rid = self._next_id()
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        assert self._proc.stdin is not None
        try:
            self._proc.stdin.write(json.dumps(msg) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise ProtocolError(f"无法写入服务器进程: {e}") from e

        deadline = time.monotonic() + (timeout or self._timeout)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise self._fail(f"等待 {method} 响应超时")
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty:
                raise self._fail(f"等待 {method} 响应超时")
            line = line.strip()
            if not line:
                continue
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                continue  # 跳过非 JSON 输出（如日志行）
            if resp.get("id") != rid:
                continue  # 通知或其他请求的回包，忽略
            if "error" in resp:
                raise ProtocolError(f"{method} 返回错误: {resp['error']}")
            return resp.get("result", {})

    def _notify(self, method: str) -> None:
        assert self._proc.stdin is not None
        self._proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self._proc.stdin.flush()

    # ---- MCP 语义方法 ----

    def initialize(self) -> dict:
        result = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "trustlens", "version": "0.1.0"},
            },
        )
        self._notify("notifications/initialized")
        return result

    def list_tools(self) -> list[dict]:
        result = self._request("tools/list", {})
        tools = result.get("tools")
        if not isinstance(tools, list):
            raise ProtocolError("tools/list 响应缺少 tools 数组")
        return tools

    def call_tool(self, name: str, arguments: dict) -> tuple[dict, float]:
        """调用工具，返回 (result, 延迟秒)。"""
        start = time.monotonic()
        result = self._request("tools/call", {"name": name, "arguments": arguments})
        return result, time.monotonic() - start

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        try:
            if self._proc.stdout:
                self._proc.stdout.close()
        except Exception:
            pass

    def __enter__(self) -> "McpStdioClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
