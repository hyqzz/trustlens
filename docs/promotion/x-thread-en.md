# X/Twitter 推文串（英文，发布时按条拆分）

1/
I benchmarked 119 real MCP servers in a clean-room, zero-credential environment.

Only 9 grade A. 66 (55%) are F — they never complete a handshake with the standard npx start and no config.

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

Live leaderboard (bilingual EN/中文, search + filter + sort + pagination, auto-updated weekly):
https://trustlens.icodestar.net/en/

5/
The numbers:
• 119 evaluated → A:9 B:12 C:25 D:7 F:66 (55% unusable)
• failure modes: 55 startup hang, 7 crash on missing API key, 3 SDK compat crash
• even official Python servers crash on import (SDK renamed McpError → MCPError)
• the good ones exist: ref-tools-mcp 100, duckduckgo-search 99.8, ifconfig-mcp 96

6/
Open source, Apache-2.0. Harshest criticism welcome:
• Is the 90s-handshake "out-of-the-box" criterion fair?
• Which servers next?
• Weights right (35/25/25/15)?

Repo: https://github.com/hyqzz/trustlens
