# TrustLens 安全说明

TrustLens 的职责是**评测不可信的第三方 MCP 服务器**，因此评测系统自身的安全边界是产品可信度的根基。本文说明我们如何隔离风险。

## 评测进程隔离

- 每个被测服务器以**独立子进程**运行，协议走 stdio JSON-RPC。
- 子进程环境变量被**剥离到最小白名单**（Windows 保留 SystemRoot/COMSPEC/PATHEXT/TEMP/TMP/USERPROFILE/LOCALAPPDATA 等运行必需项；Unix 仅 PATH + HOME）。**所有可能的密钥（API key、token、凭证）都不会进入被测进程的环境**。
- 每次评测结束后进程被强制终止（terminate → kill），不留驻留。

## CI 安全设计

- 每周评测工作流（`evaluate.yml`）**不配置任何 Secrets**——它执行不可信代码，因此持有零密钥是硬性约束。
- 真实模型 provider 的 API key 未来如需接入，只放在**不执行第三方代码**的独立任务中。

## 暂缓评测的类别

- **浏览器自动化类**（puppeteer 等）：探针调用会真实启动 Chromium 并挂起——哑探针对这类工具不公平。已在 `data/servers.json` 以 `enabled: false` 暂缓，待"按工具类型生成合理探针"的方法论升级后恢复。
- 重型/危险类（代码执行、Kubernetes、Terraform、浏览器自动化）同样不进入自动评测队列。

## 信任分本身就是安全信号

- 安全性维度（25%）对**工具描述投毒、提示注入、数据外发、硬编码凭证**做静态扫描，任何命中都会大幅扣分甚至判 0。
- 评测数据全部公开（`data/results/*.json`），任何人可复核——做信任生意，自己先透明。

## 报告问题

发现 TrustLens 自身的安全问题，请在 GitHub 仓库开 issue（可在保密诉求下私信维护者）。
