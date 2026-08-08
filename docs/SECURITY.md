# TrustLens 安全说明

TrustLens 的职责是**评测不可信的第三方 MCP 服务器**，因此评测系统自身的安全边界是产品可信度的根基。本文说明我们如何隔离风险。

## 评测进程隔离

- 每个被测服务器以**独立子进程**运行，协议走 stdio JSON-RPC。
- 子进程环境变量被**剥离到最小白名单**（Windows 保留 SystemRoot/COMSPEC/PATHEXT/TEMP/TMP/USERPROFILE/LOCALAPPDATA 等运行必需项；Unix 仅 PATH + HOME）。**所有可能的密钥（API key、token、凭证）都不会进入被测进程的环境**。
- 每次评测结束后进程被强制终止（terminate → kill），不留驻留。

## CI 安全设计

- 每周评测工作流（`evaluate.yml`）中的 **`evaluate-all` 步骤执行不可信第三方代码，该步骤持有零密钥**（硬性约束，环境变量剥离见上节）。
- 需要 API key 的步骤只有两个：**`gen-probes`（智能探针生成）与 `model-compat`（真实模型工具调用分）**。二者都**不执行任何服务器代码**——只读已提交的评测结果 + 调用 DeepSeek API，密钥以**步骤级 env** 注入，作用域仅限该步骤。
- 智能探针的输入是**不可信的服务器元数据**（工具描述/schema，可能投毒 prompt）。模型输出只作为调用参数，且必须经过**正则安全护栏**（`llm.py` 的 `_sanitize_args`）：破坏性/注入/路径穿越 → 工具整体跳过（不奖不罚）；凭证形状 → 改写为占位符；内网/本机地址 → 改写为 example.com；敏感路径 → 改写为预置探针临时文件。

## 暂缓评测的类别

- **浏览器自动化类**（puppeteer 等）：探针调用会真实启动 Chromium 并挂起，资源开销不可控。已在 `data/servers.json` 以 `enabled: false` 暂缓。
- 重型/危险类（代码执行、Kubernetes、Terraform）同样不进入自动评测队列；即使智能探针能给出参数，其真实副作用（扣费/改生产资源）也无法在评测环境中安全收敛。

## 信任分本身就是安全信号

- 安全性维度（25%）对**工具描述投毒、提示注入、数据外发、硬编码凭证**做静态扫描，任何命中都会大幅扣分甚至判 0。
- 评测数据全部公开（`data/results/*.json`），任何人可复核——做信任生意，自己先透明。

## 报告问题

发现 TrustLens 自身的安全问题，请在 GitHub 仓库开 issue（可在保密诉求下私信维护者）。
