# TrustLens

> **Agent 能力生态的信任基准** —— 自动化实测 MCP Server / Agent Skills 等"能力单元"，发布公开、可审计的质量与信任评分。
>
> Trust benchmark for the agent capability ecosystem: automated, evidence-based trust scores for MCP servers and agent skills.

[![weekly evaluation](https://github.com/hyqzz/trustlens/actions/workflows/evaluate.yml/badge.svg)](https://github.com/hyqzz/trustlens/actions/workflows/evaluate.yml)
[![leaderboard](https://img.shields.io/badge/leaderboard-live-brightgreen)](https://trustlens.icodestar.net/)

## 为什么需要 TrustLens

Agent 的能力生态正在爆炸，但**质量信号完全缺失**：

- **6 万+ 公共 MCP Server**，跨注册表安全研究发现 **66% 存在安全问题**，大量废弃、重复、低质量
- **88% 的企业 Agent 试点死在上生产之前**——不是模型不行，是没人敢保证工具组合靠谱
- Agent 经济（x402 支付 / ERC-8004 身份）已启动，但**声誉层是空的**

TrustLens 是 Agent 世界的"质检局"：装任何工具之前，先查分。

## 快速开始

```bash
# 无需安装，直接在仓库根目录运行（零第三方依赖）
python -m trustlens list                      # 查看待评测清单
python -m trustlens check <server-name>       # 评测一个服务器并给出信任分
python -m trustlens evaluate-all              # 跑完整评测（写入 data/results/）
python -m trustlens build-site                # 生成静态排行榜网站到 site/dist/

# 或者安装后使用 CLI
pip install -e .
trustlens check <server-name>
```

## 信任分模型（0–100）

| 维度 | 权重 | 测量什么 |
|---|---|---|
| 功能性 Functionality | 35 | 协议握手、工具可调用、返回结构正确 |
| 可靠性 Reliability | 25 | 响应延迟、多次调用一致性、超时率 |
| 安全性 Security | 25 | 工具描述投毒模式、凭证泄露、可疑行为静态扫描 |
| 跨模型兼容性 Compatibility | 15 | 多个模型（GPT / Claude / Qwen / DeepSeek）实际调用的成功率 |

评测数据全部以 JSON 形式提交在本仓库 `data/results/` 下——**评分依据完全透明，git 历史即审计日志**。

## 路线图：三级火箭

1. **能力可信**（当前）：能力单元（MCP Server / Skills）的质量基准与排行榜
2. **行为可信**：Agent 履约追踪与声誉分（对齐 W3C VC/DID 与 ERC-8004 标准）
3. **交易可信**：Agent 经济的信用查询层

## 安全说明

TrustLens 需要运行不可信的第三方代码进行评测。所有评测在**剥离环境变量的隔离进程**中执行；CI 中评测任务不持有任何密钥。详见 `docs/SECURITY.md`。

## License

Apache-2.0
