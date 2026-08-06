# X/Twitter 推文串（英文，发布时按条拆分）

1/
I benchmarked 12 MCP servers with an automated evaluation engine.

All four official Python servers fail to start. The official filesystem server errors on 80% of real calls. A hugely popular community server scores D.

Nobody measures this stuff. So I built the thing that does. 🧵

2/
The MCP ecosystem has 60,000+ public servers. Research shows 66% have security issues. 88% of enterprise agent pilots die before production.

There are app stores everywhere, but no quality inspection anywhere.

3/
TrustLens does what a QA lab does:
• sandboxed deployment + protocol handshake
• static scan for prompt injection / exfiltration / hardcoded creds
• real probe calls (latency, failure rate)
• multi-model compatibility (GPT/Claude/Qwen/DeepSeek)
→ one 0–100 trust score

4/
All evaluation data is committed to GitHub as JSON. Git history is the audit log. A trust product has to be transparent itself.

Live leaderboard (bilingual EN/中文, auto-updated weekly):
https://trustlens.icodestar.net/en/

5/
Some results that surprised even me:
• memory: 90.7 (A) — the healthy one
• filesystem: 68.5 — "installable" ≠ "usable"
• time/fetch/git/sqlite: all F — crash on startup (SDK renamed McpError → MCPError, servers never caught up)

6/
Open source, Apache-2.0. Would love your harshest criticism:
• Which servers should we test next?
• Are the 4 dimensions weighted right (35/25/25/15)?

Repo: https://github.com/hyqzz/trustlens
