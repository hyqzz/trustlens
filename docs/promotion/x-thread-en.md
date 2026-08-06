# X/Twitter 推文串（英文，发布时按条拆分）

1/
I benchmarked 119 real MCP servers in a clean-room, zero-credential environment.

Only 1 grade A. 69 (58%) are F — they never complete a handshake with the standard npx start and no config.

Nobody measures this stuff. So I built the thing that does. 🧵

2/
The MCP ecosystem has 60,000+ public servers. Research shows 66% have security issues. 88% of enterprise agent pilots die before production.

There are app stores everywhere, but no quality inspection anywhere.

3/
TrustLens does what a QA lab does:
• sandboxed deployment + protocol handshake
• static scan for prompt injection / exfiltration / hardcoded creds
• real probe calls (latency, failure rate)
• real-model tool-call compatibility (DeepSeek-V4 Flash, real calls)
→ one 0–100 trust score

4/
All evaluation data is committed to GitHub as JSON. Git history is the audit log. A trust product has to be transparent itself.

Live leaderboard (bilingual EN/中文, search + filter + sort + pagination, auto-updated weekly):
https://trustlens.icodestar.net/en/

5/
The numbers:
• 119 evaluated → A:1 B:13 C:13 D:23 F:69 (58% unusable)
• failure modes (audited from stderr): 30 runtime crash, 15 crash on missing API key, 11 package resolution/compat, 9 genuine hang
• the single A: duckduckgo-search (92.3) — while the hugely popular official filesystem is C (69.1) and desktop-commander is D (48.0)

6/
Open source, Apache-2.0. Harshest criticism welcome:
• Is the 90s-handshake "out-of-the-box" criterion fair?
• Which servers next?
• Weights right (35/25/25/15)?

Repo: https://github.com/hyqzz/trustlens
