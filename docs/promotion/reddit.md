# Reddit 投稿

**目标 subreddit（按优先级）**：r/mcp、r/LocalLLaMA、r/selfhosted、r/opensource

**Title:**
I benchmarked 112 distinct MCP servers — 60% are unusable out of the box. Open-source leaderboard inside.

**Body:**
Like many of you, I've been installing MCP servers blind. There are 60k+ now, and the only "signal" is GitHub stars — which say nothing about whether a server boots, behaves, or is safe.

So I built TrustLens: an evaluation engine that sandboxes each server, runs the MCP handshake, statically scans for prompt injection / data exfiltration / hardcoded credentials, generates realistic per-tool probe args with DeepSeek-V4 Flash (sanitized so nothing destructive/credential-shaped/internal gets through), makes real probe calls (latency + failure rate), and checks model tool-call compatibility. Output is a 0–100 trust score, and every byte of evidence is committed to the repo as JSON.

I ran 112 distinct real npm/PyPI servers through it in a zero-credential, out-of-the-box setup:
- **Only 8 (7%) grade A.** 67 (60%) are F — never complete a handshake with the standard `npx -y <pkg>` and no config.
- Failure modes (audited from stderr): startup crash (49), crash on missing API key (14), package resolution/compat failure (2), genuine hang (1).
- Reputation tracks nothing: the hugely popular official `filesystem` scores just C (70), `desktop-commander` sits at C (72), and even `duckduckgo-search` (84, B) and `ref-tools-mcp` (93, A) show stars ≠ reliability. The single perfect score is the tiny `ifconfig-mcp` (100).

Leaderboard (EN/中文, search/filter/sort/pagination, weekly auto-update): https://trustlens.icodestar.net/en/
Repo: https://github.com/hyqzz/trustlens (Apache-2.0, zero-dependency Python)

Questions I genuinely want input on:
1. Is the 90s-handshake "out-of-the-box" criterion fair, or should setup-required servers get partial credit?
2. Which servers should the next batch cover?
3. Scoring weights: functionality 35 / reliability 25 / security 25 / cross-model compatibility 15 — what would you change?

**注意**：先发 r/mcp（生态内最对口），正文保持"求反馈"姿态；r/LocalLLaMA 强调实测数据；间隔 1–2 天再发其他社区，不要同天全发。
