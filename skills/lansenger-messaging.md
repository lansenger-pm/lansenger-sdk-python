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

```
┌─────────────────────┬──────────────────────────────────────────────┐
│                     │  4.6.2 群聊消息                               │
├─────────────────────┼──────────────────────────────────────────────┤
│  Endpoint           │  /v1/messages/group/create                   │
│  Sender identity    │  userToken → human; no userToken → bot       │
│  appToken required  │  ✓                                           │
│  userToken required │  Optional (determines sender identity)       │
│  Recipients         │  groupId (group openId)                      │
│  msgType            │  text, oacard only                           │
│  @mention (reminder)│  ✓ — only group chat supports @mention       │
│  Attachments        │  ✓ (text type)                               │
│  Special fields     │  senderId, uuid, outlines, entryId           │
│  SDK method         │  send_text(is_group=True)                    │
│                     │  send_bot_message(is_group=True)             │
│                     │  send_group_message                           │
│  Prerequisite       │  Bot/user must be in the group                │
└─────────────────────┴──────────────────────────────────────────────┘
```

**Key difference**: everyone in the group sees the message in the same group chat window. Only group chat supports @mention.

**userToken determines group chat sender identity**:
- With userToken → message appears from a **human** (who must also be in the group)
- No userToken + senderId → message appears from specified person
- No userToken, no senderId → message appears from the **bot** (requires bot capability)

## Message Type Capability Matrix

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│  msgType     │  Markdown    │  @mention    │  Attachments │  Channel     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│  text        │  ✗           │  ✓(group)    │  ✓           │  All         │
│  formatText  │  ✓           │  ✗           │  ✗           │  4.6.3 only  │
│  oacard      │  ✗           │  ✗           │  ✗           │  All         │
│  appArticles │  ✗           │  ✗           │  ✗           │  4.6.12 only │
│  appCard     │  ✗ (div)     │  ✗           │  ✗           │  4.6.1/3/12  │
│  linkCard    │  ✗           │  ✗           │  ✗           │  4.6.1/12    │
│  verifyCard  │  ✗           │  ✗           │  ✗           │  4.6.1/12    │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## Card Type Capability Matrix

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Card Type   │  Multi-lang  │  Dynamic     │  headStatus  │
│              │  (5 langs)   │  Update      │  Info        │
├──────────────┼──────────────┼──────────────┼──────────────┤
│  appCard     │  ✗           │  ✓           │  ✓           │
│  i18nAppCard │  ✓           │  ✗           │  ✗           │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

## SDK Method Decision Tree

### Private Chat

#### Bot private chat (4.6.12) — most common

```python
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
)

# Bot → human card private chat
result = await client.send_link_card(chat_id="staff123", title="Article", link="https://...")
result = await client.send_app_card(chat_id="staff123", body_title="Approval", is_dynamic=True)
```

#### 公号 private chat (4.6.1) — public account → human

```python
result = await client.send_account_message(
    msg_type="text", msg_data={"text": {"content": "System notice"}},
    chat_ids=["staff1", "staff2"],  # can send to multiple users/depts
    department_ids=["dept1"],
    account_id="524288-xxxx",       # 公号 ID, or use entryId
)
# Each recipient sees this in their own private chat, sender = 公号
```

#### 人→人 private chat (4.6.3) — user identity private chat

```python
# userToken is REQUIRED (obtained via OAuth2)
result = await client.send_user_message(
    receiver_id="staff456",     # single recipient, 1:1
    msg_type="text",
    msg_data={"text": {"content": "Hello"}},
    user_token="userToken_from_oauth2",  # required
)
# Sender = human, looks like the person sent it themselves
```

### Group Chat

#### Bot in group (default)

```python
# Bot → group (no userToken)
result = await client.send_text(
    chat_id="group123", content="Notice",
    is_group=True,
)
```

#### Human in group (with userToken)

```python
# Human → group (with userToken, looks like person sent in group)
result = await client.send_group_message(
    group_id="group123",
    msg_type="text",
    msg_data={"text": {"content": "I'll handle it"}},
    user_token="userToken_from_oauth2",  # with = human sender
)
```

#### @mention in group chat (only group chat can @mention)

```python
# @all members
result = await client.send_text(
    chat_id="group123", content="Important notice!",
    is_group=True, reminder_all=True,
)

# @specific people
result = await client.send_text(
    chat_id="group123", content="@张三 please check",
    is_group=True, reminder_user_ids=["staff456"],
)
```

## Common Mistakes

| Mistake | Correct approach |
|---------|-----------------|
| Using send_bot_message for group chat | Group chat uses send_text(is_group=True) or send_group_message |
| @mention in private chat | Only group chat (4.6.2) supports @mention — no group context in private chat |
| Bot private chat with departmentIdList treated as group | Each department member gets their own private chat, not a group message |
| send_user_message without userToken | 4.6.3 requires userToken |
| Group chat with linkCard/appCard | Group chat (4.6.2) only supports text and oacard |
| send_text with Markdown | Use send_markdown for Markdown content |
| send_markdown with attachment | Send separately: send_markdown first, then send_file |
| i18nAppCard for approval workflow | Use appCard + isDynamic + headStatusInfo |

## Tips

- Group chat only supports text and oacard — richer cards only work in private chat
- Bot private chat (4.6.12) does not support formatText/attachments — use 4.6.3 人→人 private chat for those
- @mention only works in group chat — reminder field is meaningless in private chat
- Group chat userToken determines sender identity: present = human, absent = bot
- send_text with is_group=True now supports user_token parameter — can send as human in group
- Using send_user_message requires completing the OAuth2 flow (see lansenger-oauth skill)