---
name: lansenger-calendars
description: Lansenger calendar/schedule APIs — fetch primary calendar, create/query/delete schedules, manage attendees
license: MIT
metadata:
  sdk: lansenger-sdk
  platform: lansenger
  category: calendar
  pip: pip install lansenger-sdk
---

# Lansenger Calendar & Schedule (4.23)

Lansenger SDK provides calendar & schedule APIs for managing calendars and events. These are org/app bot APIs — they require `appToken` and at least one of `user_token` or `user_id`.

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
    user_token="userToken123",
    # or: user_id="staffOpenId",
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
    start_time={"time": 1656468000, "date": "", "timeZone": "Asia/Shanghai"},
    end_time={"time": 1656475200, "date": "", "timeZone": "Asia/Shanghai"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "yes"}, {"staffId": "staff2", "attendeeFlag": "option"}],
    description="每周项目进度同步",
    all_day="no",
    repeat_type="week",
    attendee_permissions="can_see",
    user_token="userToken123",
    # or: user_id="staffOpenId",
)
# result.schedule_id — created schedule ID
```

**startTime/endTime format**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| time | long int (秒级时间戳) | Yes* | Unix timestamp in seconds (e.g. `1656468000`) |
| date | string | Yes* | Date string format `2006-01-02` (for allDay) |
| timeZone | string | No | Default `Asia/Shanghai`. For allDay: must be `UTC` |

- When `allDay="no"`: use `time` (seconds timestamp) + `timeZone`, leave `date` empty
- When `allDay="yes"`: use `date` + `timeZone=UTC`, do NOT fill `time`

**attendees format** (create_schedule only):

| Field | Required | Values |
|-------|----------|--------|
| staffId | Yes | Participant's openStaffId |
| attendeeFlag | Yes | `"yes"` = must attend, `"option"` = optional, `"no"` = don't attend |

**Other params**:

| SDK param | Default | Description |
|-----------|---------|-------------|
| description | "" | Schedule description (max 6000 chars) |
| all_day | "no" | "yes" or "no" |
| repeat_type | "no" | no/day/week/month/year/work_day/custom |
| rule | "" | RFC 5545 repeat rule (when repeat_type != "no") |
| expire_date_type | "no" | "no" = never expire, "yes" = has expiry. Must be "no" when repeat_type="no" |
| reminder_type | "yes" | "yes" = send notification, "no" = no notification |
| attendee_permissions | "can_see" | can_modify/can_invite/can_see/none |

- Returns: `ScheduleCreateResult` — schedule_id
- **Required**: calendar_id, summary, start_time, end_time, attendees

### 3. Fetch a schedule

```python
result = await client.fetch_schedule(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    user_token="userToken123",
    # or: user_id="staffOpenId",
)
# result.schedule_id, result.summary, result.start_time, result.end_time, result.rsvp_status
```

- Returns: `ScheduleInfoResult` — schedule_id, summary, description, repeat_type, all_day, start_time, end_time, creator, rsvp_status

### 4. Delete a schedule

```python
result = await client.delete_schedule(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    reminder_type="no",               # "yes" or "no" — whether to notify attendees
    operation_type="delete_all",       # delete_all / delete_current / delete_from_current
    # current_time=0,                  # required when operation_type != delete_all
    user_token="userToken123",
)
```

- Returns: `ScheduleCreateResult` — schedule_id
- `operation_type` options:
  - `delete_all`: delete entire series (default)
  - `delete_current`: delete only current instance (for recurring events)
  - `delete_from_current`: delete from current instance onwards (for recurring events)
- `current_time` is required when `operation_type` is not `delete_all` — must be the exact start time of the instance in seconds

### 5. Fetch schedule list (time range)

```python
result = await client.fetch_schedule_list(
    calendar_id="calOpenId",
    start_time=1705276800,            # Unix timestamp in **seconds** (not ms)
    end_time=1707940800,
    user_token="userToken123",
)
# result.schedule_list — list of schedule dicts
```

- Returns: `ScheduleListResult` — schedule_list
- **Required**: calendar_id, start_time, end_time
- **Constraint**: time range (end_time - start_time) must be ≤ 42 days
- **Note**: start_time/end_time are **seconds timestamps**, not milliseconds

### 6. Fetch schedule attendees

```python
result = await client.fetch_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    page=1,
    page_size=500,
    user_token="userToken123",
)
# result.total, result.attendees
```

- Returns: `ScheduleAttendeesResult` — total, attendees (list of dicts with staffId, name, rsvpStatus, attendeeFlag)
- Default: page=1, page_size=500 (max 500)

### 7. Add attendees

```python
result = await client.add_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    attendees=["staffOpenId1", "staffOpenId2"],  # plain list of staffIds (NOT objects)
    reminder_type="yes",
    user_token="userToken123",
)
```

- Returns: `ScheduleCreateResult` — schedule_id
- **Note**: `attendees` here is a **plain string list** of staffIds, NOT `{staffId, attendeeFlag}` objects like in create_schedule

### 8. Delete attendees

```python
result = await client.delete_schedule_attendees(
    calendar_id="calOpenId",
    schedule_id="schOpenId",
    attendees=["staffOpenId2"],  # plain list of staffIds
    reminder_type="no",
    user_token="userToken123",
)
```

- Returns: `ScheduleCreateResult` — schedule_id

## Sync Client

```python
from lansenger_sdk import LansengerSyncClient

client = LansengerSyncClient.from_env()
cal = client.fetch_primary_calendar(user_token="userToken")
result = client.create_schedule(calendar_id=cal.calendar_id, summary="会议", ...)
```

## Common Patterns

### Create a meeting and notify attendees

```python
cal = await client.fetch_primary_calendar(user_token="userToken")
if cal.success:
    schedule = await client.create_schedule(
        calendar_id=cal.calendar_id,
        summary="项目周会",
        start_time={"time": 1656468000, "date": "", "timeZone": "Asia/Shanghai"},
        end_time={"time": 1656475200, "date": "", "timeZone": "Asia/Shanghai"},
        attendees=[{"staffId": "staff1", "attendeeFlag": "yes"}],
        user_token="userToken",
    )
    if schedule.success:
        await client.send_text(chat_id="staff1", content="您有一个新的会议邀请：项目周会")
```

### Create an all-day event

```python
result = await client.create_schedule(
    calendar_id="calOpenId",
    summary="Company Holiday",
    start_time={"time": 0, "date": "2024-01-15", "timeZone": "UTC"},  # allDay: use date, timeZone=UTC
    end_time={"time": 0, "date": "2024-01-16", "timeZone": "UTC"},
    attendees=[{"staffId": "staff1", "attendeeFlag": "yes"}],
    all_day="yes",
)
```

### Get today's schedules

```python
from datetime import datetime

today_start = int(datetime.now().replace(hour=0, minute=0).timestamp())  # seconds, not ms
today_end = int(datetime.now().replace(hour=23, minute=59).timestamp())

result = await client.fetch_schedule_list(
    calendar_id="calOpenId", start_time=today_start, end_time=today_end,
)
for sch in result.schedule_list:
    print(sch.get("summary"), sch.get("startTime"))
```

## Key Differences from Other APIs

| Aspect | Calendar API | Note |
|--------|-------------|------|
| `attendees` in create_schedule | List of `{staffId, attendeeFlag}` objects | attendeeFlag: "yes"/"option"/"no" |
| `attendees` in add/delete | Plain string list of staffIds | NOT objects |
| `startTime.time` | Seconds timestamp (long int) | NOT milliseconds, NOT time string like "10:00" |
| `fetch_schedule_list` times | Seconds timestamps in request body | NOT milliseconds |
| `allDay=yes` | Use `date` + `timeZone=UTC`, no `time` | Must not fill `time` field |
| `user_id` param | Available on all methods | Alternative to user_token |
| `delete_schedule.reminderType` | Required param | Not optional with default like create |