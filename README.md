# TrustLens

> **智码星 ICodeStar · Agent 能力生态的信任基准** —— 自动化实测 MCP Server / Agent Skills 等"能力单元"，发布公开、可审计的质量与信任评分。
>
> Trust benchmark for the agent capability ecosystem: automated, evidence-based trust scores for MCP servers and agent skills.

[![leaderboard](https://img.shields.io/badge/leaderboard-live-brightgreen)](https://trustlens.icodestar.net/)
[![weekly evaluation](https://github.com/hyqzz/trustlens/actions/workflows/evaluate.yml/badge.svg)](https://github.com/hyqzz/trustlens/actions/workflows/evaluate.yml)
[![tests](https://github.com/hyqzz/trustlens/actions/workflows/test.yml/badge.svg)](https://github.com/hyqzz/trustlens/actions/workflows/test.yml)

## 为什么需要 TrustLens

Agent 的能力生态正在爆炸，但**质量信号完全缺失**：

- **6 万+ 公共 MCP Server**，跨注册表安全研究发现 **66% 存在安全问题**，大量废弃、重复、低质量
- **88% 的企业 Agent 试点死在上生产之前**——不是模型不行，是没人敢保证工具组合靠谱
- Agent 经济（x402 支付 / ERC-8004 身份）已启动，但**声誉层是空的**

TrustLens 是 Agent 世界的"质检局"：装任何工具之前，先查分。

## 快速开始

```bash
# 无需安装，直接在仓库根目录运行（零第三方依赖）
python -m trustlens list                      # 查看待评测清单（120+ 个真实服务器）
python -m trustlens check <server-name>       # 评测一个服务器并给出信任分
python -m trustlens gen-probes --real         # 用 DeepSeek 生成真实参数智能探针（只读已有结果，不执行服务器代码）
python -m trustlens evaluate-all              # 跑完整评测（并发 4，--skip-f 跳过已失败）
python -m trustlens model-compat --real       # 用 DeepSeek 真实模型更新工具调用分
python -m trustlens eval-skills --real        # 评测 Agent Skills（SKILL.md）
python -m trustlens build-site                # 生成交互式双榜网站到 site/dist/

# 或者安装后使用 CLI
pip install -e .
trustlens check <server-name>
```

## 信任分模型（0–100）

| 维度 | 权重 | 测量什么 |
|---|---|---|
| 功能性 Functionality | 35 | 协议握手、工具可调用（真实参数探针）、返回结构正确 |
| 可靠性 Reliability | 25 | 响应延迟、多次调用一致性、超时率 |
| 安全性 Security | 25 | 工具描述投毒模式、凭证泄露、可疑行为静态扫描 |
| 模型工具调用 Tool-call | 15 | **DeepSeek-V4 Flash 真实调用**：能否为每个工具构造合法调用 |

评测数据全部以 JSON 形式提交在本仓库 `data/results/`、`data/skills/` 与 `data/probes.json`（智能探针参数）下——**评分依据完全透明，git 历史即审计日志**。

## 双榜单

- **MCP 服务器榜**（112 个去重真实服务器）：https://trustlens.icodestar.net/
- **Agent Skills 榜**（110 个）：https://trustlens.icodestar.net/skills.html

真实模型工具调用分由 DeepSeek-V4 Flash（OpenCode Go，最低成本档）实测得出。

## 路线图：三级火箭

1. **能力可信**（当前）：能力单元（MCP Server / Skills）的质量基准与排行榜
2. **行为可信**：Agent 履约追踪与声誉分（对齐 W3C VC/DID 与 ERC-8004 标准）
3. **交易可信**：Agent 经济的信用查询层

## 安全说明

TrustLens 需要运行不可信的第三方代码进行评测。所有评测在**剥离环境变量的隔离进程**中执行；CI 中评测任务不持有任何密钥。智能探针（DeepSeek 生成真实调用参数）在**不执行服务器代码**的独立步骤中生成，输出经**正则安全护栏**清洗（破坏性/注入值 → 工具跳过，凭证 → 改写占位符，内网 → example.com，敏感路径 → 探针临时文件）。浏览器自动化等重型/易挂起类别已按 `enabled: false` 暂缓评测（真实副作用不可控）。评测含防拖垮护栏：同一服务器连续 2 次工具调用超时即判定对真实调用不可用，跳过剩余探针。**安全维度是静态文本模式扫描，只检出明显特征（提示注入/数据外发指令/硬编码凭证），无法检出运行时外发等隐蔽行为——"安全满分"≠"已证实安全"**；评测环境剥离了被测服务器可用的密钥，降低而非消除风险。详见 `docs/SECURITY.md`。

## License

Apache-2.0
