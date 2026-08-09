# TrustLens 推广执行清单（D-Day 主清单）

> 用法：每个渠道一行，发布后勾 ☑、填链接、填信号。此清单是 Phase 0 验证门（D+14 ≥30 个"我想用"信号）的统计源。
> 所有文案集中在 `docs/promotion/` 与 `docs/launch/`，本文件只做调度与追踪。

## 0. 发布前 3 天（准备）

- [ ] 复核线上榜单数字与文案一致（112 / 60% / A8 / 唯一满分 ifconfig-mcp / filesystem C70 / Skills 110）
- [ ] 确认两个泄露 token（PAT + OpenCode key）已吊销，GitHub Actions 的 OPENCODE_API_KEY secret 已轮换
- [ ] GitHub 仓库：加 topics（`mcp`、`agent`、`benchmark`、`ai-agents`、`llm`）、确认 README 徽章、把 `8ab638a` 发布成 Release（附 changelog）
- [ ] 域名：确认 https://trustlens.icodestar.net/ 的 sitemap.xml / robots.txt / og-card 正常返回
- [ ] 各平台账号确认可登录（见 `accounts-checklist.md`）

## 1. D-Day（建议周二/周三）

| 时间(北京) | 渠道 | 文案 | 状态 | 链接/结果 | 信号 |
|---|---|---|---|---|---|
| 09:00 | 掘金（首发） | `docs/launch/01-juejin-zh.md` | ☐ | | |
| 10:00 | V2EX（分享创造） | `docs/promotion/v2ex.md` | ☐ | | |
| 12:00 | 微信公众号 | `docs/promotion/wechat-mp.md` | ☐ | | |
| 13:00–16:00 | 知乎（回答+专栏） | `docs/promotion/zhihu.md` | ☐ | | |
| 18:00 | 即刻 + 微博 | `docs/promotion/weibo-jike.md` | ☐ | | |
| 21:00（美东早） | Dev.to（英文首发） | `docs/launch/02-devto-en.md` | ☐ | | |
| 21:00 | X 推文串 | `docs/promotion/x-thread-en.md` | ☐ | | |
| 21:00 | LinkedIn L1 | `docs/promotion/linkedin.md` | ☐ | | |
| 当天 | 每 2h 刷各平台评论并回复 | — | ☐ | | |

**记住**：当天回复所有评论（尤其掘金/V2EX/Dev.to），回复速度 = 社区信任的第一印象。

## 2. D+1（周四）

| 时间 | 渠道 | 文案 | 状态 | 链接/结果 | 信号 |
|---|---|---|---|---|---|
| 21:00（=美东 9:00） | Hacker News Show HN | `docs/promotion/show-hn.md` | ☐ | | |
| 21:00 | LinkedIn L2（方法论） | `docs/promotion/linkedin.md` | ☐ | | |
| 当天 | HN 每 1–2h 盯回复（前 6h 决定生死） | — | ☐ | | |

## 3. D+2 ~ D+3

| 时间 | 渠道 | 文案 | 状态 | 链接/结果 | 信号 |
|---|---|---|---|---|---|
| D+2 | Product Hunt（美西 0 点发布） | `docs/promotion/producthunt.md` | ☐ | | |
| D+2 | Reddit r/mcp | `docs/promotion/reddit.md` | ☐ | | |
| D+2 | Medium | `docs/promotion/medium-hackernoon.md` | ☐ | | |
| D+3 | Reddit r/LocalLLaMA（隔天再发） | 同上 | ☐ | | |
| D+3 | CSDN | `docs/promotion/csdn-oschina-segmentfault.md` | ☐ | | |
| D+3 | LinkedIn L3（求职友好） | `docs/promotion/linkedin.md` | ☐ | | |

## 4. D+4 ~ D+7（沉淀与收录）

| 时间 | 渠道 | 文案 | 状态 | 链接/结果 |
|---|---|---|---|---|
| D+4 | OSCHINA | csdn-oschina-segmentfault.md | ☐ | |
| D+5 | SegmentFault | 同上 | ☐ | |
| D+5 | Lobsters | `docs/promotion/lobsters-indiehackers.md` | ☐ | |
| D+6 | IndieHackers | 同上 | ☐ | |
| D+6 | HackerNoon | `docs/promotion/medium-hackernoon.md` | ☐ | |
| D+6 | B站/视频号视频 | `docs/promotion/bilibili-script.md` | ☐ | |
| D+4–7 | awesome-mcp-servers PR ×3–5 | `docs/promotion/awesome-pr.md` | ☐ | |
| D+4–7 | 阮一峰周刊 + HelloGitHub 投稿 | `docs/promotion/weekly-submissions.md` | ☐ | |
| D+4–7 | 科技媒体投稿（量子位/机器之心等） | `docs/promotion/media-pitch-zh.md` | ☐ | |
| D+4–7 | 搜索引擎收录提交 | `docs/promotion/seo-submit.md` | ☐ | |
| D+5 | 跟进文（数据已到手） | 见下方"跟进文" | ☐ | |

**跟进文**（趁数据热点二连发）：
> 《"装得上"≠"用得好"：官方 filesystem 这类"热门"服务器为何实测只有 C 级》
> 素材已备：filesystem C70 详情页、probes 结果、desktop-commander C72。发掘金 + Dev.to + 公众号。

## 5. 进入运营节奏（D+7 之后每周）

| 时间 | 动作 | 材料 |
|---|---|---|
| 周一 | 周更结果上线 → 中文红黑榜（掘金/公众号） | `weekly-zh.md` |
| 周一 | 英文红黑榜（X / Dev.to 择一） | `weekly-en.md` |
| 周三 | 1 篇深度文 或 社区互动日（同类项目 issue 区答疑） | — |
| 周五 | 复盘：star 增量 / 榜单访问 / 各渠道转化 / 询单信号 | — |

## 6. 信号统计（Phase 0 验证门）

**"我想用"信号定义**（满足其一即可计入）：
- GitHub star（去重用户）
- GitHub issue / PR / Discussions（有效反馈）
- 各平台评论里明确"我会用 / 我想试 / 求链接"等
- 私信 / 邮箱询单（B 端或求职）

| 统计项 | 目标 | 实际 |
|---|---|---|
| GitHub star 数 | — | |
| "我想用"信号总数（D+14 统计） | **≥30** | |
| 渠道转化 top3 | — | |

**复盘分档**（对应战略）：
- ≥30 → Phase 0 通过，进入扩评测（Top 100）+ 真实模型接入
- 15–30 → 诊断是渠道还是选题问题，调整后再推一轮
- <15 → 触发止损讨论

## 7. 安全红线（每条发布前过一遍）

- [ ] 文案数字与线上榜单一致（可信链：分数即产品）
- [ ] 不引用未核实的外部研究数字（如"66% 有安全问题"必须标注为外部研究口径）
- [ ] 不泄露任何评测中遇到的真实服务器密钥/敏感数据
- [ ] 不刷评论、不买 star、不用营销号矩阵（信任生意最忌造假）
