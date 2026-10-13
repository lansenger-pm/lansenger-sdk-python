# Bootstrap 盘点报告（Harness 阶段 0 · 只读）

> 生成：2026-10-13 ｜ 分支：feat/agent-harness ｜ 依据：Harness Bootstrap Playbook v3（形态 C：产物平移自 lansenger-cli 仓已验证模板）

## ① 技术栈清单

| 维度 | 事实 | 来源 |
|---|---|---|
| 语言 | Python ≥ 3.10 | pyproject `requires-python` |
| HTTP | httpx ≥ 0.24（**唯一运行时依赖**，最小面是发布承诺） | pyproject |
| 异步 | asyncio 内核 + `asyncio.run` 同步包装（嵌套循环→线程池） | sync_client.py:81 |
| 测试 | pytest + pytest-asyncio（**485 passed, 6 skipped in 0.36s 实测**；25 文件/7344 行） | tests/ 实测 |
| Lint | ruff（F/E/W/B，line-length 120），**CI 已含** | pyproject + ci.yml |
| 构建 | setuptools；`uv build` 实测通过 | pyproject |
| CI | ci.yml：ruff + pytest 矩阵 3.10–3.13；release.yml：**tag==pyproject==__init__ 三元组硬校验** | .github/workflows 实读 |
| 类型 | py.typed 已发布；mypy 未配置 | pyproject `[tool.setuptools.package-data]` |
| 兄弟仓 | lansenger-sdk-go / lansenger-sdk-ts（同协议）；lansenger-cli（下游）；lansenger-skills-official（文档仓，PyPI 元数据错指于此） | org 实证 |

## ② 目录地图

```
lansenger-sdk-python/
├── src/lansenger_sdk/      # 28 模块 14940 行
│   ├── client.py           # 异步内核 LansengerClient
│   ├── sync_client.py      # 同步门面（_run_async/_ephemeral_call）
│   ├── models.py           # *Result dataclass
│   ├── constants.py        # API_ENDPOINTS
│   ├── config.py / auth.py / persistence.py / url_helpers.py / exceptions.py
│   └── <域>.py ×20         # oauth/groups/calendars/…（协议实现）
├── tests/                  # 25 文件 485 例（全 mock）
├── .github/workflows/      # ci.yml（ruff+test 矩阵）/ release.yml（三元组校验）
├── scripts/ docs/ harness/ evals/ templates/ AGENTS.md KNOWLEDGE.md  # 【本次新增 Harness】
└── README ×6               # md/zhHans/zhHant/zhHantHK/fr + pypi 专版
```

## ③ 已有可执行检查（盘点时已存在，实测确认）

| 检查 | 状态 |
|---|---|
| ruff check src tests | ✅ All checks passed（且 CI 已含——优于 CLI 修复前） |
| pytest（矩阵 3.10–3.13） | ✅ 485 passed, 6 skipped |
| uv build | ✅ 通过 |
| release 三元组校验 | ✅ 机制级（tag/pyproject/__init__ 三处） |
| 凭证排除意识 | ✅ .gitignore 排除 .env/*.pem/*.key/*.log |

## ④ 缺失清单（本次补齐或列待办）

| 缺失 | 处置 |
|---|---|
| AGENTS.md（且被 .gitignore 忽略——**与 CLI 修复前同款坑**） | ✅ 补齐 + .gitignore 修正 |
| verify 统一入口 / 边界表 / 架构文档 | ✅ 本次补齐 |
| 凭证扫描 + 棘轮（首跑 9 命中全部为测试夹具假值，已人工核形态后入册） | ✅ 本次补齐（详见 verify-allowlist 误报段判据） |
| KNOWLEDGE / evals / 度量 / 成熟度 | ✅ 本次补齐 |
| mypy（py.typed 已发布但无自检） | ⚠️ 演进项 M |
| sync/client 签名镜像一致性（无 lint/测试强制） | ⚠️ 演进项 S：加一致性测试 |
| pyproject Project-URL 错指 skills 仓 | ⚠️ 1.12.0 发版 PR 必修（勿混入 bootstrap 提交） |

## ⑤ 风险 Top5

1. **三语言协议漂移**（py/ts/go）：对齐靠人肉（commit 实证）→ C7' + evals CR-03。
2. **py.typed 破坏**：公共签名即下游类型 API，无 mypy 自检 → C4' + 演进项。
3. **日志泄露面**：SDK logger 直达下游 CLI `--verbose` 终端，token/secret 红线必须成文 → C9'。
4. **README ×6 同步**：比 CLI 还多一份 pypi 专版 → C8'。
5. **`~/.lansenger/sdk_state.json` 写入方**：SDK 是凭据持久化的实现者，测试须走 tmp 路径 → 边界表。

## ⑥ 推荐门禁清单（成本标尺 S≤2h / M≤2d / L>2d）

| 优先级 | 门禁 | 成本 | 状态 |
|---|---|---|---|
| P0 | verify 四态入口 + 棘轮 + 探针自检 | S | ✅ 已建（探针 FAIL=1 实证拦截） |
| P0 | AGENTS.md + 边界表 + 架构契约清单 | S | ✅ 已建 |
| P1 | 1.12.0 PR 修正 PyPI 元数据 | S | ⚠️ 随功能 PR |
| P1 | pre-commit 激活（一条命令） | S | ⚠️ 人工 |
| P2 | sync/client 签名镜像一致性测试 | S | 演进 |
| P2 | mypy 渐进接入 | M | 演进 |
| P3 | ts/go 仓同款 Harness 化 | S×2 | 待定 |

## 附注

- 凭证专项：仓库内零真凭证（9 命中全为测试夹具假值，形态证据见 allowlist）；`~/.lansenger/` 与 CI Secrets 在仓外，见 harness/report-credentials.md。
- git：main 单主干 + tag 发版；工作区开工前干净；本次 Harness 产物在 `feat/agent-harness` 分支。
