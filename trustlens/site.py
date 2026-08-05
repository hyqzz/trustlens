"""静态排行榜网站生成器：总榜 index.html + 每个服务器一页详情。

零依赖、纯 HTML + 内联 CSS，输出到 site/dist/，可直接由 GitHub Pages 托管。
"""
from __future__ import annotations

import html
import time
from pathlib import Path

from .engine import slugify
from .models import ServerReport
from .report import load_all

DIST = Path("site/dist")

CSS = """
:root{color-scheme:light dark}
body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;max-width:960px;margin:0 auto;padding:2rem 1rem;line-height:1.6}
h1{margin-bottom:.2rem}
.subtitle{opacity:.7;margin-top:0}
table{width:100%;border-collapse:collapse;margin-top:1.5rem}
th,td{padding:.6rem .8rem;text-align:left;border-bottom:1px solid #8884}
th{white-space:nowrap}
a{color:#4f8ef7;text-decoration:none}
a:hover{text-decoration:underline}
.score{font-weight:700;font-variant-numeric:tabular-nums}
.grade{display:inline-block;min-width:1.6em;text-align:center;border-radius:.3em;padding:.05em .3em;color:#fff;font-weight:700}
.gA{background:#2da44e}.gB{background:#6f9e1f}.gC{background:#bf8700}.gD{background:#cf6020}.gF{background:#cf222e}
.dim{margin:.4rem 0}
.dim b{display:inline-block;width:9em}
.finding{font-size:.9em;opacity:.85;margin-left:1em}
.crit{color:#cf222e}.warn{color:#bf8700}
footer{margin-top:3rem;opacity:.6;font-size:.85rem}
.badge{background:#4f8ef7;color:#fff;border-radius:.3em;padding:.1em .5em;font-size:.8em}
"""

GRADE_LABEL = {"A": "可信", "B": "良好", "C": "及格", "D": "风险", "F": "不可信"}
DIM_LABEL = {"functionality": "功能性", "reliability": "可靠性",
             "security": "安全性", "compatibility": "跨模型兼容"}


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _grade_badge(grade: str) -> str:
    return f'<span class="grade g{grade}">{grade}</span> {GRADE_LABEL.get(grade, "")}'


def _render_index(reports: list[ServerReport]) -> str:
    rows = []
    for r in sorted(reports, key=lambda x: -x.total_score):
        slug = slugify(r.name)
        dims = " · ".join(f"{DIM_LABEL.get(k, k)} {r.dimensions[k].value:.0f}"
                          for k in ("functionality", "security") if k in r.dimensions)
        rows.append(
            f'<tr><td><a href="server/{slug}.html">{_esc(r.name)}</a></td>'
            f'<td class="score">{r.total_score:.1f}</td>'
            f"<td>{_grade_badge(r.grade)}</td>"
            f'<td style="font-size:.85em;opacity:.75">{dims}</td></tr>'
        )
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TrustLens 排行榜 — Agent 能力生态信任基准</title>
<style>{CSS}</style></head><body>
<h1>TrustLens 排行榜 <span class="badge">LIVE</span></h1>
<p class="subtitle">Agent 能力生态的信任基准：自动化实测 MCP Server / Skills，每周更新。<br>
装任何工具之前，先查分。评分依据全部公开于
<a href="https://github.com/hyqzz/trustlens">GitHub 仓库</a>（git 历史即审计日志）。</p>
<table><thead><tr><th>能力单元</th><th>信任分</th><th>等级</th><th>速览</th></tr></thead>
<tbody>{''.join(rows) if rows else '<tr><td colspan="4">暂无评测数据</td></tr>'}</tbody></table>
<footer>共 {len(reports)} 个评测对象 · 更新于 {ts} · 由 TrustLens 自动生成</footer>
</body></html>"""


def _render_detail(r: ServerReport) -> str:
    dims_html = []
    for key, dim in r.dimensions.items():
        findings = "".join(
            f'<div class="finding {"crit" if f.severity == "critical" else "warn" if f.severity == "warning" else ""}">'
            f"[{_esc(f.code)}] {_esc(f.message)}</div>"
            for f in dim.findings
        )
        dims_html.append(f'<div class="dim"><b>{DIM_LABEL.get(key, key)} {dim.value:.1f}</b>{findings}</div>')
    tools_html = "".join(
        f"<li><code>{_esc(t.name)}</code> — {_esc(t.description[:160]) or '<i>无描述</i>'}</li>"
        for t in r.tools
    ) or "<li>无</li>"
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(r.evaluated_at))
    error = f'<p class="crit">错误：{_esc(r.error)}</p>' if r.error else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(r.name)} — TrustLens 质检报告</title>
<style>{CSS}</style></head><body>
<p><a href="../index.html">← 返回排行榜</a></p>
<h1>{_esc(r.name)}</h1>
<p class="subtitle">信任分 <span class="score">{r.total_score:.1f}/100</span> · {_grade_badge(r.grade)}</p>
{error}
<h2>维度明细</h2>{''.join(dims_html)}
<h2>工具清单（{len(r.tools)}）</h2><ul>{tools_html}</ul>
<footer>评测于 {ts} · 引擎版本 {r.engine_version} · 来源 {_esc(r.source) or '未知'}</footer>
</body></html>"""


def build_site(results_dir: Path | None = None, dist: Path | None = None) -> Path:
    dist = Path(dist) if dist else DIST
    reports = load_all(results_dir)
    (dist / "server").mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(_render_index(reports), encoding="utf-8")
    for r in reports:
        (dist / "server" / f"{slugify(r.name)}.html").write_text(_render_detail(r), encoding="utf-8")
    return dist
