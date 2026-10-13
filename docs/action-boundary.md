# 三级行动边界表（docs/action-boundary.md）

> 定位：Harness ⑥权限层 + ④变更层。Agent 在本仓库的授权边界**唯一事实源**；与 AGENTS.md 冲突以本表为准，取更严者。
> 维护：新增/调整须经人工确认；每季度审计从未生效条目考虑裁剪。

## ✅ 一级：始终执行（无需询问）

- 跑 `bash scripts/verify.sh`、pytest、ruff、uv build（`--frozen` 优先，防锁漂移）
- 读仓库文件与检索（排除构建产物与 `.venv/`）
- git 只读：status / diff / log / show / tag -l / branch -a
- 任务范围内文件编辑（编辑后 `git diff` 回读核对）
- 用 `uv run python -c` 做无副作用的接口形态验证（import、签名检查）

## ⚠️ 二级：事先询问（默认列待办，明确授权后才做）

- 新增第三方依赖（当前运行时依赖仅 `httpx`——保持最小面是发布承诺）
- 改公共契约：`API_ENDPOINTS`、`*Result` 字段、公共方法签名（触发 C1'–C4' 联动）
- 协议变更的 ts/go 对齐策略（三仓联动 or 显式登记不同步——C7'）
- 改 `.github/workflows/`
- 删除文件 / 拆分大模块（sync_client 900+ 行）
- 单任务 >10 文件；同文件并发改动
- `git add` / `git commit`（verify 全绿 → 展示 diff → 确认 → 原子提交；push 另行确认）
- 对真实蓝信环境执行任何联网验证（SDK 测试全 mock；真实联调需要用户提供 stage 测试凭证并明确授权）
- `uv build` 后发布相关操作（`uv publish` 禁由 Agent 执行）

## 🚫 三级：绝对禁止

- git 丢弃类：`stash` / `reset --hard` / `checkout .` / `clean` / 改历史
- 绕过 verify 提交；推未验证改动；删失败测试凑绿
- 提交或输出密钥、token、密码；读取或回显 `~/.lansenger/sdk_state.json` 值
- **logger 输出 token/secret 值**（C9'：`--verbose` DEBUG 日志是下游 CLI 的攻击面）
- 协议静默漂移：改端点/参数/响应解析而不评估 ts/go 对齐（C7'）
- 破坏 `py.typed`：删改公共类型注解、改公共方法签名不升 `feat!:`（C4'）
- 把 `pyproject.toml` 的 `Project-URL` 再指向无关仓（当前错指 skills 仓为历史 bug，1.12.0 修正，勿复制该错误）
- 单凭一次检索「无匹配」下清零结论；同一失败连试 3 次不换方法

## CLI 子命令白名单（冲突取更严；新 CLI 先入表再用）

| CLI | ✅ 可直接调用 | ⚠️ 需人工授权 | 🚫 禁止 |
|---|---|---|---|
| `git` | status/diff/log/show/tag（只读） | add/commit（verify 全绿 + diff 确认）、push | 丢弃类、force-push、改 hooksPath |
| `uv` | run --frozen / lock --locked / build | `uv add`（=新增依赖）、`uv lock` 升级 | `uv publish`（发版只走 tag 流程） |
| `pytest` / `ruff` | 全部 | — | deselect/注释失败用例凑绿 |
| `python -c` | 无副作用形态验证 | 依赖真实凭证的联网验证 | 用真实生产凭证调用 |

## 本仓库特有高危项（阶段 0 探测登记）

| 高危项 | 说明 | 防线 |
|---|---|---|
| 三语言协议漂移 | py/ts/go 三实现，静默漂移=下游事故 | C7' + evals CR-03 + 交付报告登记字段 |
| py.typed 类型契约 | 公共签名即下游类型 API | C4' + feat! 语义 + 评审拦截 |
| `~/.lansenger/sdk_state.json` | SDK 自己实现持久化（写入方！）——文件含真实凭据 | 只测 store 逻辑用 tmp 路径；禁读真实文件值 |
| `--verbose` DEBUG 日志 | SDK logger 直接面向下游 CLI 用户终端 | C9' 红线 + evals 用例（日志断言不含 token 值） |
| PyPI 发布 | release.yml 自动发布 | tag==version==`__init__` 三元组硬校验；Agent 不执行发布 |
| README ×6 | 漏改即漂移 | C8' + evals CR-05 |

## ④变更约束（内置于本表）

- diff 软上限：单任务 >10 文件先拆（⚠️）
- 重试上限：同败 3 次换方法（🚫 兜底）
- 受控提交：verify 全绿 → diff 确认 → 原子提交（⚠️ 流程）
