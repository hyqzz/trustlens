# Reddit 投稿

**目标 subreddit（按优先级）**：r/mcp、r/LocalLLaMA、r/selfhosted、r/opensource

**Title:**
I benchmarked 119 real MCP servers — 55% are unusable out of the box, and the official Python servers crash on import. Open-source leaderboard inside.

**Body:**
Like many of you, I've been installing MCP servers blind. There are 60k+ now, and the only "signal" is GitHub stars — which say nothing about whether a server boots, behaves, or is safe.

So I built TrustLens: an evaluation engine that sandboxes each server, runs the MCP handshake, statically scans for prompt injection / data exfiltration / hardcoded credentials, makes real probe calls (latency + failure rate), and checks multi-model tool-call compatibility. Output is a 0–100 trust score, and every byte of evidence is committed to the repo as JSON.

I ran 119 real npm/PyPI servers through it in a zero-credential, out-of-the-box setup:
- **Only 9 (8%) grade A.** 66 (55%) are F — never complete a handshake with the standard `npx -y <pkg>` and no config.
- Failure modes: startup hang (55), crash on missing API key (7), SDK compat crash (3) — including official Python servers dying on import after `McpError` → `MCPError`.
- The good ones exist: ref-tools-mcp 100, duckduckgo-search 99.8, ifconfig-mcp 96.

Leaderboard (EN/中文, search/filter/sort/pagination, weekly auto-update): https://trustlens.icodestar.net/en/
Repo: https://github.com/hyqzz/trustlens (Apache-2.0, zero-dependency Python)

Questions I genuinely want input on:
1. Is the 90s-handshake "out-of-the-box" criterion fair, or should setup-required servers get partial credit?
2. Which servers should the next batch cover?
3. Scoring weights: functionality 35 / reliability 25 / security 25 / cross-model compatibility 15 — what would you change?

**注意**：先发 r/mcp（生态内最对口），正文保持"求反馈"姿态；r/LocalLLaMA 强调实测数据；间隔 1–2 天再发其他社区，不要同天全发。
