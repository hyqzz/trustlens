# 周刊投稿模板：阮一峰科技爱好者周刊 / HelloGitHub

> 这两个渠道靠"被收录"，核心是提供一段 3 行内、可复制的项目简介，让编辑直接采用。
> 数据核验：提交前对照 https://trustlens.icodestar.net/ 复核数字。

## 阮一峰「科技爱好者周刊」

**投稿方式**：GitHub issue（https://github.com/ruanyf/weekly/issues/new），标题 `投稿：TrustLens —— 实测 MCP 服务器的信任分排行榜`

**正文（可直接用）：**

推荐开源项目 **TrustLens（智码星 ICodeStar）**：Agent 能力生态的信任基准。

背景：MCP 生态两年不到已有 6 万+ 公共服务器，但没有任何质量信号。跨注册表安全研究发现 66% 存在安全问题；88% 的企业 Agent 试点死在上生产之前。

TrustLens 在隔离沙箱、零凭证条件下实测真实发布的 MCP 服务器与 Agent Skills，输出 0–100 信任分（功能 35 / 可靠 25 / 安全 25 / 模型调用 15），每周自动更新。目前实测 **112 个去重服务器，60%（67 个）按文档装完、连协议握手都完不成**；110 个 Agent Skills 三维评测。

- 功能维度用 **DeepSeek 智能探针**：按每个工具的真实场景生成调用参数，安全护栏清洗后真实调用——"同一个工具，模型到底能不能用起来"，这份数据没人发布过
- 全部评测数据以 JSON 提交在仓库，**git 历史即审计日志**，做信任生意自己先透明
- 中英双语排行榜：https://trustlens.icodestar.net/ （仓库：github.com/hyqzz/trustlens，Apache-2.0）

**格式要求**：阮一峰周刊接受的是"项目一句话 + 亮点"，正文尽量精简到能一眼扫完。

## HelloGitHub

**投稿方式**：GitHub issue（https://github.com/521xueweihan/HelloGitHub/issues/new/choose，选"推荐项目"模板）

**推荐理由（精简版）：**

> **TrustLens**：一个给 AI Agent 工具做"质检"的开源项目。它把真实发布的 MCP 服务器装进隔离沙箱实测，按功能/可靠/安全/模型调用打 0–100 信任分，每周自动更新。已实测 112 个去重服务器：**60% 装完根本没法用**，官方 filesystem 只有 C 级——星标多不代表能用。数据全公开（git 即审计日志），中英双语排行榜在线：https://trustlens.icodestar.net/

**注意**：HelloGitHub 每期入选有限，简介要突出"反直觉结论"（60% 不能用）而不是"我做了一个评测网站"。

## 其他可投的收录渠道（备选）

| 渠道 | 方式 | 亮点侧重 |
|---|---|---|
| 阮一峰周刊 | GitHub issue | 数据 + 透明 |
| HelloGitHub | GitHub issue | 反直觉结论 |
| Python 中文社区 | 论坛/公众号投稿 | 零依赖 Python 实现 |
| 开源中国新闻 | 官网提交 | 项目已上线、周更 |
| InfoQ 投稿 | 邮箱 | 方法论 + 行业数据（见 media-pitch） |
