# Harness 成熟度自评（harness/maturity.md）

> 评估：2026-10-13（Bootstrap 首建轮终审，分支 feat/agent-harness）｜ 六组件各 0–2 分（0 缺失 / 1 提示级 / 2 机制级）。
> 总分 **9 / 12**（合格线 7–9，门禁/权限/指令 ≥2 ✅）。

| 组件 | 得分 | 依据（本轮实证） | 距 2 分差距 |
|---|---|---|---|
| 指令 | 2 | AGENTS.md 94 行纯索引+红线；分层落 docs/（架构 C1'–C9' + 边界）、harness/、evals/、KNOWLEDGE；只迁移不删除约定成文 | 度量驱动裁剪刚开始累积 |
| 工具 | 1 | verify.sh 四态固化；`--frozen` 纪律；uv.lock+dev 组齐 | 高频操作（新增域 API 脚手架）无封装 |
| 门禁 | 2 | verify 一条命令四态**实测跑通**；探针负向自检 FAIL=1 实证拦截；存量 9 假值入册棘轮；CI 原有 ruff+test 矩阵 + release 三元组校验 | pre-commit 待一条命令激活；ci.yml 未接扫描 |
| 权限 | 2 | 三级边界表 + CLI 白名单 + 特有高危（三语言漂移/py.typed/日志红线/凭据写入方）+ 凭证三件套（盘点/扫描器/响应手册） | 真实环境联调授权无技术强制（靠边界表） |
| 记忆 | 1 | KNOWLEDGE 首建即沉淀 7 条真实坑（含 verify.sh 参数 bug 双仓同款） | 回写靠纪律 |
| 评估 | 1 | evals 5 案例（含本仓特有的 CR-03 跨语言对齐、CR-04 py.typed）+ 回放表 | 重放手动 |

## 首建轮关键事件

1. **探针负向自检**：注入 `API_SECRET` 假字面量 → FAIL=1 拦截（EXIT 1）→ 清理恢复全绿（CLI 仓教训直接复用）。
2. **扫描器三处机制化**：egg-info 目录排除（按 path parts）· 占位符值过滤（is_placeholder：大写占位/占位词/小写标识/模板）→ 68 文件扫描从 80+ 命中降噪到 9 个夹具假值，全部人工核形态（5 重复模式合成 + 4 非真值字符集）后入册。
3. **verify.sh 辅助函数参数 bug**（$2/$3 vs 2 参调用）SDK 首跑即踩——同日修复 CLI 仓同款潜伏 bug（「首跑全路径覆盖」价值实证）。
4. **dev 依赖双轨**（extra pytest 7 vs group pytest 9）识别并固化为 `--frozen --extra dev` 口径。

## 下一批演进建议（性价比排序）

| # | 建议 | 成本 |
|---|---|---|
| 1 | 人工激活 pre-commit：`git config core.hooksPath scripts/hooks` | S |
| 2 | 1.12.0 PR 修正 pyproject Project-URL（勿混入 bootstrap 提交） | S |
| 3 | ci.yml 接入 secrets 扫描 | S |
| 4 | sync/client 签名镜像一致性测试（防双面透传漂移） | S |
| 5 | mypy 渐进（先 auth/persistence/token 链路） | M |
| 6 | ts/go 仓同款 Harness 化（协议对齐三仓门禁化） | S×2 |

## 持续演化约定

- 周回顾三问：哪些约束被违反？（→机制化）哪些从未生效？（→裁剪）verify 有无新 SKIP？
- 约束变更 → evals 重放；模型升级 → evals 重放；新事故 → 新案例。
- 度量从下一个真实需求（预计 = deviceflow 1.12.0）开始累积。
