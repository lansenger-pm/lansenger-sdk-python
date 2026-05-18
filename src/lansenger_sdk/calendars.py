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

Calendar/schedule endpoints require app_token and at least one of user_token or user_id.

Note: 4.23.1-8 (calendar CRUD, subscribe, unsubscribe, member list) are marked
"暂不开放" (not yet open) — not implemented here.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .models import (
    CalendarPrimaryResult,
    ScheduleCreateResult,
    ScheduleInfoResult,
    ScheduleListResult,
    ScheduleAttendeesResult,
)
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.calendars")


async def _do_get(
    config: LansengerConfig,
    url: str,
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return None, f"HTTP error: {e}"
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return None, f"Request error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None


async def _do_post(
    config: LansengerConfig,
    url: str,
    body: Dict[str, Any],
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=body)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return None, f"HTTP error: {e}"
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return None, f"Request error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None


def _parse_api_response(data: dict) -> tuple[bool, Optional[str]]:
    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return False, f"API error (errCode={err_code}): {msg}"
    return True, None


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
    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return CalendarPrimaryResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
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
    all_day: str = "no",
    repeat_type: str = "no",
    rule: str = "",
    expire_date_type: str = "no",
    reminder_type: str = "yes",
    attendee_permissions: str = "can_see",
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
        all_day: "yes" or "no".
        repeat_type: "no"/"day"/"week"/"month"/"year"/"work_day"/"custom".
        rule: RFC 5545 repeat rule when repeat_type != "no".
        attendee_permissions: "can_modify"/"can_invite"/"can_see"/"none".
    """
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not summary:
        return ScheduleCreateResult(success=False, error="summary is required")
    if not start_time:
        return ScheduleCreateResult(success=False, error="start_time is required")
    if not end_time:
        return ScheduleCreateResult(success=False, error="end_time is required")
    if not attendees:
        return ScheduleCreateResult(success=False, error="attendees is required")

    url = build_api_url(config, "calendars", "schedule_create", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id)

    body: Dict[str, Any] = {
        "summary": summary,
        "startTime": start_time,
        "endTime": end_time,
        "attendees": attendees,
    }
    if description:
        body["description"] = description
    if all_day:
        body["allDay"] = all_day
    if repeat_type:
        body["repeatType"] = repeat_type
    if rule:
        body["rule"] = rule
    if expire_date_type:
        body["expireDateType"] = expire_date_type
    if reminder_type:
        body["reminderType"] = reminder_type
    if attendee_permissions:
        body["attendeePermissions"] = attendee_permissions

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
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
    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return ScheduleInfoResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
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
        "reminder_type": reminder_type,
    }
    if operation_type != "delete_all":
        body["operationType"] = operation_type
        body["currentTime"] = current_time

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return ScheduleCreateResult(
        success=True,
        schedule_id=d.get("scheduleIds", [schedule_id])[0] if isinstance(d.get("scheduleIds"), list) else schedule_id,
        raw_response=data,
    )


async def fetch_schedule_list(
    config: LansengerConfig,
    app_token: str,
    calendar_id: str,
    start_time: int,
    end_time: int,
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
    if not start_time or not end_time:
        return ScheduleListResult(success=False, error="start_time and end_time are required")

    url = build_api_url(config, "calendars", "schedule_list", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id)

    body: Dict[str, Any] = {"startTime": start_time, "endTime": end_time}

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return ScheduleListResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
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

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return ScheduleAttendeesResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
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
    reminder_type: str = "yes",
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Add attendees to a schedule (4.23.16)."""
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleCreateResult(success=False, error="schedule_id is required")
    if not attendees:
        return ScheduleCreateResult(success=False, error="attendees is required")

    url = build_api_url(config, "calendars", "attendees_create", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {"attendees": attendees}
    if reminder_type:
        body["reminderType"] = reminder_type

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
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
    reminder_type: str = "no",
    user_token: str = "",
    user_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ScheduleCreateResult:
    """Delete attendees from a schedule (4.23.18)."""
    if not calendar_id:
        return ScheduleCreateResult(success=False, error="calendar_id is required")
    if not schedule_id:
        return ScheduleCreateResult(success=False, error="schedule_id is required")
    if not attendees:
        return ScheduleCreateResult(success=False, error="attendees is required")

    url = build_api_url(config, "calendars", "attendees_delete", app_token, user_token=user_token, user_id=user_id, calendar_id=calendar_id, schedule_id=schedule_id)

    body: Dict[str, Any] = {"attendees": attendees}
    if reminder_type:
        body["reminderType"] = reminder_type

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return ScheduleCreateResult(success=False, error=http_err)
    ok, api_err = _parse_api_response(data)
    if not ok:
        return ScheduleCreateResult(success=False, error=api_err)

    return ScheduleCreateResult(success=True, schedule_id=schedule_id, raw_response=data)