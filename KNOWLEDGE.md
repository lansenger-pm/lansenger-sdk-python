# KNOWLEDGE.md（踩坑沉淀）

> 分节：构建 / 测试 / 工具坑。约定：任务收尾回顾回写；**同一问题反复 3 次必须机制化**。
> 条目格式：`- [日期] 现象 → 根因 → 处置（✅机制 = 已做进脚本/门禁）`。

## 构建

- [2026-10-13] `uv run pytest` 直接可用但会解析 dependency-group（pytest 9 系）；CI 用 `pip install -e ".[dev]"` 是 extra（pytest 7 系）——**dev 依赖双轨**（`[project.optional-dependencies].dev` vs `[dependency-groups].dev`，版本下限不同）。verify 统一用 `uv run --frozen --extra dev pytest`（✅机制），与 CI extra 口径对齐；`--frozen` 防 `uv run` 顺手改锁。
- [2026-10-13] 构建：`uv build` 产 dist/（已 ignore），勿手改产物。

## 测试

- [2026-10-13] 测试全 mock 不打真实 API（453 passed/6 skipped，0.69s）——新增域测试沿用此模式；真实联调属 ⚠️ 级（需用户提供测试凭证并授权）。
- [2026-10-13] tests 里有 9 处夹具假 token（非占位词形态，混合字符集）——已人工核非真值并入棘轮存量段（harness/verify-allowlist）。**新增测试用假凭证时：优先用占位词形态**（`test-token-001` 等，扫描器 is_placeholder 自动放行），避免棘轮噪音。

## 工具坑

- [2026-10-13] **.gitignore 曾忽略 AGENTS.md/CLAUDE.md**（与 lansenger-cli 修复前同款坑）→ 已解除（✅机制：约束产物必须入库）。
- [2026-10-13] **PyPI 元数据错填**：pyproject Project-URL 指向 lansenger-skills-official（实为 AI Skills 文档仓），真源码仓是本仓 `lansenger-sdk-python`——**勿据包元数据找源码**；1.12.0 发版 PR 必修。
- [2026-10-13] verify.sh 的 skip/warn 辅助函数曾用 `$2/$3` 但调用只传 2 参，`set -u` 下首踩 unbound 报错（lansenger-cli 同款潜伏 bug 同日修复）——教训：**辅助函数参数个数与调用点必须对齐，set -u 下未走过的分支=没测过**（✅机制：两仓已修 + SDK 首跑即踩证明了「首跑全路径覆盖」的价值）。
- [2026-10-13] 凭证扫描器 egg-info 排除曾按文件名判定，漏掉目录内文件（PKG-INFO=README 拷贝被误扫）→ 改按 path parts 判定（✅机制）。
- [2026-10-13] 门禁负向自检（探针注入）PASS→FAIL→恢复全绿全流程通过——**绿≠能拦，每次 verify 层改动后必须重放探针**。
- [2026-10-13] **安全门机制化（提交前校验条件）**：scan_secrets 升级三类检测器——internal-endpoint（内部测试环境主机族 open-*/user-*.{e,t}.lanxin.cn）/ long-hex-value（≥32 位 hex）/ blocklisted-value（本地黑名单 harness/security-blocklist.local，gitignored+0600，绝不入库）。探针负向自检：注入内部端点+hex → FAIL 拦截 ✅。教训：新检测器上线首跑即在存量测试数据抓到 11 处 long-hex（callbacks 密文向量/persistence 夹具）——**新检测器必须先全量试跑再定基线**，legit 形态走存量入册而非放宽规则（✅机制：已入棘轮）。
- [2026-10-13] release.yml 三元组校验（tag/pyproject/`__init__.__version__`）——发版三处同 PR 改齐。

## 事故档案

（暂无；按 incident-response.md 处理过的真实事件在此登记脱敏摘要。）
