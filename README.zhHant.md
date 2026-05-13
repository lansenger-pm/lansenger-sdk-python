[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# lansenger-sdk

藍信（Lansenger）平臺的框架無關 Python SDK — 支援 藍信應用、組織機器人 及 個人機器人。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests: 268](https://img.shields.io/badge/Tests-268-green)](https://github.com/lansenger-pm/lansenger-skills-official)

> 💠 零框架依賴——僅依賴 `httpx`。可適配任何異步或同步 Python 專案。

## 支援的機器人類型

| 機器人類型 | 認證 | WebSocket 入站 | 所有 API |
|------------|------|-----------------|----------|
| **藍信應用** | appToken + userToken | ✗（使用 webhook） | ✓ |
| **組織機器人** | appToken + userToken | ✗（使用 webhook） | ✓ |
| **個人機器人** | appToken | ✓（WebSocket） | ✓（非機器人 API 有部分限制） |

三種機器人類型使用相同的認證機制：每次 API 呼叫都需要 `appToken`；`userToken` 僅在特定使用者級操作時需要（使用者資訊、員工搜尋、日曆等）。

## 功能特色

- **異步 + 同步雙客戶端** — `LansengerClient`（異步）+ `LansengerSyncClient`（阻塞）
- **OAuth2 使用者認證** — 構建授權 URL、換取 userToken、刷新令牌
- **組織與部門** — 組織資訊、部門詳情/子部門/員工
- **員工與通訊錄** — 基礎/詳細資訊、ID 映射、部門祖先鏈、搜尋
- **訊息傳遞** — 3 種私聊通道（機器人、公眾號、人→人）+ 群聊，支援所有訊息類型，含 @提及和真人/機器人發送身分
- **富卡片** — appCard（支援動態狀態更新）、oacard、linkCard、verifyCard、appArticles
- **流式訊息** — SSE 即時投遞，專為 AI Agent 設計
- **媒體上傳/下載** — 檔案、圖片、影片，自動偵測類型
- **訊息管理** — 撤回、動態卡片更新
- **群組** — 建立、查詢資訊/成員/列表、檢查成員、更新設定與成員
- **日曆日程** — 主日曆、日程 CRUD、參會人管理
- **統一待辦** — 建立、更新、刪除、查詢、執行人管理、狀態統計
- **回調事件** — 26 種事件類型、訊息解析、簽名驗證

## 快速安裝

```bash
pip install lansenger-sdk
```

開發模式：

```bash
pip install -e ".[dev]"
```

## 1. 認證

### appToken — 所有 API 呼叫均需

每個 SDK 方法都需要 `appToken`。客戶端使用 `app_id` + `app_secret` 自動取得並刷新 appToken，透過 `GET /v1/apptoken/create` 端點。你無需手動管理 appToken — `TokenManager` 負責整個生命週期：

1. **首次呼叫** → 使用 app_id + app_secret 請求 `GET /v1/apptoken/create` → 回傳 `appToken`（有效期 2 小時）
2. **後續呼叫** → 重用緩衝的 appToken 直到過期
3. **令牌過期** → 自動透過同一端點刷新

```python
# appToken 由 TokenManager 自動管理——只需設定 app_id + app_secret
client = LansengerClient(app_id="your-appid", app_secret="your-secret")

# 也可以手動取得/失效令牌
token = await client.get_token()
client.invalidate_token()  # 強制下次呼叫時刷新
```

### userToken — 僅在特定端點需要

`userToken` 代表特定藍信使用者的授權（透過 OAuth2 取得）。僅在以下場景需要：
- 使用者級資訊（fetch_user_info、fetch_staff_detail、search_staff）
- 日曆與日程操作（fetch_primary_calendar、create_schedule 等）
- 作為真人發送者的群組操作

### 取得憑證

| 機器人類型 | 如何取得 app_id + app_secret |
|------------|-------------------------------|
| **個人機器人** | 藍信桌面端 → 通訊錄 → 智能機器人 → 個人機器人 → 點擊右側 ℹ️ 圖標（行動端不支援查看憑證） |
| **藍信應用** | 在藍信開發者中心建立，可能需要向組織管理員申請 |
| **組織機器人** | 在藍信開發者中心建立，可能需要向組織管理員申請 |

### OAuth2 使用者級認證

```python
# 構建授權 URL——將使用者重定向到藍信通行證頁面
url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")

# 使用者授權後，用 code 換取 userToken + refreshToken
token_result = await client.exchange_code(code="auth_code_from_callback")

# 刷新過期的 userToken
new_token = await client.refresh_user_token(refresh_token=token_result.refresh_token)

# 取得使用者資料
user_info = await client.fetch_user_info(user_token=token_result.user_token)
```

## 2. 組織與部門

```python
# 組織資訊
org = await client.fetch_org_info(org_id="orgId")

# 部門層級
detail = await client.fetch_department_detail(department_id="deptId")
children = await client.fetch_department_children(department_id="deptId")
staffs = await client.fetch_department_staffs(department_id="deptId")
```

## 3. 員工與通訊錄

```python
# 基本員工資訊
staff = await client.fetch_staff_basic_info(staff_id="staffOpenId")

# 詳細資料（建議使用 userToken）
detail = await client.fetch_staff_detail(staff_id="staffOpenId", user_token="ut")

# 手機號 → staffId 映射
mapping = await client.fetch_staff_id_mapping(
    org_id="orgId", id_type="mobile", id_value="13800138000"
)

# 員工的部門祖先鏈
ancestors = await client.fetch_department_ancestors(staff_id="staffOpenId")

# 搜尋員工（需要 userToken 或 userId）
results = await client.search_staff(keyword="張三", user_token="ut")

# 組織擴展欄位 ID
fields = await client.fetch_org_extra_field_ids(org_id="orgId")
```

## 4. 訊息與媒體

#### 機器人私聊——最常用

```python
result = await client.send_text(chat_id="staff123", content="Hello!")
result = await client.send_markdown(chat_id="staff123", content="**Bold**")
result = await client.send_file(chat_id="staff123", file_path="/path/to/report.pdf")
```

#### 公眾號通道

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"], account_id="524288-xxxx",
)
```

#### 人→人 代發通道（需要 userToken）

```python
result = await client.send_user_message(
    receiver_id="staff456", msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="ut",  # 必填
)
```

#### 群聊

```python
# 機器人 → 群組
result = await client.send_text(chat_id="group123", content="Notice", is_group=True)

# 真人 → 群組（需要 userToken）
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="ut",
)

# 群聊支援所有訊息類型（text、formatText、oacard、appCard、linkCard 等）
result = await client.send_group_message(
    group_id="group123", msg_type="appCard",
    msg_data={"appCard": {"bodyTitle": "審批", "isDynamic": True}},
    user_token="ut",
)

# 群聊 @提及
result = await client.send_text(
    chat_id="group123", content="Important!", is_group=True, reminder_all=True,
)
```

#### 富卡片

```python
result = await client.send_app_card(chat_id="staff123", body_title="審批", is_dynamic=True)
result = await client.send_link_card(chat_id="staff123", title="文章", link="https://...")
result = await client.send_app_articles(chat_id="staff123", articles=[...])

# 更新動態卡片狀態
result = await client.update_dynamic_card(msg_id="msg123", is_last_update=True)
```

#### 流式訊息（用於 AI Agent）

```python
result = await client.create_stream_message(receiver_id="staff1", receiver_type="staff", stream_id="s1")
result = await client.fetch_stream_message(msg_id="msg123")
```

#### 媒體

```python
# 上傳
upload = await client.upload_media(file_path="/path/to/file.pdf")

# 下載
download = await client.download_media(media_id="media123")

# 撤回訊息
result = await client.revoke_message(message_ids=["msg1", "msg2"])
```

## 5. 群組

```python
# 建立群組
group = await client.create_group(name="專案討論", org_id="orgId", staff_id_list=["s1","s2","s3"])

# 取得資訊與成員
info = await client.fetch_group_info(group_id="groupOpenId")
members = await client.fetch_group_members(group_id="groupOpenId")
groups = await client.fetch_group_list()

# 檢查成員身分
result = await client.check_is_in_group(group_id="groupOpenId", staff_id="staff1")

# 更新設定
await client.update_group_info(group_id="groupId", name="新名稱", manage_mode=1)

# 新增/移除成員
await client.update_group_members(
    group_id="groupId", add_user_list=["staff4"], del_user_list=["staff3"],
)
```

## 6. 日曆日程

```python
# 取得主日曆（需要 userToken 或 userId）
cal = await client.fetch_primary_calendar(user_token="ut")

# 建立日程
schedule = await client.create_schedule(
    calendar_id=cal.calendar_id, summary="團隊會議",
    start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
    end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
    user_token="ut",
)

# 查詢/刪除日程
info = await client.fetch_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.delete_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")

# 時間範圍內的日程列表（最多 42 天）
schedules = await client.fetch_schedule_list(
    calendar_id="cal1", start_time=1705276800000, end_time=1707940800000, user_token="ut",
)

# 參會人管理
attendees = await client.fetch_schedule_attendees(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.add_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
await client.delete_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
```

## 7. 統一待辦

```python
from lansenger_sdk import TODO_TYPE_APPROVAL, TODO_TODO_STATUS_DONE

# 建立待辦任務
todo = await client.create_todo_task(
    title="審批請求", link="https://app.com/a/1", pc_link="https://pc.app.com/a/1",
    executor_ids=["staff1"], org_id="org1", type=TODO_TYPE_APPROVAL,
)

# 更新狀態（11=待閱, 12=已閱, 21=待辦, 22=已辦）
await client.update_todo_task_status(todotask_id="taskId", status=TODO_TODO_STATUS_DONE, org_id="org1")

# 更新內容
await client.update_todo_task(todotask_id="taskId", title="已更新", link="l", pc_link="p", org_id="org1")

# 刪除（僅限發送者）
await client.delete_todo_task(todotask_id="taskId", org_id="org1")

# 查詢
list_result = await client.fetch_todo_task_list(org_id="org1")
task = await client.fetch_todo_task_by_id(todotask_id="taskId", org_id="org1")
task = await client.fetch_todo_task_by_source_id(source_id="src1", org_id="org1")
counts = await client.fetch_todo_task_status_counts(staff_id="staff1", org_id="org1")

# 執行人管理
await client.add_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
await client.delete_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
executors = await client.fetch_executor_list(todotask_id="taskId", org_id="org1")
await client.update_executor_status(
    executor_status_list=[{"executorId": "staff1", "todotaskId": "taskId", "status": "22"}],
    org_id="org1",
)
```

## 8. 回調事件

```python
from lansenger_sdk import parse_callback_payload, verify_callback_signature

# 解析 webhook 訊息
events = parse_callback_payload(encrypted_data, encoding_key="your_key")

# 驗證簽名
is_valid = verify_callback_signature(timestamp, nonce, signature, encoding_key)

# 可用事件類型
types = client.get_callback_event_types()  # 14 大類共 26 種事件類型
```

## 訊息類型能力矩陣

| msgType | Markdown | @提及 | 附件 | 私聊通道 | 群聊 | 備註 |
|---------|----------|-------|------|----------|------|------|
| `text` | ✗ | ✓(群聊) | ✓ | 機器人、公眾號、人→人 | ✓ | 上限 6000 字節 |
| `formatText` | ✓ | ✗ | ✗ | 僅人→人 | ✓ | Markdown（formatType=1） |
| `oacard` | ✗ | ✗ | ✗ | 機器人、公眾號、人→人 | ✓ | 簡單卡片含欄位 |
| `appCard` | ✓(div) | ✗ | ✗ | 機器人、公眾號、人→人 | ✓ | 富卡片，支援動態更新 |
| `linkCard` | ✗ | ✗ | ✗ | 機器人、公眾號 | ✓ | 連結預覽卡片 |
| `appArticles` | ✗ | ✗ | ✗ | 僅機器人私聊 | ✓ | 文章列表（1+篇） |
| `verifyCard` | ✗ | ✗ | ✗ | 機器人、公眾號 | ✓ | 驗證卡片含按鈕 |
| `system` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 系統通知 |
| `systemAction` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 系統操作含圖標 |
| `redPacket` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 紅包 |
| `transferOrder` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 轉帳通知 |
| `document` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 公文卡片 |
| `i18nAppCard` | ✓(div) | ✗ | ✗ | 機器人、公眾號、人→人 | ✓ | 多語 appCard |
| `i18nSystemAction` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 多語系統操作 |
| `i18nSystem` | ✗ | ✗ | ✗ | 平台內部 | ✓ | 多語系統訊息 |

**群聊**支援所有訊息類型。只有群聊支援 @提及。

## 配置

### 環境變數

| 變數 | 必填 | 說明 | 預設值 |
|------|------|------|--------|
| `LANSENGER_APP_ID` | ✓ | 應用/機器人 ID | — |
| `LANSENGER_APP_SECRET` | ✓ | 應用/機器人 Secret | — |
| `LANSENGER_API_GATEWAY_URL` | ✗ | API 网关 URL | `https://open.e.lanxin.cn/open/apigw` |
| `LANSENGER_PASSPORT_URL` | ✗ | 通行證 URL（OAuth2 需要） | — |

### 同步客戶端

所有方法在 `LansengerSyncClient` 上可用，簽名完全相同（阻塞式）：

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.send_text(chat_id="staff123", content="Hello!")
org = client.fetch_org_info(org_id="orgId")
```

## 專案結構

```
lansenger-skills-official/
├── src/lansenger_sdk/
│   ├── __init__.py          # 全部导出
│   ├── client.py            # LansengerClient（異步）
│   ├── sync_client.py       # LansengerSyncClient（同步）
│   ├── config.py            # LansengerConfig
│   ├── auth.py              # TokenManager — appToken 生命週期管理
│   ├── oauth.py             # OAuth2 輔助函式
│   ├── constants.py         # API 端點、媒體類型、OAuth 范围
│   ├── exceptions.py        # LansengerError 异常层级
│   ├── models.py            # 35+ dataclass 结果类型
│   ├── contacts.py          # 員工與組織資訊 API
│   ├── departments.py       # 部門 API
│   ├── account_messages.py  # 公眾號通道
│   ├── user_messages.py     # 人→人通道
│   ├── group_messages.py    # 群聊通道
│   ├── media.py             # 上傳/下載
│   ├── streaming.py         # SSE 流式訊息
│   ├── callbacks.py         # 回調事件
│   ├── groups.py            # 群組 API
│   ├── todos.py             # 統一待辦
│   ├── calendars.py         # 日曆日程
│   └── users.py             # 使用者資訊
├── tests/                   # 268 個測試，全部通過
├── skills/                  # 9 個 skill 文件 + manifest
├── pyproject.toml
└── README*.md               # 5 語言 README
```

## 開發

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 授權

MIT — 見 [LICENSE](LICENSE)。