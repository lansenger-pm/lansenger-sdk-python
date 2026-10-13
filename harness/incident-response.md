# 泄露响应手册（harness/incident-response.md）

> Agent 发现泄露迹象：立即停止相关操作并报告人工（只提供 文件:行:键名 定位），本手册动作由人工执行。

## app_id / app_secret（蓝信开放平台应用凭证）

- **止血**：蓝信开放平台后台重置 Secret；删除泄露副本；若经 SDK 写入过本地 `~/.lansenger/sdk_state.json`，删除该文件。
- **排因**：git 历史（`git log -p`）、CI 日志、终端历史；SDK 侧注意 **app_secret 走 URL query**——网关/代理访问日志是额外外泄面（report-credentials.md #2）。
- **加固**：`bash scripts/verify.sh` 全绿；优先 env 变量通道；曾入 git 历史则人工评估历史清理。

## appToken / userToken（访问令牌，2h/72h 级）

- **止血**：appToken 在开放平台后台强制失效（或等 2h 自然过期并轮换 secret 后旧 token 失效链路确认）；userToken 走 Passport 吊销会话。
- **排因**：重点查 `--verbose` DEBUG 日志（SDK logger 直达下游终端）、CI 输出、分享截图。
- **加固**：C9' 红线回归（evals 日志断言用例）；下游 CLI 的日志透出同样检查。

## PyPI 发布凭证（GitHub Actions Secrets）

- **止血**：PyPI 项目页撤销 token；GitHub 侧删除重建。
- **排因**：GitHub Security → Secret scanning / Audit log；确认 release.yml 无异常改动。
- **加固**：保持最小权限 scoped token；`.github/workflows/` 改动走 ⚠️ 级授权。

## 通用升级路径

Agent：发现即停 → 只报告定位 → 不自行轮换/改历史。
人工：三段处置 → KNOWLEDGE.md 记脱敏坑 → 高频场景回登记边界表或升级机制。
