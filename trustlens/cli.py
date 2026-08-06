"""CLI：trustlens check / evaluate-all / build-site / list。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import report as report_mod
from .engine import evaluate_server

SERVERS_FILE = Path("data/servers.json")


def _load_servers(path: Path = SERVERS_FILE) -> list[dict]:
    if not path.exists():
        print(f"错误：找不到服务器清单 {path}", file=sys.stderr)
        sys.exit(2)
    data = json.loads(path.read_text(encoding="utf-8"))
    # enabled: false 的条目暂停评测（如方法论待升级的类别）
    return [s for s in data.get("servers", []) if s.get("enabled", True)]


def _resolve_command(server: dict) -> list[str]:
    cmd = server["command"]
    if cmd == "{python}":
        cmd = sys.executable
    return [cmd, *server.get("args", [])]


def _print_report(r) -> None:
    status = "✅" if r.ok else "❌"
    print(f"\n{status} {r.name}  信任分 {r.total_score}/100 ({r.grade})")
    if r.error:
        print(f"   错误: {r.error}")
    labels = {"functionality": "功能性", "reliability": "可靠性",
              "security": "安全性", "compatibility": "跨模型兼容"}
    for key, label in labels.items():
        dim = r.dimensions.get(key)
        if dim:
            print(f"   {label:<8} {dim.value:>5.1f}")
            for f in dim.findings:
                icon = {"critical": "⛔", "warning": "⚠️ ", "info": "ℹ️ "}.get(f.severity, "")
                print(f"      {icon}[{f.code}] {f.message}")


def cmd_list(_args) -> int:
    for s in _load_servers():
        print(f"- {s['name']} ({s.get('type', '?')})  来源: {s.get('source', '?')}")
    return 0


def cmd_check(args) -> int:
    servers = {s["name"]: s for s in _load_servers()}
    if args.name in servers:
        s = servers[args.name]
        command = _resolve_command(s)
        r = evaluate_server(args.name, command, s.get("type", "mcp-server"),
                            s.get("source", ""), timeout=args.timeout)
    else:
        # 支持直接评测任意命令：trustlens check --cmd "npx -y some-server"
        if not args.cmd:
            print(f"错误：清单中没有 {args.name!r}，且未提供 --cmd", file=sys.stderr)
            return 2
        import shlex
        r = evaluate_server(args.name, shlex.split(args.cmd), timeout=args.timeout)
    _print_report(r)
    path = report_mod.save_report(r)
    print(f"\n报告已写入 {path}")
    return 0 if r.ok else 1


def cmd_evaluate_all(args) -> int:
    servers = _load_servers()
    print(f"开始评测 {len(servers)} 个能力单元…")
    failed = 0
    for s in servers:
        r = evaluate_server(s["name"], _resolve_command(s), s.get("type", "mcp-server"),
                            s.get("source", ""), timeout=args.timeout)
        _print_report(r)
        report_mod.save_report(r)
        if not r.ok:
            failed += 1
    print(f"\n完成：{len(servers) - failed}/{len(servers)} 成功")
    return 0


def cmd_build_site(_args) -> int:
    from .site import build_site
    out = build_site()
    print(f"网站已生成到 {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trustlens",
        description="Agent 能力生态的信任基准：实测 MCP Server / Skills，给出 0–100 信任分。")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="列出待评测清单")
    p_list.set_defaults(func=cmd_list)

    p_check = sub.add_parser("check", help="评测一个服务器")
    p_check.add_argument("name", help="清单中的名称，或自定义名称（配合 --cmd）")
    p_check.add_argument("--cmd", help="直接指定启动命令，如 'npx -y some-server'")
    p_check.add_argument("--timeout", type=float, default=15.0)
    p_check.set_defaults(func=cmd_check)

    p_all = sub.add_parser("evaluate-all", help="评测清单中的全部服务器")
    p_all.add_argument("--timeout", type=float, default=15.0)
    p_all.set_defaults(func=cmd_evaluate_all)

    p_site = sub.add_parser("build-site", help="生成静态排行榜网站")
    p_site.set_defaults(func=cmd_build_site)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
