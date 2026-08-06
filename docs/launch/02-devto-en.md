# I benchmarked 16 MCP servers — all four official Python servers fail to start. So I built a trust benchmark.

> Project: https://github.com/hyqzz/trustlens
> Live leaderboard (auto-updated weekly): https://trustlens.icodestar.net/en/

## The problem

Less than two years after MCP shipped, there are **60,000+ public MCP servers** — and:

- Cross-registry security research finds **66% have security issues**
- **88% of enterprise agent pilots never reach production** — not because models are weak, but because nobody can vouch for the tools
- Before installing any MCP server, there is **nowhere** to check whether it actually works or is safe

The ecosystem has app stores, but no review system. Thousands of products, no quality inspection.

## First real data: the official Python servers are all broken

I ran my automated evaluation engine against 16 servers — official reference implementations and popular community projects:

| Server | Source | Trust score | Verdict |
|---|---|---|---|
| memory | official | 90.7 (A) | Healthiest official server |
| context7 | Upstash | 89.3 (B) | Best third-party |
| everything | official | 82.5 (B) | Works, 20% call failure rate |
| filesystem | official | 68.5 (C) | **80% of probe calls error out** |
| playwright | Microsoft | 64.0 (C) | Big-tech built, middling score |
| desktop-commander | community | 53.2 (D) | Hugely popular, worrying quality |
| sequential-thinking | official | 47.2 (D) | Official, but D grade |
| **duckduckgo-search** | community | **98.9 (A)** | **Top scorer** |
| excel | community | 64.0 (C) | Middling |
| commands | community | 64.0 (C) | Middling |
| **time / fetch / git / sqlite / weather** | 4 official + 1 community | 25.0 (F) | **None of them start** |

Three facts that should make you pause:

1. **All four archived official Python servers fail to boot.** The `mcp` SDK renamed `McpError` to `MCPError`; the servers never caught up — they crash on import. Run `uvx mcp-server-time` today and it dies in front of you.
2. **"Installable" ≠ "usable"**: filesystem handshakes and lists tools fine, but 80% of real probe calls return errors.
3. **Popular ≠ reliable**: desktop-commander has massive downloads and scores a D.

READMEs don't tell you this. Measured data does.

## What TrustLens is

An open-source trust benchmark for the agent capability ecosystem:

1. **Automated evaluation pipeline**: sandboxed deployment → protocol handshake → static security scan (prompt injection / exfiltration / hardcoded credentials) → real probe calls → multi-model compatibility → 0–100 trust score
2. **Public leaderboard**: bilingual (EN/中文), auto-updated weekly, one inspection report per server
3. **CLI**: check before you install

```bash
python -m trustlens check <server-name>
```

**All evaluation data is committed to the repo as JSON — git history is the audit log.** A trust product has to be transparent itself.

## Roadmap & feedback wanted

1. **Capability trust** (now): top 100 registry servers + Agent Skills; real-model tool-call accuracy across GPT/Claude/Qwen/DeepSeek — **no public dataset exists for Chinese models today**
2. **Behavior trust**: agent track-record reputation (W3C VC/DID, ERC-8004)
3. **Transaction trust**: a credit layer for the agent economy

Questions for you:

- Would you check a score before installing an MCP server? What report would actually help you decide?
- Which servers should we evaluate next?
- Are the four dimensions weighted sensibly (functionality 35 / reliability 25 / security 25 / compatibility 15)?

Stars, issues, and harsh criticism welcome: https://github.com/hyqzz/trustlens
