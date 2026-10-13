# 交付报告 · device flow 复核修复（harness/delivery-deviceflow.md）

> 需求：OAuth2 设备码授权 grant（CLI + SDK）的代码复核与修复 ｜ 分支：`deviceflow-1.12.0`（基线 = PR #3 head `69aa63b`）｜ 日期：2026-10-13
> 模板：templates/delivery-report.md（首建轮占位，本轮为首个真实需求轮）

## A. 业界五指标

| 指标 | 本轮值 | 累计口径 |
|---|---|---|
| 任务接受率 | —（待人类评审后判定） | 采纳数 / 总任务数 |
| 升级介入率 | 1（人类复核发起，并要求先证伪再动手） | 人工接管数 / 总任务数 |
| 幻觉缺陷率 | 0（3 条结论均有可复现探针） | 幻觉数 / 总任务数 |
| Token 成本 | —（未统计） | 每任务均值 |
| eval 通过率 | —（未重放 evals/） | 重放通过 / 案例总数 |

## B. 项目自定义字段

| 字段 | 本轮值 | 备注 |
|---|---|---|
| 返工次数 | 1 | 分类器首版改动过宽（「已知状态 + 未知码」也被判真实错误），既有用例 `test_authorization_unknown_error_code_is_unsupported` 立即失败 → 收窄为「仅 `error` 为非对象形态」 |
| 失败原因分类 | 事实错误 + 约束违反 | 事实错误：`data["error"].get("code")` 对 RFC 6749 字符串 `error` 抛 `AttributeError`；约束违反：C8'（README ×6）与 C7'（三语言登记）未落实 |
| **被违反约束名 → 候选机制化** | C8' / C7' | 候选：verify.sh 增加「端点表 ↔ README ×6 关键词」一致性检查；交付报告缺 C7' 字段时门禁告警 |
| **未生效约束 → 候选裁剪** | — | C3'/C4'/C5' 均按预期生效（分类表、公共签名、版本三元组无一被破坏） |
| **C7' 三语言对齐登记** | **未同步（显式登记）** | 理由：device authorization grant 是 Python SDK 新增协议面（`device_authorization` / `device_token` 两端点 + `request_device_authorization` / `poll_device_token` + 2 个结果类），`lansenger-sdk-go` / `lansenger-sdk-ts` 尚无该 grant 实现；三仓联动超出本次复核范围 → 按 AGENTS.md §4 显式登记，另立需求推进（与 harness/report.md 风险 #1 同源） |
| 子代理使用 | 0 | 单 Agent 复核 + 3 个离线探针脚本（无真实 API 调用） |

## 本轮实证（2026-10-13）

- 改动：`src/lansenger_sdk/oauth.py` 两个分类器（非对象 `error` 判真实 API 错误）· `tests/test_device.py` +7 例
- 门禁：`bash scripts/verify.sh` → **FAIL=0**（lint / test / build / secrets；6 WARN 均为存量 allowlist）
- 单测：**485 passed, 6 skipped**（修复前 478）
- 文档：README ×6（C8'）· AGENTS.md / KNOWLEDGE.md / docs/architecture.md / harness/report.md 计数同步 · docs/architecture.md C3' 分类表语义同步
- 未覆盖：真实环境联调（⚠️ 级，需人类凭证并授权；本轮按红线未打真实 API）
- 下游：CLI 仓已钉 `lansenger-sdk>=1.12.0`；本修复不改变任何公共签名 → CLI 无需改代码
- 发布顺序：SDK 1.12.0 先发 PyPI（tag `v1.12.0`），再合 CLI（C6'）
