# Show HN 投稿（Hacker News）

**Title:**
Show HN: TrustLens – I benchmarked 12 MCP servers; all 4 official Python ones fail to start

**Text:**
The MCP ecosystem hit 60k+ public servers with essentially no quality signal — research shows 66% have security issues, and anyone who has picked a server blind knows the feeling.

TrustLens is an open-source evaluation engine that actually runs each server in a sandbox: protocol handshake, static security scan (prompt injection / exfiltration / hardcoded creds), real probe calls with latency and failure tracking, and multi-model compatibility checks. It outputs a 0–100 trust score with fully public evidence (JSON data committed to the repo; git history is the audit log).

First batch results were worse than I expected:
- All four archived official Python servers (time/fetch/git/sqlite) crash on startup — the mcp SDK renamed McpError → MCPError and they never caught up
- The official filesystem server handshakes fine but 80% of real probe calls error
- A very popular community server (desktop-commander) scores D

Leaderboard (bilingual, auto-updated weekly by CI): https://trustlens.icodestar.net/en/
Repo (Apache-2.0, zero-dependency Python): https://github.com/hyqzz/trustlens

Happy to answer anything about the scoring model. Which servers should go into the next batch?

**投稿时间建议**：周二或周三，UTC 13:00–15:00（美东早上，流量高峰）。
