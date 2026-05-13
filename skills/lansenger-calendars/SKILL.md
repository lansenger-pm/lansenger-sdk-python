---
name: lansenger-calendars
description: Lansenger calendar/schedule APIs — fetch primary calendar, create/query/delete schedules, manage attendees
license: MIT
compatibility: opencode
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: calendar
  pip: pip install lansenger-sdk
---

# Lansenger Calendar & Schedule (4.23)

Lansenger SDK provides calendar & schedule APIs for managing calendars and events. These are org/app bot APIs — they require `appToken` and at least one of `userToken` or `userId`.

Note: Calendar CRUD endpoints (4.23.1-8) are marked "暂不开放" (not yet open). Only schedule operations (4.23.9-18) are available.

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `fetch_primary_calendar` | GET /v1/calendars/primary | Get primary calendar |
| `create_schedule` | POST /v1/calendars/:cid/schedules/create | Create a schedule/event |
| `fetch_schedule` | GET /v1/calendars/:cid/schedules/:sid/fetch | Query a schedule |
| `delete_schedule` | POST /v1/calendars/:cid/schedules/:sid/delete | Delete a schedule |
| `fetch_schedule_list` | POST /v1/calendars/:cid/schedules/fetch | Schedule list in time range |
| `fetch_schedule_attendees` | GET /v1/calendars/:cid/schedules/:sid/members/fetch | Get attendee list |
| `add_schedule_attendees` | POST /v1/calendars/:cid/schedules/:sid/members/create | Add attendees |
| `delete_schedule_attendees` | POST /v1/calendars/:cid/schedules/:sid/members/delete | Delete attendees |

## Auth Requirements

Calendar endpoints require `app_token` AND at least one of `user_token` or `user_id`:
- With `user_token`: acts as the human user (see their calendar, create schedules as them)
- With `user_id`: acts as the specified user by openId
- Neither: uses the app robot's calendar

## SDK Method Reference

### 1. Fetch primary calendar

```python
result = await client.fetch_primary_calendar(
    user_token="userToken123",    # or user_id="staffOpenId"
)
# result.calendar_id, result.summary, result.type, result.role, result.permissions
```

- Returns: `CalendarPrimaryResult` — calendar_id, summary, description, permissions, color, type, role
- When no user_token/user_id: returns bot's own primary calendar

### 2. Create a schedule/event

```python
result = await client.create_schedule(
    calendar_id="calOpenId",
    summary="项目周会",
    start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
    end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
    description="每周项目进度同步",
    all_day="no",                     # "yes" or "no"
    repeat_type="week",              # no/day/week/month/year/work_day/custom
    attendee_permissions="can_see",   # can_modify/can_invite/can_see/none
    user_token="userToken123",
)
# result.schedule_id — created schedule ID
```

- Returns: `ScheduleCreateResult` — schedule_id
- **Required**: calendar_id, summary, start_time, end_time, attendees
- Optional: description (max 6000 chars), all_day, repeat_type, rule (RFC 5545), expire_date_type, reminder_type, attendee_permissions
- `attendees`: list of dicts with `staffId` + `attendeeFlag` (required/optional)
- `attendee_permissions`: determines what attendees can do with the schedule

### 3. Fetch a schedule

```python
result = await client.fetch_schedule(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
)
# result.schedule_id, result.summary, result.start_time, result.end_time, result.rsvp_status
```

- Returns: `ScheduleInfoResult` — schedule_id, summary, description, repeat_type, all_day, start_time, end_time, creator, rsvp_status

### 4. Delete a schedule

```python
result = await client.delete_schedule(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    reminder_type="no",               # "yes" or "no"
    operation_type="delete_all",       # delete_all / delete_current / delete_from_current
)
```

- Returns: `ScheduleCreateResult` — schedule_id
- `operation_type` options:
  - `delete_all`: delete entire series (default)
  - `delete_current`: delete only current instance (for recurring events)
  - `delete_from_current`: delete from current instance onwards (for recurring events)

### 5. Fetch schedule list (time range)

```python
result = await client.fetch_schedule_list(
    calendar_id="calOpenId",
    start_time=1705276800000,         # Unix timestamp in ms
    end_time=1707940800000,
)
# result.schedule_list — list of schedule dicts
```

- Returns: `ScheduleListResult` — schedule_list
- **Required**: calendar_id, start_time, end_time
- **Constraint**: time range (end_time - start_time) must be ≤ 42 days

### 6. Fetch schedule attendees

```python
result = await client.fetch_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    page=1,
    page_size=500,
)
# result.total, result.attendees
```

- Returns: `ScheduleAttendeesResult` — total, attendees (list)
- Default: page=1, page_size=500

### 7-8. Add/delete attendees

```python
# Add attendees
result = await client.add_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    attendees=["staffOpenId1", "staffOpenId2"],
    reminder_type="yes",
)

# Delete attendees
result = await client.delete_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    attendees=["staffOpenId2"],
    reminder_type="no",
)
```

- Both return: `ScheduleCreateResult` — schedule_id

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
cal = client.fetch_primary_calendar(user_token="userToken")
result = client.create_schedule(calendar_id=cal.calendar_id, summary="会议", ...)
```

## Common Patterns

### Create a meeting and notify attendees via message

```python
cal = await client.fetch_primary_calendar(user_token="userToken")
if cal.success:
    schedule = await client.create_schedule(
        calendar_id=cal.calendar_id,
        summary="项目周会",
        start_time={"date": "2024-01-15", "time": "10:00", "timeZone": "Asia/Shanghai"},
        end_time={"date": "2024-01-15", "time": "11:00", "timeZone": "Asia/Shanghai"},
        attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
        user_token="userToken",
    )
    if schedule.success:
        await client.send_text(chat_id="staff1", content="您有一个新的会议邀请：项目周会")
```

### Get today's schedules

```python
from datetime import datetime

today_start = int(datetime.now().replace(hour=0, minute=0).timestamp() * 1000)
today_end = int(datetime.now().replace(hour=23, minute=59).timestamp() * 1000)

result = await client.fetch_schedule_list(
    calendar_id="calOpenId", start_time=today_start, end_time=today_end,
)
for sch in result.schedule_list:
    print(sch.get("summary"), sch.get("startTime"))
```