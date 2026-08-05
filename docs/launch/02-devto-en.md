# I benchmarked 6 official MCP servers — 2 of them don't even start. That's why I built TrustLens.

> Project: https://github.com/hyqzz/trustlens
> Live leaderboard (auto-updated weekly): https://hyqzz.github.io/trustlens/

## The problem

Less than two years after MCP shipped, there are **60,000+ public MCP servers** — and:

- Cross-registry security research finds **66% have security issues**
- **88% of enterprise agent pilots never reach production** — not because models are weak, but because nobody can vouch for the tools
- Before you install any MCP server, there is **nowhere** to check whether it actually works or is safe

The ecosystem has app stores, but no review system. Thousands of products, no quality inspection.

## First batch of real data: even official servers fail

TrustLens' first evaluation batch covered 6 servers, including official reference implementations:

| Server | Source | Trust score | Verdict |
|---|---|---|---|
| memory | official | 90.7 (A) | Works well |
| everything | official | 82.5 (B) | Works, 20% call failure rate |
| filesystem | official | 68.5 (C) | Works, but 80% of probe calls error out |
| **time** | official | 25.0 (F) | **Doesn't start**: incompatible with the current `mcp` SDK — `McpError` was renamed to `MCPError`, crashes on import |
| **fetch** | official | 25.0 (F) | **Same disease**, same ImportError |
| mock-echo | built-in poisoned fixture | 75.0 | Security scan caught 4 poisoning behaviors (prompt injection, exfiltration) |

Two takeaways:

1. **Two official Python servers don't even boot with the current SDK.** If you `uvx mcp-server-time` today, it crashes on your user's machine. You'd never know without measured data — READMEs don't tell you this.
2. filesystem's 80% call failure rate shows that **"installable" and "usable" are very different things.**

That's what TrustLens measures: **evidence, not claims.**

## What TrustLens is

An open-source trust benchmark for the agent capability ecosystem:

1. **Automated evaluation pipeline**: sandboxed deployment → protocol handshake → static security scan (prompt injection / exfiltration / hardcoded credentials) → real probe calls → multi-model compatibility scoring → 0–100 trust score
2. **Public leaderboard**: auto-updated weekly, one inspection report per server
3. **CLI**: check before you install

```bash
python -m trustlens check <server-name>
```

**All evaluation data is committed to the repo as JSON — git history is the audit log.** A trust product has to be transparent itself.

## Roadmap & what I need from you

1. **Capability trust** (in progress): expand to top 100 registry servers + Agent Skills; real-model tool-call accuracy across GPT/Claude/Qwen/DeepSeek — **no public dataset exists for Chinese models today**
2. **Behavior trust**: agent track-record reputation (aligned with W3C VC/DID, ERC-8004)
3. **Transaction trust**: a credit layer for the agent economy

Feedback wanted:

- Would you check a score before installing an MCP server? What report would actually help you decide?
- Which servers should we evaluate first?
- Are the four dimensions (functionality / reliability / security / cross-model compatibility) weighted sensibly?

Stars, issues, and harsh criticism all welcome: https://github.com/hyqzz/trustlens
