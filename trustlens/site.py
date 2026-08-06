"""静态排行榜网站生成器：智码星 ICodeStar 品牌、中英双语、浏览器语言自适应、SEO/AEO。

输出结构（site/dist/）：
  index.html            中文总榜        /en/index.html        英文总榜
  server/<slug>.html    中文详情页      /en/server/<slug>.html 英文详情页
  sitemap.xml / robots.txt

语言自适应：静态站无法做服务端协商，采用首访 JS 检测
（navigator.language 以 zh 开头 → 中文页，否则 → 英文页）；
用户手动切换后写入 sessionStorage 不再强制跳转。站内链接全相对路径，
任意 base path 可部署（自有域名 / GitHub Pages 调试镜像）。
SEO：canonical、hreflang、meta description、Open Graph、Twitter Card
AEO：JSON-LD（Dataset + ItemList + FAQPage）、FAQ 问答块
"""
from __future__ import annotations

import html
import json
import os
import time
from pathlib import Path

from .engine import slugify
from .models import ServerReport
from .report import load_all

DIST = Path("site/dist")
BASE_URL = os.environ.get("TRUSTLENS_BASE_URL", "https://trustlens.icodestar.net")
REPO_URL = "https://github.com/hyqzz/trustlens"

FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<text y='.9em' font-size='90'>🛡️</text></svg>")

CSS = """
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',sans-serif;
     max-width:1000px;margin:0 auto;padding:0 1rem 2rem;line-height:1.65}
.brandbar{display:flex;align-items:center;gap:.6rem;padding:.9rem 0;border-bottom:1px solid #8884;margin-bottom:1.2rem}
.brand-logo{font-size:1.5rem}
.brand-name{font-weight:800;font-size:1.05rem;letter-spacing:.02em}
.brand-name .en{background:linear-gradient(90deg,#4f8ef7,#9b5cf6);-webkit-background-clip:text;background-clip:text;color:transparent}
.brand-sub{opacity:.55;font-size:.8rem;margin-left:.1rem}
.lang{margin-left:auto;font-size:.88rem;border:1px solid #8886;border-radius:1em;padding:.15em .8em}
h1{margin:.4rem 0 .2rem;font-size:1.7rem}
.subtitle{opacity:.7;margin-top:0}
table{width:100%;border-collapse:collapse;margin-top:1.2rem;font-size:.95rem}
th,td{padding:.65rem .8rem;text-align:left;border-bottom:1px solid #8883}
th{white-space:nowrap;opacity:.75;font-weight:600}
tbody tr{transition:background .15s}
tbody tr:hover{background:#8881}
a{color:#4f8ef7;text-decoration:none}
a:hover{text-decoration:underline}
.score{font-weight:800;font-variant-numeric:tabular-nums}
.grade{display:inline-block;min-width:1.7em;text-align:center;border-radius:.4em;padding:.08em .35em;color:#fff;font-weight:700;font-size:.85em}
.gA{background:#2da44e}.gB{background:#6f9e1f}.gC{background:#bf8700}.gD{background:#cf6020}.gF{background:#cf222e}
.dim{margin:.5rem 0;padding:.55rem .8rem;border:1px solid #8883;border-radius:.5rem}
.dim b{display:inline-block;min-width:11em}
.finding{font-size:.88em;opacity:.85;margin:.15rem 0 0 .4rem;word-break:break-all}
.crit{color:#cf222e}.warn{color:#bf8700}
footer{margin-top:2.5rem;padding-top:1rem;border-top:1px solid #8884;opacity:.6;font-size:.85rem}
.badge{background:linear-gradient(90deg,#4f8ef7,#9b5cf6);color:#fff;border-radius:.35em;padding:.12em .55em;font-size:.75rem;vertical-align:middle}
.faq{margin-top:2.2rem}
.faq h2{font-size:1.15rem}
.faq details{margin:.5rem 0;border:1px solid #8883;border-radius:.5rem;padding:.55rem .9rem}
.faq summary{cursor:pointer;font-weight:600}
.faq p{opacity:.85;margin:.4rem 0 .2rem}
"""

# ---- 文案（双语） ----

T = {
    "zh": {
        "lang": "zh-CN",
        "is_zh": True,
        "title": "TrustLens 信任榜 — 智码星 ICodeStar",
        "heading": "TrustLens 信任榜",
        "tagline": "Agent 能力生态的信任基准：自动化实测 MCP Server / Skills，每周更新。",
        "tagline2": "装任何工具之前，先查分。评分依据全部公开于 GitHub 仓库（git 历史即审计日志）。",
        "meta_desc": "智码星 ICodeStar 出品的 TrustLens 实测 MCP Server 与 Agent Skills 的功能性、可靠性、安全性与跨模型兼容性，发布 0–100 信任分与每周排行榜。装 Agent 工具之前先查分。",
        "col_name": "能力单元", "col_score": "信任分", "col_grade": "等级", "col_brief": "速览",
        "empty": "暂无评测数据",
        "footer": "共 {n} 个评测对象 · 更新于 {ts}",
        "copyright": "© 智码星 ICodeStar · TrustLens 开源项目（Apache-2.0）",
        "back": "← 返回排行榜",
        "report_title": "{name} 质检报告 — TrustLens · 智码星",
        "score_line": "信任分",
        "dims_heading": "维度明细", "tools_heading": "工具清单（{n}）",
        "report_footer": "评测于 {ts} · 引擎版本 {v} · 来源 {src}",
        "error_prefix": "错误：",
        "no_desc": "无描述",
        "switch": "English",
        "switch_href": "en/",
        "faq_heading": "常见问题",
        "faq": [
            ("TrustLens 的信任分是怎么算出来的？",
             "每个能力单元在隔离环境中自动化实测：协议握手与工具调用（功能性 35%）、多次调用的延迟与失败率（可靠性 25%）、静态安全扫描含提示注入/数据外发/硬编码凭证（安全性 25%）、多个大模型实际调用成功率（跨模型兼容性 15%），加权合成 0–100 分。评测数据以 JSON 公开在 GitHub 仓库，可审计。"),
            ("装 MCP Server 之前为什么要查分？",
             "生态内 6 万+ 公共服务器中约 66% 存在安全问题，且大量服务器已废弃或与当前 SDK 不兼容——我们实测发现 4 个官方 Python 服务器在当前环境下全部无法启动。不实测，README 不会告诉你这些。"),
            ("评测数据多久更新一次？",
             "每周自动复测并更新排行榜，评测流水线全程无人值守，结果自动提交到 GitHub 并重建本站。"),
            ("我可以提交自己的服务器参与评测吗？",
             "可以。在 GitHub 仓库提交 issue 或 PR，把服务器加入 data/servers.json 清单即可进入下一周评测批次。"),
        ],
    },
    "en": {
        "lang": "en",
        "is_zh": False,
        "title": "TrustLens Leaderboard — ICodeStar",
        "heading": "TrustLens Leaderboard",
        "tagline": "The trust benchmark for the agent capability ecosystem: automated, evidence-based evaluation of MCP servers and agent skills, updated weekly.",
        "tagline2": "Check the score before you install any tool. All evaluation data is public in the GitHub repo — git history is the audit log.",
        "meta_desc": "TrustLens by ICodeStar measures functionality, reliability, security and cross-model compatibility of MCP servers and agent skills, publishing 0-100 trust scores on a weekly leaderboard. Check before you install.",
        "col_name": "Capability", "col_score": "Trust score", "col_grade": "Grade", "col_brief": "At a glance",
        "empty": "No evaluation data yet",
        "footer": "{n} evaluated · Updated {ts}",
        "copyright": "© ICodeStar · TrustLens is open source (Apache-2.0)",
        "back": "← Back to leaderboard",
        "report_title": "{name} Inspection Report — TrustLens · ICodeStar",
        "score_line": "Trust score",
        "dims_heading": "Dimension breakdown", "tools_heading": "Tools ({n})",
        "report_footer": "Evaluated {ts} · Engine v{v} · Source: {src}",
        "error_prefix": "Error: ",
        "no_desc": "no description",
        "switch": "中文",
        "switch_href": "../",
        "faq_heading": "FAQ",
        "faq": [
            ("How is the TrustLens trust score calculated?",
             "Each capability is tested automatically in an isolated environment: protocol handshake and real tool calls (functionality, 35%), latency and failure rate across repeated calls (reliability, 25%), static security scanning for prompt injection, data exfiltration and hardcoded credentials (security, 25%), and real call success rate across multiple LLMs (cross-model compatibility, 15%). The weighted 0-100 score is fully auditable — evaluation data is published as JSON in the GitHub repo."),
            ("Why check a score before installing an MCP server?",
             "Around 66% of the 60,000+ public servers have security issues, and many are abandoned or incompatible with the current SDK — in our first batch, all four official Python servers failed to even start. READMEs don't tell you this; measured data does."),
            ("How often is the data updated?",
             "Weekly. The evaluation pipeline runs unattended, commits results to GitHub, and rebuilds this site automatically."),
            ("Can I submit my own server for evaluation?",
             "Yes — open an issue or PR on GitHub to add it to data/servers.json, and it will be included in the next weekly batch."),
        ],
    },
}

GRADE_LABEL = {
    "zh": {"A": "可信", "B": "良好", "C": "及格", "D": "风险", "F": "不可信"},
    "en": {"A": "Trusted", "B": "Good", "C": "Fair", "D": "Risky", "F": "Untrusted"},
}
DIM_LABEL = {
    "zh": {"functionality": "功能性", "reliability": "可靠性",
           "security": "安全性", "compatibility": "跨模型兼容"},
    "en": {"functionality": "Functionality", "reliability": "Reliability",
           "security": "Security", "compatibility": "Compatibility"},
}

# 语言自适应脚本：首访按浏览器语言跳转，手动切换后记住选择
LANG_SCRIPT = """<script>
function tlSetLang(){try{sessionStorage.setItem('tl-lang','1')}catch(e){}}
(function(){try{
if(sessionStorage.getItem('tl-lang'))return;
var zh=/^zh([-_]|$)/i.test(navigator.language||navigator.userLanguage||'');
if(zh!==%(is_zh)s){location.replace('%(alt)s');}
}catch(e){}})();
</script>"""


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _grade_badge(grade: str, lang: str) -> str:
    return f'<span class="grade g{grade}">{grade}</span> {GRADE_LABEL[lang].get(grade, "")}'


def _brandbar(t: dict, toggle_href: str) -> str:
    return f"""<div class="brandbar">
<span class="brand-logo">🛡️</span>
<span class="brand-name"><span class="en">ICodeStar</span> 智码星<span class="brand-sub">TrustLens</span></span>
<a class="lang" href="{toggle_href}" onclick="tlSetLang()">{t['switch']}</a>
</div>"""


def _head(t: dict, title: str, path: str, alt_path: str, rel_alt: str) -> str:
    """<head>：SEO meta + OG + Twitter Card + canonical + hreflang + 语言自适应脚本。"""
    canonical = f"{BASE_URL}{path}"
    alt = f"{BASE_URL}{alt_path}"
    is_zh = "true" if t["is_zh"] else "false"
    script = LANG_SCRIPT % {"is_zh": is_zh, "alt": rel_alt}
    return f"""<!doctype html>
<html lang="{t['lang']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(t['meta_desc'])}">
<link rel="icon" href="{FAVICON}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{t['lang']}" href="{canonical}">
<link rel="alternate" hreflang="{'en' if t['is_zh'] else 'zh-CN'}" href="{alt}">
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/en/">
<meta property="og:type" content="website">
<meta property="og:title" content="{_esc(title)}">
<meta property="og:description" content="{_esc(t['meta_desc'])}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="TrustLens · ICodeStar">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{_esc(title)}">
<meta name="twitter:description" content="{_esc(t['meta_desc'])}">
{script}
<style>{CSS}</style></head><body>"""


def _faq_html(t: dict) -> str:
    items = "".join(f"<details><summary>{_esc(q)}</summary><p>{_esc(a)}</p></details>"
                    for q, a in t["faq"])
    return f'<section class="faq"><h2>{t["faq_heading"]}</h2>{items}</section>'


def _faq_jsonld(t: dict) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in t["faq"]
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def _index_jsonld(reports: list[ServerReport], t: dict) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": t["title"],
        "description": t["meta_desc"],
        "url": BASE_URL + ("/en/" if not t["is_zh"] else "/"),
        "dateModified": time.strftime("%Y-%m-%d", time.gmtime()),
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "creator": {"@type": "Organization", "name": "ICodeStar 智码星", "url": BASE_URL},
        "hasPart": [
            {"@type": "SoftwareApplication", "name": r.name,
             "url": f"{BASE_URL}{'' if t['is_zh'] else '/en'}/server/{slugify(r.name)}.html",
             "aggregateRating": {"@type": "AggregateRating", "ratingValue": r.total_score,
                                 "bestRating": 100, "worstRating": 0, "ratingCount": 1}}
            for r in sorted(reports, key=lambda x: -x.total_score)
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def _render_index(reports: list[ServerReport], lang: str) -> str:
    t = T[lang]
    en = lang == "en"
    rows = []
    for r in sorted(reports, key=lambda x: -x.total_score):
        slug = slugify(r.name)
        dims = " · ".join(f"{DIM_LABEL[lang].get(k, k)} {r.dimensions[k].value:.0f}"
                          for k in ("functionality", "security") if k in r.dimensions)
        rows.append(
            f'<tr><td><a href="server/{slug}.html">{_esc(r.name)}</a></td>'
            f'<td class="score">{r.total_score:.1f}</td>'
            f"<td>{_grade_badge(r.grade, lang)}</td>"
            f'<td style="font-size:.85em;opacity:.75">{dims}</td></tr>'
        )
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    tagline2 = t["tagline2"].replace("GitHub 仓库", f'<a href="{REPO_URL}">GitHub 仓库</a>') \
                           .replace("GitHub repo", f'<a href="{REPO_URL}">GitHub repo</a>')
    body = f"""
{_brandbar(t, t['switch_href'])}
<h1>{t['heading']} <span class="badge">LIVE</span></h1>
<p class="subtitle">{t['tagline']}<br>{tagline2}</p>
<table><thead><tr><th>{t['col_name']}</th><th>{t['col_score']}</th><th>{t['col_grade']}</th><th>{t['col_brief']}</th></tr></thead>
<tbody>{''.join(rows) if rows else f'<tr><td colspan="4">{t["empty"]}</td></tr>'}</tbody></table>
{_faq_html(t)}
<footer>{t['footer'].format(n=len(reports), ts=ts)}<br>{t['copyright']}</footer>
{_index_jsonld(reports, t)}
{_faq_jsonld(t)}
</body></html>"""
    return _head(t, t["title"], "/en/" if en else "/", "/" if en else "/en/", t["switch_href"]) + body


def _render_detail(r: ServerReport, lang: str) -> str:
    t = T[lang]
    en = lang == "en"
    slug = slugify(r.name)
    back_href = "../"
    toggle_href = f"../../server/{slug}.html" if en else f"../en/server/{slug}.html"
    dims_html = []
    for key, dim in r.dimensions.items():
        findings = "".join(
            f'<div class="finding {"crit" if f.severity == "critical" else "warn" if f.severity == "warning" else ""}">'
            f"[{_esc(f.code)}] {_esc(f.message)}</div>"
            for f in dim.findings
        )
        dims_html.append(f'<div class="dim"><b>{DIM_LABEL[lang].get(key, key)} {dim.value:.1f}</b>{findings}</div>')
    no_desc_html = f"<i>{t['no_desc']}</i>"
    tool_items = []
    for t2 in r.tools:
        desc = _esc(t2.description[:160]) if t2.description else no_desc_html
        tool_items.append(f"<li><code>{_esc(t2.name)}</code> — {desc}</li>")
    tools_html = "".join(tool_items) or f"<li>{t['empty']}</li>"
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(r.evaluated_at))
    error = f'<p class="crit">{t["error_prefix"]}{_esc(r.error)}</p>' if r.error else ""
    body = f"""
{_brandbar(t, toggle_href)}
<p><a href="{back_href}">{t['back']}</a></p>
<h1>{_esc(r.name)}</h1>
<p class="subtitle">{t['score_line']} <span class="score">{r.total_score:.1f}/100</span> · {_grade_badge(r.grade, lang)}</p>
{error}
<h2>{t['dims_heading']}</h2>{''.join(dims_html)}
<h2>{t['tools_heading'].format(n=len(r.tools))}</h2><ul>{tools_html}</ul>
<footer>{t['report_footer'].format(ts=ts, v=r.engine_version, src=_esc(r.source) or '?')}<br>{t['copyright']}</footer>
</body></html>"""
    title = t["report_title"].format(name=r.name)
    path = f"{'/en' if en else ''}/server/{slug}.html"
    alt = f"{'' if en else '/en'}/server/{slug}.html"
    return _head(t, title, path, alt, toggle_href) + body


def _render_sitemap(reports: list[ServerReport]) -> str:
    today = time.strftime("%Y-%m-%d", time.gmtime())

    def url(loc: str) -> str:
        return f"  <url><loc>{BASE_URL}{loc}</loc><lastmod>{today}</lastmod></url>"

    locs = ["/", "/en/"]
    for r in reports:
        slug = slugify(r.name)
        locs += [f"/server/{slug}.html", f"/en/server/{slug}.html"]
    body = "\n".join(url(l) for l in locs)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def _render_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"


def build_site(results_dir: Path | None = None, dist: Path | None = None) -> Path:
    dist = Path(dist) if dist else DIST
    reports = load_all(results_dir)
    for sub in ("server", "en", "en/server"):
        (dist / sub).mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(_render_index(reports, "zh"), encoding="utf-8")
    (dist / "en" / "index.html").write_text(_render_index(reports, "en"), encoding="utf-8")
    for r in reports:
        slug = slugify(r.name)
        (dist / "server" / f"{slug}.html").write_text(_render_detail(r, "zh"), encoding="utf-8")
        (dist / "en" / "server" / f"{slug}.html").write_text(_render_detail(r, "en"), encoding="utf-8")
    (dist / "sitemap.xml").write_text(_render_sitemap(reports), encoding="utf-8")
    (dist / "robots.txt").write_text(_render_robots(), encoding="utf-8")
    return dist
