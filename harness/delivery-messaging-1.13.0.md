# 交付报告 · 消息能力文档同步（harness/delivery-messaging-1.13.0.md）

> 需求：按线上文档补齐 4 项 —— 表情回复（4.6.17）· 机器人消息回调新字段（4.10.1.3）· authorizationReq 授权请求消息（4.6.4.14）· 上传素材权限提示（4.5.1）｜ 分支：`feat/messaging-doc-sync-1.13.0`（基线 = main `90b038c` = 1.12.2）｜ 日期：2026-10-14
> 模板：templates/delivery-report.md

## A. 业界五指标

| 指标 | 本轮值 | 累计口径 |
|---|---|---|
| 任务接受率 | —（待人类评审后判定） | 采纳数 / 总任务数 |
| 升级介入率 | 0（人类一次性批准「全都做」，中途无接管） | 人工接管数 / 总任务数 |
| 幻觉缺陷率 | 0（4 份线上文档逐页实读，字段名以文档为准） | 幻觉数 / 总任务数 |
| Token 成本 | —（未统计） | 每任务均值 |
| eval 通过率 | —（未重放 evals/） | 重放通过 / 案例总数 |

## B. 项目自定义字段

| 字段 | 本轮值 | 备注 |
|---|---|---|
| 返工次数 | 0 | 代码与文档一次通过 verify（lint/test/build/secrets 四态全绿） |
| 失败原因分类 | 需求不清（1 处，未致返工） | 需求文字写 `emojiType`，实读接口文档为 `emojiId`（取值 `TYPE_*`）；按文档实现并已向人类说明差异 |
| **被违反约束名 → 候选机制化** | — | 本轮未违反约束（C1'/C8'/C7' 均按要求落实） |
| **未生效约束 → 候选裁剪** | — | — |
| **C7' 三语言对齐登记** | **未同步（显式登记）** | 新增协议面：`POST /v1/messages/reply/create`（表情回复）、`authorizationReq` 消息体（`authorizationType`）、`bot_private_message`/`bot_group_message` 回调新增 `fromName`/`osType` 两个字段。`lansenger-sdk-go` / `lansenger-sdk-ts` 均无对应实现，三仓联动超出本轮范围 → 按 AGENTS.md §4 显式登记，另立需求推进 |
| 子代理使用 | 1 | README ×6 文档同步交由子代理执行（人类可见面文案由主 Agent diff 复核） |

## 本轮实证（2026-10-14）

- 代码：`src/lansenger_sdk/message_replies.py`（`reply_message`）· `src/lansenger_sdk/authorization_requests.py`（`authorization_req_payload`）· `constants.py`（`reply_create` 端点 + `REPLY_TYPE_*` / `EMOJI_IDS` / `MSG_TYPE_AUTHORIZATION_REQ` / `AUTHORIZATION_TYPE_LOCATION` / `OS_TYPES`）· `models.py`（`ReplyMessageResult`）· `client.py` / `sync_client.py`（`reply_message`、`send_authorization_request` 异步+同步双面）· `callbacks.py`（`from_name` / `os_type` 字段与映射）· `media.py`（上传素材权限 docstring）
- 测试：新增 `tests/test_message_replies.py`（13 例，含 6 个 `TYPE_*` 参数化）· `tests/test_authorization_requests.py`（2 例）· `tests/test_callback_message_fields.py`（3 例，含「老版本服务端缺字段时为空串」）；**511 passed, 6 skipped**（前 493）
- 门禁：`bash scripts/verify.sh` → **FAIL=0**（lint / test / build / secrets；WARN 均为存量 allowlist）
- 文档：README ×6（C8'）· CHANGELOG `## [1.13.0]` · AGENTS.md / docs/architecture.md / harness/report.md 计数同步
- 未覆盖：真实环境联调（⚠️ 级，需人类凭证并授权；本轮全 mock，未打真实 API）——`fromName` / `osType` 需服务端 prs5.10.0+，老版本缺字段时按空串处理
- 下游：CLI 需补 `message reply` / `message send-authorization-request` 两条命令 + 5 份 README（另 PR）；本版本新增公共方法 → CLI 下限抬到 `>=1.13.0`（C6'）
- 发布顺序：SDK 1.13.0 先发 PyPI（tag `v1.13.0`），再合 CLI
