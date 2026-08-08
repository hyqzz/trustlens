"""CLI：trustlens check / evaluate-all / gen-probes / build-site / list。"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import report as report_mod
from .engine import MAX_TOOLS_TO_CALL, evaluate_server, slugify
from .models import ServerReport

SERVERS_FILE = Path("data/servers.json")
PROBES_FILE = Path("data/probes.json")


def _load_probes(path: Path = PROBES_FILE) -> dict:
    """读回智能探针（server-slug → {tool: {"args": {...}} | {"__skip__": True}}）。"""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("probes", {})
    except json.JSONDecodeError:
        return {}


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
    probes_by_slug = _load_probes()
    servers = {s["name"]: s for s in _load_servers()}
    if args.name in servers:
        s = servers[args.name]
        command = _resolve_command(s)
        r = evaluate_server(args.name, command, s.get("type", "mcp-server"),
                            s.get("source", ""), timeout=args.timeout,
                            probe_args=probes_by_slug.get(slugify(args.name)))
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


def _existing_report(name: str):
    """读取已有评测结果（无则返回 None）。"""
    path = report_mod.RESULTS_DIR / f"{slugify(name)}.json"
    if path.exists():
        try:
            return ServerReport.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, TypeError):
            return None
    return None


def cmd_gen_probes(args) -> int:
    """用真实模型为已评测服务器生成智能探针参数（只读已有结果，不执行服务器代码）。

    与 model-compat 同级安全：本步骤持 key，但无不可信代码运行。
    工具元数据来自不可信服务器（可能投毒 prompt），模型输出经正则安全护栏清洗后才落盘；
    API 失败的工具不写条目 → 评测时回退 dummy 参数。
    """
    from concurrent.futures import ThreadPoolExecutor

    from . import llm

    providers = llm.default_providers(use_real=args.real)
    if not providers or isinstance(providers[0], llm.MockProvider):
        print("错误：未启用真实模型。设置 OPENCODE_API_KEY（推荐）并加 --real。", file=sys.stderr)
        return 2
    provider = providers[0]
    reports = [r for r in report_mod.load_all() if r.tools]
    if not reports:
        print("警告：暂无已评测且有工具的结果，无法生成探针。", file=sys.stderr)
    print(f"用 {provider.name} 为 {len(reports)} 个服务器生成智能探针（并发 {args.workers}）…")

    api_errors = 0

    def _gen(r):
        nonlocal api_errors
        out: dict = {}
        # 只生成评测实际会探测的前 MAX_TOOLS_TO_CALL 个工具：既省调用，也把
        # CI 的 gen-probes 步长压在 30min 超时内（每工具一次真实模型调用）。
        for tool in r.tools[:MAX_TOOLS_TO_CALL]:
            pa, err = provider.probe_args(tool)
            if err:
                api_errors += 1
                continue  # API 失败：不写条目 → 评测时回退 dummy
            out[tool.name] = {"args": pa} if pa else {"__skip__": True}
        return slugify(r.name), out

    probes: dict = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for slug, out in ex.map(_gen, reports):
            if out:
                probes[slug] = out
    payload = {"generated_at": time.time(), "engine": provider.name, "probes": probes}
    out_path = Path(args.output) if args.output else PROBES_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    total_tools = sum(len(v) for v in probes.values())
    print(f"完成：{len(probes)} 个服务器 / {total_tools} 个工具探针 → {out_path}"
          f"（API 错误 {api_errors} 次已回退 dummy）")
    return 0


def cmd_evaluate_all(args) -> int:
    from concurrent.futures import ThreadPoolExecutor

    servers = _load_servers()
    skipped = 0
    if args.skip_f:
        keep = []
        for s in servers:
            existing = _existing_report(s["name"])
            if existing is not None and (not existing.ok or not existing.tools):
                skipped += 1
                continue
            keep.append(s)
        servers = keep
    probes_by_slug = _load_probes()
    print(f"开始评测 {len(servers)} 个能力单元（并发 {args.workers}，跳过已有失败 {skipped}，"
          f"智能探针 {len(probes_by_slug)} 个服务器）…")

    def _run(s: dict):
        r = evaluate_server(s["name"], _resolve_command(s), s.get("type", "mcp-server"),
                            s.get("source", ""), timeout=args.timeout, quick=args.quick,
                            probe_args=probes_by_slug.get(slugify(s["name"])))
        report_mod.save_report(r)
        return r

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(_run, s) for s in servers]
        for i, f in enumerate(futures, 1):
            r = f.result()
            _print_report(r)
            print(f"[{i}/{len(servers)}]")
            results.append(r)
    failed = sum(1 for r in results if not r.ok)
    print(f"\n完成：{len(results) - failed}/{len(results)} 成功")
    return 0


def cmd_model_compat(args) -> int:
    """用真实模型更新全部已存结果的跨模型兼容维度（不执行服务器代码，可安全持 key）。"""
    from concurrent.futures import ThreadPoolExecutor

    from . import llm
    from .engine import apply_compatibility

    providers = llm.default_providers(use_real=args.real)
    if not providers or isinstance(providers[0], llm.MockProvider):
        print("错误：未启用真实模型。设置 OPENCODE_API_KEY（推荐）或对应厂商 key，并加 --real。",
              file=sys.stderr)
        return 2
    targets = [r for r in report_mod.load_all() if r.tools]
    print(f"用真实模型（{', '.join(p.name for p in providers)}）更新 "
          f"{len(targets)} 个有工具的服务器（并发 {args.workers}）…")

    def _run(r):
        apply_compatibility(r, providers)
        report_mod.save_report(r)
        return f"✓ {r.name}: 兼容 {r.dimensions['compatibility'].value:.1f} → 总分 {r.total_score} ({r.grade})"

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for line in ex.map(_run, targets):
            print(line)
    print(f"\n完成：{len(targets)} 个服务器已用真实模型更新跨模型兼容分")
    return 0


def cmd_eval_skills(args) -> int:
    """评估 Agent Skills（SKILL.md）：静态质量 + 安全 + 可选 LLM 质量评分。"""
    from . import skills as skills_mod
    from . import llm as llm_mod

    provider = None
    if args.real:
        providers = llm_mod.default_providers(use_real=True)
        if providers and not isinstance(providers[0], llm_mod.MockProvider):
            provider = providers[0]  # 用第一个（deepseek-v4-flash）做质量评分，成本最低
            print(f"LLM 质量评分模型: {provider.name}")
        else:
            print("警告：未启用真实模型，仅做静态评测。设置 OPENCODE_API_KEY + --real。")
    reports = skills_mod.evaluate_all(llm=provider, target=args.count)
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
    p_all.add_argument("--timeout", type=float, default=90.0, help="单请求超时秒数")
    p_all.add_argument("--workers", type=int, default=4, help="并发评测数")
    p_all.add_argument("--skip-f", action="store_true",
                       help="跳过已有结果为失败/无工具的服务器（失败保持原样，周更提速）")
    p_all.add_argument("--quick", action="store_true",
                       help="快速模式：每服务器仅 2 工具 × 1 次试调用，用于每周快速复检")
    p_all.set_defaults(func=cmd_evaluate_all)

    p_mc = sub.add_parser("model-compat", help="用真实模型更新已存结果的跨模型兼容分（不执行服务器代码）")
    p_mc.add_argument("--real", action="store_true", help="使用真实模型（需配置 API key）")
    p_mc.add_argument("--workers", type=int, default=6, help="并发数")
    p_mc.set_defaults(func=cmd_model_compat)

    p_gp = sub.add_parser("gen-probes",
                          help="用真实模型生成智能探针参数（只读已有结果，不执行服务器代码）")
    p_gp.add_argument("--real", action="store_true", help="使用真实模型（需配置 API key）")
    p_gp.add_argument("--workers", type=int, default=8, help="并发数")
    p_gp.add_argument("--output", help="探针文件输出路径（默认 data/probes.json）")
    p_gp.set_defaults(func=cmd_gen_probes)

    p_site = sub.add_parser("build-site", help="生成静态排行榜网站")
    p_site.set_defaults(func=cmd_build_site)

    p_sk = sub.add_parser("eval-skills", help="评测 Agent Skills（SKILL.md）")
    p_sk.add_argument("--count", type=int, default=110, help="评测多少个 skill")
    p_sk.add_argument("--real", action="store_true", help="使用真实模型做质量评分")
    p_sk.set_defaults(func=cmd_eval_skills)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
