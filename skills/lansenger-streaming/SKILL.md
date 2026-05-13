---
name: lansenger-streaming
description: Lansenger streaming message APIs for AI-agent real-time message delivery — create and fetch stream messages for progressive typing output
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: streaming
  pip: pip install lansenger-sdk
---

# Lansenger Streaming Messages (AI-Agent SSE)

Lansenger SDK provides streaming message APIs for AI-agent real-time message delivery. These enable the "typing..." progressive output experience that AI assistants need.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_stream_message` | POST /v1/sse/msg/create | Create a streaming message session |
| `fetch_stream_message` | POST /v1/sse/msg/fetch | Fetch stream message status/content |

## SDK Method Reference

### 1. Create a streaming message

```python
result = await client.create_stream_message(
    receiver_id="staffOpenId123",    # or group openId
    receiver_type="staff",           # "staff" | "group"
    stream_id="unique-stream-id",    # your unique stream identifier
)
# result.message_id — the msgId for subsequent fetch/update operations
```

- Returns: `StreamMessageResult` — message_id (msgId)
- **Required**: `receiver_id`, `receiver_type` ("staff" or "group"), `stream_id`
- `stream_id` is your app-generated unique ID for the stream session

### 2. Fetch a streaming message

```python
result = await client.fetch_stream_message(msg_id="msgIdFromCreate")
# result.message_id
```

- Returns: `StreamMessageResult` — message_id
- Used to check the status/content of a previously created stream message

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
result = client.create_stream_message(
    receiver_id="staffOpenId123",
    receiver_type="staff",
    stream_id="unique-stream-id",
)
result = client.fetch_stream_message(msg_id="msgId")
```

## AI-Agent Streaming Pattern

The typical pattern for an AI chatbot:

1. User sends a message to the bot (received via callback)
2. Bot calls `create_stream_message()` → creates a "typing..." placeholder in the user's chat
3. Bot generates AI response progressively → updates the stream content
4. Bot calls `fetch_stream_message()` to verify status
5. Final content is delivered and the "typing..." indicator resolves

```python
# Step 1: Create stream placeholder
stream = await client.create_stream_message(
    receiver_id=callback_staff_id,
    receiver_type="staff",
    stream_id=f"ai-reply-{uuid.uuid4().hex}",
)

# Step 2: After AI generates content, send the final message
await client.send_text(chat_id=callback_staff_id, content="AI generated response...")
```

## Common Mistakes

| Wrong | Right |
|-------|-------|
| Using "user" as receiver_type | Use "staff" or "group" only |
| Not generating unique stream_id | Each stream needs a unique stream_id |
| Confusing stream message with regular message | Stream is for progressive/typing output; send_text for final content |