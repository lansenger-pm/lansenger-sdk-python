"""Tests for Lansenger SDK calendar & schedule (4.23) module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.calendars import (
    fetch_primary_calendar,
    create_schedule,
    fetch_schedule,
    delete_schedule,
    fetch_schedule_list,
    fetch_schedule_attendees,
    add_schedule_attendees,
    delete_schedule_attendees,
    update_schedule_attendees,
)
from lansenger_sdk.models import (
    CalendarPrimaryResult,
    ScheduleAttendeesUpdateResult,
    ScheduleCreateResult,
    ScheduleInfoResult,
    ScheduleListResult,
    ScheduleAttendeesResult,
)
from lansenger_sdk.client import LansengerClient

from unittest.mock import AsyncMock, patch, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://test-gateway.example.com",
    )


def _mock_http_client(response_data):
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"errCode":0}'
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    mock.post.return_value = mock_response
    mock.get.return_value = mock_response
    mock.aclose = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_fetch_primary_calendar_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {
            "calendarId": "cal123",
            "summary": "My Calendar",
            "description": "Primary",
            "permissions": "owner",
            "color": "#0000ff",
            "type": "primary",
            "role": "owner",
        },
    })
    result = await fetch_primary_calendar(config, app_token="tok", http_client=mock_client)
    assert result.success is True
    assert result.calendar_id == "cal123"
    assert result.summary == "My Calendar"
    assert result.type == "primary"


@pytest.mark.asyncio
async def test_fetch_primary_calendar_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 40001, "errMsg": "Invalid token"})
    result = await fetch_primary_calendar(config, app_token="tok", http_client=mock_client)
    assert result.success is False
    assert "errCode=40001" in result.error


@pytest.mark.asyncio
async def test_create_schedule_no_calendar_id():
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="", summary="s",
        start_time={"time": "10:00"}, end_time={"time": "11:00"}, attendees=[{"staffId": "s1"}],
    )
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_create_schedule_no_summary():
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="",
        start_time={"time": "10:00"}, end_time={"time": "11:00"}, attendees=[{"staffId": "s1"}],
    )
    assert result.success is False
    assert "summary is required" in result.error


@pytest.mark.asyncio
async def test_create_schedule_no_start_time():
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="s",
        start_time={}, end_time={"time": "11:00"}, attendees=[{"staffId": "s1"}],
    )
    assert result.success is False
    assert "start_time is required" in result.error


@pytest.mark.asyncio
async def test_create_schedule_no_end_time():
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="s",
        start_time={"time": "10:00"}, end_time={}, attendees=[{"staffId": "s1"}],
    )
    assert result.success is False
    assert "end_time is required" in result.error


@pytest.mark.asyncio
async def test_create_schedule_no_attendees():
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="s",
        start_time={"time": "10:00"}, end_time={"time": "11:00"}, attendees=[],
    )
    assert result.success is False
    assert "attendees is required" in result.error


@pytest.mark.asyncio
async def test_create_schedule_auto_fill_attendees_with_user_id():
    """Empty attendees + user_id → auto-fills [{staffId: user_id, attendeeFlag: "required"}]."""
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"scheduleId": "sch_auto"}})
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="Meeting",
        start_time={"date": "2024-01-01", "time": "10:00", "timeZone": "Asia/Shanghai"},
        end_time={"date": "2024-01-01", "time": "11:00", "timeZone": "Asia/Shanghai"},
        attendees=[],  # empty — triggers auto-fill
        user_id="user456",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.schedule_id == "sch_auto"
    # Verify the auto-filled attendees were sent in the POST body
    sent_body = mock_client.post.call_args.kwargs.get("json", {})
    assert "attendees" in sent_body
    assert sent_body["attendees"] == [{"staffId": "user456", "attendeeFlag": "required"}]


@pytest.mark.asyncio
async def test_create_schedule_preserves_provided_attendees_with_user_id():
    """Explicit attendees + user_id → provided attendees are used as-is (no override)."""
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"scheduleId": "sch1"}})
    custom_attendees = [{"staffId": "staff1", "attendeeFlag": "optional"}]
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="Meeting",
        start_time={"date": "2024-01-01", "time": "10:00", "timeZone": "Asia/Shanghai"},
        end_time={"date": "2024-01-01", "time": "11:00", "timeZone": "Asia/Shanghai"},
        attendees=custom_attendees,  # explicitly provided — no auto-fill
        user_id="user456",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.schedule_id == "sch1"
    # Verify the original attendees were sent, not auto-filled
    sent_body = mock_client.post.call_args.kwargs.get("json", {})
    assert "attendees" in sent_body
    assert sent_body["attendees"] == custom_attendees


@pytest.mark.asyncio
async def test_create_schedule_no_attendees_no_user_id_error():
    """Neither attendees nor user_id provided → returns clear error message."""
    config = _make_config()
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="s",
        start_time={"time": "10:00"}, end_time={"time": "11:00"},
        attendees=[], user_id="",
    )
    assert result.success is False
    assert "attendees is required (or provide user_id to auto-fill creator)" in result.error


@pytest.mark.asyncio
async def test_create_schedule_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"scheduleId": "sch1"}})
    result = await create_schedule(
        config, app_token="tok", calendar_id="cal1", summary="Meeting",
        start_time={"date": "2024-01-01", "time": "10:00", "timeZone": "Asia/Shanghai"},
        end_time={"date": "2024-01-01", "time": "11:00", "timeZone": "Asia/Shanghai"},
        attendees=[{"staffId": "staff1", "attendeeFlag": "required"}],
        http_client=mock_client,
    )
    assert result.success is True
    assert result.schedule_id == "sch1"


@pytest.mark.asyncio
async def test_fetch_schedule_no_calendar_id():
    config = _make_config()
    result = await fetch_schedule(config, app_token="tok", calendar_id="", schedule_id="sch1")
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_schedule_no_schedule_id():
    config = _make_config()
    result = await fetch_schedule(config, app_token="tok", calendar_id="cal1", schedule_id="")
    assert result.success is False
    assert "schedule_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_schedule_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {
            "scheduleId": "sch1",
            "summary": "Meeting",
            "description": "Team sync",
            "repeatType": "no",
            "allDay": "no",
            "startTime": {"date": "2024-01-01"},
            "endTime": {"date": "2024-01-01"},
            "creator": {"staffId": "staff1"},
            "rsvpStatus": "accepted",
        },
    })
    result = await fetch_schedule(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", http_client=mock_client)
    assert result.success is True
    assert result.schedule_id == "sch1"
    assert result.summary == "Meeting"
    assert result.rsvp_status == "accepted"


@pytest.mark.asyncio
async def test_delete_schedule_no_calendar_id():
    config = _make_config()
    result = await delete_schedule(config, app_token="tok", calendar_id="", schedule_id="sch1")
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_delete_schedule_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"scheduleIds": ["sch1"]}})
    result = await delete_schedule(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", http_client=mock_client)
    assert result.success is True
    assert result.schedule_id == "sch1"


@pytest.mark.asyncio
async def test_fetch_schedule_list_no_calendar_id():
    config = _make_config()
    result = await fetch_schedule_list(config, app_token="tok", calendar_id="", start_time=100, end_time=200)
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_schedule_list_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"scheduleList": [{"scheduleId": "sch1"}, {"scheduleId": "sch2"}]},
    })
    result = await fetch_schedule_list(config, app_token="tok", calendar_id="cal1", start_time=100, end_time=200, http_client=mock_client)
    assert result.success is True
    assert result.schedule_list is not None
    assert len(result.schedule_list) == 2


@pytest.mark.asyncio
async def test_fetch_schedule_attendees_no_calendar_id():
    config = _make_config()
    result = await fetch_schedule_attendees(config, app_token="tok", calendar_id="", schedule_id="sch1")
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_schedule_attendees_no_schedule_id():
    config = _make_config()
    result = await fetch_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="")
    assert result.success is False
    assert "schedule_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_schedule_attendees_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"total": 3, "attendees": [{"staffId": "s1"}, {"staffId": "s2"}, {"staffId": "s3"}]},
    })
    result = await fetch_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", http_client=mock_client)
    assert result.success is True
    assert result.total == 3
    assert result.attendees is not None


@pytest.mark.asyncio
async def test_add_schedule_attendees_no_calendar_id():
    config = _make_config()
    result = await add_schedule_attendees(config, app_token="tok", calendar_id="", schedule_id="sch1", attendees=["s1"])
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_add_schedule_attendees_no_attendees():
    config = _make_config()
    result = await add_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", attendees=[])
    assert result.success is False
    assert "attendees is required" in result.error


@pytest.mark.asyncio
async def test_add_schedule_attendees_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"scheduleIds": ["sch1"]}})
    result = await add_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", attendees=["staff1", "staff2"], http_client=mock_client)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_schedule_attendees_no_calendar_id():
    config = _make_config()
    result = await delete_schedule_attendees(config, app_token="tok", calendar_id="", schedule_id="sch1", attendees=["s1"])
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_delete_schedule_attendees_no_attendees():
    config = _make_config()
    result = await delete_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", attendees=[])
    assert result.success is False
    assert "attendees is required" in result.error


@pytest.mark.asyncio
async def test_delete_schedule_attendees_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {}})
    result = await delete_schedule_attendees(config, app_token="tok", calendar_id="cal1", schedule_id="sch1", attendees=["staff1"], http_client=mock_client)
    assert result.success is True
    assert result.schedule_id == "sch1"


@pytest.mark.asyncio
async def test_calendar_models_to_dict():
    r = CalendarPrimaryResult(success=True, calendar_id="cal1", summary="My Calendar")
    d = r.to_dict()
    assert d["success"] is True
    assert d["calendar_id"] == "cal1"
    assert d["summary"] == "My Calendar"

    r2 = ScheduleCreateResult(success=True, schedule_id="sch1")
    d2 = r2.to_dict()
    assert d2["success"] is True
    assert d2["schedule_id"] == "sch1"

    r3 = ScheduleInfoResult(success=True, schedule_id="sch1", summary="Meeting", rsvp_status="accepted")
    d3 = r3.to_dict()
    assert d3["success"] is True
    assert d3["rsvp_status"] == "accepted"

    r4 = ScheduleListResult(success=True, schedule_list=[{"id": "s1"}])
    d4 = r4.to_dict()
    assert d4["success"] is True
    assert d4["schedule_list"] is not None

    r5 = ScheduleAttendeesResult(success=True, total=3, attendees=[{"staffId": "s1"}])
    d5 = r5.to_dict()
    assert d5["success"] is True
    assert d5["total"] == 3


@pytest.mark.asyncio
async def test_client_fetch_primary_calendar():
    client = LansengerClient(app_id="test", app_secret="test")
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_token = AsyncMock(return_value="tok")
    client._http_client = mock_http
    client._token_manager = MagicMock()
    client._token_manager.get_token = mock_token
    client._owns_http_client = False

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"errCode":0,"data":{"calendarId":"cal1"}}'
    mock_response.json.return_value = {"errCode": 0, "data": {"calendarId": "cal1"}}
    mock_response.raise_for_status = MagicMock()
    mock_http.get.return_value = mock_response
    mock_http.aclose = AsyncMock()

    result = await client.fetch_primary_calendar()
    assert result.success is True
    assert result.calendar_id == "cal1"


@pytest.mark.asyncio
async def test_client_create_schedule_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.create_schedule(calendar_id="", summary="s", start_time={}, end_time={}, attendees=[])
    assert result.success is False
    assert "calendar_id is required" in result.error
    await client.close()


# ── update_schedule_attendees (4.23.19) ──────────────────────────────

@pytest.mark.asyncio
async def test_update_schedule_attendees_no_calendar_id():
    config = _make_config()
    result = await update_schedule_attendees(config, app_token="tok", calendar_id="", schedule_id="s1")
    assert result.success is False
    assert "calendar_id is required" in result.error


@pytest.mark.asyncio
async def test_update_schedule_attendees_no_attendees():
    config = _make_config()
    result = await update_schedule_attendees(config, app_token="tok", calendar_id="c1", schedule_id="s1")
    assert result.success is False
    assert "add_attendees or delete_attendees" in result.error


@pytest.mark.asyncio
async def test_update_schedule_attendees_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"scheduleIds": ["s1", "s2"], "attendees": ["failed1"]},
    })
    result = await update_schedule_attendees(
        config, app_token="tok", calendar_id="c1", schedule_id="s1",
        add_attendees=["a1", "a2"], delete_attendees=["a3"],
        http_client=mock_client,
    )
    assert result.success is True
    assert result.schedule_ids == ["s1", "s2"]
    assert result.failed_attendees == ["failed1"]


@pytest.mark.asyncio
async def test_update_schedule_attendees_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 10005, "errMsg": "no permission"})
    result = await update_schedule_attendees(
        config, app_token="tok", calendar_id="c1", schedule_id="s1",
        add_attendees=["a1"], http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10005" in result.error


@pytest.mark.asyncio
async def test_client_update_schedule_attendees_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.update_schedule_attendees(calendar_id="", schedule_id="s1")
    assert result.success is False
    assert "calendar_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_fetch_schedule_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.fetch_schedule(calendar_id="", schedule_id="s1")
    assert result.success is False
    assert "calendar_id is required" in result.error
    await client.close()