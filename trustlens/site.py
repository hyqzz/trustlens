"""静态排行榜网站生成器：智码星 ICodeStar 品牌、中英双语、浏览器语言自适应、交互式榜单、SEO/AEO。

输出结构（site/dist/）：
  index.html            中文总榜        /en/index.html        英文总榜
  server/<slug>.html    中文详情页      /en/server/<slug>.html 英文详情页
  sitemap.xml / robots.txt

交互式榜单：数据以 JSON 内嵌，服务端先渲染全部行（SEO/无 JS 兜底），
JS 增强为 搜索 + 等级筛选 + 来源筛选 + 排序 + 分页 + URL 参数同步。
语言自适应：首访 JS 检测浏览器语言跳转，手动切换后 sessionStorage 记忆。
站内链接全相对路径，任意 base path 可部署。
"""
from __future__ import annotations

import html
import json
import os
import shutil
import time
from collections import Counter
from pathlib import Path

from .engine import slugify
from .models import ServerReport
from .report import load_all

DIST = Path("site/dist")
BASE_URL = os.environ.get("TRUSTLENS_BASE_URL", "https://trustlens.icodestar.net")
REPO_URL = "https://github.com/hyqzz/trustlens"
PAGE_SIZE = 20
SKILLS_FILE = Path("data/skills/skills.json")


def load_skills() -> list[dict]:
    if SKILLS_FILE.exists():
        try:
            return json.loads(SKILLS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def _skill_slugs(skills: list[dict]) -> dict[str, str]:
    """skill url → 唯一详情页 slug。同名 skill（不同仓库各一份）用仓库名消歧，
    避免详情页互相覆盖、榜单链接指向错误版本。以 url（含仓库+路径）为唯一键。"""
    base = Counter(slugify(s.get("name", "")) for s in skills)
    out: dict[str, str] = {}
    used: set[str] = set()
    for s in skills:
        url = s.get("url", "")
        name = s.get("name", "")
        slug = slugify(name)
        if base[slug] > 1:
            repo = slugify((s.get("repo") or "").rsplit("/", 1)[-1]) or "repo"
            slug = f"{slug}-{repo}"
        n = 1
        candidate = slug
        while candidate in used:
            n += 1
            candidate = f"{slug}-{n}"
        used.add(candidate)
        out[url] = candidate
    return out

FAVICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
           "<text y='.9em' font-size='90'>🛡️</text></svg>")

CSS = """
:root{color-scheme:light dark;--accent:#4f8ef7;--accent2:#9b5cf6;--line:#8884;--bg-card:#8881}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',sans-serif;
     max-width:1060px;margin:0 auto;padding:0 1rem 2rem;line-height:1.6}
.brandbar{display:flex;align-items:center;gap:.6rem;padding:.9rem 0;border-bottom:1px solid var(--line);margin-bottom:1.1rem;position:sticky;top:0;background:color-mix(in srgb,Canvas 92%,transparent);backdrop-filter:blur(6px);z-index:10}
.brand-logo{font-size:1.4rem}
.brand-name{font-weight:800;font-size:1.05rem;letter-spacing:.02em}
.brand-name .en{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
.brand-sub{opacity:.55;font-size:.8rem;margin-left:.15rem}
.nav{display:flex;gap:.4rem;margin:.4rem 0 .3rem;flex-wrap:wrap}
.nav a{font-size:.88rem;border:1px solid var(--line);border-radius:1.4em;padding:.22em .95em;text-decoration:none}
.nav a.on{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;border-color:transparent}
.nav a:hover:not(.on){border-color:var(--accent)}
.method{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:.55rem;padding:.5rem .85rem;font-size:.83rem;opacity:.85;margin:.8rem 0}
.method b{opacity:1}
.lang{margin-left:auto;font-size:.86rem;border:1px solid var(--line);border-radius:1.2em;padding:.18em .85em;text-decoration:none}
.lang:hover{text-decoration:none;background:var(--bg-card)}
h1{margin:.3rem 0 .2rem;font-size:1.65rem}
.subtitle{opacity:.72;margin-top:0}
.badge{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;border-radius:.35em;padding:.12em .55em;font-size:.72rem;vertical-align:middle}

/* 统计卡片 */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.7rem;margin:1.1rem 0}
.stat{border:1px solid var(--line);border-radius:.7rem;padding:.6rem .8rem}
.stat .v{font-size:1.45rem;font-weight:800;font-variant-numeric:tabular-nums}
.stat .l{opacity:.65;font-size:.8rem}
.stat .v.gA{color:#2da44e}.stat .v.gD{color:#cf6020}.stat .v.gF{color:#cf222e}
.distbar{display:flex;height:.55rem;border-radius:.3rem;overflow:hidden;margin-top:.35rem}
.distbar i{display:block;height:100%}

/* 工具栏 */
.toolbar{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;margin:.9rem 0;position:sticky;top:52px;background:color-mix(in srgb,Canvas 94%,transparent);backdrop-filter:blur(6px);padding:.5rem 0;z-index:9}
.toolbar input[type=search]{flex:1 1 220px;min-width:160px;padding:.5rem .8rem;border:1px solid var(--line);border-radius:.6rem;background:Canvas;font:inherit}
.toolbar select{padding:.5rem .6rem;border:1px solid var(--line);border-radius:.6rem;background:Canvas;font:inherit}
.toolbar input:focus,.toolbar select:focus{outline:2px solid var(--accent);outline-offset:1px}
.chips{display:flex;gap:.35rem;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:1.2em;padding:.22em .8em;cursor:pointer;font-size:.84rem;background:Canvas;user-select:none}
.chip:hover{border-color:var(--accent)}
.chip.on{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;border-color:transparent}
.resultcount{font-size:.84rem;opacity:.75;margin-left:auto;white-space:nowrap}

/* 表格 */
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:.7rem}
table{width:100%;border-collapse:collapse;font-size:.92rem;min-width:680px}
thead th{position:sticky;top:104px;background:Canvas;opacity:.75;font-weight:600;text-align:left;padding:.55rem .8rem;border-bottom:1px solid var(--line);white-space:nowrap;z-index:5}
tbody td{padding:.55rem .8rem;border-bottom:1px solid #8882;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr{transition:background .12s}
tbody tr:hover{background:var(--bg-card)}
.rank{opacity:.5;font-variant-numeric:tabular-nums;font-size:.85rem;width:3em}
.name{font-weight:600}
.name small{display:block;opacity:.5;font-weight:400;font-size:.78rem;max-width:26em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.score{font-weight:800;font-variant-numeric:tabular-nums;font-size:1.05rem}
.grade{display:inline-block;min-width:1.7em;text-align:center;border-radius:.4em;padding:.1em .4em;color:#fff;font-weight:700;font-size:.82em}
.gA{background:#2da44e}.gB{background:#6f9e1f}.gC{background:#bf8700}.gD{background:#cf6020}.gF{background:#cf222e}
.src{opacity:.7;font-size:.8rem}
.dims{font-size:.78rem;opacity:.7;white-space:nowrap}
.dims b{font-variant-numeric:tabular-nums}

/* 分页 */
.pager{display:flex;gap:.4rem;align-items:center;justify-content:center;margin:1rem 0;flex-wrap:wrap}
.pager button{border:1px solid var(--line);background:Canvas;border-radius:.5rem;padding:.35rem .75rem;cursor:pointer;font:inherit;font-size:.88rem}
.pager button:hover:not(:disabled){border-color:var(--accent)}
.pager button:disabled{opacity:.4;cursor:not-allowed}
.pager .pg.on{background:linear-gradient(90deg,var(--accent),var(--accent2));color:#fff;border-color:transparent}
.empty{border:1px dashed var(--line);border-radius:.7rem;padding:2rem;text-align:center;opacity:.7;margin:1rem 0}

/* 详情页维度 */
.dim{margin:.5rem 0;padding:.55rem .8rem;border:1px solid var(--line);border-radius:.55rem}
.dim b{display:inline-block;min-width:11em}
.finding{font-size:.87em;opacity:.85;margin:.15rem 0 0 .4rem;word-break:break-all}
.crit{color:#cf222e}.warn{color:#bf8700}
/* 来源与安装 */
.srcbox{border:1px solid var(--line);border-left:3px solid var(--accent2);border-radius:.55rem;padding:.7rem .95rem;margin:.8rem 0;font-size:.9rem}
.srcbox h2{margin:.1rem 0 .5rem;font-size:1.05rem}
.inst{display:flex;align-items:baseline;gap:.5rem;flex-wrap:wrap;margin:.4rem 0}
.inst>span{opacity:.7;font-size:.84rem;min-width:3.4em}
.inst code{background:var(--bg-card);border:1px solid var(--line);border-radius:.4rem;padding:.22em .6em;word-break:break-all;font-size:.88rem}
.inst a{word-break:break-all}
.insthint{font-size:.84rem;opacity:.8;margin:.45rem 0 .25rem}
.copybtn{border:1px solid var(--line);background:Canvas;border-radius:.4rem;padding:.2em .7em;cursor:pointer;font:inherit;font-size:.8rem;white-space:nowrap}
.copybtn:hover{border-color:var(--accent)}
.copybtn.copied{border-color:#2da44e;color:#2da44e}
.skillmeta{font-size:.84rem;opacity:.75;margin:.6rem 0 0}
.skillmeta b{opacity:1;font-variant-numeric:tabular-nums}
footer{margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--line);opacity:.6;font-size:.85rem}
.faq{margin-top:2rem}
.faq h2{font-size:1.15rem}
.faq details{margin:.5rem 0;border:1px solid var(--line);border-radius:.55rem;padding:.55rem .9rem}
.faq summary{cursor:pointer;font-weight:600}
.faq p{opacity:.85;margin:.4rem 0 .2rem}
@media (max-width:640px){.toolbar{position:static}thead th{position:static}.dims{display:none}}
"""

# ---- 文案（双语） ----

T = {
    "zh": {
        "lang": "zh-CN", "is_zh": True,
        "title": "TrustLens 信任榜 — 智码星 ICodeStar",
        "heading": "TrustLens 信任榜",
        "tagline": "Agent 能力生态的信任基准：自动化实测 MCP Server / Skills，每周更新。",
        "tagline2": "装任何工具之前，先查分。评分依据全部公开于 GitHub 仓库（git 历史即审计日志）。",
        "meta_desc": "智码星 ICodeStar 出品的 TrustLens 实测 MCP Server 与 Agent Skills 的功能性、可靠性、安全性与跨模型兼容性，发布 0–100 信任分与每周排行榜。装 Agent 工具之前先查分。",
        "col_rank": "#", "col_name": "能力单元", "col_score": "信任分", "col_grade": "等级",
        "col_src": "来源", "col_dims": "速览",
        "stat_total": "评测对象", "stat_avg": "平均信任分", "stat_a": "A 级·可信", "stat_f": "F 级·不可用",
        "search_ph": "搜索服务器名称…",
        "filt_grade": "全部等级", "filt_src": "全部来源",
        "sort_label": "排序：", "sort_desc": "信任分 ↓", "sort_asc": "信任分 ↑", "sort_name": "名称 A–Z",
        "prev": "上一页", "next": "下一页", "page_of": "第 {p} / {n} 页", "reset": "重置筛选",
        "empty_title": "没有匹配的评测对象", "empty_hint": "试试清空搜索或换个筛选条件",
        "no_desc": "无描述", "back": "← 返回排行榜",
        "nav_mcp": "MCP 服务器", "nav_skills": "Skills",
        "method_mcp": "<b>评测方法</b>：隔离沙箱 + 零凭证开箱即用（90s 握手超时）实测；模型工具调用维度由 <b>DeepSeek-V4 Flash</b> 真实调用评测。全部数据以 JSON 公开在仓库，git 历史即审计日志。",
        "method_skills": "<b>评测方法</b>：对每个 SKILL.md 做结构质量 + 安全扫描（静态），并由 <b>DeepSeek-V4 Flash</b> 实测可执行性质量分。来源：GitHub 公开的官方与社区技能仓库。",
        "sk_heading": "Skills 信任榜", "sk_badge": "SKILLS",
        "sk_tagline": "Agent Skills（SKILL.md 能力单元）的质量与信任基准：结构、安全、可执行性三维实测。",
        "sk_col_skill": "技能", "sk_col_repo": "来源", "sk_col_struct": "结构",
        "sk_col_sec": "安全", "sk_col_llm": "质量(LLM)",
        "sk_stat_total": "评测 Skills", "sk_stat_avg": "平均分", "sk_meta_title": "Skills 信任榜 — Agent Skills 质量评测 · TrustLens",
        "sk_desc": "TrustLens 实测 GitHub 上的 Agent Skills（SKILL.md）：结构完整性、安全性与大模型可执行性三维评分，发布 0–100 信任分榜单。装/用任何 skill 之前先查分。",
        "report_title": "{name} 质检报告 — TrustLens · 智码星", "score_line": "信任分",
        "dims_heading": "维度明细", "tools_heading": "工具清单（{n}）",
        "report_footer": "评测于 {ts} · 引擎版本 {v} · 来源 {src}", "error_prefix": "错误：",
        "srcbox_heading": "来源与安装", "src_label": "来源", "pkg_label": "包页",
        "install_label": "安装", "copy": "复制", "copied": "已复制",
        "install_mcp_hint": "在支持 MCP 的客户端中添加该服务器（示例，Claude Code）：",
        "install_mcp_prefix": "claude mcp add {name} --",
        "no_install": "内置样例，不可安装",
        "sk_report_title": "{name} 评测报告 — TrustLens · 智码星",
        "sk_back": "← 返回 Skills 榜",
        "sk_dims_heading": "三维评分", "sk_findings_heading": "安全发现",
        "sk_llm_heading": "LLM 可执行性点评", "sk_llm_none": "未评测",
        "sk_no_findings": "无发现", "repo_label": "仓库", "skill_path_label": "SKILL.md",
        "install_skill_hint": "克隆仓库后，把该 skill 目录（含 SKILL.md）复制到你 agent 的 skills 目录（Claude Code：~/.claude/skills/）：",
        "view_skill": "查看 SKILL.md",
        "sk_meta": "评测于 {ts} · {chars} 字符 · {scripts} 个脚本 · {fm}frontmatter",
        "fm_yes": "有", "fm_no": "无",
        "sk_dim_struct": "结构", "sk_dim_sec": "安全", "sk_dim_llm": "质量(LLM)",
        "footer": "共 {n} 个评测对象 · 更新于 {ts} · © 智码星 ICodeStar · TrustLens 开源（Apache-2.0）",
        "switch": "English", "switch_href": "en/",
        "faq_heading": "常见问题",
        "faq": [
            ("TrustLens 的信任分是怎么算出来的？",
             "每个能力单元在隔离环境中自动化实测：协议握手与工具调用（功能性 35%）、多次调用的延迟与失败率（可靠性 25%）、静态安全扫描含提示注入/数据外发/硬编码凭证（安全性 25%）、多个大模型实际调用成功率（跨模型兼容性 15%），加权合成 0–100 分。评测数据以 JSON 公开在 GitHub 仓库，可审计。"),
            ("装 MCP Server 之前为什么要查分？",
             "生态内 6 万+ 公共服务器中约 66% 存在安全问题，且大量服务器已废弃或与当前 SDK 不兼容——我们实测发现多个官方 Python 服务器在当前环境下无法启动。不实测，README 不会告诉你这些。"),
            ("评测数据多久更新一次？",
             "每周自动复测并更新排行榜，评测流水线全程无人值守，结果自动提交到 GitHub 并重建本站。"),
            ("我可以提交自己的服务器参与评测吗？",
             "可以。在 GitHub 仓库提交 issue 或 PR，把服务器加入 data/servers.json 清单即可进入下一周评测批次。"),
        ],
    },
    "en": {
        "lang": "en", "is_zh": False,
        "title": "TrustLens Leaderboard — ICodeStar",
        "heading": "TrustLens Leaderboard",
        "tagline": "The trust benchmark for the agent capability ecosystem: automated, evidence-based evaluation of MCP servers and agent skills, updated weekly.",
        "tagline2": "Check the score before you install any tool. All evaluation data is public in the GitHub repo — git history is the audit log.",
        "meta_desc": "TrustLens by ICodeStar measures functionality, reliability, security and cross-model compatibility of MCP servers and agent skills, publishing 0-100 trust scores on a weekly leaderboard. Check before you install.",
        "col_rank": "#", "col_name": "Capability", "col_score": "Trust score", "col_grade": "Grade",
        "col_src": "Source", "col_dims": "At a glance",
        "stat_total": "Evaluated", "stat_avg": "Avg score", "stat_a": "Grade A", "stat_f": "Grade F",
        "search_ph": "Search servers…",
        "filt_grade": "All grades", "filt_src": "All sources",
        "sort_label": "Sort: ", "sort_desc": "Score ↓", "sort_asc": "Score ↑", "sort_name": "Name A–Z",
        "prev": "Prev", "next": "Next", "page_of": "Page {p} / {n}", "reset": "Reset",
        "empty_title": "No matching capability units", "empty_hint": "Clear the search or change filters",
        "no_desc": "no description", "back": "← Back to leaderboard",
        "nav_mcp": "MCP Servers", "nav_skills": "Skills",
        "method_mcp": "<b>Method</b>: isolated sandbox, zero-credential out-of-the-box eval (90s handshake). Model tool-call accuracy is measured with real calls by <b>DeepSeek-V4 Flash</b>. All data is public JSON in the repo — git history is the audit log.",
        "method_skills": "<b>Method</b>: static structure + security scan of each SKILL.md, plus an actionability score judged by <b>DeepSeek-V4 Flash</b>. Sources: official and community skill repos on GitHub.",
        "sk_heading": "Skills Leaderboard", "sk_badge": "SKILLS",
        "sk_tagline": "Trust benchmark for Agent Skills (SKILL.md): structure, security and actionability, measured in three dimensions.",
        "sk_col_skill": "Skill", "sk_col_repo": "Source", "sk_col_struct": "Struct",
        "sk_col_sec": "Security", "sk_col_llm": "Quality(LLM)",
        "sk_stat_total": "Skills", "sk_stat_avg": "Avg score",
        "sk_meta_title": "Skills Leaderboard — Agent Skills Quality · TrustLens",
        "sk_desc": "TrustLens evaluates Agent Skills (SKILL.md) from GitHub: structure completeness, security, and LLM-measured actionability, published as a 0-100 trust leaderboard. Check before you use any skill.",
        "report_title": "{name} Inspection Report — TrustLens · ICodeStar", "score_line": "Trust score",
        "dims_heading": "Dimension breakdown", "tools_heading": "Tools ({n})",
        "report_footer": "Evaluated {ts} · Engine v{v} · Source: {src}", "error_prefix": "Error: ",
        "srcbox_heading": "Source & Install", "src_label": "Source", "pkg_label": "Package",
        "install_label": "Install", "copy": "Copy", "copied": "Copied",
        "install_mcp_hint": "Add this server to your MCP client (example, Claude Code):",
        "install_mcp_prefix": "claude mcp add {name} --",
        "no_install": "Built-in fixture, not installable",
        "sk_report_title": "{name} Skill Report — TrustLens · ICodeStar",
        "sk_back": "← Back to Skills leaderboard",
        "sk_dims_heading": "Three dimensions", "sk_findings_heading": "Security findings",
        "sk_llm_heading": "LLM actionability notes", "sk_llm_none": "Not evaluated",
        "sk_no_findings": "No findings", "repo_label": "Repo", "skill_path_label": "SKILL.md",
        "install_skill_hint": "Clone the repo, then copy the skill folder (containing SKILL.md) into your agent's skills directory (Claude Code: ~/.claude/skills/):",
        "view_skill": "View SKILL.md",
        "sk_meta": "Evaluated {ts} · {chars} chars · {scripts} scripts · {fm} frontmatter",
        "fm_yes": "has", "fm_no": "no",
        "sk_dim_struct": "Struct", "sk_dim_sec": "Security", "sk_dim_llm": "Quality(LLM)",
        "footer": "{n} evaluated · Updated {ts} · © ICodeStar · TrustLens is open source (Apache-2.0)",
        "switch": "中文", "switch_href": "../",
        "faq_heading": "FAQ",
        "faq": [
            ("How is the TrustLens trust score calculated?",
             "Each capability is tested automatically in an isolated environment: protocol handshake and real tool calls (functionality, 35%), latency and failure rate across repeated calls (reliability, 25%), static security scanning for prompt injection, data exfiltration and hardcoded credentials (security, 25%), and real call success rate across multiple LLMs (cross-model compatibility, 15%). The weighted 0-100 score is fully auditable — evaluation data is published as JSON in the GitHub repo."),
            ("Why check a score before installing an MCP server?",
             "Around 66% of the 60,000+ public servers have security issues, and many are abandoned or incompatible with the current SDK — in our evaluation, several official Python servers failed to even start. READMEs don't tell you this; measured data does."),
            ("How often is the data updated?",
             "Weekly. The evaluation pipeline runs unattended, commits results to GitHub, and rebuilds this site automatically."),
            ("Can I submit my own server for evaluation?",
             "Yes — open an issue or PR on GitHub to add it to data/servers.json, and it will be included in the next weekly batch."),
        ],
    },
}

GRADE_LABEL = {"zh": {"A": "可信", "B": "良好", "C": "及格", "D": "风险", "F": "不可用"},
               "en": {"A": "Trusted", "B": "Good", "C": "Fair", "D": "Risky", "F": "Broken"}}
DIM_LABEL = {"zh": {"functionality": "功能性", "reliability": "可靠性", "security": "安全性", "compatibility": "模型调用"},
             "en": {"functionality": "Func", "reliability": "Rel", "security": "Sec", "compatibility": "Tool-call"}}
GRADE_COLOR = {"A": "2da44e", "B": "6f9e1f", "C": "bf8700", "D": "cf6020", "F": "cf222e"}

LANG_SCRIPT = """<script>
function tlSetLang(){try{sessionStorage.setItem('tl-lang','1')}catch(e){}}
(function(){try{if(sessionStorage.getItem('tl-lang'))return;
var zh=/^zh([-_]|$)/i.test(navigator.language||navigator.userLanguage||'');
if(zh!==%(is_zh)s){location.replace('%(alt)s');}}catch(e){}})();
</script>"""


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _grade_badge(grade: str, lang: str) -> str:
    return f'<span class="grade g{grade}">{grade}</span> {GRADE_LABEL[lang].get(grade, "")}'


def _pkg_url(command: str, args: list[str]) -> str:
    """从启动命令推导包页链接（npm / PyPI），便于用户直达安装来源。"""
    if command == "npx" and "-y" in args:
        pkg = args[args.index("-y") + 1].replace("@latest", "")
        return f"https://www.npmjs.com/package/{pkg}"
    if command == "uvx" and args:
        return f"https://pypi.org/project/{args[0]}"
    return ""


COPY_JS = """<script>
document.querySelectorAll('.copybtn').forEach(function(b){
  b.addEventListener('click', function(){
    var code=b.closest('.inst').querySelector('code');
    var txt=code?code.textContent:'';
    navigator.clipboard.writeText(txt).then(function(){
      var old=b.textContent; b.textContent='%(copied)s'; b.classList.add('copied');
      setTimeout(function(){b.textContent=old;b.classList.remove('copied');},1400);
    }).catch(function(){});
  });
});
</script>"""


def _brandbar(t: dict, toggle_href: str) -> str:
    return (f'<div class="brandbar"><span class="brand-logo">🛡️</span>'
            f'<span class="brand-name"><span class="en">ICodeStar</span> 智码星'
            f'<span class="brand-sub">TrustLens</span></span>'
            f'<a class="lang" href="{toggle_href}" onclick="tlSetLang()">{t["switch"]}</a></div>')


def _nav(t: dict, en: bool, current: str) -> str:
    """MCP 榜 / Skills 榜 切换。current: 'mcp' | 'skills'"""
    mcp_href = "en/index.html" if en else "index.html"
    sk_href = "en/skills.html" if en else "skills.html"
    mcp_on = ' class="on"' if current == "mcp" else ""
    sk_on = ' class="on"' if current == "skills" else ""
    return (f'<nav class="nav"><a href="{mcp_href}"{mcp_on}>{t["nav_mcp"]}</a>'
            f'<a href="{sk_href}"{sk_on}>{t["nav_skills"]}</a></nav>')


def _head(t: dict, title: str, path: str, alt_path: str, rel_alt: str) -> str:
    canonical = f"{BASE_URL}{path}"
    alt = f"{BASE_URL}{alt_path}"
    script = LANG_SCRIPT % {"is_zh": "true" if t["is_zh"] else "false", "alt": rel_alt}
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
    return ('<section class="faq"><h2>' + t["faq_heading"] + "</h2>" +
            "".join(f"<details><summary>{_esc(q)}</summary><p>{_esc(a)}</p></details>" for q, a in t["faq"]) +
            "</section>")


def _faq_jsonld(t: dict) -> str:
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def _index_jsonld(reports: list[ServerReport], t: dict) -> str:
    data = {"@context": "https://schema.org", "@type": "Dataset",
            "name": t["title"], "description": t["meta_desc"],
            "url": BASE_URL + ("/en/" if not t["is_zh"] else "/"),
            "dateModified": time.strftime("%Y-%m-%d", time.gmtime()),
            "license": "https://www.apache.org/licenses/LICENSE-2.0",
            "creator": {"@type": "Organization", "name": "ICodeStar 智码星", "url": BASE_URL},
            "hasPart": [{"@type": "SoftwareApplication", "name": r.name,
                         "url": f"{BASE_URL}{'' if t['is_zh'] else '/en'}/server/{slugify(r.name)}.html",
                         "aggregateRating": {"@type": "AggregateRating", "ratingValue": r.total_score,
                                             "bestRating": 100, "worstRating": 0, "ratingCount": 1}}
                        for r in sorted(reports, key=lambda x: -x.total_score)]}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


LEADERBOARD_JS = """
<script>
(function(){
var DATA = JSON.parse(document.getElementById('tl-data').textContent);
var L = %(labels)s;
var state = {q:'', grade:'all', src:'all', sort:'desc', page:1, size:20};

function readParams(){
  var p = new URLSearchParams(location.search);
  state.q = p.get('q')||''; state.grade = p.get('grade')||'all'; state.src = p.get('src')||'all';
  state.sort = p.get('sort')||'desc';
  var pg = parseInt(p.get('page'),10); state.page = isNaN(pg)||pg<1 ? 1 : pg;
}
function writeParams(){
  var p = new URLSearchParams();
  if(state.q) p.set('q',state.q); if(state.grade!=='all') p.set('grade',state.grade);
  if(state.src!=='all') p.set('src',state.src); if(state.sort!=='desc') p.set('sort',state.sort);
  if(state.page>1) p.set('page',String(state.page));
  history.replaceState(null,'',location.pathname + (p.toString()?'?'+p.toString():''));
}
function filtered(){
  var q = state.q.trim().toLowerCase();
  var rows = DATA.filter(function(r){
    if(q && r.name.toLowerCase().indexOf(q)===-1) return false;
    if(state.grade!=='all' && r.grade!==state.grade) return false;
    if(state.src!=='all' && r.source!==state.src) return false;
    return true;
  });
  rows.sort(function(a,b){
    if(state.sort==='name') return a.name.localeCompare(b.name);
    return state.sort==='asc' ? a.score-b.score : b.score-a.score;
  });
  return rows;
}
function esc(s){var d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}
function rowsHtml(rows){
  var base = location.pathname;
  var start = (state.page-1)*state.size;
  return rows.slice(start,start+state.size).map(function(r,i){
    var src = r.source.replace(/^registry-/,'').replace(/-/g,' ');
    var dims = '<span class="dims"><b>'+r.dim.f+'</b> F · <b>'+r.dim.s+'</b> S · <b>'+r.dim.c+'</b> C</span>';
    return '<tr><td class="rank">'+(start+i+1)+'</td>'+
      '<td class="name"><a href="server/'+r.slug+'.html">'+esc(r.name)+'</a>'+
      (r.error?'<small>'+esc(r.error.split("|")[0])+'</small>':'')+'</td>'+
      '<td class="score" style="color:#'+r.color+'">'+r.score.toFixed(1)+'</td>'+
      '<td><span class="grade g'+r.grade+'">'+r.grade+'</span></td>'+
      '<td class="src">'+esc(src)+'</td><td>'+dims+'</td></tr>';
  }).join('');
}
function pager(rows,totalPages){
  var pages=[];
  var cur=state.page;
  for(var i=1;i<=totalPages;i++){
    if(i===1||i===totalPages||(i>=cur-2&&i<=cur+2)) pages.push(i);
    else if(pages[pages.length-1]!=='…') pages.push('…');
  }
  var html='<button data-p="'+(cur-1)+'" '+(cur<=1?'disabled':'')+'>'+L.prev+'</button>';
  pages.forEach(function(p){
    if(p==='…'){html+='<span style="opacity:.5;padding:0 .2em">…</span>';}
    else{html+='<button class="pg'+(p===cur?' on':'')+'" data-p="'+p+'">'+p+'</button>';}
  });
  html+='<button data-p="'+(cur+1)+'" '+(cur>=totalPages?'disabled':'')+'>'+L.next+'</button>';
  return html;
}
function render(){
  var rows = filtered();
  var totalPages = Math.max(1,Math.ceil(rows.length/state.size));
  if(state.page>totalPages){state.page=totalPages;}
  var tbody=document.getElementById('tl-body');
  tbody.innerHTML = rows.length ? rowsHtml(rows) :
    '<tr><td colspan="6"><div class="empty"><div style="font-weight:700">'+L.empty_title+
    '</div><div>'+L.empty_hint+'</div></div></td></tr>';
  document.getElementById('tl-pager').innerHTML = pager(rows,totalPages);
  document.getElementById('tl-count').textContent =
    (rows.length===DATA.length?'':'') + rows.length + ' / ' + DATA.length;
  document.getElementById('tl-pageof').textContent = L.page_of.replace('{p}',state.page).replace('{n}',totalPages);
  document.getElementById('tl-reset').style.display = (state.q||state.grade!=='all'||state.src!=='all')?'':'none';
  writeParams();
}
function bind(){
  var si=document.getElementById('tl-search'); si.value=state.q;
  var gd=document.getElementById('tl-grade'); gd.value=state.grade;
  var sc=document.getElementById('tl-src'); sc.value=state.src;
  var st=document.getElementById('tl-sort'); st.value=state.sort;
  si.addEventListener('input',function(){state.q=si.value;state.page=1;render();});
  gd.addEventListener('change',function(){state.grade=gd.value;state.page=1;render();});
  sc.addEventListener('change',function(){state.src=sc.value;state.page=1;render();});
  st.addEventListener('change',function(){state.sort=st.value;state.page=1;render();});
  document.getElementById('tl-pager').addEventListener('click',function(e){
    var b=e.target.closest('button[data-p]'); if(!b||b.disabled) return;
    state.page=parseInt(b.getAttribute('data-p'),10); render();
    window.scrollTo({top:0,behavior:'smooth'});
  });
  document.getElementById('tl-reset').addEventListener('click',function(){
    state.q='';state.grade='all';state.src='all';state.sort='desc';state.page=1;
    si.value='';gd.value='all';sc.value='all';st.value='desc';render();
  });
}
readParams(); bind(); render();
})();
</script>
"""


def _render_index(reports: list[ServerReport], lang: str) -> str:
    t = T[lang]
    en = lang == "en"
    total = len(reports)
    avg = round(sum(r.total_score for r in reports) / total, 1) if total else 0
    counts = {g: sum(1 for r in reports if r.grade == g) for g in "ABCDF"}
    pct = lambda g: round(counts[g] * 100 / total, 0) if total else 0

    def dims_of(r: ServerReport) -> dict:
        vals = {k: int(r.dimensions[k].value) if k in r.dimensions else 0
                for k in ("functionality", "security", "compatibility")}
        return {"f": vals["functionality"], "s": vals["security"], "c": vals["compatibility"]}

    data = [{
        "name": r.name, "slug": slugify(r.name), "score": r.total_score,
        "grade": r.grade, "source": r.source, "color": GRADE_COLOR[r.grade],
        "error": r.error, "dim": dims_of(r),
    } for r in sorted(reports, key=lambda x: -x.total_score)]

    labels = {k: t.get(k, "") for k in (
        "prev", "next", "page_of", "empty_title", "empty_hint", "reset")}
    labels["page_of"] = labels["page_of"].replace("{p}", "{p}").replace("{n}", "{n}")
    js = LEADERBOARD_JS % {"labels": json.dumps(labels, ensure_ascii=False)}

    sources = sorted({r.source for r in reports})

    # 服务端渲染全部行（SEO / 无 JS 兜底）
    rows = []
    for i, r in enumerate(sorted(reports, key=lambda x: -x.total_score), 1):
        slug = slugify(r.name)
        dims = " · ".join(f"{DIM_LABEL[lang].get(k, k)} {r.dimensions[k].value:.0f}"
                          for k in ("functionality", "security", "compatibility") if k in r.dimensions)
        rows.append(
            f'<tr><td class="rank">{i}</td>'
            f'<td class="name"><a href="server/{slug}.html">{_esc(r.name)}</a></td>'
            f'<td class="score">{r.total_score:.1f}</td>'
            f'<td><span class="grade g{r.grade}">{r.grade}</span></td>'
            f'<td class="src">{_esc(r.source)}</td>'
            f'<td class="dims">{dims}</td></tr>')

    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    tagline2 = t["tagline2"].replace("GitHub 仓库", f'<a href="{REPO_URL}">GitHub 仓库</a>') \
                            .replace("GitHub repo", f'<a href="{REPO_URL}">GitHub repo</a>')
    dist = "".join(f'<i class="g{g}" style="width:{pct(g)}%"></i>' for g in "ABCDF")
    grade_opts = "".join(f'<option value="{g}">{g}</option>' for g in "ABCDF")
    src_opts = "".join(f'<option value="{s}">{s}</option>' for s in sources)
    body = f"""
{_brandbar(t, t['switch_href'])}
{_nav(t, en, 'mcp')}
<h1>{t['heading']} <span class="badge">LIVE</span></h1>
<p class="subtitle">{t['tagline']}<br>{tagline2}</p>
<div class="method">{t['method_mcp']}</div>

<div class="stats">
  <div class="stat"><div class="v">{total}</div><div class="l">{t['stat_total']}</div></div>
  <div class="stat"><div class="v">{avg:.1f}</div><div class="l">{t['stat_avg']}</div></div>
  <div class="stat"><div class="v gA">{counts['A']}</div><div class="l">{t['stat_a']}</div><div class="distbar">{dist}</div></div>
  <div class="stat"><div class="v gF">{counts['F']}</div><div class="l">{t['stat_f']}</div></div>
</div>

<div class="toolbar">
  <input type="search" id="tl-search" placeholder="{t['search_ph']}" aria-label="{t['search_ph']}">
  <select id="tl-grade" aria-label="{t['filt_grade']}"><option value="all">{t['filt_grade']}</option>{grade_opts}</select>
  <select id="tl-src" aria-label="{t['filt_src']}"><option value="all">{t['filt_src']}</option>{src_opts}</select>
  <select id="tl-sort" aria-label="{t['sort_label']}"><option value="desc">{t['sort_desc']}</option><option value="asc">{t['sort_asc']}</option><option value="name">{t['sort_name']}</option></select>
  <button id="tl-reset" class="chip" style="display:none">{t['reset']}</button>
  <span class="resultcount" id="tl-count" aria-live="polite">{total} / {total}</span>
</div>

<div class="tablewrap"><table>
<thead><tr>
  <th>{t['col_rank']}</th><th>{t['col_name']}</th><th>{t['col_score']}</th>
  <th>{t['col_grade']}</th><th>{t['col_src']}</th><th>{t['col_dims']}</th>
</tr></thead>
<tbody id="tl-body">{''.join(rows)}</tbody></table></div>

<div class="pager" id="tl-pager"></div>
<div style="text-align:center;opacity:.7;font-size:.86rem" id="tl-pageof"></div>

<script id="tl-data" type="application/json">{json.dumps(data, ensure_ascii=False)}</script>
{_faq_html(t)}
<footer>{t['footer'].format(n=total, ts=ts)}</footer>
{_index_jsonld(reports, t)}
{_faq_jsonld(t)}
{js}
</body></html>"""
    return _head(t, t["title"], "/en/" if en else "/", "/" if en else "/en/", t["switch_href"]) + body


SKILLS_JS = """
<script>
(function(){
var DATA = JSON.parse(document.getElementById('sk-data').textContent);
var L = %(labels)s;
var st = {q:'', grade:'all', sort:'desc', page:1, size:20};
function filtered(){
  var q=st.q.trim().toLowerCase();
  var rows=DATA.filter(function(r){
    if(q && r.name.toLowerCase().indexOf(q)===-1) return false;
    if(st.grade!=='all' && r.grade!==st.grade) return false;
    return true;
  });
  rows.sort(function(a,b){ return st.sort==='asc'?a.score-b.score:b.score-a.score; });
  return rows;
}
function esc(s){var d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}
function rowsHtml(rows){
  var start=(st.page-1)*st.size;
  return rows.slice(start,start+st.size).map(function(r,i){
    return '<tr><td class="rank">'+(start+i+1)+'</td>'+
      '<td class="name"><a href="skill/'+r.slug+'.html">'+esc(r.name)+'</a>'+
      (r.description?'<small>'+esc(r.description)+'</small>':'')+'</td>'+
      '<td class="score" style="color:#'+r.color+'">'+r.score.toFixed(1)+'</td>'+
      '<td><span class="grade g'+r.grade+'">'+r.grade+'</span></td>'+
      '<td class="src">'+esc(r.repo)+'</td>'+
      '<td class="dims">'+r.structure+'</td><td class="dims">'+r.security+'</td>'+
      '<td class="dims">'+(r.llm==null?'—':r.llm)+'</td></tr>';
  }).join('');
}
function pager(rows,tp){
  var cur=st.page,ps=[];
  for(var i=1;i<=tp;i++){ if(i===1||i===tp||(i>=cur-2&&i<=cur+2))ps.push(i); else if(ps[ps.length-1]!=='…')ps.push('…'); }
  var h='<button data-p="'+(cur-1)+'" '+(cur<=1?'disabled':'')+'>'+L.prev+'</button>';
  ps.forEach(function(p){ if(p==='…'){h+='<span style="opacity:.5;padding:0 .2em">…</span>';} else {h+='<button class="pg'+(p===cur?' on':'')+'" data-p="'+p+'">'+p+'</button>';} });
  h+='<button data-p="'+(cur+1)+'" '+(cur>=tp?'disabled':'')+'>'+L.next+'</button>';
  return h;
}
function render(){
  var rows=filtered(), tp=Math.max(1,Math.ceil(rows.length/st.size));
  if(st.page>tp) st.page=tp;
  document.getElementById('sk-body').innerHTML = rows.length?rowsHtml(rows):
    '<tr><td colspan="8"><div class="empty"><div style="font-weight:700">'+L.empty_title+'</div><div>'+L.empty_hint+'</div></div></td></tr>';
  document.getElementById('sk-pager').innerHTML = pager(rows,tp);
  document.getElementById('sk-count').textContent = rows.length+' / '+DATA.length;
  document.getElementById('sk-pageof').textContent = L.page_of.replace('{p}',st.page).replace('{n}',tp);
}
function bind(){
  var si=document.getElementById('sk-search'); si.value=st.q;
  var gd=document.getElementById('sk-grade'); gd.value=st.grade;
  var so=document.getElementById('sk-sort'); so.value=st.sort;
  si.addEventListener('input',function(){st.q=si.value;st.page=1;render();});
  gd.addEventListener('change',function(){st.grade=gd.value;st.page=1;render();});
  so.addEventListener('change',function(){st.sort=so.value;st.page=1;render();});
  document.getElementById('sk-pager').addEventListener('click',function(e){
    var b=e.target.closest('button[data-p]'); if(!b||b.disabled)return;
    st.page=parseInt(b.getAttribute('data-p'),10); render(); window.scrollTo({top:0,behavior:'smooth'});
  });
}
render(); bind();
})();
</script>
"""


def _render_skills_index(skills: list[dict], lang: str, slugs: dict[str, str]) -> str:
    t = T[lang]
    en = lang == "en"
    total = len(skills)
    avg = round(sum(s["total_score"] for s in skills) / total, 1) if total else 0
    counts = {g: sum(1 for s in skills if s["grade"] == g) for g in "ABCDF"}
    pct = lambda g: round(counts[g] * 100 / total, 0) if total else 0

    data = [{"name": s["name"], "slug": slugs[s["url"]], "repo": s["repo"], "url": s["url"],
             "score": s["total_score"],
             "grade": s["grade"], "color": GRADE_COLOR[s["grade"]],
             "structure": int(s["structure"]), "security": int(s["security"]),
             "llm": int(s["llm_quality"]) if s.get("llm_quality") is not None else None,
             "description": s.get("description", "")[:90]}
            for s in sorted(skills, key=lambda x: -x["total_score"])]
    labels = {k: t.get(k, "") for k in ("prev", "next", "page_of", "empty_title", "empty_hint")}
    js = SKILLS_JS % {"labels": json.dumps(labels, ensure_ascii=False)}

    rows = []
    for i, s in enumerate(sorted(skills, key=lambda x: -x["total_score"]), 1):
        llm = f"{s['llm_quality']:.0f}" if s.get("llm_quality") is not None else "—"
        desc = s.get("description", "")
        desc_html = f"<small>{_esc(desc[:90])}</small>" if desc else ""
        rows.append(
            f'<tr><td class="rank">{i}</td>'
            f'<td class="name"><a href="skill/{slugs[s["url"]]}.html">{_esc(s["name"])}</a>{desc_html}</td>'
            f'<td class="score">{s["total_score"]:.1f}</td>'
            f'<td><span class="grade g{s["grade"]}">{s["grade"]}</span></td>'
            f'<td class="src">{_esc(s["repo"])}</td>'
            f'<td class="dims">{s["structure"]:.0f}</td><td class="dims">{s["security"]:.0f}</td>'
            f'<td class="dims">{llm}</td></tr>')

    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    dist = "".join(f'<i class="g{g}" style="width:{pct(g)}%"></i>' for g in "ABCDF")
    grade_opts = "".join(f'<option value="{g}">{g}</option>' for g in "ABCDF")
    body = f"""
{_brandbar(t, t['switch_href'])}
{_nav(t, en, 'skills')}
<h1>{t['sk_heading']} <span class="badge">{t['sk_badge']}</span></h1>
<p class="subtitle">{t['sk_tagline']}</p>
<div class="method">{t['method_skills']}</div>

<div class="stats">
  <div class="stat"><div class="v">{total}</div><div class="l">{t['sk_stat_total']}</div></div>
  <div class="stat"><div class="v">{avg:.1f}</div><div class="l">{t['sk_stat_avg']}</div></div>
  <div class="stat"><div class="v gA">{counts['A']}</div><div class="l">{t['stat_a']}</div><div class="distbar">{dist}</div></div>
  <div class="stat"><div class="v gF">{counts['F']}</div><div class="l">{t['stat_f']}</div></div>
</div>

<div class="toolbar">
  <input type="search" id="sk-search" placeholder="{t['search_ph']}" aria-label="{t['search_ph']}">
  <select id="sk-grade" aria-label="{t['filt_grade']}"><option value="all">{t['filt_grade']}</option>{grade_opts}</select>
  <select id="sk-sort" aria-label="{t['sort_label']}"><option value="desc">{t['sort_desc']}</option><option value="asc">{t['sort_asc']}</option></select>
  <span class="resultcount" id="sk-count" aria-live="polite">{total} / {total}</span>
</div>

<div class="tablewrap"><table>
<thead><tr><th>{t['col_rank']}</th><th>{t['sk_col_skill']}</th><th>{t['col_score']}</th><th>{t['col_grade']}</th>
<th>{t['sk_col_repo']}</th><th>{t['sk_col_struct']}</th><th>{t['sk_col_sec']}</th><th>{t['sk_col_llm']}</th></tr></thead>
<tbody id="sk-body">{''.join(rows)}</tbody></table></div>

<div class="pager" id="sk-pager"></div>
<div style="text-align:center;opacity:.7;font-size:.86rem" id="sk-pageof"></div>
<script id="sk-data" type="application/json">{json.dumps(data, ensure_ascii=False)}</script>
{_faq_html(t)}
<footer>{t['footer'].format(n=total, ts=ts)}</footer>
{_faq_jsonld(t)}
{js}
</body></html>"""
    return _head(t, t["sk_meta_title"], f"{'/en/' if en else '/'}skills.html",
                 f"{'' if en else '/en/'}skills.html", "") + body


def _render_detail(r: ServerReport, lang: str, install_cmd: list[str] | None = None) -> str:
    t = T[lang]
    en = lang == "en"
    slug = slugify(r.name)
    back_href = "../"
    toggle_href = f"../../server/{slug}.html" if en else f"../en/server/{slug}.html"
    dims_html = []
    for key, dim in r.dimensions.items():
        findings = "".join(
            f'<div class="finding {"crit" if f.severity == "critical" else "warn" if f.severity == "warning" else ""}">'
            f"[{_esc(f.code)}] {_esc(f.message)}</div>" for f in dim.findings)
        dims_html.append(f'<div class="dim"><b>{DIM_LABEL[lang].get(key, key)} {dim.value:.1f}</b>{findings}</div>')
    no_desc_html = f"<i>{t['no_desc']}</i>"
    tool_items = []
    for t2 in r.tools:
        desc = _esc(t2.description[:160]) if t2.description else no_desc_html
        tool_items.append(f"<li><code>{_esc(t2.name)}</code> — {desc}</li>")
    tools_html = "".join(tool_items) or "<li>—</li>"
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(r.evaluated_at))
    error = f'<p class="crit">{t["error_prefix"]}{_esc(r.error)}</p>' if r.error else ""

    # 来源与安装（让用户看完分就能直接装）
    srcbox = ""
    if install_cmd:
        cmd_text = " ".join(install_cmd)
        pkg_url = _pkg_url(install_cmd[0], install_cmd[1:]) if len(install_cmd) > 1 else ""
        if install_cmd[0] == "{python}":
            srcbox = (f'<div class="srcbox"><h2>{t["srcbox_heading"]}</h2>'
                      f'<div class="inst"><span>{t["src_label"]}</span><code>{_esc(r.source or "?")}</code></div>'
                      f'<div class="inst"><span>{t["install_label"]}</span><span>{t["no_install"]}</span></div></div>')
        else:
            pkg_html = (f'<div class="inst"><span>{t["pkg_label"]}</span>'
                        f'<a href="{pkg_url}" target="_blank" rel="noopener">{_esc(pkg_url)}</a></div>') if pkg_url else ""
            mcp_add = t["install_mcp_prefix"].format(name=r.name) + " " + cmd_text
            srcbox = (f'<div class="srcbox"><h2>{t["srcbox_heading"]}</h2>'
                      f'<div class="inst"><span>{t["src_label"]}</span><code>{_esc(r.source or "?")}</code></div>'
                      f'<div class="inst"><span>{t["install_label"]}</span><code>{_esc(cmd_text)}</code>'
                      f'<button class="copybtn">{t["copy"]}</button></div>'
                      f'<div class="insthint">{_esc(t["install_mcp_hint"])}</div>'
                      f'<div class="inst"><code>{_esc(mcp_add)}</code>'
                      f'<button class="copybtn">{t["copy"]}</button></div>'
                      f'{pkg_html}</div>')

    body = f"""
{_brandbar(t, toggle_href)}
<p><a href="{back_href}">{t['back']}</a></p>
<h1>{_esc(r.name)}</h1>
<p class="subtitle">{t['score_line']} <span class="score">{r.total_score:.1f}/100</span> · {_grade_badge(r.grade, lang)}</p>
{srcbox}
{error}
<h2>{t['dims_heading']}</h2>{''.join(dims_html)}
<h2>{t['tools_heading'].format(n=len(r.tools))}</h2><ul>{tools_html}</ul>
<footer>{t['report_footer'].format(ts=ts, v=r.engine_version, src=_esc(r.source) or '?')}</footer>
{COPY_JS % {"copied": t["copied"]}}
</body></html>"""
    title = t["report_title"].format(name=r.name)
    path = f"{'/en' if en else ''}/server/{slug}.html"
    alt = f"{'' if en else '/en'}/server/{slug}.html"
    return _head(t, title, path, alt, toggle_href) + body


def _render_skill_detail(s: dict, lang: str, slug: str) -> str:
    t = T[lang]
    en = lang == "en"
    name_display = s["name"].split("/")[-1] if "/" in s["name"] else s["name"]
    back_href = "../"
    toggle_href = f"../../skill/{slug}.html" if en else f"../en/skill/{slug}.html"

    # 三维评分
    dims = [
        ("structure", t["sk_dim_struct"], s.get("structure")),
        ("security", t["sk_dim_sec"], s.get("security")),
        ("llm_quality", t["sk_dim_llm"], s.get("llm_quality")),
    ]
    dims_html = []
    for key, label, val in dims:
        if val is None:
            dims_html.append(f'<div class="dim"><b>{label}</b><div class="finding">{_esc(t["sk_llm_none"])}</div></div>')
        else:
            dims_html.append(f'<div class="dim"><b>{label} {float(val):.0f}</b></div>')

    # 安全发现
    findings = s.get("findings") or []
    if findings:
        fhtml = "".join(
            f'<div class="finding {"crit" if f.get("severity") == "critical" else "warn" if f.get("severity") == "warning" else ""}">'
            f"[{_esc(f.get('code', ''))}] {_esc(f.get('message', ''))}</div>" for f in findings)
    else:
        fhtml = f'<div class="finding">{_esc(t["sk_no_findings"])}</div>'

    # LLM 可执行性点评
    llm_reason = s.get("llm_reason")
    llm_html = f'<div class="finding">{_esc(llm_reason)}</div>' if llm_reason else ""

    # 来源与安装（看完分即可 clone / 找到 SKILL.md）
    repo = s.get("repo", "")
    repo_url = f"https://github.com/{repo}" if repo else ""
    s_url = s.get("url", "")
    clone_cmd = f"git clone https://github.com/{repo}.git" if repo else ""
    srcbox = (f'<div class="srcbox"><h2>{t["srcbox_heading"]}</h2>'
              f'<div class="inst"><span>{t["repo_label"]}</span>'
              f'<a href="{repo_url}" target="_blank" rel="noopener">{_esc(repo)}</a></div>'
              f'<div class="inst"><span>{t["skill_path_label"]}</span><code>{_esc(s.get("path", ""))}</code></div>'
              f'<div class="inst"><span>{t["install_label"]}</span><code>{_esc(clone_cmd)}</code>'
              f'<button class="copybtn">{t["copy"]}</button></div>'
              f'<div class="inst"><span>📋</span>{_esc(t["install_skill_hint"])}</div>'
              f'<div class="inst"><a href="{s_url}" target="_blank" rel="noopener">{t["view_skill"]} →</a></div></div>')

    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(s.get("evaluated_at", 0)))
    meta = t["sk_meta"].format(ts=ts, chars=int(s.get("md_chars", 0)),
                               scripts=int(s.get("script_count", 0)),
                               fm=t["fm_yes"] if s.get("has_frontmatter") else t["fm_no"])
    desc_html = f'<p class="subtitle">{_esc(s.get("description", ""))}</p>' if s.get("description") else ""
    body = f"""
{_brandbar(t, toggle_href)}
<p><a href="{back_href}">{t['sk_back']}</a></p>
<h1>{_esc(name_display)} <span class="badge">{t['sk_badge']}</span></h1>
{desc_html}
<p class="subtitle">{t['score_line']} <span class="score">{s['total_score']:.1f}/100</span> · {_grade_badge(s['grade'], lang)}</p>
{srcbox}
<h2>{t['sk_dims_heading']}</h2>{''.join(dims_html)}
<h2>{t['sk_findings_heading']}</h2>{fhtml}
{f'<h2>{t["sk_llm_heading"]}</h2>{llm_html}' if llm_html else ''}
<footer>{_esc(meta)}</footer>
{COPY_JS % {"copied": t["copied"]}}
</body></html>"""
    title = t["sk_report_title"].format(name=name_display)
    path = f"{'/en' if en else ''}/skill/{slug}.html"
    alt = f"{'' if en else '/en'}/skill/{slug}.html"
    return _head(t, title, path, alt, toggle_href) + body


def _render_sitemap(reports: list[ServerReport], skills: list[dict] | None = None,
                    skill_slugs: dict[str, str] | None = None) -> str:
    today = time.strftime("%Y-%m-%d", time.gmtime())

    def url(loc: str) -> str:
        return f"  <url><loc>{BASE_URL}{loc}</loc><lastmod>{today}</lastmod></url>"

    locs = ["/", "/en/", "/skills.html", "/en/skills.html"]
    for r in reports:
        slug = slugify(r.name)
        locs += [f"/server/{slug}.html", f"/en/server/{slug}.html"]
    for s in skills or []:
        slug = (skill_slugs or {}).get(s.get("url", "")) or slugify(s.get("name", ""))
        if slug and slug != "unnamed":
            locs += [f"/skill/{slug}.html", f"/en/skill/{slug}.html"]
    body = "\n".join(url(l) for l in locs)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def _render_robots() -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"


def build_site(results_dir: Path | None = None, dist: Path | None = None) -> Path:
    dist = Path(dist) if dist else DIST
    reports = load_all(results_dir)
    skills = load_skills()
    skill_slugs = _skill_slugs(skills)

    # 从 servers.json 取启动命令，供详情页展示安装方式
    install_map: dict[str, list[str]] = {}
    servers_file = Path("data/servers.json")
    if servers_file.exists():
        try:
            for s in json.loads(servers_file.read_text(encoding="utf-8")).get("servers", []):
                install_map[s["name"]] = [s.get("command", ""), *s.get("args", [])]
        except (json.JSONDecodeError, KeyError):
            pass

    # 详情页目录先清空再重建（slug 会随消歧/改名变化，避免残留陈旧页面）
    for sub in ("server", "skill", "en/server", "en/skill"):
        d = dist / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(_render_index(reports, "zh"), encoding="utf-8")
    (dist / "en" / "index.html").write_text(_render_index(reports, "en"), encoding="utf-8")
    (dist / "skills.html").write_text(_render_skills_index(skills, "zh", skill_slugs), encoding="utf-8")
    (dist / "en" / "skills.html").write_text(_render_skills_index(skills, "en", skill_slugs), encoding="utf-8")
    for r in reports:
        slug = slugify(r.name)
        cmd = install_map.get(r.name)
        (dist / "server" / f"{slug}.html").write_text(_render_detail(r, "zh", install_cmd=cmd), encoding="utf-8")
        (dist / "en" / "server" / f"{slug}.html").write_text(_render_detail(r, "en", install_cmd=cmd), encoding="utf-8")
    for s in skills:
        slug = skill_slugs[s["url"]]
        (dist / "skill" / f"{slug}.html").write_text(_render_skill_detail(s, "zh", slug), encoding="utf-8")
        (dist / "en" / "skill" / f"{slug}.html").write_text(_render_skill_detail(s, "en", slug), encoding="utf-8")
    (dist / "sitemap.xml").write_text(_render_sitemap(reports, skills, skill_slugs), encoding="utf-8")
    (dist / "robots.txt").write_text(_render_robots(), encoding="utf-8")
    return dist
