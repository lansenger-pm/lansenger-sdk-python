[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# lansenger-sdk

藍信（Lansenger）平臺的框架無關 Python SDK — 支援 藍信應用、組織機器人 及 個人機器人。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests: 341](https://img.shields.io/badge/Tests-341-green)](https://github.com/lansenger-pm/lansenger-sdk-python)

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
- **憑證與令牌持久化** — `CredentialStore` 將 app_id、app_secret、URL、appToken、userToken 保存至檔案（重啟不丟失）
- **OAuth2 使用者認證** — 構建授權 URL、換取 userToken、刷新令牌
- **組織與部門** — 組織資訊、部門詳情/子部門/員工
- **員工與通訊錄** — 基礎/詳細資訊、ID 映射、部門祖先鏈、搜尋
- **訊息傳遞** — 3 種私聊通道（機器人、公眾號、人→人）+ 群聊，支援所有訊息類型，含 @提及和真人/機器人傳送身分，加急提醒
- **富卡片** — appCard（支援動態狀態更新）、oacard、linkCard、verifyCard、appArticles
- **流式訊息** — SSE 即時投遞，專為 AI Agent 設計
- **媒體上傳/下載** — 檔案、圖片、影片，自動偵測類型，媒體路徑取得
- **訊息管理** — 撤回、動態卡片更新
- **群組** — 建立、查詢資訊/成員/列表、檢查成員、更新設定與成員、解散
- **日曆日程** — 主日曆、日程 CRUD + 更新、參會人管理 + 參會人元資料
- **統一待辦** — 建立、更新、刪除、查詢、執行人管理、狀態統計
- **回調事件** — 25 種事件類型、結構化解析、AES 解密（按 4.10.1.4規範）、SHA1 簽名驗證

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
- 作為真人傳送者的群組操作

### 取得憑證

| 機器人類型 | 如何取得 app_id + app_secret |
|------------|-------------------------------|
| **個人機器人** | 藍信桌面端 → 通訊錄 → 智慧機器人 → 個人機器人 → 點擊右側 ℹ️ 圖標（行動端不支援查看憑證） |
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

# 取得下載路徑（4.5.3）
path_result = await client.fetch_media_path(media_id="media123")

# 撤回訊息
result = await client.revoke_message(message_ids=["msg1", "msg2"])
```

#### 加急提醒（4.6.14）

```python
from lansenger_sdk import REMINDER_TYPE_POPUP, REMINDER_TYPE_SMS, REMINDER_TYPE_PHONE

result = await client.send_reminder(
    msg_id="msg123",
    reminder_types=[REMINDER_TYPE_POPUP, REMINDER_TYPE_SMS],
    user_id_list=["staff1", "staff2"],
)
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

# 解散群組（僅群主，4.28.6）
await client.dismiss_group(group_id="groupId")
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

# 更新日程（4.23.12）
await client.update_schedule(
    calendar_id="cal1", schedule_id="sch1",
    summary="更新的會議", operation_type="modify_all",
    user_token="ut",
)

# 更新參會人元資料（4.23.17）— RSVP、顏色、忙/閒、提醒
await client.update_schedule_attendee_meta(
    calendar_id="cal1", schedule_id="sch1",
    rsvp_status="accept", busy_free_state="busy",
    remind_times=[5, 15], user_token="ut",
)
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

# 刪除（僅限傳送者）
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

SDK 同時支援明文 JSON 和 AES 加密回調載荷（按藍信接口規範 4.10.1.4）。

### 配置

設定 `encoding_key` 和 `callback_token`（來自藍信開發者中心回調設定）：

```python
client = LansengerClient(
    app_id="your-appid", app_secret="your-secret",
    encoding_key="BASE64_AES密鑰",
    callback_token="回調簽名令牌",
)
```

也可透過環境變數：`LANSENGER_ENCODING_KEY`、`LANSENGER_CALLBACK_TOKEN`。

### 解析回調載荷（自動辨識加密/明文）

```python
from lansenger_sdk import parse_callback_payload, decrypt_callback_payload

# 明文 JSON
events = parse_callback_payload('{"events": [...]}')

# AES 加密載荷（自動用 encoding_key 解密）
events = parse_callback_payload(
    encrypted_data,
    encoding_key="BASE64_AES密鑰",
    known_app_id="your-appid",  # 輔助解密後 orgId/appId 的邊界拆分
)
```

### 驗證簽名

```python
from lansenger_sdk import verify_callback_signature

# sha1(sort(token, timestamp, nonce, dataEncrypt))
is_valid = verify_callback_signature(
    timestamp, nonce, signature, encoding_key,
    data_encrypt=encrypted_data,
    callback_token="回調簽名令牌",  # 為空時回退到 encoding_key
)
```

### 直接解密

```python
result = decrypt_callback_payload(encrypted_data, encoding_key="密鑰", known_app_id="應用ID")
# result = {"orgId": "...", "appId": "...", "events": [...], "length": N}
```

### 事件類型

```python
types = client.get_callback_event_types()  # 13 個類別共 25 種事件類型
```

AES 解密需安裝 `pycryptodome` 或 `cryptography` 包（自動檢測）。

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
| `LANSENGER_REDIRECT_URI` | ✗ | OAuth2 回調地址 | `http://localhost:8765` |
| `LANSENGER_ENCODING_KEY` | ✗ | 回調 AES 加密密鑰（Base64） | — |
| `LANSENGER_CALLBACK_TOKEN` | ✗ | 回調簽名令牌 | — |

### 憑證與令牌持久化

預設情況下，憑證和令牌僅保留在記憶體中（程式退出即消失）。透過 `store_path` 啟用檔案持久化：

```python
from lansenger_sdk import LansengerClient, CredentialStore

# 持久化至 ~/.lansenger/sdk_state.json（0600 權限）
client = LansengerClient(
    app_id="...", app_secret="...",
    encoding_key="BASE64_AES密鑰", callback_token="回調簽名令牌",
    store_path="~/.lansenger/sdk_state.json",
)

# 或從環境變數建立並持久化
client = LansengerClient.from_env(store_path="~/.lansenger/sdk_state.json")

# 手動操作儲存
store = CredentialStore(path="~/.lansenger/sdk_state.json")
store.save_credentials("app_id", "app_secret", api_gateway_url="...", passport_url="...")
store.save_user_token("user_token", refresh_token="refresh_token")
token = store.load_app_token()  # 過期則回傳 None
```

啟用持久化後：
- **appToken** 每次取得後自動儲存，重啟時復用（避免重複請求）
- **userToken + refreshToken** 在 OAuth2 換取後自動儲存
- **憑證 + URL** 一併儲存，完整復原設定

所有方法在 `LansengerSyncClient` 上可用，簽名完全相同（阻塞式）：

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.send_text(chat_id="staff123", content="Hello!")
org = client.fetch_org_info(org_id="orgId")
```

## 身份與權限

### 身份能力矩陣

藍信平台具有三種身份類型，API 存取權限各不相同：

| 命令域 | 個人機器人 | 組織應用(自建) | 組織應用+機器人 | 備註 |
|--------|:---:|:---:|:---:|------|
| `message send-text/markdown/file/...` (機器人私聊) | **Y** | N | **Y** | 僅機器人可傳送機器人私聊 |
| `message send-text --group` (群聊) | N* | N | **Y** | 個人機器人 API 支援但暫無加群功能 |
| `message send-group-message` | N* | N | **Y** | 同上 |
| `message send-account-message` (公眾號) | N | **Y** | **Y** | 需要公眾號能力 |
| `message send-user-message` (人→人) | N | **Y** | **Y** | 需要 userToken + OAuth2 |
| `message revoke` | **Y** | **Y** | **Y** | 撤回自己發出的訊息 |
| `staff *` (通訊錄唯讀) | N | **Y** | **Y** | `search` 額外需要 userToken |
| `department *` | N | **Y** | **Y** | 僅組織級應用 |
| `calendar *` | N | **Y** | **Y** | 攜帶 userToken = 使用者身份；不攜帶 = 機器人身份 |
| `todo *` | N | **Y** | **Y** | 僅組織級應用 |
| `chat list/messages` | N | **Y** | **Y** | 僅組織級應用 |
| `group *` (群組管理 V2) | N | N | **Y** | 需要機器人在群內 |
| `media upload` | **Y** | **Y** | **Y** | 通用上傳 |
| `media upload-app` | N | **Y** | **Y** | 僅自建應用（非 ISV） |
| `media download/path` | **Y** | **Y** | **Y** | 通用下載 |
| `oauth *` | N | **Y** | **Y** | 僅組織級應用 |
| `streaming *` | N | **Y** | **Y** | 僅組織級應用 |
| `callback *` (事件解析) | N/A | N/A | N/A | 純資料操作，無需身份 |

> \* **N\*** = API 能力存在，但加群功能尚未就緒。

> **個人機器人**只能收發訊息和上傳/下載檔案。無法存取通訊錄、群組、日曆或 OAuth2。
>
> **組織應用 vs 組織應用+機器人**：相同的 appID/appSecret。唯一區別是訊息通道——只有機器人可以傳送機器人私聊和群聊訊息（因為只有機器人可以加入群）。所有其他 API（通訊錄、日曆、待辦、聊天、OAuth2、流式訊息）對於兩者完全相同。目前僅自建應用支援機器人能力。

### 開發者中心權限

除了身份類型，特定 API 呼叫還取決於藍信開發者中心的權限開關。組織可能限制開發者存取，需要管理員協助。

**基礎權限（預設開啟）：**

| 權限 | 描述 |
|------|------|
| 獲取使用者基本資訊 | 獲取人員基本資訊用於系統/應用登入 |
| 傳送通知訊息 | 獲取組織訊息通道，向個人/群組傳送訊息 |

**高階權限（預設關閉，需手動開啟）：**

| 權限 | 描述 |
|------|------|
| 通訊錄唯讀 | 通訊錄讀取權限 |
| 通訊錄編輯 | 通訊錄編輯權限（新增/修改/刪除人員） |
| 敏感資訊-手機號 | 獲取使用者手機號 |
| 敏感資訊-郵箱 | 獲取使用者郵箱 |
| 敏感資訊-身份證號 | 獲取使用者身份證號 |
| 敏感資訊-員工工號 | 獲取使用者員工工號 |
| 映射唯一屬性到員工ID | 將手機號/郵箱/員工工號映射到員工 ID |
| 應用編輯 | 建立和更新應用 |
| 群組唯讀 | 群組讀取權限 |
| 群組編輯 | 群組編輯權限 |
| 日曆唯讀 | 日曆和日程讀取權限 |
| 日曆編輯 | 日曆和日程編輯權限 |
| 上傳媒體 | 上傳媒體檔案權限 |
| 工作台範本讀取 | 工作台範本讀取權限 |
| 工作台範本寫入 | 工作台範本寫入權限 |

遇到權限錯誤時，首先確認身份類型是否支援該操作，然後提示使用者在開發者中心開啟對應的高階權限（如無法存取請聯絡組織管理員）。

## 專案結構

```
lansenger-sdk-python/
├── src/lansenger_sdk/
│   ├── __init__.py          # 全部导出
│   ├── client.py            # LansengerClient（異步）
│   ├── sync_client.py       # LansengerSyncClient（同步）
│   ├── config.py            # LansengerConfig
│   ├── auth.py              # TokenManager — appToken 生命週期管理
│   ├── oauth.py             # OAuth2 輔助函式
│   ├── constants.py         # API 端點、媒體類型、OAuth 范围
│   ├── exceptions.py        # LansengerError 异常层级
│   ├── models.py            # 38+ dataclass 结果类型
│   ├── contacts.py          # 員工與組織資訊 API
│   ├── departments.py       # 部門 API
│   ├── account_messages.py  # 公眾號通道
│   ├── user_messages.py     # 人→人通道
│   ├── group_messages.py    # 群聊通道
│   ├── media.py             # 上傳/下載
│   ├── streaming.py         # SSE 流式訊息
│   ├── persistence.py       # CredentialStore — 憑證與令牌檔案持久化
│   ├── callbacks.py         # 回調事件 — 25 種事件類型、結構化解析、AES 解密（4.10.1.4）、SHA1 簽名驗證
│   ├── groups.py            # 群組 API（含解散 4.28.6）
│   ├── todos.py             # 統一待辦
│   ├── calendars.py         # 日曆日程（含更新 4.23.12、參會人元資料 4.23.17）
│   ├── reminders.py         # 加急提醒（4.6.14）
│   └── users.py             # 使用者資訊
├── tests/                   # 341 個測試，全部通過
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