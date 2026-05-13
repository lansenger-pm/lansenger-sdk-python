[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# lansenger-sdk

蓝信（Lansenger）平台框架无关的 Python SDK — 支持 蓝信应用、组织机器人 和 个人机器人。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests: 296](https://img.shields.io/badge/Tests-296-green)](https://github.com/lansenger-pm/lansenger-skills-official)

> 💠 零框架依赖 — 仅依赖 `httpx`。兼容任何异步或同步 Python 项目。

## 支持的机器人类型

| 机器人类型 | 认证方式 | WebSocket 入站 | 全部 API |
|----------|------|-------------------|----------|
| **蓝信应用** | appToken + userToken | ✗（使用 webhook） | ✓ |
| **组织机器人** | appToken + userToken | ✗（使用 webhook） | ✓ |
| **个人机器人** | appToken | ✓（WebSocket） | ✓（非机器人 API 受限） |

三种机器人类型使用相同的认证机制：`appToken` 为每次 API 调用所必需；`userToken` 仅在特定用户级操作（用户信息、员工搜索、日程等）中需要。

## 功能特性

- **异步与同步客户端** — `LansengerClient`（异步）+ `LansengerSyncClient`（阻塞）
- **凭据与令牌持久化** — `CredentialStore` 将 app_id、app_secret、URL、appToken、userToken 保存到文件（重启后不丢失）
- **OAuth2 用户认证** — 授权 URL、code 换取、令牌刷新
- **组织与部门** — 组织信息、部门详情/子部门/员工列表
- **员工与通讯录** — 基础/详细信息、ID 映射、部门祖辈链、搜索
- **消息发送** — 3 种私聊通道（机器人、公众号、人→人）+ 群聊，支持所有消息类型，含 @提及和真人/机器人发送身份
- **富卡片** — appCard（支持动态状态更新）、oacard、linkCard、verifyCard、appArticles
- **流式消息** — 基于 SSE 的实时推送，适用于 AI 智能体
- **媒体上传/下载** — 文件、图片、视频，自动类型检测
- **消息管理** — 撤回、动态卡片更新
- **群组** — 创建、信息、成员、列表、成员检查、更新设置与成员
- **日历与日程** — 主日历、日程 CRUD、参会人管理
- **统一待办** — 创建、更新、删除、查询、执行人管理、状态计数
- **回调事件** — 25 种事件类型、结构化数据解析、签名验证

## 快速安装

```bash
pip install lansenger-sdk
```

开发安装：

```bash
pip install -e ".[dev]"
```

## 1. 认证

### appToken — 所有 API 调用必需

每个 SDK 方法都需要 `appToken`。客户端使用 `app_id` + `app_secret` 通过 `GET /v1/apptoken/create` 自动获取并刷新 appToken，由 `TokenManager` 自动管理生命周期，无需手动处理：

1. **首次调用** → `GET /v1/apptoken/create`（携带 app_id + app_secret） → 返回 `appToken`（有效期 2 小时）
2. **后续调用** → 复用缓存的 appToken，直到过期
3. **令牌过期** → 自动通过同一端点刷新

```python
# appToken 由 TokenManager 自动管理 — 只需配置 app_id + app_secret
client = LansengerClient(app_id="your-appid", app_secret="your-secret")

# 也可以手动获取/失效令牌
token = await client.get_token()
client.invalidate_token()  # 强制下次调用时刷新
```

### userToken — 仅特定端点需要

`userToken` 代表特定蓝信用户的授权（通过 OAuth2 获取），仅在以下操作中需要：
- 用户级信息（fetch_user_info、fetch_staff_detail、search_staff）
- 日历与日程操作（fetch_primary_calendar、create_schedule 等）
- 以人类身份发送的群聊操作

### 获取凭证

| 机器人类型 | 如何获取 app_id + app_secret |
|----------|--------------------------------|
| **个人机器人** | 蓝信桌面端 → 通讯录 → 智能机器人 → 个人机器人 → 点击右侧 ℹ️ 图标（移动端不支持查看凭证） |
| **蓝信应用** | 在蓝信开发者中心创建，可能需要向组织管理员申请 |
| **组织机器人** | 在蓝信开发者中心创建，可能需要向组织管理员申请 |

### OAuth2 用户级认证

```python
# 构建授权 URL — 将用户重定向到蓝信通行证
url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")

# 用户授权后，用 code 换取 userToken + refreshToken
token_result = await client.exchange_code(code="auth_code_from_callback")

# 刷新过期的 userToken
new_token = await client.refresh_user_token(refresh_token=token_result.refresh_token)

# 获取用户资料
user_info = await client.fetch_user_info(user_token=token_result.user_token)
```

## 2. 组织与部门

```python
# 组织信息
org = await client.fetch_org_info(org_id="orgId")

# 部门层级
detail = await client.fetch_department_detail(department_id="deptId")
children = await client.fetch_department_children(department_id="deptId")
staffs = await client.fetch_department_staffs(department_id="deptId")
```

## 3. 员工与通讯录

```python
# 基础员工信息
staff = await client.fetch_staff_basic_info(staff_id="staffOpenId")

# 详细资料（推荐使用 userToken）
detail = await client.fetch_staff_detail(staff_id="staffOpenId", user_token="ut")

# 手机号 → staffId 映射
mapping = await client.fetch_staff_id_mapping(
    org_id="orgId", id_type="mobile", id_value="13800138000"
)

# 员工的部门祖辈链
ancestors = await client.fetch_department_ancestors(staff_id="staffOpenId")

# 搜索员工（需要 userToken 或 userId）
results = await client.search_staff(keyword="张三", user_token="ut")

# 组织扩展字段 ID
fields = await client.fetch_org_extra_field_ids(org_id="orgId")
```

## 4. 消息与媒体

#### 机器人私聊 — 最常用

```python
result = await client.send_text(chat_id="staff123", content="Hello!")
result = await client.send_markdown(chat_id="staff123", content="**Bold**")
result = await client.send_file(chat_id="staff123", file_path="/path/to/report.pdf")
```

#### 公众号通道

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"], account_id="524288-xxxx",
)
```

#### 人→人 代发通道（需要 userToken）

```python
result = await client.send_user_message(
    receiver_id="staff456", msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="ut",  # 必需
)
```

#### 群聊

```python
# 机器人 → 群
result = await client.send_text(chat_id="group123", content="Notice", is_group=True)

# 人类 → 群（需要 userToken）
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="ut",
)

# 群聊支持所有消息类型（text、formatText、oacard、appCard、linkCard 等）
result = await client.send_group_message(
    group_id="group123", msg_type="appCard",
    msg_data={"appCard": {"bodyTitle": "审批", "isDynamic": True}},
    user_token="ut",
)

# 群内 @提及
result = await client.send_text(
    chat_id="group123", content="Important!", is_group=True, reminder_all=True,
)
```

#### 富卡片

```python
result = await client.send_app_card(chat_id="staff123", body_title="审批", is_dynamic=True)
result = await client.send_link_card(chat_id="staff123", title="文章", link="https://...")
result = await client.send_app_articles(chat_id="staff123", articles=[...])

# 更新动态卡片状态
result = await client.update_dynamic_card(msg_id="msg123", is_last_update=True)
```

#### 流式消息（适用于 AI 智能体）

```python
result = await client.create_stream_message(receiver_id="staff1", receiver_type="staff", stream_id="s1")
result = await client.fetch_stream_message(msg_id="msg123")
```

#### 媒体

```python
# 上传
upload = await client.upload_media(file_path="/path/to/file.pdf")

# 下载
download = await client.download_media(media_id="media123")

# 撤回消息
result = await client.revoke_message(message_ids=["msg1", "msg2"])
```

## 5. 群组

```python
# 创建群
group = await client.create_group(name="项目讨论", org_id="orgId", staff_id_list=["s1","s2","s3"])

# 获取信息与成员
info = await client.fetch_group_info(group_id="groupOpenId")
members = await client.fetch_group_members(group_id="groupOpenId")
groups = await client.fetch_group_list()

# 检查成员身份
result = await client.check_is_in_group(group_id="groupOpenId", staff_id="staff1")

# 更新设置
await client.update_group_info(group_id="groupId", name="新名称", manage_mode=1)

# 添加/移除成员
await client.update_group_members(
    group_id="groupId", add_user_list=["staff4"], del_user_list=["staff3"],
)
```

## 6. 日历与日程

```python
# 获取主日历（需要 userToken 或 userId）
cal = await client.fetch_primary_calendar(user_token="ut")

# 创建日程
schedule = await client.create_schedule(
    calendar_id=cal.calendar_id, summary="团队会议",
    start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
    end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
    user_token="ut",
)

# 获取/删除日程
info = await client.fetch_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.delete_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")

# 时间范围内的日程列表（最长 42 天）
schedules = await client.fetch_schedule_list(
    calendar_id="cal1", start_time=1705276800000, end_time=1707940800000, user_token="ut",
)

# 参会人管理
attendees = await client.fetch_schedule_attendees(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.add_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
await client.delete_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
```

## 7. 统一待办

```python
from lansenger_sdk import TODO_TYPE_APPROVAL, TODO_TODO_STATUS_DONE

# 创建待办任务
todo = await client.create_todo_task(
    title="审批请求", link="https://app.com/a/1", pc_link="https://pc.app.com/a/1",
    executor_ids=["staff1"], org_id="org1", type=TODO_TYPE_APPROVAL,
)

# 更新状态（11=待阅, 12=已阅, 21=待办, 22=已办）
await client.update_todo_task_status(todotask_id="taskId", status=TODO_TODO_STATUS_DONE, org_id="org1")

# 更新内容
await client.update_todo_task(todotask_id="taskId", title="已更新", link="l", pc_link="p", org_id="org1")

# 删除（仅发起人）
await client.delete_todo_task(todotask_id="taskId", org_id="org1")

# 查询
list_result = await client.fetch_todo_task_list(org_id="org1")
task = await client.fetch_todo_task_by_id(todotask_id="taskId", org_id="org1")
task = await client.fetch_todo_task_by_source_id(source_id="src1", org_id="org1")
counts = await client.fetch_todo_task_status_counts(staff_id="staff1", org_id="org1")

# 执行人管理
await client.add_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
await client.delete_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
executors = await client.fetch_executor_list(todotask_id="taskId", org_id="org1")
await client.update_executor_status(
    executor_status_list=[{"executorId": "staff1", "todotaskId": "taskId", "status": "22"}],
    org_id="org1",
)
```

## 8. 回调事件

```python
from lansenger_sdk import parse_callback_payload, verify_callback_signature

# 解析 webhook 载荷
events = parse_callback_payload(encrypted_data, encoding_key="your_key")

# 验证签名
is_valid = verify_callback_signature(timestamp, nonce, signature, encoding_key)

# 可用事件类型
types = client.get_callback_event_types()  # 14 个类别下的 26 种事件类型
```

## 消息类型能力矩阵

| msgType | Markdown | @提及 | 附件 | 私聊通道 | 群聊 | 备注 |
|---------|----------|-------|------|----------|------|------|
| `text` | ✗ | ✓(群聊) | ✓ | 机器人、公众号、人→人 | ✓ | 上限 6000 字节 |
| `formatText` | ✓ | ✗ | ✗ | 仅人→人 | ✓ | Markdown（formatType=1） |
| `oacard` | ✗ | ✗ | ✗ | 机器人、公众号、人→人 | ✓ | 简单卡片含字段 |
| `appCard` | ✓(div) | ✗ | ✗ | 机器人、公众号、人→人 | ✓ | 富卡片，支持动态更新 |
| `linkCard` | ✗ | ✗ | ✗ | 机器人、公众号 | ✓ | 链接预览卡片 |
| `appArticles` | ✗ | ✗ | ✗ | 仅机器人私聊 | ✓ | 文章列表（1+篇） |
| `verifyCard` | ✗ | ✗ | ✗ | 机器人、公众号 | ✓ | 验证卡片含按钮 |
| `i18nAppCard` | ✓(div) | ✗ | ✗ | 机器人、公众号、人→人 | ✓ | 多语言 appCard |
| `i18nSystemAction` | ✗ | ✗ | ✗ | 平台内部 | ✓ | 多语言系统操作 |
| `i18nSystem` | ✗ | ✗ | ✗ | 平台内部 | ✓ | 多语言系统消息 |

**群聊**支持所有消息类型。只有群聊支持 @提及。

## 配置

### 环境变量

| 变量 | 必需 | 说明 | 默认值 |
|----------|----------|-------------|---------|
| `LANSENGER_APP_ID` | ✓ | 应用/机器人 ID | — |
| `LANSENGER_APP_SECRET` | ✓ | 应用/机器人 Secret | — |
| `LANSENGER_API_GATEWAY_URL` | ✗ | API 网关 URL | `https://open.e.lanxin.cn/open/apigw` |
| `LANSENGER_PASSPORT_URL` | ✗ | 通行证 URL（用于 OAuth2） | — |

### 凭据与令牌持久化

默认情况下，凭据和令牌仅保存在内存中（进程退出即丢失）。通过 `store_path` 开启文件持久化：

```python
from lansenger_sdk import LansengerClient, CredentialStore

# 持久化到 ~/.lansenger/sdk_state.json（0600 权限）
client = LansengerClient(app_id="...", app_secret="...", store_path="~/.lansenger/sdk_state.json")

# 或从环境变量创建并持久化
client = LansengerClient.from_env(store_path="~/.lansenger/sdk_state.json")

# 手动操作存储
store = CredentialStore(path="~/.lansenger/sdk_state.json")
store.save_credentials("app_id", "app_secret", api_gateway_url="...", passport_url="...")
store.save_user_token("user_token", refresh_token="refresh_token")
token = store.load_app_token()  # 过期则返回 None
```

开启持久化后：
- **appToken** 每次获取后自动保存，重启时复用（避免重复请求）
- **userToken + refreshToken** 在 OAuth2 换取后自动保存
- **凭据 + URL** 一同保存，完整恢复配置

`LansengerSyncClient` 提供所有方法，签名完全一致（阻塞式）：

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.send_text(chat_id="staff123", content="Hello!")
org = client.fetch_org_info(org_id="orgId")
```

## 项目结构

```
lansenger-skills-official/
├── src/lansenger_sdk/
│   ├── __init__.py          # 全部导出
│   ├── client.py            # LansengerClient（异步）
│   ├── sync_client.py       # LansengerSyncClient（同步）
│   ├── config.py            # LansengerConfig
│   ├── auth.py              # TokenManager — appToken 生命周期
│   ├── oauth.py             # OAuth2 工具
│   ├── constants.py         # API 端点、媒体类型、OAuth 范围
│   ├── exceptions.py        # LansengerError 异常层级
│   ├── models.py            # 35+ dataclass 结果类型
│   ├── contacts.py          # 员工与组织信息 API
│   ├── departments.py       # 部门 API
│   ├── account_messages.py  # 公众号通道
│   ├── user_messages.py     # 人→人通道
│   ├── group_messages.py    # 群聊通道
│   ├── media.py             # 上传/下载
│   ├── streaming.py         # SSE 流式推送
│   ├── persistence.py       # CredentialStore — 凭据与令牌文件持久化
│   ├── callbacks.py         # 回调事件
│   ├── groups.py            # 群组 API
│   ├── todos.py             # 统一待办
│   ├── calendars.py         # 日历与日程
│   └── users.py             # 用户信息
├── tests/                   # 296 项测试，全部通过
├── skills/                  # 9 项技能文档 + manifest
├── pyproject.toml
└── README*.md               # 5 语言 README
```

## 开发

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 许可证

MIT — 见 [LICENSE](LICENSE)。