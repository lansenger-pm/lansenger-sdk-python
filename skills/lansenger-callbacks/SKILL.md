---
name: lansenger-callbacks
description: Lansenger callback event parsing — 25 event types across 14 categories, structured dataclass parsing, payload parsing, signature verification
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: callbacks
  pip: pip install lansenger-sdk
---

# Lansenger Callback Events (Webhook)

Lansenger SDK provides callback event parsing for processing webhook payloads sent by the Lansenger platform to your app's HTTP callback endpoint. This is purely data-side — no HTTP calls involved.

## Event Type Categories

Lansenger sends 25 event types grouped into 14 categories:

| Category | Event Types |
|----------|-------------|
| **bot** | `bot_private_message`, `bot_group_message` |
| **public_account** | `account_message`, `account_subscribe`, `account_unsubscribe` |
| **staff** | `staff_info`, `staff_modify`, `staff_create`, `staff_delete` |
| **department** | `dept_modify`, `dept_create`, `dept_delete` |
| **group** | `group_create_approve` |
| **tag** | `tag_member` |
| **app** | `app_install_org`, `app_uninstall_org` |
| **notification** | `telephone_track` |
| **certificate** | `ua_cert_create`, `ua_cert_delete` |
| **location** | `report_location` |
| **auth** | `user_logout` |
| **data_scope** | `data_scope` |
| **workbench** | `wb_visible_config` |
| **calendar** | `schedule_modify`, `schedule_delete` |

## SDK Method Reference

### 1. Parse a callback payload

```python
from lansenger_sdk import LansengerClient, CallbackEvent

# For plain JSON payloads (most common)
events = LansengerClient.parse_callback_payload(json_string)

# For encrypted payloads (requires encoding_key — NOT YET IMPLEMENTED)
# events = LansengerClient.parse_callback_payload(
#     encrypted_data, encoding_key="...", verify_signature=True,
#     timestamp="...", nonce="...", signature="...",
# )
# NOTE: decryption placeholder raises NotImplementedError if encoding_key provided
```

- Returns: `list[CallbackEvent]`
- Each `CallbackEvent` has: event_id, event_type, category, data (structured dataclass), app_id, org_id

### 2. Verify callback signature (placeholder)

```python
is_valid = LansengerClient.verify_callback_signature(
    timestamp="...", nonce="...", signature="...", encoding_key="..."
)
# NOTE: placeholder implementation — always returns True
# Actual verification algorithm needs encryption spec from Lansenger docs section 4.10.1.4
```

### 3. Get all event type mappings

```python
event_types = LansengerClient.get_callback_event_types()
# Returns dict: {"bot_private_message": "bot", "staff_info": "staff", ...}
```

## CallbackEvent Dataclass

```python
@dataclass
class CallbackEvent:
    event_id: int        # eventId from payload
    event_type: str      # eventType string (e.g. "bot_private_message")
    category: str        # mapped category (e.g. "bot", "staff", "department")
    data: dataclass      # structured event-specific dataclass (not raw dict)
    app_id: str          # appId
    org_id: str          # orgId
```

## Common Patterns

### Handle bot messages from callback

```python
raw_body = request.body  # from your HTTP endpoint
events = LansengerClient.parse_callback_payload(raw_body)

for event in events:
    if event.category == "bot" and event.event_type == "bot_private_message":
        staff_id = event.data.staff_id
        content = event.data.content
        # Process and reply...
        await client.send_text(chat_id=staff_id, content="收到！")
```

### Filter events by category

```python
bot_events = [e for e in events if e.category == "bot"]
staff_events = [e for e in events if e.category == "staff"]
dept_events = [e for e in events if e.category == "department"]
```

### Sync client also has static methods

```python
from lansenger_sdk import LansengerSyncClient

events = LansengerSyncClient.parse_callback_payload(json_string)
is_valid = LansengerSyncClient.verify_callback_signature(ts, nonce, sig, key)
event_types = LansengerSyncClient.get_callback_event_types()
```

## Implementation Status

| Feature | Status |
|---------|--------|
| Plain JSON payload parsing | Done |
| Encrypted payload decryption | Placeholder (raises NotImplementedError) |
| Signature verification | Placeholder (always returns True) |

To use encrypted payloads currently, decrypt externally and pass the already-decrypted JSON string as `encrypted_data` without providing `encoding_key`.

## Common Mistakes

| Wrong | Right |
|-------|-------|
| Passing encrypted data without decoding | Decrypt externally first, or don't provide encoding_key |
| Expecting a single event per payload | Payloads may contain multiple events (list) or a single event (dict) — SDK handles both |
| Using callbacks to send messages | Callbacks are inbound only — use send_text/send_markdown to reply |