---
name: lansenger-messaging
description: Lansenger messaging strategy — understand 4 messaging channels (bot/private/account/group), text/formatText/appCard/linkCard/appArticles capability boundaries, @mention rules, and SDK method selection
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: messaging
  pip: pip install lansenger-sdk
---

# Lansenger Messaging Strategy

Lansenger has **private chat** and **group chat** message channels. Each has different sender identity options. Choosing the wrong channel leads to incorrect sender identity or missing features.

## Two Message Categories: Private Chat & Group Chat

### Private Chat — 1:1 Conversation

Three different private chat channels, distinguished by **who is speaking**:

```
┌─────────────────────┬──────────────────────┬──────────────────────┬────────────────────────┐
│                     │  4.6.1 公号私聊       │  4.6.3 人→人私聊     │  4.6.12 机器人私聊      │
│                     │  (Public Account)     │  (User Impersonate)  │  (Bot)                 │
├─────────────────────┼──────────────────────┼──────────────────────┼────────────────────────┤
│  Endpoint           │  /v1/messages/create │  /v1/messages/chat/  │  /v1/bot/messages/     │
│                     │                      │  create              │  create                │
│  Sender identity    │  公号 (Public Acct)  │  Human (OAuth2 user) │  Bot                   │
│  appToken required  │  ✓                   │  ✓                   │  ✓                     │
│  userToken required │  Optional            │  **Required**        │  Optional              │
│  Recipients         │  userIdList/          │  receiverId          │  userIdList/           │
│                     │  departmentIdList     │  (single user 1:1)   │  departmentIdList      │
│  msgType            │  text, oacard,        │  text, formatText,   │  text, oacard,         │
│                     │  linkCard, appCard,   │  appCard, etc.       │  linkCard, appCard,    │
│                     │  verifyCard           │                      │  verifyCard            │
│  @mention           │  ✗ (no group context) │  ✗                   │  ✗                     │
│  Attachments        │  ✗                   │  ✓ (text type)       │  ✗                     │
│  Markdown           │  ✗                   │  ✓ (formatText)      │  ✗                     │
│  Special fields     │  accountId, entryId,  │  uuid, msgData       │  entryId               │
│                     │  attach, tagUnitList  │  .common             │                        │
│  SDK method         │  send_account_message│  send_user_message   │  send_text/send_mark-  │
│                     │                      │                      │  down/send_bot_message │
│  Prerequisite       │  App has 公号         │  User OAuth2 auth    │  App has bot capability│
└─────────────────────┴──────────────────────┴──────────────────────┴────────────────────────┘
```

**Each recipient gets an independent 1:1 private chat** — even if you send to 5 people in userIdList, each person sees the message in their own private chat window, not visible to others. Same for departmentIdList: each department member gets their own private chat.

### Group Chat — In-Group Conversation

Group chat supports **all developer-accessible msgType** (text, formatText, oacard, appCard, linkCard, appArticles, verifyCard).

```
┌─────────────────────┬──────────────────────────────────────────────┐
│                     │  4.6.2 群聊消息                               │
├─────────────────────┼──────────────────────────────────────────────┤
│  Endpoint           │  /v1/messages/group/create                   │
│  Sender identity    │  userToken → human; no userToken → bot       │
│  appToken required  │  ✓                                           │
│  userToken required │  Optional (determines sender identity)       │
│  Recipients         │  groupId (group openId)                      │
│  msgType            │  ALL developer-accessible types              │
│  @mention (reminder)│  ✓ — ONLY text & formatText                  │
│  Attachments        │  ✓ (text type)                               │
│  Special fields     │  senderId, uuid, outlines, entryId           │
│  SDK method         │  send_text(is_group=True)                    │
│                     │  send_markdown(is_group=True)                 │
│                     │  send_file(is_group=True)                     │
│                     │  send_link_card(is_group=True)                │
│                     │  send_app_articles(is_group=True)             │
│                     │  send_app_card(is_group=True)                 │
│                     │  send_oacard(is_group=True)                    │
│                     │  send_bot_message(is_group=True)               │
│                     │  send_group_message(reminder_all=...)         │
│  Prerequisite       │  Bot/user must be in the group                │
└─────────────────────┴──────────────────────────────────────────────┘
```

**Key difference**: everyone in the group sees the message in the same group chat window.

**userToken determines group chat sender identity**:
- With userToken → message appears from a **human** (who must also be in the group)
- No userToken + senderId → message appears from specified person
- No userToken, no senderId → message appears from the **bot** (requires bot capability)

**@mention (reminder) rules**:
- **Only text and formatText** support @mention (reminder_all, reminder_user_ids)
- All other msgTypes (appCard, linkCard, appArticles, etc.) **do NOT** support @mention — reminder parameters are silently ignored for these types
- If reminder fails for text/formatText, SDK automatically retries without reminder

## Message Type Capability Matrix

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  msgType     │  Markdown    │  @mention    │  Attachments │  Group chat  │  Channel     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│  text        │  ✗           │  ✓(group)    │  ✓           │  ✓           │  All         │
│  formatText  │  ✓           │  ✓(group)    │  ✗           │  ✓           │  4.6.3/4.6.2 │
│  oacard      │  ✗           │  ✗           │  ✗           │  ✓           │  All         │
│  appArticles │  ✗           │  ✗           │  ✗           │  ✓           │  All         │
│  appCard     │  ✗ (div)     │  ✗           │  ✗           │  ✓           │  All         │
│  linkCard    │  ✗           │  ✗           │  ✗           │  ✓           │  All         │
│  verifyCard  │  ✗           │  ✗           │  ✗           │  ✓           │  All         │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## Card Type Capability Matrix

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  Card Type   │  Multi-lang  │  Dynamic     │  headStatus  │  Pad Link   │
│              │  (5 langs)   │  Update      │  Info        │  Fields     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│  appCard     │  ✗           │  ✓           │  ✓           │  padCardLink│
│  i18nAppCard │  ✓           │  ✗           │  ✗           │  ✗          │
│  linkCard    │  ✗           │  ✗           │  ✗           │  padLink    │
│  oacard      │  ✗           │  ✗           │  ✗           │  padLink    │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## oaCard (OA审批卡片) — Full Reference

oaCard is a special card type for OA approval workflows. Key differences from other cards:

- Uses `staffID` (uppercase) in API JSON (mapped from `staff_id` param)
- Has `padLink` for Pad-specific click-through
- Has `cardAction` for interactive card actions (prs5.3.0)

```python
# Private chat oaCard
result = await client.send_oacard(
    chat_id="staff123",
    title="Leave Approval",
    head="OA审批",
    sub_title="Annual Leave Request",
    staff_id="staff456",
    fields=[{"key": "Type", "value": "Annual Leave"}, {"key": "Days", "value": "3"}],
    link="https://oa.example.com/approve/123",
    pc_link="https://oa.example.com/approve/123?client=pc",
    pad_link="https://oa.example.com/approve/123?client=pad",
    card_action={"action": "approve", "params": {"id": "123"}},
)

# Group chat oaCard
result = await client.send_oacard(
    chat_id="group123", title="Leave Approval",
    head="OA审批", is_group=True,
)

# Using OaCardParams dataclass
from lansenger_sdk import OaCardParams
params = OaCardParams(
    chat_id="staff123", title="Leave Approval",
    head="OA审批", fields=[{"key": "Type", "value": "Annual Leave"}],
    link="https://oa.example.com/approve/123",
)
result = await client.send_oacard_with_params(params)
```

**oaCard fields**:

| SDK param | API JSON field | Description |
|-----------|---------------|-------------|
| head | head | Card header text |
| title | title | Card title (required) |
| sub_title | subTitle | Card subtitle |
| staff_id | staffID | Staff ID for sender avatar |
| fields | fields | Key-value pairs (max 10) |
| link | link | Card click-through link |
| pc_link | pcLink | PC client click-through link |
| pad_link | padLink | Pad client click-through link |
| card_action | cardAction | Card action dict (prs5.3.0) |

## Pad-Specific Link Fields

Each card type has a different Pad link field name:

| Card Type | SDK param | API JSON field | Version |
|-----------|-----------|---------------|---------|
| appCard | pad_card_link | padCardLink | prs4.6.0 |
| linkCard | pad_link | padLink | prs4.6.0 |
| oaCard | pad_link | padLink | prs4.6.0 |
| appArticles | pad_url | padUrl | prs4.6.0 |

```python
# appCard with Pad link
result = await client.send_app_card(
    chat_id="staff123", body_title="Approval",
    card_link="https://app.com/card", pad_card_link="https://app.com/card?pad=1",
)

# linkCard with Pad link
result = await client.send_link_card(
    chat_id="staff123", title="Article", link="https://article.com",
    pc_link="https://article.com?pc=1", pad_link="https://article.com?pad=1",
)

# appArticles with Pad link per article
result = await client.send_app_articles(
    chat_id="staff123", articles=[
        {"title": "News", "link": "https://news.com", "padUrl": "https://news.com?pad=1"},
    ],
)
```

## Other SDK Methods

### send_image_url — Send image from URL

Downloads an image from a URL and sends it as a media message:

```python
result = await client.send_image_url(
    chat_id="staff123", image_url="https://example.com/photo.jpg",
    caption="Team photo",
)

# Group chat
result = await client.send_image_url(
    chat_id="group123", image_url="https://example.com/photo.jpg",
    is_group=True,
)
```

- **Required**: chat_id, image_url
- Optional: caption, is_group, user_token, sender_id

### update_dynamic_card — Update a live appCard

Updates a previously sent dynamic appCard in-place (only works on appCards sent with `is_dynamic=True`):

```python
result = await client.update_dynamic_card(
    msg_id="previous_msg_id",
    head_status_info={"text": "Approved ✓", "color": "green"},
    links=[{"name": "View Details", "link": "https://app.com/details"}],
    is_last_update=True,
)

# Using DynamicCardUpdateParams
from lansenger_sdk import DynamicCardUpdateParams
params = DynamicCardUpdateParams(msg_id="msg123", is_last_update=True)
result = await client.update_dynamic_card_with_params(params)
```

- **Required**: msg_id
- Optional: head_status_info, links, is_last_update

### revoke_message — Retract a sent message

```python
result = await client.revoke_message(
    message_ids=["msg123", "msg456"],
    chat_type="private",  # "private" or "group"
    sender_id="staff1",   # optional
)
```

- **Required**: message_ids (list), chat_type

### Media upload/download

```python
# Upload a file and get mediaId
result = await client.upload_media(file_path="/path/to/file.pdf", media_type=3)
# result.message_id contains the mediaId

# Download media by mediaId to bytes
result = await client.download_media(media_id="media123")

# Download media and save to local file
result = await client.download_media_to_file(
    media_id="media123", save_path="/path/to/save.pdf",
)
```

### Health check & token management

```python
# Verify credentials work
ok = await client.health_check()  # returns True/False

# Get current appToken (auto-managed)
token = await client.get_token()

# Force refresh appToken
await client.invalidate_token()
```

## SDK Method Decision Tree

### Private Chat

#### Bot private chat (4.6.12) — most common

```python
from lansenger_sdk import LansengerClient

client = LansengerClient.from_env()

# Bot → human private chat
result = await client.send_text(chat_id="staff123", content="Hello")

# Bot → human Markdown private chat
result = await client.send_markdown(chat_id="staff123", content="**Bold**")

# Bot → human with attachment
result = await client.send_text(chat_id="staff123", content="Report", file_path="/path/to/file.pdf")

# Bot → multiple people (each gets independent private chat)
result = await client.send_bot_message(
    msg_type="text", msg_data={"text": {"content": "Notice"}},
    chat_ids=["staff1", "staff2"], department_ids=["dept1"],
    entry_id="entry_openId",              # optional
)

# Bot → human card private chat
result = await client.send_link_card(chat_id="staff123", title="Article", link="https://...")
result = await client.send_app_card(chat_id="staff123", body_title="Approval", is_dynamic=True)
result = await client.send_oacard(chat_id="staff123", title="Leave Approval", head="OA审批", staff_id="staff456", fields=[{"key": "Type", "value": "Annual Leave"}])
```

#### 公号 private chat (4.6.1) — public account → human

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"],
    department_ids=["dept1"],
    account_id="524288-xxxx",       # 公号 ID, or use entryId
    attach={"name": "report.pdf", "size": 1024, "mediaId": "m123"},  # optional attachment
    entry_id="entry_openId",        # optional 公号 entryId
)
# Each recipient sees this in their own private chat, sender = 公号
```

#### 人→人 private chat (4.6.3) — user identity private chat

```python
# userToken is REQUIRED (obtained via OAuth2)
result = await client.send_user_message(
    receiver_id="staff456",
    msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="userToken_from_oauth2",
    uuid="unique-msg-id",                # optional dedup key
    common={"attachmentList": [...]},     # optional msgData.common
)
# Sender = human, looks like the person sent it themselves
```

### Group Chat

#### Bot in group (default — no userToken)

```python
# Bot → group text
result = await client.send_text(chat_id="group123", content="Notice", is_group=True)

# Bot → group Markdown
result = await client.send_markdown(chat_id="group123", content="**Bold**", is_group=True)

# Bot → group card
result = await client.send_app_card(chat_id="group123", body_title="Approval", is_group=True)

# Bot → group link card
result = await client.send_link_card(chat_id="group123", title="Article", link="https://...", is_group=True)

# Bot → group OA card
result = await client.send_oacard(chat_id="group123", title="Leave Approval", head="OA审批", is_group=True)

# Bot → group file
result = await client.send_file(chat_id="group123", file_path="/path/to/file.pdf", is_group=True)
```

#### Human in group (with userToken)

```python
# Human → group (looks like person sent in group)
result = await client.send_text(
    chat_id="group123", content="I'll handle it",
    is_group=True, user_token="userToken_from_oauth2",
)

# Human → group card
result = await client.send_app_card(
    chat_id="group123", body_title="My Approval",
    is_group=True, user_token="userToken_from_oauth2", sender_id="staff456",
)

# Human → group via send_group_message
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="userToken_from_oauth2",
)
```

#### @mention in group chat — ONLY text & formatText

```python
# @all members (text only)
result = await client.send_text(
    chat_id="group123", content="Important notice!",
    is_group=True, reminder_all=True,
)

# @specific people (text only)
result = await client.send_text(
    chat_id="group123", content="@张三 please check",
    is_group=True, reminder_user_ids=["staff456"],
)

# @all with Markdown (formatText only)
result = await client.send_markdown(
    chat_id="group123", content="**紧急通知**",
    is_group=True, reminder_all=True,
)

# @mention via send_group_message
result = await client.send_group_message(
    group_id="group123", msg_type="text",
    msg_data={"text": {"content": "Important"}},
    reminder_all=True, reminder_user_ids=["staff456"],
)

# ⚠️ appCard/linkCard/appArticles/oaCard do NOT support @mention
# reminder parameters are silently ignored for non-text/formatText types
result = await client.send_app_card(
    chat_id="group123", body_title="Approval",
    is_group=True, reminder_all=True,  # reminder_all is SILENTLY IGNORED here
)
```

#### Bot message to multiple groups

```python
# send_bot_message with is_group=True sends to each group ID
result = await client.send_bot_message(
    msg_type="text", msg_data={"text": {"content": "Notice"}},
    chat_ids=["group1", "group2"],
    is_group=True,
)
```

### Reading Chat Messages (4.24 MCP)

SDK can also **read** conversation data, not just send:

```python
# Query user's chat list (private + group)
result = await client.fetch_chat_list(chat_type=0, user_token="ut1")

# Get private chat messages with a specific person
result = await client.fetch_chat_messages(
    staff_id="staff123", user_token="ut1", page_size=50,
)

# Get group chat messages
result = await client.fetch_chat_messages(
    group_id="group123", user_token="ut1", page_size=50,
)

# Deep pagination — use last_version from previous result
result = await client.fetch_chat_messages(
    group_id="group123", base_version="v100", page_size=50,
)
```

See `lansenger-chats` skill for detailed chat reading API reference.

## Common Mistakes

| Mistake | Correct approach |
|---------|-----------------|
| @mention in private chat | Only group chat (4.6.2) supports @mention — no group context in private chat |
| Bot private chat with departmentIdList treated as group | Each department member gets their own private chat, not a group message |
| send_user_message without userToken | 4.6.3 requires userToken |
| send_text with Markdown | Use send_markdown for Markdown content |
| send_markdown with attachment | Send separately: send_markdown first, then send_file |
| i18nAppCard for approval workflow | Use appCard + isDynamic + headStatusInfo |

## Tips

- Group chat supports **all** developer-accessible msgType (see Group Chat table above)
- @mention (reminder) only works on text and formatText in group chat (see @mention rules above)
- If reminder fails, SDK auto-retries without reminder for text/formatText
- Using send_user_message requires completing the OAuth2 flow (see lansenger-oauth skill)
- To read chat history, use fetch_chat_list and fetch_chat_messages (see lansenger-chats skill)