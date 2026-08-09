# Medium / HackerNoon 长文发布

> Medium 靠标签 SEO + 关注流，HackerNoon 是开发者内容平台、提交后约 1–3 天过审。核心正文复用 `docs/launch/02-devto-en.md`，做 SEO 与平台适配。
> 数据核验：发前对照 https://trustlens.icodestar.net/en/ 复核。

## Medium

**标题（SEO 优化）：**
I Benchmarked 112 Real MCP Servers — 60% Are Unusable Out of the Box (and I Built an Open-Source "QA Lab" for the Agent Ecosystem)

**设置：**
- Tags（最多 5 个）：`AI` `Open Source` `MCP` `LLM` `Developer Tools`
- 发布为公开 + 勾选"追加到出版物"（若有合适的 Medium 出版物可投，如 Towards Data Science、Level Up Coding——他们收 AI 基础设施类）
- 每段小标题用英文"##"，命令块保留；表格 Medium 支持不佳 → 等级表改成列表或 HTML 表格

**正文适配（相对 devto 文）：**
1. 开头加 2 行 summary："**TL;DR**：112 distinct npm/PyPI MCP servers, zero credentials, 90s handshake → only 8 grade A, 67 (60%) are F. All data public (git = audit log)."
2. 结尾 CTA 改为："If you'd like the data for your own research, all JSON is in the repo — and the leaderboard refreshes weekly. Comments welcome."
3. 段落之间留白更大（Medium 阅读器吃短段落）

## HackerNoon

**提交标题：**
60% of Public MCP Servers Are Unusable Out of the Box — Here's the Data

**正文**：复用 devto 文（加 TL;DR）。HackerNoon 喜欢"数字 + 可复现"：强调测评方法是公开可复现的（README 里有 `python -m trustlens check <name>` 本地复现命令）。

**HackerNoon 注意：**
- 有"机器审核"关键词（避免过度营销词，如 best、revolutionary）
- 每篇文章需要选一个"Story Type"（选 Tutorial / Tech Story）
- 过审后可在首页申请 feature，通常提交后 1–3 天

---

**两者共用检查：**
- [ ] 配图用 og-card-en.png 做封面
- [ ] 文末固定放：Leaderboard + GitHub + "built by ICodeStar (智码星)"
- [ ] 发布后回复所有评论（Medium 评论会推到作者）
- [ ] Medium 可加"Member-only"（默认开启即可，能积累关注者）
