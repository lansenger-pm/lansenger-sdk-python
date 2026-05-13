# lansenger-sdk

Framework-independent Python SDK for the Lansenger (蓝信) platform — supports Lansenger apps, organization bots, and personal bots.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests: 296](https://img.shields.io/badge/Tests-296-green)](https://github.com/lansenger-pm/lansenger-skills-official)

> 💠 Zero framework dependencies — only `httpx`. Works with any async or sync Python codebase.

## Supported Bot Types

| Bot Type | Auth | WebSocket Inbound | All APIs |
|----------|------|-------------------|----------|
| **Lansenger App** | appToken + userToken | ✗ (uses webhook) | ✓ |
| **Organization Bot** | appToken + userToken | ✗ (uses webhook) | ✓ |
| **Personal Bot** | appToken | ✓ (WebSocket) | ✓ (limited for non-bot APIs) |

All three bot types use the same auth mechanism: `appToken` is required for every API call; `userToken` is only needed for specific user-level operations (user info, staff search, calendar, etc.).

## Features

- **Async & Sync clients** — `LansengerClient` (async) + `LansengerSyncClient` (blocking)
- **Credential & token persistence** — `CredentialStore` saves app_id, app_secret, URLs, appToken, userToken to file (survives restarts)
- **OAuth2 user authentication** — authorize URL, code exchange, token refresh
- **Organization & departments** — org info, department detail/children/staff
- **Staff & contacts** — basic/detailed info, ID mapping, department ancestors, search
- **Messaging** — 3 private chat channels (bot, official account, user impersonate) + group chat, all message types, @mention, human/bot sender identity
- **Rich cards** — appCard (with dynamic status updates), oacard, linkCard, verifyCard, appArticles
- **Streaming messages** — SSE-based real-time delivery for AI agents
- **Media upload/download** — files, images, videos with auto type detection
- **Message management** — revoke, dynamic card update
- **Groups** — create, info, members, list, membership check, update settings & members
- **Calendar & schedule** — primary calendar, schedule CRUD, attendee management
- **Unified todo** — create, update, delete, query, executor management, status counts
- **Callback events** — 25 event types, structured data parsing, signature verification

## Quick Install

```bash
pip install lansenger-sdk
```

For development:

```bash
pip install -e ".[dev]"
```

## 1. Authentication

### appToken — Required for all API calls

Every SDK method requires `appToken`. The client automatically obtains and refreshes it using your `app_id` + `app_secret`. You never need to manage appToken manually — the `TokenManager` handles the lifecycle:

1. **First call** → `GET /v1/apptoken/create` with app_id + app_secret → returns `appToken` (valid 2 hours)
2. **Subsequent calls** → reuse cached appToken until expiry
3. **Token expired** → automatically refresh via the same endpoint

```python
# appToken is managed automatically — just configure app_id + app_secret
client = LansengerClient(app_id="your-appid", app_secret="your-secret")

# You can also get/invalidate token manually
token = await client.get_token()
client.invalidate_token()  # force refresh on next call
```

### userToken — Only needed for specific endpoints

`userToken` represents a specific Lansenger user's authorization (obtained via OAuth2). It's only required for:
- User-level information (fetch_user_info, fetch_staff_detail, search_staff)
- Calendar & schedule operations (fetch_primary_calendar, create_schedule, etc.)
- Group operations as a human sender

### Getting Credentials

| Bot Type | How to get app_id + app_secret |
|----------|--------------------------------|
| **Personal Bot** | Lansenger desktop → Contacts → Smart Bots → Personal Bots → click ℹ️ icon (mobile client does NOT show credentials) |
| **Lansenger App** | Create at [Lansenger Developer Center](https://dev.lanxin.cn) — may require organization admin approval |
| **Organization Bot** | Create at [Lansenger Developer Center](https://dev.lanxin.cn) — may require organization admin approval |

### OAuth2 user-level auth

```python
# Build authorize URL — redirect user to Lansenger passport
url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")

# After user authorizes, exchange code for userToken + refreshToken
token_result = await client.exchange_code(code="auth_code_from_callback")

# Refresh expired userToken
new_token = await client.refresh_user_token(refresh_token=token_result.refresh_token)

# Fetch user profile
user_info = await client.fetch_user_info(user_token=token_result.user_token)
```

## 2. Organization & Departments

```python
# Organization info
org = await client.fetch_org_info(org_id="orgId")

# Department hierarchy
detail = await client.fetch_department_detail(department_id="deptId")
children = await client.fetch_department_children(department_id="deptId")
staffs = await client.fetch_department_staffs(department_id="deptId")
```

## 3. Staff & Contacts

```python
# Basic staff info
staff = await client.fetch_staff_basic_info(staff_id="staffOpenId")

# Detailed profile (userToken recommended)
detail = await client.fetch_staff_detail(staff_id="staffOpenId", user_token="ut")

# Map phone → staffId
mapping = await client.fetch_staff_id_mapping(
    org_id="orgId", id_type="mobile", id_value="13800138000"
)

# Department ancestors for a staff member
ancestors = await client.fetch_department_ancestors(staff_id="staffOpenId")

# Search staff (requires userToken or userId)
results = await client.search_staff(keyword="Zhang San", user_token="ut")

# Org extra field IDs
fields = await client.fetch_org_extra_field_ids(org_id="orgId")
```

## 4. Messaging & Media

#### Bot private chat — most common

```python
result = await client.send_text(chat_id="staff123", content="Hello!")
result = await client.send_markdown(chat_id="staff123", content="**Bold**")
result = await client.send_file(chat_id="staff123", file_path="/path/to/report.pdf")
```

#### Public account channel

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"], account_id="524288-xxxx",
)
```

#### User impersonate channel (requires userToken)

```python
result = await client.send_user_message(
    receiver_id="staff456", msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="ut",  # required
)
```

#### Group chat

```python
# Bot → group
result = await client.send_text(chat_id="group123", content="Notice", is_group=True)

# Human → group (with userToken)
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="ut",
)

# Group chat supports ALL message types (text, formatText, oacard, appCard, linkCard, etc.)
result = await client.send_group_message(
    group_id="group123", msg_type="appCard",
    msg_data={"appCard": {"bodyTitle": "Approval", "isDynamic": True}},
    user_token="ut",
)

# @mention in group
result = await client.send_text(
    chat_id="group123", content="Important!", is_group=True, reminder_all=True,
)
```

#### Rich cards

```python
result = await client.send_app_card(chat_id="staff123", body_title="Approval", is_dynamic=True)
result = await client.send_link_card(chat_id="staff123", title="Article", link="https://...")
result = await client.send_app_articles(chat_id="staff123", articles=[...])

# Update dynamic card status
result = await client.update_dynamic_card(msg_id="msg123", is_last_update=True)
```

#### Streaming messages (for AI agents)

```python
result = await client.create_stream_message(receiver_id="staff1", receiver_type="staff", stream_id="s1")
result = await client.fetch_stream_message(msg_id="msg123")
```

#### Media

```python
# Upload
upload = await client.upload_media(file_path="/path/to/file.pdf")

# Download
download = await client.download_media(media_id="media123")

# Revoke messages
result = await client.revoke_message(message_ids=["msg1", "msg2"])
```

## 5. Groups

```python
# Create group
group = await client.create_group(name="Project Chat", org_id="orgId", staff_id_list=["s1","s2","s3"])

# Fetch info & members
info = await client.fetch_group_info(group_id="groupOpenId")
members = await client.fetch_group_members(group_id="groupOpenId")
groups = await client.fetch_group_list()

# Check membership
result = await client.check_is_in_group(group_id="groupOpenId", staff_id="staff1")

# Update settings
await client.update_group_info(group_id="groupId", name="New Name", manage_mode=1)

# Add/remove members
await client.update_group_members(
    group_id="groupId", add_user_list=["staff4"], del_user_list=["staff3"],
)
```

## 6. Calendar & Schedule

```python
# Get primary calendar (requires userToken or userId)
cal = await client.fetch_primary_calendar(user_token="ut")

# Create schedule
schedule = await client.create_schedule(
    calendar_id=cal.calendar_id, summary="Team Meeting",
    start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
    end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
    user_token="ut",
)

# Fetch/delete schedule
info = await client.fetch_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.delete_schedule(calendar_id="cal1", schedule_id="sch1", user_token="ut")

# Schedule list in time range (max 42 days)
schedules = await client.fetch_schedule_list(
    calendar_id="cal1", start_time=1705276800000, end_time=1707940800000, user_token="ut",
)

# Attendee management
attendees = await client.fetch_schedule_attendees(calendar_id="cal1", schedule_id="sch1", user_token="ut")
await client.add_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
await client.delete_schedule_attendees(calendar_id="cal1", schedule_id="sch1", attendees=["staff2"], user_token="ut")
```

## 7. Unified Todo

```python
from lansenger_sdk import TODO_TYPE_APPROVAL, TODO_TODO_STATUS_DONE

# Create todo task
todo = await client.create_todo_task(
    title="Approval Request", link="https://app.com/a/1", pc_link="https://pc.app.com/a/1",
    executor_ids=["staff1"], org_id="org1", type=TODO_TYPE_APPROVAL,
)

# Update status (11=pending-read, 12=read, 21=pending-do, 22=done)
await client.update_todo_task_status(todotask_id="taskId", status=TODO_TODO_STATUS_DONE, org_id="org1")

# Update content
await client.update_todo_task(todotask_id="taskId", title="Updated", link="l", pc_link="p", org_id="org1")

# Delete (sender only)
await client.delete_todo_task(todotask_id="taskId", org_id="org1")

# Query
list_result = await client.fetch_todo_task_list(org_id="org1")
task = await client.fetch_todo_task_by_id(todotask_id="taskId", org_id="org1")
task = await client.fetch_todo_task_by_source_id(source_id="src1", org_id="org1")
counts = await client.fetch_todo_task_status_counts(staff_id="staff1", org_id="org1")

# Executor management
await client.add_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
await client.delete_executors(executor_ids=["staff2"], org_id="org1", todotask_id="taskId")
executors = await client.fetch_executor_list(todotask_id="taskId", org_id="org1")
await client.update_executor_status(
    executor_status_list=[{"executorId": "staff1", "todotaskId": "taskId", "status": "22"}],
    org_id="org1",
)
```

## 8. Callback Events

```python
from lansenger_sdk import parse_callback_payload, verify_callback_signature

# Parse webhook payload
events = parse_callback_payload(encrypted_data, encoding_key="your_key")

# Verify signature
is_valid = verify_callback_signature(timestamp, nonce, signature, encoding_key)

# Available event types
types = client.get_callback_event_types()  # 26 event types across 14 categories
```

## Message Type Capability Matrix

| msgType | Markdown | @mention | Attachments | Private Channels | Group Chat | Notes |
|---------|----------|----------|-------------|------------------|------------|-------|
| `text` | ✗ | ✓ (group) | ✓ | Bot, Official Account, User Impersonate | ✓ | Up to 6000 bytes |
| `formatText` | ✓ | ✗ | ✗ | User Impersonate only | ✓ | Markdown via formatType=1 |
| `oacard` | ✗ | ✗ | ✗ | Bot, Official Account, User Impersonate | ✓ | Simple card with fields |
| `appCard` | ✓ (div tags) | ✗ | ✗ | Bot, Official Account, User Impersonate | ✓ | Rich card, dynamic updates |
| `linkCard` | ✗ | ✗ | ✗ | Bot, Official Account | ✓ | Link preview card |
| `appArticles` | ✗ | ✗ | ✗ | Bot private only | ✓ | Article list (1+ articles) |
| `verifyCard` | ✗ | ✗ | ✗ | Bot, Official Account | ✓ | Verification card with buttons |
| `i18nAppCard` | ✓ (div tags) | ✗ | ✗ | Bot, Official Account, User Impersonate | ✓ | Multilingual appCard (zhHans/zhHant/zhHantHK/en/fr) |
| `i18nSystemAction` | ✗ | ✗ | ✗ | Platform internal | ✓ | Multilingual systemAction |
| `i18nSystem` | ✗ | ✗ | ✗ | Platform internal | ✓ | Multilingual system message |

**Group chat** supports all message types. Only group chat supports @mention.

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `LANSENGER_APP_ID` | ✓ | App/Bot ID | — |
| `LANSENGER_APP_SECRET` | ✓ | App/Bot Secret | — |
| `LANSENGER_API_GATEWAY_URL` | ✗ | API Gateway URL | `https://open.e.lanxin.cn/open/apigw` |
| `LANSENGER_PASSPORT_URL` | ✗ | Passport URL (for OAuth2) | — |

### Credential & Token Persistence

By default, credentials and tokens stay in memory only (lost on process exit). Enable file persistence with `store_path`:

```python
from lansenger_sdk import LansengerClient, CredentialStore

# Auto-persist to ~/.lansenger/sdk_state.json (0600 permissions)
client = LansengerClient(app_id="...", app_secret="...", store_path="~/.lansenger/sdk_state.json")

# Or from env with persistence
client = LansengerClient.from_env(store_path="~/.lansenger/sdk_state.json")

# Manual store operations
store = CredentialStore(path="~/.lansenger/sdk_state.json")
store.save_credentials("app_id", "app_secret", api_gateway_url="...", passport_url="...")
store.save_user_token("user_token", refresh_token="refresh_token")
token = store.load_app_token()  # None if expired
```

When persistence is enabled:
- **appToken** is saved after each API fetch and restored on restart (skips redundant API calls)
- **userToken + refreshToken** are saved after OAuth2 exchange
- **Credentials + URLs** are saved together for full config recovery

### Sync Client

All methods available on `LansengerSyncClient` with identical signatures (blocking):

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.send_text(chat_id="staff123", content="Hello!")
org = client.fetch_org_info(org_id="orgId")
```

## Project Structure

```
lansenger-skills-official/
├── src/lansenger_sdk/
│   ├── __init__.py          # All exports
│   ├── client.py            # LansengerClient (async)
│   ├── sync_client.py       # LansengerSyncClient (sync)
│   ├── config.py            # LansengerConfig
│   ├── auth.py              # TokenManager — appToken lifecycle
│   ├── oauth.py             # OAuth2 helpers
│   ├── constants.py         # API endpoints, media types, OAuth scopes
│   ├── exceptions.py        # LansengerError hierarchy
│   ├── models.py            # 35+ dataclass result types
│   ├── contacts.py          # Staff & org info APIs
│   ├── departments.py       # Department APIs
│   ├── account_messages.py  # Public account channel
│   ├── user_messages.py     # User impersonate channel
│   ├── group_messages.py    # Group chat channel
│   ├── media.py             # Upload/download
│   ├── streaming.py         # SSE streaming
│   ├── persistence.py       # CredentialStore — file-based token & credential persistence
│   ├── callbacks.py         # Callback events
│   ├── groups.py            # Group APIs
│   ├── todos.py             # Unified Todo
│   ├── calendars.py         # Calendar & Schedule
│   └── users.py             # User info
├── tests/                   # 296 tests, all passing
├── skills/                  # 9 skills (Agent Skills standard: <name>/SKILL.md) + manifest
├── pyproject.toml
└── README*.md               # 5-language READMEs
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).