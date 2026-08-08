# I benchmarked 118 real MCP servers (55% unusable) + 110 Agent Skills. So I built a "quality inspection" lab for the agent ecosystem.

> Project: https://github.com/hyqzz/trustlens
> Live leaderboard (118 MCP servers + 110 Skills, searchable/filterable/paginated, auto-updated weekly): https://trustlens.icodestar.net/en/

## The problem

Less than two years after MCP shipped, there are **60,000+ public MCP servers** — and:

- Cross-registry security research finds **66% have security issues**
- **88% of enterprise agent pilots never reach production** — not because models are weak, but because nobody can vouch for the tools
- Before installing any MCP server, there is **nowhere** to check whether it actually works or is safe

The ecosystem has app stores, but no review system. Thousands of products, no quality inspection.

## Large-scale measurement: 55% of public servers are unusable

I took **122 real MCP servers published on npm/PyPI** (official reference implementations + community servers), and evaluated them in an isolated, **zero-credential** environment. Three (puppeteer, @enfyra, @mapbox) are paused pending methodology, and our built-in self-test fixture is not ranked — the leaderboard covers **118 real servers**:

| Grade | Count | Share | Meaning |
|---|---|---|---|
| A | 1 | 1% | Works out of the box |
| B | 14 | 12% | Usable, minor issues |
| C | 30 | 25% | Mediocre |
| D | 5 | 4% | Risky |
| **F** | **68** | **58%** | **Cannot be used** |

**More than half of public MCP servers, installed per their README with no extra credentials, never even complete a protocol handshake.** Failure modes (audited from each process's stderr):

- **Runtime crash / code error (30)**: the process dies within the handshake window (JS/Python stack, module load failure)
- **Requires API credentials just to boot (15)**: crashes on a missing key the docs never mention
- **Package resolution / compatibility (11)**: `npx` can't even find an executable entry, or deps fail to install
- **Genuine startup hang (9)**: the process starts but never completes initialize within 90s — many silently wait for undocumented config or interactive input

**The good ones exist:** exactly one server earns an A — `ifconfig-mcp` (100). Even high-scoring favorites like `ref-tools-mcp` (85) and `duckduckgo-search` (84) fall short. Meanwhile the hugely popular official `filesystem` server scores just 72 (C) and `desktop-commander` sits at 54 (D). **"Popular" and "usable" are different things; "obscure" and "reliable" are different things too.**

## What TrustLens is

An open-source trust benchmark for the agent capability ecosystem — two evaluations, one UI:

1. **MCP server QA pipeline**: sandboxed deployment → protocol handshake → static security scan (prompt injection / exfiltration / hardcoded credentials) → real probe calls → **real tool-call evaluation by DeepSeek-V4 Flash** → 0–100 trust score
2. **Agent Skills evaluation**: structure + security + LLM-measured actionability of each SKILL.md — **110 real Skills evaluated** (official and community repos on GitHub)
3. **Public leaderboard**: bilingual (EN/中文), MCP + Skills tabs, **search, filter, sort, paginate**, one inspection report per server, auto-updated weekly

```bash
python -m trustlens check <server-name>
```

**All evaluation data is committed to the repo as JSON — git history is the audit log.** A trust product has to be transparent itself.

## Why real-model tool-call measurement matters

Every MCP server has a "model tool-call" score — not a static estimate, but **DeepSeek-V4 Flash actually reading each tool's definition and judging whether it would call it and could construct valid arguments.** Nobody has published this data: **for a given tool, can a model actually use it?**

## Methodology (stated plainly)

- Servers run in **env-stripped, sandboxed processes** — they get **zero credentials**
- **Out-of-the-box criterion**: start via the standard `npx -y <pkg>`, no config, no API key; handshake must complete within 90s. This is deliberate: **a server that needs you to hunt for a key just to boot is unusable for most users**
- **Fail-fast guardrail**: 2 consecutive tool-call timeouts → the server is judged unusable for calls and the remaining probes are skipped (otherwise one pathological server can stall an entire evaluation round)
- Model tool-call scores come from real calls by **DeepSeek-V4 Flash** (cheapest tier)
- **Boundary of the security dimension**: a static text-pattern scan that catches obvious prompt-injection, exfiltration-style commands and hardcoded credentials — it **cannot detect runtime exfiltration or covert behavior; a 100 security score is not a safety certification**. The '66% have security issues' figure is an external research finding, measured under a different methodology than this leaderboard
- Skills: structure completeness + security scan + model actionability judgment
- Pipeline re-runs weekly and publishes automatically

## Roadmap & feedback wanted

1. **Capability trust** (now): **DeepSeek-V4 Flash** real tool-call accuracy is live (cheapest tier); planning to expand to multi-model comparison — **no public dataset exists for Chinese models today**
2. **Behavior trust**: agent track-record reputation (W3C VC/DID, ERC-8004)
3. **Transaction trust**: a credit layer for the agent economy

Questions for you:

- Would you check a score before installing an MCP server? What report would actually help you decide?
- Is the 90s handshake "out-of-the-box" criterion fair?
- Should the dimension weights shift (functionality 35 / reliability 25 / security 25 / compatibility 15)?

Stars, issues, and harsh criticism welcome: https://github.com/hyqzz/trustlens

---

Built by ICodeStar (智码星). Long-term project — weekly updates, committed for years, not weeks.
