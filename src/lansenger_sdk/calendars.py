"""Lansenger calendar & schedule API — manage calendars and schedules (4.23).

Only the verified/open endpoints are implemented:
- 4.23.9  GET  /v1/calendars/primary             — get primary calendar
- 4.23.10 POST /v1/calendars/:cid/schedules/create — create schedule
- 4.23.11 GET  /v1/calendars/:cid/schedules/:sid/fetch — query schedule
- 4.23.12 POST /v1/calendars/:cid/schedules/:sid/update — update schedule
- 4.23.13 POST /v1/calendars/:cid/schedules/:sid/delete — delete schedule
- 4.23.14 POST /v1/calendars/:cid/schedules/fetch — get schedule list
- 4.23.15 GET  /v1/calendars/:cid/schedules/:sid/members/fetch — get attendees
- 4.23.16 POST /v1/calendars/:cid/schedules/:sid/members/create — add attendees
- 4.23.17 POST /v1/calendars/:cid/schedules/:sid/members/meta/update — update attendee metadata
- 4.23.18 POST /v1/calendars/:cid/schedules/:sid/members/delete — delete attendees
- 4.23.19 POST /v1/calendars/:cid/schedules/:sid/members/update — batch add/delete attendees

Calendar/schedule endpoints require app_token and at least one of user_token or user_id.

Note: 4.23.1-8 (calendar CRUD, subscribe, unsubscribe, member list) are marked
"暂不开放" (not yet open) — not implemented here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import LansengerConfig
from .models import (
    CalendarPrimaryResult,
    ScheduleAttendeeMetaResult,
    ScheduleAttendeesResult,
    ScheduleAttendeesUpdateResult,
    ScheduleCreateResult,
    ScheduleInfoResult,
    ScheduleListResult,
    ScheduleUpdateResult,
)
from .url_helpers import build_api_url
from .api_utils import do_get, do_post, parse_api_response


async def fetch_primary_calendar(
    config: LansengerConfig,
    app_token: str,
    *,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> CalendarPrimaryResult:
    """Get the primary calendar (4.23.9).

    At least one of user_token or user_id must be valid.
    When absent, uses app robot's primary calendar.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        user_token: Optional userToken.
        user_id: Optional user ID (alternative to user_token).
        http_client: Optional httpx client.
    """
    url = build_api_url(config, "calendars", "primary", app_token, user_token=user_token, user_id=user_id)
    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return CalendarPrimaryResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return CalendarPrimaryResult(success=False, error=api_err)

    d = data.get("data", {})
    return CalendarPrimaryResult(
        success=True,
        calendar_id=d.get("calendarId"),
        summary=d.get("summary"),
        description=d.get("description"),
        permissions=d.get("permissions"),
        color=d.get("color"),
        type=d.get("type"),
        role=d.get("role"),
        raw_response=data,
    )


async def create_schedule(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    summary: str,
    start_time: dict,
    end_time: dict,
    attendees: List[Dict[str, str]],
    *,
    description: str = "",
    all_day: Optional[str] = None,
    repeat_type: Optional[str] = None,
    rule: str = "",
    expire_date_type: Optional[str] = None,
    reminder_type: Optional[str] = None,
    attendee_permissions: Optional[str] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Create a schedule/event (4.23.10).

    Args:
        calendar_id: Calendar openId.
        summary: Schedule title (max 1000 chars).
        start_time: Dict with time/date/timeZone.
        end_time: Dict with time/date/timeZone.
        attendees: List of dicts with staffId + attendeeFlag.
        description: Optional description (max 6000 chars).
        all_day: "yes" or "no". Defaults to "no" if omitted.
        repeat_type: "no"/"day"/"week"/"month"/"year"/"work_day"/"custom". Defaults to "no" if omitted.
        rule: RFC 5545 repeat rule when repeat_type != "no".
        expire_date_type: "no" or "yes". Defaults to "no" if omitted.
        reminder_type: "yes" or "no". Defaults to "yes" if omitted.
        attendee_permissions: "can_modify"/"can_invite"/"can_see"/"none". Defaults to "can_see" if omitted.
    """
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not summary:
        return ScheduleCreateResult(success=False, error="summary is required")
    if not start_time:
        return ScheduleCreateResult(success=False, error="start_time is required")
    if not end_time:
        return ScheduleCreateResult(success=False, error="end_time is required")
    if not attendees and not user_id:
        return ScheduleCreateResult(success=False, error="attendees is required (or provide user_id to auto-fill creator)")
    if not attendees and user_id:
        attendees = [{"staffId": user_id, "attendeeFlag": "required"}]

    url = build_api_url(config, "calendars", "schedule_create", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id)

    body: Dict[str, Any] = {
        "summary": summary,
        "startTime": start_time,
        "endTime": end_time,
        "attendees": attendees,
    }
    if description:
        body["description"] = description
    if all_day is not None:
        body["allDay"] = all_day
    if repeat_type is not None:
        body["repeatType"] = repeat_type
    if rule:
        body["rule"] = rule
    if expire_date_type is not None:
        body["expireDateType"] = expire_date_type
    if reminder_type is not None:
        body["reminderType"] = reminder_type
    if attendee_permissions is not None:
        body["attendeePermissions"] = attendee_permissions

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleCreateResult(
        success=True,
        schedule_id=d.get("scheduleId"),
        raw_response=data,
    )


async def fetch_schedule(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    *,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleInfoResult:
    """Query a schedule (4.23.11)."""
    if not calendar_id:
        return ScheduleInfoResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleInfoResult(success=False, error="schedule_id is required")

    url = build_api_url(config, "calendars", "schedule_fetch", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)
    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return ScheduleInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleInfoResult(
        success=True,
        schedule_id=d.get("scheduleId"),
        summary=d.get("summary"),
        description=d.get("description"),
        repeat_type=d.get("repeatType"),
        all_day=d.get("allDay"),
        start_time=d.get("startTime"),
        end_time=d.get("endTime"),
        creator=d.get("creator"),
        rsvp_status=d.get("rsvpStatus"),
        raw_response=data,
    )


async def delete_schedule(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    reminder_type: str = "no",
    *,
    operation_type: str = "delete_all",
    current_time: int = 0,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Delete a schedule (4.23.13)."""
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleCreateResult(success=False, error="schedule_id is required")

    url = build_api_url(config, "calendars", "schedule_delete", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {
        "reminderType": reminder_type,
    }
    if operation_type != "delete_all":
        body["operationType"] = operation_type
        body["currentTime"] = current_time

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleCreateResult(
        success=True,
        schedule_id=d.get("scheduleIds", [schedule_id])[0] if isinstance(d.get("scheduleIds"), list) else schedule_id,
        raw_response=data,
    )


async def update_schedule(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    *,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    operation_type: str = "modify_all",
    current_time: Optional[int] = None,
    reminder_type: Optional[str] = None,
    repeat_type: Optional[str] = None,
    rule: Optional[str] = None,
    expire_date_type: Optional[str] = None,
    all_day: Optional[str] = None,
    attendee_permissions: Optional[str] = None,
    start_time: Optional[Dict[str, Any]] = None,
    end_time: Optional[Dict[str, Any]] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleUpdateResult:
    """Update a schedule (4.23.12).

    Only sends fields you explicitly provide. operation_type defaults to
    "modify_all" (modify entire repeating series). Use "modify_current" or
    "modify_current_after" for specific instances of repeating schedules.

    Args:
        calendar_id: Calendar openId (required).
        schedule_id: Schedule openId (required).
        summary: New schedule title.
        description: New schedule description.
        operation_type: "modify_current"/"modify_current_after"/"modify_all".
        current_time: Required when operation_type is NOT modify_all.
        reminder_type: "yes" or "no".
        repeat_type: "no"/"day"/"week"/"month"/"year"/"work_day"/"custom".
        rule: RFC 5545 repeat rule.
        expire_date_type: "no" or "yes".
        all_day: "yes" or "no".
        attendee_permissions: "can_modify"/"can_invite"/"can_see"/"none".
        start_time: Dict with time/date/timeZone.
        end_time: Dict with time/date/timeZone.
    """
    if not calendar_id:
        return ScheduleUpdateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleUpdateResult(success=False, error="schedule_id is required")

    url = build_api_url(config, "calendars", "schedule_update", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {}
    if summary is not None:
        body["summary"] = summary
    if description is not None:
        body["description"] = description
    if operation_type != "modify_all":
        body["operationType"] = operation_type
        if current_time is not None:
            body["currentTime"] = current_time
    if reminder_type is not None:
        body["reminderType"] = reminder_type
    if repeat_type is not None:
        body["repeatType"] = repeat_type
    if rule is not None:
        body["rule"] = rule
    if expire_date_type is not None:
        body["expireDateType"] = expire_date_type
    if all_day is not None:
        body["allDay"] = all_day
    if attendee_permissions is not None:
        body["attendeePermissions"] = attendee_permissions
    if start_time is not None:
        body["startTime"] = start_time
    if end_time is not None:
        body["endTime"] = end_time

    if not body:
        return ScheduleUpdateResult(success=False, error="at least one field to update is required")

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleUpdateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleUpdateResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleUpdateResult(
        success=True,
        schedule_ids=d.get("scheduleIds"),
        raw_response=data,
    )


async def fetch_schedule_list(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    *,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleListResult:
    """Get schedule list for a calendar in a time range (4.23.14).

    endTime - startTime must be <= 42 days.
    """
    if not calendar_id:
        return ScheduleListResult(success=False, error="calendar_id is required")
    if start_time is None or end_time is None:
        return ScheduleListResult(success=False, error="start_time and end_time are required")

    url = build_api_url(config, "calendars", "schedule_list", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id)

    body: Dict[str, Any] = {"startTime": start_time, "endTime": end_time}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleListResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleListResult(
        success=True,
        schedule_list=d.get("scheduleList"),
        raw_response=data,
    )


async def fetch_schedule_attendees(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    *,
    page: int = 1,
    page_size: int = 500,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleAttendeesResult:
    """Get schedule attendee list (4.23.15)."""
    if not calendar_id:
        return ScheduleAttendeesResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleAttendeesResult(success=False, error="schedule_id is required")

    url = build_api_url(config, "calendars", "attendees_fetch", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)
    url += f"&page={page}&page_size={page_size}"

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return ScheduleAttendeesResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleAttendeesResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleAttendeesResult(
        success=True,
        total=d.get("total", 0),
        attendees=d.get("attendees"),
        raw_response=data,
    )


async def add_schedule_attendees(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    attendees: List[str],
    *,
    reminder_type: Optional[str] = None,
    operation_type: Optional[str] = None,
    current_time: Optional[int] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Add attendees to a schedule (4.23.16).

    Args:
        reminder_type: "yes" or "no".
        operation_type: For recurring schedules — "modify_current", "modify_current_after", "modify_all"
        current_time: Required when operation_type != "modify_all" — start time of the specific occurrence
    """
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleCreateResult(success=False, error="schedule_id is required")
    if not attendees:
        return ScheduleCreateResult(success=False, error="attendees is required")

    url = build_api_url(config, "calendars", "attendees_create", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {"attendees": attendees}
    if reminder_type is not None:
        body["reminderType"] = reminder_type
    if operation_type is not None:
        body["operationType"] = operation_type
    if current_time is not None:
        body["currentTime"] = current_time

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleCreateResult(
        success=True,
        schedule_id=d.get("scheduleIds", [schedule_id])[0] if isinstance(d.get("scheduleIds"), list) else schedule_id,
        raw_response=data,
    )


async def delete_schedule_attendees(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    attendees: List[str],
    *,
    reminder_type: Optional[str] = None,
    operation_type: Optional[str] = None,
    current_time: Optional[int] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Delete attendees from a schedule (4.23.18).

    Args:
        reminder_type: "yes" or "no".
        operation_type: For recurring schedules — "modify_current", "modify_current_after", "modify_all"
        current_time: Required when operation_type != "modify_all" — start time of the specific occurrence
    """
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleCreateResult(success=False, error="schedule_id is required")
    if not attendees:
        return ScheduleCreateResult(success=False, error="attendees is required")

    url = build_api_url(config, "calendars", "attendees_delete", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {"attendees": attendees}
    if reminder_type is not None:
        body["reminderType"] = reminder_type
    if operation_type is not None:
        body["operationType"] = operation_type
    if current_time is not None:
        body["currentTime"] = current_time

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    return ScheduleCreateResult(success=True, schedule_id=schedule_id, raw_response=data)


async def update_schedule_attendee_meta(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    *,
    rsvp_status: Optional[str] = None,
    color: Optional[str] = None,
    permissions: Optional[str] = None,
    busy_free_state: Optional[str] = None,
    remind_times: Optional[List[int]] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleAttendeeMetaResult:
    """Update schedule attendee metadata (4.23.17).

    Updates RSVP status, color, visibility, busy/free state, and reminder
    times for the current identity on a specific schedule.

    Args:
        calendar_id: Calendar openId (required).
        schedule_id: Schedule openId (required).
        rsvp_status: "accept"/"tentative"/"decline".
        color: Hex color string (e.g. "#FF347AFC").
        permissions: "private"/"public"/"default".
        busy_free_state: "busy"/"free".
        remind_times: Reminder time offsets in minutes (list of ints).
    """
    if not calendar_id:
        return ScheduleAttendeeMetaResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleAttendeeMetaResult(success=False, error="schedule_id is required")

    url = build_api_url(config, "calendars", "attendees_meta_update", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {}
    if rsvp_status is not None:
        body["rsvpStatus"] = rsvp_status
    if color is not None:
        body["color"] = color
    if permissions is not None:
        body["permissions"] = permissions
    if busy_free_state is not None:
        body["busyFreeState"] = busy_free_state
    if remind_times is not None:
        body["remindTimes"] = remind_times

    if not body:
        return ScheduleAttendeeMetaResult(success=False, error="at least one field to update is required")

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleAttendeeMetaResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleAttendeeMetaResult(success=False, error=api_err)

    return ScheduleAttendeeMetaResult(success=True, raw_response=data)


async def update_schedule_attendees(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    schedule_id: str,
    *,
    add_attendees: Optional[List[str]] = None,
    delete_attendees: Optional[List[str]] = None,
    reminder_type: Optional[str] = None,
    operation_type: Optional[str] = None,
    current_time: Optional[int] = None,
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleAttendeesUpdateResult:
    """Batch add and/or delete schedule attendees (4.23.19).

    Allows adding and removing attendees in a single API call.

    Args:
        calendar_id: Calendar openId (required).
        schedule_id: Schedule openId (required).
        add_attendees: List of staff openIds to add.
        delete_attendees: List of staff openIds to remove.
        reminder_type: "yes" or "no".
        operation_type: For recurring schedules — "modify_current",
            "modify_current_after", "modify_all".
        current_time: Required when operation_type != "modify_all" —
            start time of the specific occurrence.
    """
    if not calendar_id:
        return ScheduleAttendeesUpdateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleAttendeesUpdateResult(success=False, error="schedule_id is required")
    if not add_attendees and not delete_attendees:
        return ScheduleAttendeesUpdateResult(success=False, error="at least one of add_attendees or delete_attendees is required")

    url = build_api_url(
        config, "calendars", "attendees_update", app_token,
        user_token=user_token, user_id=user_id,
        calendar_id=calendar_id, schedule_id=schedule_id,
    )

    body: Dict[str, Any] = {}
    if add_attendees is not None:
        body["addAttendees"] = add_attendees
    if delete_attendees is not None:
        body["deleteAttendees"] = delete_attendees
    if reminder_type is not None:
        body["reminderType"] = reminder_type
    if operation_type is not None:
        body["operationType"] = operation_type
    if current_time is not None:
        body["currentTime"] = current_time

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return ScheduleAttendeesUpdateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return ScheduleAttendeesUpdateResult(success=False, error=api_err)

    d = data.get("data", {})
    schedule_ids = d.get("scheduleIds")
    if isinstance(schedule_ids, list):
        schedule_ids = [str(s) for s in schedule_ids]
    else:
        schedule_ids = None
    attendees = d.get("attendees")
    if isinstance(attendees, list):
        attendees = [str(a) for a in attendees]

    return ScheduleAttendeesUpdateResult(
        success=True,
        schedule_ids=schedule_ids,
        failed_attendees=attendees,
        raw_response=data,
    )