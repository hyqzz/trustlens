# I benchmarked 119 real MCP servers — 55% are unusable out of the box. So I built a "quality inspection" lab for the agent ecosystem.

> Project: https://github.com/hyqzz/trustlens
> Live leaderboard (119 servers, searchable/filterable/paginated, auto-updated weekly): https://trustlens.icodestar.net/en/

## The problem

Less than two years after MCP shipped, there are **60,000+ public MCP servers** — and:

- Cross-registry security research finds **66% have security issues**
- **88% of enterprise agent pilots never reach production** — not because models are weak, but because nobody can vouch for the tools
- Before installing any MCP server, there is **nowhere** to check whether it actually works or is safe

The ecosystem has app stores, but no review system. Thousands of products, no quality inspection.

## Large-scale measurement: 55% of public servers are unusable

I took **122 real MCP servers published on npm/PyPI** (official reference implementations + community servers), and evaluated **119** in an isolated, **zero-credential** environment:

| Grade | Count | Share | Meaning |
|---|---|---|---|
| A | 9 | 8% | Works out of the box |
| B | 12 | 10% | Usable, minor issues |
| C | 25 | 21% | Mediocre |
| D | 7 | 6% | Risky |
| **F** | **66** | **55%** | **Cannot be used** |

**More than half of public MCP servers, installed per their README with no extra credentials, never even complete a protocol handshake.** Failure modes:

- **Startup hang / no response (55)**: the process starts but never completes initialize within 90s — many silently wait for undocumented config or interactive input
- **Requires API credentials just to boot (7)**: crashes on a missing key the docs never mention
- **SDK compatibility crash (3)**: official Python servers crash on import after the mcp SDK renamed `McpError` → `MCPError`

Three more (puppeteer, @enfyra, @mapbox) are paused pending methodology — they hard-hang the harness, which itself flags a gap: browser-automation tools need type-aware probes, not blind ones.

**The good news:** `ref-tools-mcp`, `duckduckgo-search`, `ifconfig-mcp` score A or perfect. **"Popular" and "usable" are different things; "obscure" and "reliable" are different things too.**

## What TrustLens is

An open-source trust benchmark for the agent capability ecosystem:

1. **Automated evaluation pipeline**: sandboxed deployment → protocol handshake → static security scan (prompt injection / exfiltration / hardcoded credentials) → real probe calls → multi-model compatibility → 0–100 trust score
2. **Public leaderboard**: bilingual (EN/中文), **search, filter by grade/source, sort, paginate**, one inspection report per server
3. **CLI**: check before you install

```bash
python -m trustlens check <server-name>
```

**All evaluation data is committed to the repo as JSON — git history is the audit log.** A trust product has to be transparent itself.

## Methodology (stated plainly)

- Servers run in **env-stripped, sandboxed processes** — they get **zero credentials**
- **Out-of-the-box criterion**: start via the standard `npx -y <pkg>`, no config, no API key; handshake must complete within 90s
- This is deliberate: **a server that needs you to hunt through docs for a key just to boot is unusable for most users**
- Pipeline re-runs weekly and publishes automatically

## Roadmap & feedback wanted

1. **Capability trust** (now): expand to the Skills ecosystem; real-model tool-call accuracy across GPT/Claude/Qwen/DeepSeek — **no public dataset exists for Chinese models today**
2. **Behavior trust**: agent track-record reputation (W3C VC/DID, ERC-8004)
3. **Transaction trust**: a credit layer for the agent economy

Questions for you:

- Would you check a score before installing an MCP server? What report would actually help you decide?
- Is the 90s handshake "out-of-the-box" criterion fair?
- Should the dimension weights shift (functionality 35 / reliability 25 / security 25 / compatibility 15)?

Stars, issues, and harsh criticism welcome: https://github.com/hyqzz/trustlens

---

Built by ICodeStar (智码星). Long-term project — weekly updates, committed for years, not weeks.
