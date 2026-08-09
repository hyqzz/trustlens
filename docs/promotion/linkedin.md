# LinkedIn 发布卡

> LinkedIn 是 B2B / 招聘信号最强的渠道。对失业求职者，这既是产品推广也是个人技术品牌输出。发 3 条：首发条 + 方法论条 + 求职友好条。
> 数据核验：发前对照 https://trustlens.icodestar.net/en/ 复核。

## L1 · 首发条（D-Day 当天）

**标题：**
60% of public MCP servers are unusable out of the box — I benchmarked 112 of them.

**正文：**
I've spent the last month building TrustLens, an open-source "QA lab" for the agent ecosystem: it runs real MCP servers in a zero-credential sandbox, checks the protocol handshake, generates realistic probe args with DeepSeek-V4 Flash, and outputs a 0–100 trust score — with every byte of evidence committed to the repo (git history is the audit log).

First real run: **112 distinct npm/PyPI servers → only 8 grade A (7%), 67 are F (60%)** — they never complete a handshake with the standard `npx -y <pkg>` and no config. The official filesystem server scores C (70). "Popular" is not a reliability signal.

Leaderboard (bilingual, weekly auto-update): https://trustlens.icodestar.net/en/
Repo: https://github.com/hyqzz/trustlens

Questions I'd genuinely like input on: is the 90s-handshake out-of-the-box criterion fair? Should setup-required servers get partial credit?

#AI #MCP #LLM #OpenSource #DeveloperTools

## L2 · 方法论条（D+2 左右）

**标题：**
"A 100 security score is not a safety certification."

**正文：**
When I publish trust scores for MCP servers, I get asked: "so it's safe?" No — here's the honest boundary. Our security dimension is a static text-pattern scan (prompt injection, exfiltration-style commands, hardcoded credentials). It cannot detect runtime exfiltration or covert behavior. A 100 on security means "no obvious red flags in a static scan," nothing more.

Why say this publicly? Because if a trust benchmark lies about its own limits, it's worthless. The whole point is that the scores are auditable — which is why all evidence is JSON in the repo and git history is the audit log.

Full methodology is in the README: https://github.com/hyqzz/trustlens

#AISecurity #TrustButVerify #AgentEcosystem

## L3 · 求职友好条（D+4 之后）

**标题：**
I left a stable role to build agent-infrastructure tooling. Here's what 15 years of software engineering taught me about shipping trust.

**正文：**
15 years in software, mostly backend and distributed systems. Now I build TrustLens — a trust benchmark for the agent ecosystem (MCP servers + agent skills), fully open source.

Three things this project forced me to relearn:
1. **Auditability beats claims.** Every score ships with its evidence; git history is the audit log. In a "trust" product, transparency is the product.
2. **"Out of the box" is a spec, not a wish.** 60% of the 112 real MCP servers I benchmarked never complete a handshake with zero config. Most users are not power users.
3. **Harsh, specific feedback is the best gift.** The HN / r/mcp threads taught me more in a week than a year of retrospectives.

Looking for opportunities in agent infrastructure / AI tooling / developer platforms. Remote-friendly, happy to share the full data and methodology.

#JobSearch #AI #MCP #OpenToWork

---

**发布建议：**
- L1 的 9:00 美东（= 北京 21:00）发，赶上美国上班
- 每条带 1 个链接 + 2–4 个话题标签，别堆
- 评论区和私信及时回（HR/技术负责人可能私信）
- 头像/封面换成品牌风（与 og-card 一致），profile 里挂 GitHub
