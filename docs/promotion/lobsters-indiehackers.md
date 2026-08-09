# Lobsters / IndieHackers 提交

> Lobsters 是 HN 的"工程师版"（偏系统/底层），IndieHackers 偏独立开发者商业视角。两者都反感营销，用"数据 + 透明 + 求反馈"语气。
> 数据核验：发前对照 https://trustlens.icodestar.net/en/ 复核。

## Lobsters

**提交标题：**
I benchmarked 112 distinct MCP servers — ~60% are unusable out of the box

**提交描述：**
MCP has 60k+ public servers and essentially no quality signal. I built an evaluation engine that runs each server in a sandbox (zero credentials, 90s handshake, DeepSeek-generated smart probes, real-model tool-call checks) and outputs a 0–100 trust score with all evidence committed to the repo.

First real run over 112 distinct npm/PyPI servers: **only 7 (6.3%) grade A, 68 (60.7%) are F** — they never complete a handshake with the standard `npx -y <pkg>` and no config. Failure modes (audited from stderr): startup crashes and missing-API-key crashes dominate, plus a few package-resolution/compat failures and an occasional genuine hang. Even the official filesystem server is C (70).

All data is JSON in the repo — git history is the audit log. Leaderboard: https://trustlens.icodestar.net/en/

**Lobsters 注意**：不设"vouch"门槛就直接提交可能没人理，先在站上积累一些有质量的评论再提交本家项目；如果一次没上去，2 周后可再试。

## IndieHackers

**提交标题 / 帖子：**
Building TrustLens — a trust benchmark for MCP servers, 60% of which don't work out of the box

**正文要点（偏"我怎么做产品/怎么获得初始用户"）：**
1. 为什么做：MCP 生态 6 万+ 服务器零质量信号，88% 企业 Agent 试点死在上生产前
2. 怎么冷启动：先自证（数据全公开、git 即审计日志），再谈用户——"装之前先查分"这个需求谁有？
3. 商业化思考（诚实版）：短期先做信源（免费榜单 + 周更），信任建立后才谈 B 端（给企业 Agent 交付前的工具尽调 / API）
4. 求反馈：你怎么看"90 秒开箱即用"的评分标准？如果我要做 Top 100 扩评，优先补哪类服务器？

**IndieHackers 注意**：这个社区吃"真实过程"胜过"结果"——多写你踩过的坑（比如评测时被不可信包拖垮、加护栏），少写"我很棒"。

---

**两者共用发布检查：**
- [ ] 账号用真实 GitHub 绑定的 profile（IndieHackers 用 GitHub 登录）
- [ ] 主贴带 1 个外链（排行榜），GitHub 链接放在正文里，不堆链接
- [ ] 发完 2 小时内盯首条评论，认真回
- [ ] 间隔：Lobsters 与 HN 的 Show HN 错开 2 天；IndieHackers 可放 D+3~D+5
