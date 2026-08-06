"""从注册表发现的真实 MCP 服务器生成 servers.json（过滤挂起/重型/纯 SDK 类）。"""
import json

shortlist = json.load(open("deploy/_mcp_npm_shortlist.json", encoding="utf-8"))
existing = {s["name"] for s in json.load(open("data/servers.json", encoding="utf-8"))["servers"]}

# 会真启动浏览器/重型运行时导致探针挂起的，或纯 SDK 非服务器
block = {
    "chrome-devtools-mcp", "onestep-puppeteer-mcp-server", "puppeteer-mcp-server",
    "playwright-mcp-server", "@agent-infra/mcp-server-browser", "terraform-mcp-server",
    "kubernetes-mcp-server", "kubernetes-mcp-server-linux-amd64", "mcp-server-kubernetes",
    "mcp-server-code-runner", "argocd-mcp", "codex-mcp-server", "@openbnb/mcp-server-airbnb",
    "malicious-mcp-server", "learn-mcp", "mcp-server-sqlite-npx",
}

def npm(name):
    return {"name": name, "type": "mcp-server", "source": "registry-npm",
            "command": "npx", "args": ["-y", name]}

servers = []
seen = set()

# 现有 16 个保留
for s in json.load(open("data/servers.json", encoding="utf-8"))["servers"]:
    servers.append(s); seen.add(s["name"])

# npm 注册表发现的
for name in sorted(shortlist):
    if name in seen or name in block:
        continue
    servers.append(npm(name)); seen.add(name)

# 官方 JS 实现（npm）
official_js = {
    "server-time": "@modelcontextprotocol/server-time",
    "server-fetch": "@modelcontextprotocol/server-fetch",
    "server-git": "@modelcontextprotocol/server-git",
    "server-sqlite": "@modelcontextprotocol/server-sqlite",
}
for short, pkg in official_js.items():
    if short in seen: continue
    servers.append({"name": short, "type": "mcp-server", "source": "official-reference",
                    "command": "npx", "args": ["-y", pkg]}); seen.add(short)

# uvx Python 实现
uvx_add = {
    "mcp-server-math": "数学工具（Python）",
}
for pkg, note in uvx_add.items():
    servers.append({"name": pkg, "type": "mcp-server", "source": "registry-pypi",
                    "command": "uvx", "args": [pkg]}); seen.add(pkg)

out = {"$comment": "真实 MCP 服务器清单（来源：npm/PyPI 注册表发现 + 官方实现），enabled:false 表示暂停评测。",
       "servers": servers}
json.dump(out, open("data/servers.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("total servers:", len(servers))
print("by source:", {k: sum(1 for s in servers if s["source"] == k) for k in sorted({s["source"] for s in servers})})
