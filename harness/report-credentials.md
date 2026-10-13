# 凭证盘点报告（harness/report-credentials.md）

> 纪律：全程只读元数据，禁止摘录/回显/转存任何凭证值。分级：高/中/低。
> 盘点：2026-10-13 ｜ 手段：scripts/scan_secrets.py + 文件系统元数据探测。

| # | 工具/位置 | 盘点结果（键名级） | 风险 | 说明 |
|---|---|---|---|---|
| 1 | `src/lansenger_sdk/persistence.py`（CredentialStore） | SDK **自身是凭据持久化实现方**：写 `~/.lansenger/sdk_state.json`（appToken/userToken/app_id/app_secret 键面） | 高 | 测试只用 tmp 路径（test_persistence.py 实证）；Agent 禁读真实文件值 |
| 2 | `src/lansenger_sdk/auth.py`（TokenManager） | 处理 app_secret（GET query 传递 `grant_type=client_credential&appid=…&secret=…`） | 高 | secret 走 URL query——**网关访问日志可能留痕**（平台侧设计，登记为已知面）；SDK 侧禁日志输出 |
| 3 | 仓库内源码/文档/CI | 扫描 68 文件：**零真凭证**；9 命中全为 tests 夹具假值（人工核：5 个重复模式合成 + 4 个混合字符集 ≠ 真实平台 36hex 形态），已入存量棘轮段 | — | 详见 harness/verify-allowlist |
| 4 | 环境变量 `LANSENGER_*`（用户 shell/CI） | 键名面见 config.py；值在环境 | 中 | 禁 print/export 回显 |
| 5 | GitHub Actions Secrets（PyPI 发布） | 平台侧配置 | 中 | 轮换入口：repo Settings → Secrets |
| 6 | 测试中的凭证 | 全 mock/tmp 路径，无真实凭证 | — | 保持：新增测试禁引入真实凭证 |

## 已执行动作（权限收紧：只减不增、逐条可逆）

- N/A——仓库内无过宽权限位文件；#1/#4/#5 在仓外或属实现逻辑，不触碰。

## 遗留风险与预案（诚实登记）

| 做不到什么 | 拿什么补 | 人工待办 |
|---|---|---|
| app_secret 经 URL query 传给网关（SDK 协议既有设计） | 平台侧访问日志治理；SDK 侧日志红线（C9'） | 向平台确认 query 传 secret 的日志留存策略；若可改建议评估 header 传递（协议变更，走 C7' 三仓联动） |
| 无 gitleaks 级数据流扫描 | 最小键名集 + 占位符机制化过滤 + 棘轮 | 团队确认是否引入 gitleaks |
| CI 无扫描步骤 | 本地 verify + 评审拦截 | P1：ci.yml 加 scan_secrets（随 1.12.0 或单独 PR） |

## 安全门（提交前校验条件，2026-10-13 起）

verify 第 4 步即安全门，以下检测器任一命中 = FAIL 阻断提交（probe 负向自检已验证拦截）：

| 检测器 | 抓什么 | 误报出口 |
|---|---|---|
| 凭证形态（R1/R2 + 占位符过滤） | 键值形态的 secret/token/credential… | 误报段判据 / is_placeholder 机制 |
| `internal-endpoint` | 内部测试环境主机族（open-*/user-*.{e,t}.lanxin.cn） | 误报段 |
| `long-hex-value` | ≥32 位涣散 hex（stray token/哈希） | 误报段（legit 依赖哈希等）/ 存量棘轮段（callbacks 密文向量、persistence 夹具已入册） |
| `blocklisted-value` | 本地黑名单片段（会话真实凭证/测试 appId/内部端点） | 黑名单文件本身维护（gitignored+0600） |

维护规则：新增高危值 → 追加 `harness/security-blocklist.local` 一行（该文件绝不入库）；黑名单内容本身含敏感片段，泄露面 = 本机。

响应手册见 [harness/incident-response.md](incident-response.md)。
