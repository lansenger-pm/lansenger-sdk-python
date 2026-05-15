---
name: lansenger-chats
description: Lansenger chat reading APIs — fetch personal chat list (private + group conversations) and pull messages from a specific conversation
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: messaging
  pip: pip install lansenger-sdk
---

# Lansenger Chat Reading APIs

SDK can **read** conversation data via two APIs in the 4.24 MCP category. These are POST endpoints that require appToken; userToken is optional but recommended for human-scoped access.

## Two APIs

### 1. fetch_chat_list — 查询个人会话列表

`POST /v1/chats/fetch?app_token=TOKEN&user_token=TOKEN`

Query a user's personal chat list — both private chats and group chats.

```python
from lansenger_sdk import LansengerClient

client = LansengerClient.from_env()

# Get all conversations (private + group)
result = await client.fetch_chat_list()
# result.staff_infos  — list of ChatStaffInfo (private chat partners)
# result.group_infos  — list of ChatGroupInfo (group conversations)

# Filter by type: 0=all, 1=private only, 2=group only
result = await client.fetch_chat_list(chat_type=1)  # private chats only
result = await client.fetch_chat_list(chat_type=2)  # group chats only

# With userToken — gets conversations for a specific human user
result = await client.fetch_chat_list(user_token="ut1", chat_type=0)
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chat_type | int | No | 0=all, 1=private, 2=group (default 0) |
| keyword | string | No | Search by name (only works when chat_type is 1 or 2) |
| start_time | int64 | No | Filter start time (microseconds) |
| end_time | int64 | No | Filter end time (microseconds) |
| user_token | string | No | Human identity token |

**Returns**:

| Field | Type | Description |
|-------|------|-------------|
| staff_infos | ChatStaffInfo[] | Private chat partners |
| group_infos | ChatGroupInfo[] | Group conversations |

**ChatStaffInfo**:

| Field | Type | Description |
|-------|------|-------------|
| staff_id | string | Partner's openStaffId |
| staff_name | string | Partner's name |
| sector_names | string[] | Partner's department names |

**ChatGroupInfo**:

| Field | Type | Description |
|-------|------|-------------|
| group_id | string | Group's openGroupId |
| group_name | string | Group name |

### 2. fetch_chat_messages — 拉取特定会话的消息

`POST /v1/messages/fetch?app_token=TOKEN&user_token=TOKEN&page_size=100&base_version=0`

Fetch messages from a specific private chat (by staffId) or group chat (by groupId). **staff_id and group_id are mutually exclusive — pick one.**

```python
# Fetch private chat messages with a person
result = await client.fetch_chat_messages(
    staff_id="staff123",
    page_size=50,
)
# result.messages  — list of ChatMessageInfo
# result.has_more  — True if more pages exist
# result.last_version  — cursor for deep pagination

# Fetch group chat messages
result = await client.fetch_chat_messages(
    group_id="group123",
    page_size=50,
)

# Deep pagination — use last_version from previous call
result2 = await client.fetch_chat_messages(
    group_id="group123",
    base_version=result.last_version,
    page_size=50,
)

# Filter by time range (microseconds)
result = await client.fetch_chat_messages(
    group_id="group123",
    start_time=1700000000000000,  # start timestamp in μs
    end_time=1700100000000000,    # end timestamp in μs
)

# Filter by sender
result = await client.fetch_chat_messages(
    group_id="group123",
    sender_id="staff456",
)
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| staff_id | string | No* | Private chat partner's staffId (pick staff_id or group_id) |
| group_id | string | No* | Group openId (pick staff_id or group_id) |
| page_size | int | No | Per-page count (max 100, default 100) |
| base_version | string | No | Deep pagination cursor. First call: "0" |
| start_time | int64 | No | Filter start time (microseconds) |
| end_time | int64 | No | Filter end time (microseconds) |
| sender_id | string | No | Filter by sender staffId |
| user_token | string | No | Human identity token |

*At least one of staff_id or group_id is required.

**Returns**:

| Field | Type | Description |
|-------|------|-------------|
| has_more | bool | True if more pages exist |
| total | int64 | Total message count |
| last_version | string | Cursor for next page (deep pagination) |
| name | string | Conversation name |
| chat_type | string | Conversation type (private/group) |
| messages | ChatMessageInfo[] | Message list |

**ChatMessageInfo**:

| Field | Type | Description |
|-------|------|-------------|
| send_time | string | Send timestamp |
| sender | string | Sender name |
| message_type | string | Message type (text, staff_card, group_card, location, link, sticker, box, other) |
| content | dict | Type-specific content |

**Content types**:

| message_type | Content fields |
|--------------|----------------|
| text | text, attachments, mediaIds, fileUrls |
| staff_card | name, dept |
| group_card | groupName |
| location | placeName, address, gcs{latitude, longitude} |
| link | url |
| sticker | name |
| box | title |
| other | unknowContent |

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()

result = client.fetch_chat_list(chat_type=0)
result = client.fetch_chat_messages(group_id="group123", page_size=50)
```

## Error Codes

| Code | Description |
|------|-------------|
| 10000 | API service unavailable |
| 63000 | Parameter error (chats/fetch) |
| 63001 | Failed to fetch chat list |
| 63002 | Parameter error (messages/fetch) |

## Tips

- First call uses base_version="0", subsequent calls use last_version from previous result
- page_size max is 100; for large histories, paginate with base_version
- userToken recommended — without it, results may be bot-scoped
- Time filters use microseconds (not milliseconds)
- keyword only works when chat_type is 1 or 2 (not 0)