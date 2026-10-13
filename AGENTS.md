# lansenger-sdk Agent 指南（AGENTS.md）

> **项目身份**：蓝信（Lansenger）Smart Bot API 的框架无关 Python SDK——httpx 异步内核 + `asyncio.run` 同步包装，`py.typed` 类型化，发布 PyPI `lansenger-sdk`；Go/TS 同协议兄弟仓（`lansenger-sdk-go` / `lansenger-sdk-ts`）。本文件是 Agent 的**索引 + 高频红线**；细则按第 10 节索引下沉加载，新增约束先落细则层、本文件只加一行指针（只迁移不删除）。

## 1. 目录地图与模块职责

| 路径 | 职责 |
|---|---|
| `src/lansenger_sdk/client.py` | 异步内核 `LansengerClient`（httpx.AsyncClient，域方法的主实现） |
| `src/lansenger_sdk/sync_client.py` | 同步包装 `LansengerSyncClient`：`_run_async`（已有事件循环时转线程池）+ `_ephemeral_call`（按调用临时建 client） |
| `src/lansenger_sdk/models.py` | 结果类 `*Result` dataclass（`success` + `to_dict()` 模式）——CLI/用户的消费契约 |
| `src/lansenger_sdk/constants.py` | **`API_ENDPOINTS` 端点总表**（新增端点唯一登记处） |
| `src/lansenger_sdk/config.py` / `auth.py` / `persistence.py` | 配置解析（env 优先）/ `TokenManager`（appToken 生命周期，支持 external 模式）/ `CredentialStore`（`~/.lansenger/sdk_state.json` 持久化） |
| `src/lansenger_sdk/<域>.py` ×20 | 业务域模块（oauth/groups/calendars/…）：async 函数 = 协议实现 |
| `tests/` | pytest + pytest-asyncio，**453 passed / 6 skipped**（全 mock，不打真实 API） |
| `docs/` · `harness/` · `scripts/` · `evals/` · `templates/` | Harness 产物（架构与契约 · 盘点与治理 · verify 与扫描 · 约束回归 · 度量） |

依赖方向：域模块 → `url_helpers`/`constants`/`models`/`exceptions` → httpx；`sync_client` 只包装不实现协议。禁止域模块互相 import。

## 2. 常用命令（实测三档标注）

| 用途 | 命令 | 状态 |
|---|---|---|
| 统一验证（提交前必跑） | `bash scripts/verify.sh` | ✅ 可用（lint+test+build+secrets 四态） |
| Lint（对齐 CI） | `uv run --frozen ruff check src tests` | ✅ 可用 |
| 单测 | `uv run --frozen --extra dev pytest -q` | ✅ 可用（453 passed；**`--frozen` 防锁漂移**） |
| 构建 | `uv build` | ✅ 可用 |
| pip 安装 | `pip install -e ".[dev]"` | ⚠️ 受限可用（CI 同款；本地未实测） |
| 类型检查 | mypy/pyright | 🚫 未配置（py.typed 已发布，接入=演进项，勿臆造命令） |

## 3. 编码规范要点（从现有代码归纳，不要发明新规范）

- **结果类模式**：每个 API 返回 `*Result` dataclass，含 `success: bool` 与 `to_dict()`；字段 snake_case。
- **端点集中**：URL 一律 `build_api_url(config, category, endpoint, app_token)` + `constants.API_ENDPOINTS`；禁止裸拼 URL。
- **双面透传**：新 API = 域模块 async 实现 + `LansengerClient` 方法 + `LansengerSyncClient` 透传（`_ephemeral_call`），三处同步。
- 不加注释（除非必要）；ruff line-length=120，select F/E/W/B；ignore E501/F401/F821/F841。
- 测试不打真实 API（mock httpx 层/客户端）；`--verbose` 下 logger 不得输出 token/secret 值（见 docs/action-boundary.md）。

## 4. 「不要做」清单

- 🚫 协议变更不同步 `lansenger-sdk-go`/`lansenger-sdk-ts`（必须三仓联动，或在交付报告**显式登记**不同步及理由）。
- 🚫 破坏 `py.typed` 公共签名（下游有 mypy 用户）：改公共 API 必须 `feat!:` + CHANGELOG breaking + 评估 CLI 仓联动。
- 🚫 绕过 `__version__` 三元组：tag / pyproject `version` / `src/lansenger_sdk/__init__.py __version__` 三处同 PR 改齐（release.yml 硬校验）。
- ⚠️ 用户可见面变更（新端点/方法/结果字段）**必须同步 README ×6**（md/zhHans/zhHant/zhHantHK/fr + `README.pypi.md`）。
- 🚫 不提交/回显任何凭证；不读取用户机器上的 `~/.lansenger/sdk_state.json` 值。
- 🚫 不绕过 verify；不删失败测试；同一失败连试 3 次不换方法。
- 不改 `dist/`、`src/lansenger_sdk.egg-info/` 等构建产物。

## 5. 非目标（本仓库不负责什么）

- 不做 CLI（在 `lansenger-cli` 仓）；不做 Go/TS 实现（各在兄弟仓）。
- 不绑定具体 Web 框架（framework-independent 是发布承诺）。
- 不做交付定制域（先例：1.11.0 `feat!:` 移除 7 个应用域——只保留「交付给谁都不变」的标准接口）。

## 6. 行动边界（详见 docs/action-boundary.md）

✅ 始终执行：verify/测试/构建/检索/git 只读/任务范围内编辑（编辑后 diff 回读）
⚠️ 事先询问：新增依赖 · 改公共契约（结果类/端点表/公共签名）· 删文件 · 单任务 >10 文件 · 改 CI 与发布配置
🚫 绝对禁止：git 丢弃类 · 绕过门禁 · 推未验证改动 · 删失败测试 · 凭证值进上下文/日志/提交 · 协议静默漂移（不同步 ts/go）
CLI 子命令白名单（git/uv/pytest/ruff）按表执行，冲突取更严者。

## 7. 提交纪律

1. **验证先于断言**：提交前 `bash scripts/verify.sh` 全绿（0 FAIL）；其中**安全门为阻断条件**——凭证形态 / 内部端点 / 高熵 hex / 本地黑名单（harness/security-blocklist.local）任一命中即不得提交。
2. **原子提交**：一个独立需求一个提交；conventional 前缀（`feat!:` 破坏性必须写明迁移路径）。
3. 发版 = tag `v*` == pyproject version == `__init__.__version__` + CHANGELOG 条目；同时修正 PyPI 元数据（当前 Homepage 错指 skills 仓，见 KNOWLEDGE.md）。

## 8. 踩坑沉淀约定

任务收尾回顾：坑回写 [KNOWLEDGE.md](KNOWLEDGE.md)（构建/测试/工具坑分节）；**同一问题反复出现 3 次必须机制化**。约束回归案例进 `evals/`。

## 9. 跨仓关系（兄弟仓与下游）

`lansenger-cli`（下游消费方，pyproject 钉 `lansenger-sdk>=X`）· `lansenger-sdk-go` / `lansenger-sdk-ts`（同协议对齐）· `lansenger-skills-official`（AI Skills 文档仓——注意：PyPI 元数据错指于此，勿据包元数据找源码）。

## 10. 细则索引（按需加载）

| 任务 | 先读 |
|---|---|
| 理解架构 / 新增 API | docs/architecture.md（含跨仓契约同步清单） |
| 判断能否执行某操作 | docs/action-boundary.md（三级边界 + 特有高危项） |
| 提交 / 发版 | 本文件 §7 · CHANGELOG.md |
| verify 失败排查 | harness/verify-logs/ · harness/verify-allowlist（棘轮规则） |
| 追历史坑 / 约束回归 | KNOWLEDGE.md · evals/README.md |
| 交付度量 | templates/delivery-report.md |
