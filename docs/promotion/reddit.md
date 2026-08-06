# Reddit 投稿

**目标 subreddit（按优先级）**：r/mcp（如允许自荐）、r/LocalLLaMA、r/selfhosted、r/opensource

**Title:**
I built an open-source trust benchmark for MCP servers and tested 12 — all four official Python servers fail to start, and the official filesystem server errors on 80% of calls

**Body:**
Like many of you, I've been installing MCP servers blind. There are 60k+ of them now, and the only "signal" is GitHub stars — which say nothing about whether a server boots, behaves, or is safe.

So I built TrustLens: an evaluation engine that sandboxes each server, runs the MCP handshake, statically scans for prompt injection / data exfiltration / hardcoded credentials, makes real probe calls (latency + failure rate), and checks multi-model tool-call compatibility. Output is a 0–100 trust score, and every byte of evidence is committed to the repo as JSON.

First batch findings:
- time / fetch / git / sqlite (official, archived): all crash on startup. The mcp SDK renamed McpError → MCPError and the servers never caught up.
- filesystem (official): handshakes fine, but 80% of probe calls return errors
- sequential-thinking (official): 47/100
- desktop-commander (very popular): 53/100
- memory (official): 91/100 — the good news exists too

Leaderboard (EN/中文, weekly auto-update): https://trustlens.icodestar.net/en/
Repo: https://github.com/hyqzz/trustlens (Apache-2.0, zero-dependency Python)

Questions I genuinely want input on:
1. What would make you actually trust a score like this?
2. Which servers should the next batch cover?
3. Scoring weights right now: functionality 35 / reliability 25 / security 25 / cross-model compatibility 15 — what would you change?

**注意**：Reddit 对纯自荐敏感——先发 r/mcp（生态内最对口），正文保持"求反馈"姿态；r/LocalLLaMA 强调实测数据；不要同天全发，间隔 1–2 天，每个帖子的首条评论自己补充评测方法细节。
