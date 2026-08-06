# TrustLens 推广排期计划

> 目标：Phase 0 验证门 = **≥30 个真实"我想用"信号**（star / issue / 评论 / 私信均可计入）
> 所有宣传统一指向自有域名：**https://trustlens.icodestar.net/**（英文用户给 /en/）
> 原则：同一天不集中轰炸；每个平台语气适配；发完当天必须盯评论区。

## 核心叙事（119 数据集，所有文案围绕这个）

- **一个数字打天下**：实测 119 个真实 MCP 服务器，**55%（66 个）开箱即用连协议握手都完不成**；只有 9 个（8%）A 级
- 失败原因可讲故事：启动挂起 55 / 缺 API key 崩 7 / SDK 兼容崩溃 3（官方 Python 服务器 McpError→MCPError 启动即崩）
- 反例也成立：ref-tools-mcp 100 分、duckduckgo-search 99.8——**"热门≠靠谱"**
- 方法论是盾：90 秒握手超时 + 零凭证隔离沙箱 + git 历史即审计日志
- 界面是加分项：中英双语、搜索/筛选/分页/排序、浏览器语言自动适配

## 发布日（D-Day，建议选一个周二或周三）

| 时间（北京） | 动作 | 材料 |
|---|---|---|
| 09:00 | **掘金**发布中文首发文 | `docs/launch/01-juejin-zh.md` |
| 10:00 | **V2EX**「分享创造」发帖 | `docs/promotion/v2ex.md` |
| 12:00 | **公众号**推送（复用掘金文，排版适配） | 同上 |
| 21:00–23:00 | **Dev.to** 发布英文文 + **X** 推文串（= 美东上午） | `docs/launch/02-devto-en.md`、`x-thread-en.md` |
| 当天 | 每 2 小时看一次各平台评论，**当天回复所有评论** | — |

## D+1（周四）

| 时间 | 动作 | 材料 |
|---|---|---|
| 北京时间晚 21:00（= UTC 13:00，美东早 9 点） | **Hacker News** 投 Show HN | `docs/promotion/show-hn.md` |
| 当天 | HN 每 1–2 小时盯一次，前 6 小时的回复速度决定生死 | — |

## D+2 ~ D+3

| 动作 | 材料 |
|---|---|
| **Reddit** r/mcp（先发最对口的） | `docs/promotion/reddit.md` |
| 隔 1 天再发 r/LocalLLaMA 或 r/selfhosted（不要同天） | 同上 |
| **知乎**：把掘金文改写成"如何看待 66% 的 MCP 服务器有安全问题？"的回答/文章 | 基于 01 改写 |

## D+4 ~ D+7（沉淀与收录）

| 动作 | 说明 |
|---|---|
| 给 **awesome-mcp-servers** 等 3–5 个 awesome 列表提 PR 自荐 | 生态内长期流量入口 |
| 投稿 **阮一峰科技爱好者周刊**（GitHub issue 自荐）、**HelloGitHub** | 中文技术圈放大器 |
| 搜索引擎收录提交：Google Search Console + Bing Webmaster + 百度站长（提交 sitemap） | 地址 https://trustlens.icodestar.net/sitemap.xml |
| 写一篇跟进文：《"装得上"≠"用得好"：filesystem 80% 失败率深挖》 | 数据已在手，趁热点二连发 |

## 每周固定（进入运营节奏后）

- **周一**：周更评测结果已自动上线 → 发"本周 MCP 红黑榜"短文（掘金+公众号+X）
- **周三**：1 篇深度文或 1 个社区互动日（去同类项目 issue 区答疑）
- **周五**：复盘数据表（star 增量 / 榜单访问 / 各渠道转化 / 询单信号）

## 验证门复盘节点（对应战略文档）

- **D+14**：统计"我想用"信号总数。≥30 → Phase 0 通过，进入扩评测目标（Top 100）+ 真实模型接入；15–30 → 诊断渠道还是选题问题，调整后再推一轮；<15 → 触发止损讨论（此时损失约 4 周，仍有充足缓冲）

## 渠道-材料速查

| 渠道 | 语言 | 文件 |
|---|---|---|
| 掘金/公众号/知乎 | 中 | `docs/launch/01-juejin-zh.md` |
| V2EX | 中 | `docs/promotion/v2ex.md` |
| Dev.to / X | 英 | `docs/launch/02-devto-en.md` / `docs/promotion/x-thread-en.md` |
| Hacker News | 英 | `docs/promotion/show-hn.md` |
| Reddit | 英 | `docs/promotion/reddit.md` |
