"""Agent Skills 评估：SKILL.md 静态质量 + 安全扫描 + 便宜模型质量评分。

Skills 不是 MCP 服务器，评测对象是 SKILL.md 文档（含 frontmatter + 指令 + 引用脚本）。
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .checks import CREDENTIAL_PATTERNS, INJECTION_PATTERNS
from .llm import OpenAICompatProvider, ToolUseProvider
from .models import Finding, grade_of

SKILLS_DIR = Path("data/skills")

# ---- 精选策略：官方 + 知名策展集合全取，巨量集合跨域抽样 ----
CURATED_REPOS = ["anthropics/skills", "antfu/skills", "vercel-labs/agent-skills",
                 "addyosmani/agent-skills", "obra/superpowers", "browserbase/skills"]
MEGA_REPOS = ["sickn33/agentic-awesome-skills", "ComposioHQ/awesome-claude-skills",
              "alirezarezvani/claude-skills", "mukul975/Anthropic-Cybersecurity-Skills",
              "thedaviddias/Front-End-Checklist", "affaan-m/ECC", "K-Dense-AI/scientific-agent-skills"]


def curate(candidates: list[dict], target: int = 110) -> list[dict]:
    """优先官方与策展集合，再从巨量集合跨域抽样到 target。"""
    picked: list[dict] = []
    seen: set[str] = set()

    def take(c: dict) -> bool:
        k = (c["repo"], c["path"])
        if k in seen:
            return False
        if "/template" in c["path"] or c["path"].endswith("template/SKILL.md"):
            return False
        seen.add(k)
        picked.append(c)
        return True

    by_repo: dict[str, list[dict]] = {}
    for c in candidates:
        by_repo.setdefault(c["repo"], []).append(c)

    for repo in CURATED_REPOS:
        for c in by_repo.get(repo, []):
            take(c)

    # 巨量集合：每个仓库抽若干条，优先路径较浅（更像独立 skill）的
    for repo in MEGA_REPOS:
        items = by_repo.get(repo, [])
        items = sorted(items, key=lambda c: c["path"].count("/"))
        for c in items:
            if len(picked) >= target:
                break
            take(c)
        if len(picked) >= target:
            break

    # 兜底：任意候选补足
    for c in candidates:
        if len(picked) >= target:
            break
        take(c)
    return picked


def _raw(url: str, timeout: float = 20.0) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": "trustlens-skills/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _referenced_scripts(md: str, base_dir_url: str) -> list[str]:
    """从 SKILL.md 文本里提取引用的脚本文件名，构造其 raw 地址。"""
    scripts = []
    for m in re.finditer(r"(?:`|\)|>|\s)((?:\./)?(?:scripts?/)?[\w.\-]+\.(?:py|sh|js|ts|mjs|rb|pl))\b", md):
        name = m.group(1).lstrip("./")
        if name not in scripts:
            scripts.append(name)
    return scripts[:5]


def evaluate_skill(cand: dict, llm: ToolUseProvider | None = None,
                   timeout: float = 20.0) -> dict:
    """评估一个 skill，返回可序列化报告。"""
    repo, path = cand["repo"], cand["path"]
    base_url = cand["url"].rsplit("/", 1)[0]
    md = _raw(cand["url"], timeout) or ""
    scripts: dict[str, str] = {}
    for s in _referenced_scripts(md, base_url):
        content = _raw(base_url + "/" + urllib.parse.quote(s), timeout)
        if content is not None:
            scripts[s] = content

    # ---- 静态结构评分 ----
    findings: list[Finding] = []
    stats = {"md_chars": len(md), "script_count": len(scripts)}
    front = re.match(r"^---\s*\n(.*?)\n---\s*\n?", md, re.S)
    fm = {}
    if front:
        for line in front.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    has_name = bool(fm.get("name"))
    has_desc = bool(fm.get("description"))
    body = md[front.end():] if front else md
    has_steps = bool(re.search(r"(步骤|step\s*1|Step 1|#{2,3}\s|1\.\s|1\)\s)", body))
    has_example = bool(re.search(r"(example|示例|Example|例如)", body, re.I))

    struct = 0
    if has_name:
        struct += 15
    if has_desc:
        struct += 15
    if len(body) >= 200:
        struct += 20
    if has_steps:
        struct += 25
    if has_example:
        struct += 10
    if len(body) >= 800:
        struct += 15
    if not has_name:
        findings.append(Finding("warning", "SKILL-NONAME", "SKILL.md 缺少 name frontmatter"))
    if not has_desc:
        findings.append(Finding("warning", "SKILL-NODESC", "SKILL.md 缺少 description frontmatter"))

    # ---- 安全扫描（SKILL.md + 引用的脚本）----
    haystack = md + "\n" + "\n".join(scripts.values())
    sec = 100
    for pattern, code, msg in INJECTION_PATTERNS + CREDENTIAL_PATTERNS:
        if re.search(pattern, haystack, re.IGNORECASE if code.startswith("SEC-") else 0):
            sec -= 30
            findings.append(Finding("critical" if sec <= 40 else "warning", code, f"{msg}"))
    if re.search(r"\b(curl|wget)\b[^\n]{0,60}\|\s*(sudo\s+)?(bash|sh)\b", haystack):
        sec -= 30
        findings.append(Finding("critical", "SKILL-PIPEBASH", "疑似 curl|bash 远程代码执行"))
    if re.search(r"\brm\s+-rf\s+[/~]", haystack):
        sec -= 30
        findings.append(Finding("critical", "SKILL-RM", "含危险删除命令"))

    # ---- LLM 质量评分（可选，便宜模型）----
    llm_score = None
    llm_note = ""
    if llm is not None and md and hasattr(llm, "complete"):
        prompt = (
            "你是一个 Agent Skills 质量评估器。以下是某个技能的 SKILL.md 文档。"
            "请从【可执行性】打分：指令是否清晰、步骤是否可落地、是否足够详细、模型能否照着做。"
            f"\n\n--- SKILL.md 开始 ---\n{md[:3500]}\n--- SKILL.md 结束 ---\n\n"
            '只输出一个 JSON：{"score": 0到100的整数, "reason": "一句话理由"}'
        )
        text, err = llm.complete(prompt, max_tokens=200)
        if not err and text:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    llm_score = float(parsed.get("score", 60))
                    llm_note = str(parsed.get("reason", ""))[:120]
                except Exception:
                    llm_note = text[:120]
            else:
                llm_note = text[:120]
        else:
            llm_note = (err or "无输出")[:120]

    # ---- 合成总分（权重已是 100 制，勿再乘 100）----
    struct_ratio = min(struct / 100.0, 1.0)
    sec_ratio = max(sec, 0) / 100.0
    if llm_score is not None:
        total = 40 * struct_ratio + 30 * sec_ratio + 30 * (llm_score / 100)
    else:
        total = 60 * struct_ratio + 40 * sec_ratio
    total = round(min(total, 100), 1)

    return {
        "name": cand["skill"],
        "repo": repo,
        "url": f"https://github.com/{repo}/blob/HEAD/{path}",
        "path": path,
        "description": (fm.get("description") or "")[:140],
        "md_chars": stats["md_chars"],
        "script_count": stats["script_count"],
        "has_frontmatter": bool(front),
        "structure": round(struct, 1),
        "security": round(max(sec, 0), 1),
        "llm_quality": llm_score,
        "llm_reason": llm_note,
        "total_score": total,
        "grade": grade_of(total),
        "findings": [{"severity": f.severity, "code": f.code, "message": f.message} for f in findings],
        "evaluated_at": time.time(),
    }


def evaluate_all(llm: ToolUseProvider | None = None, target: int = 110,
                 candidates_file: Path = Path("data/skills-candidates.json"),
                 timeout: float = 20.0) -> list[dict]:
    candidates = json.loads(candidates_file.read_text(encoding="utf-8"))
    picked = curate(candidates, target)
    reports = []
    ok = 0
    for i, cand in enumerate(picked, 1):
        r = evaluate_skill(cand, llm, timeout)
        reports.append(r)
        if r["md_chars"] > 0:
            ok += 1
        print(f"[{i}/{len(picked)}] {r['name']}: {r['total_score']} ({r['grade']}) "
              f"结构{r['structure']} 安全{r['security']} "
              f"{'LLM' + str(r['llm_quality']) if r['llm_quality'] is not None else ''}")
    print(f"完成：{len(picked)} 个 skill 已评测（{ok} 个可获取内容）")
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    (SKILLS_DIR / "skills.json").write_text(json.dumps(reports, ensure_ascii=False, indent=1), encoding="utf-8")
    return reports
