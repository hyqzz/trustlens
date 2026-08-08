# Show HN 投稿（Hacker News）

**Title:**
Show HN: I benchmarked 118 real MCP servers — 55% are unusable out of the box

**Text:**
The MCP ecosystem hit 60k+ public servers with essentially no quality signal. Research says 66% have security issues; 88% of enterprise agent pilots die before production. There's an app store but no review system.

TrustLens is an open-source evaluation engine that actually runs each server in a sandbox: protocol handshake, static security scan (prompt injection / exfiltration / hardcoded creds), real probe calls with latency and failure tracking, real-model tool-call compatibility. It outputs a 0–100 trust score with fully public evidence (JSON data committed to the repo; git history is the audit log).

I evaluated 118 real npm/PyPI MCP servers in a zero-credential environment. Result: **exactly one earns an A (ifconfig-mcp, 100); 68 (58%) are F** — they never complete a handshake with the standard `npx -y <pkg>` start and no config. Failure modes (audited from stderr): runtime crash (30), crash on missing API key (15), package resolution/compat failure (11), genuine hang (9).

Leaderboard (bilingual EN/中文, searchable/filterable/paginated, auto-updated weekly by CI): https://trustlens.icodestar.net/en/
Repo (Apache-2.0, zero-dependency Python): https://github.com/hyqzz/trustlens

Is the 90s-handshake "out-of-the-box" criterion fair? Which servers should go into the next batch?

**投稿时间建议**：周二或周三，UTC 13:00–15:00（美东早上，流量高峰）。
