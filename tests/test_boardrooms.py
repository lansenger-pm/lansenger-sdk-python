"""Tests for Lansenger SDK boardroom (会议室预定 V2) module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.boardrooms import (
    reserve_boardroom,
    edit_boardroom_reserve,
    cancel_boardroom_reserve,
    confirm_boardroom_sign,
    fetch_boardroom_list,
    fetch_boardroom_detail,
    fetch_boardroom_schedule,
    fetch_boardroom_reserve_detail,
    fetch_my_boardroom_reserves,
    fetch_boardroom_gradings,
    fetch_boardroom_area_offices,
    BOARDROOM_STATUS_RESERVED,
    BOARDROOM_RESERVE_TYPE_SINGLE,
    BOARDROOM_EDIT_TYPE_CURRENT,
)
from lansenger_sdk.models import (
    BoardroomListResult,
    BoardroomReserveResult,
)
from lansenger_sdk.client import LansengerClient

from unittest.mock import AsyncMock, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
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


_PAGE_INFO = {"errCode": 0, "data": {"count": 1, "data": [
    {"id": "room1", "name": "第一会议室", "peopleNum": 20, "status": "1", "areaName": "望京"},
], "code": 0, "msg": ""}}


@pytest.mark.asyncio
async def test_reserve_boardroom_no_boardroom_id():
    r = await reserve_boardroom(_make_config(), app_token="tok", boardroom_id="", name="n",
                                grading_id="g", reserve_time_start="s", reserve_time_end="e", notice_time="立即提醒")
    assert r.success is False and "boardroom_id is required" in r.error


@pytest.mark.asyncio
async def test_reserve_boardroom_no_name():
    r = await reserve_boardroom(_make_config(), app_token="tok", boardroom_id="r", name="",
                                grading_id="g", reserve_time_start="s", reserve_time_end="e", notice_time="立即提醒")
    assert r.success is False and "name is required" in r.error


@pytest.mark.asyncio
async def test_reserve_boardroom_no_notice_time():
    r = await reserve_boardroom(_make_config(), app_token="tok", boardroom_id="r", name="n",
                                grading_id="g", reserve_time_start="s", reserve_time_end="e", notice_time="")
    assert r.success is False and "notice_time is required" in r.error


@pytest.mark.asyncio
async def test_reserve_boardroom_success_body_shape():
    mock = _mock_http_client({"errCode": 0, "data": {
        "id": "res1", "reserveCode": "BR001", "boardRoomName": "第一会议室",
        "name": "周会", "status": "5", "reserveTime": "1小时",
    }})
    r = await reserve_boardroom(
        _make_config(), app_token="tok", boardroom_id="room1", name="周会",
        grading_id="g1", reserve_time_start="2026-07-22 09:00:00",
        reserve_time_end="2026-07-22 10:00:00", notice_time="会前15分钟",
        people_number="10", is_video="1", invitation_user_list=["U1"],
        http_client=mock,
    )
    assert r.success is True
    assert r.reserve_id == "res1" and r.reserve_code == "BR001" and r.status == "5"
    body = mock.post.call_args.kwargs["json"]
    assert body["boardRoomId"] == "room1" and body["noticeTime"] == "会前15分钟"
    assert body["reserveType"] == BOARDROOM_RESERVE_TYPE_SINGLE
    assert body["invitationUserList"] == ["U1"]
    assert "id" not in body and "editType" not in body


@pytest.mark.asyncio
async def test_edit_reserve_carries_id_and_edit_type():
    mock = _mock_http_client({"errCode": 0, "data": {"id": "res1", "reserveCode": "BR001"}})
    r = await edit_boardroom_reserve(
        _make_config(), app_token="tok", reserve_id="res1", boardroom_id="room1",
        name="改期", grading_id="g1", reserve_time_start="2026-07-23 09:00:00",
        reserve_time_end="2026-07-23 10:00:00", notice_time="立即提醒",
        edit_type="2", http_client=mock,
    )
    assert r.success is True
    body = mock.post.call_args.kwargs["json"]
    assert body["id"] == "res1" and body["editType"] == "2"


@pytest.mark.asyncio
async def test_cancel_no_reserve_id():
    r = await cancel_boardroom_reserve(_make_config(), app_token="tok", reserve_id="")
    assert r.success is False and "reserve_id is required" in r.error


@pytest.mark.asyncio
async def test_cancel_success_body():
    mock = _mock_http_client({"errCode": 0, "data": True})
    r = await cancel_boardroom_reserve(
        _make_config(), app_token="tok", reserve_id="res1",
        cancel_reason="会议取消", is_send=True, cancel_type="2", http_client=mock,
    )
    assert r.success is True and r.done is True
    body = mock.post.call_args.kwargs["json"]
    assert body == {"id": "res1", "cancelReason": "会议取消", "isSend": True, "cancelType": "2"}


@pytest.mark.asyncio
async def test_confirm_sign_success():
    mock = _mock_http_client({"errCode": 0, "data": True})
    r = await confirm_boardroom_sign(_make_config(), app_token="tok", reserve_id="res1", http_client=mock)
    assert r.success is True and r.done is True


@pytest.mark.asyncio
async def test_fetch_boardroom_list_page_info():
    mock = _mock_http_client(_PAGE_INFO)
    r = await fetch_boardroom_list(_make_config(), app_token="tok", grading_id="g1", http_client=mock)
    assert r.success is True and r.count == 1
    assert r.items[0]["name"] == "第一会议室"
    body = mock.post.call_args.kwargs["json"]
    assert body["gradingId"] == "g1" and "lxUserId" not in body


@pytest.mark.asyncio
async def test_fetch_boardroom_schedule_requires_fields():
    r = await fetch_boardroom_schedule(_make_config(), app_token="tok", room_id="", query_date="d", grading_id="g")
    assert r.success is False and "room_id is required" in r.error
    r = await fetch_boardroom_schedule(_make_config(), app_token="tok", room_id="r", query_date="", grading_id="g")
    assert r.success is False and "query_date is required" in r.error
    r = await fetch_boardroom_schedule(_make_config(), app_token="tok", room_id="r", query_date="d", grading_id="")
    assert r.success is False and "grading_id is required" in r.error


@pytest.mark.asyncio
async def test_fetch_boardroom_schedule_extracts():
    mock = _mock_http_client({"errCode": 0, "data": {
        "id": "room1", "name": "第一会议室", "peopleNum": 20, "canReserveFlag": "1",
        "reserveDtoList": [{"id": "res1", "name": "周会", "status": "5"}],
        "deactivatedInfoList": [],
    }})
    r = await fetch_boardroom_schedule(_make_config(), app_token="tok", room_id="room1",
                                       query_date="2026-07-22", grading_id="g1", http_client=mock)
    assert r.success is True
    assert r.reserves[0]["name"] == "周会" and r.deactivations == []


@pytest.mark.asyncio
async def test_fetch_my_reserves_requires_grading():
    r = await fetch_my_boardroom_reserves(_make_config(), app_token="tok", grading_id="")
    assert r.success is False and "grading_id is required" in r.error


@pytest.mark.asyncio
async def test_fetch_gradings_and_areas():
    mock = _mock_http_client({"errCode": 0, "data": [{"id": "g1", "name": "默认分级", "type": "GRADING_ADMIN"}]})
    r = await fetch_boardroom_gradings(_make_config(), app_token="tok", http_client=mock)
    assert r.success is True and r.total == 1 and r.gradings[0]["id"] == "g1"

    mock2 = _mock_http_client({"errCode": 0, "data": [{"id": "area1", "areaName": "望京", "fooler": []}]})
    r2 = await fetch_boardroom_area_offices(_make_config(), app_token="tok", grading_id="g1", http_client=mock2)
    assert r2.success is True and r2.areas[0]["areaName"] == "望京"


@pytest.mark.asyncio
async def test_boardroom_list_api_error():
    mock = _mock_http_client({"errCode": 10000, "errMsg": "API 服务不可得"})
    r = await fetch_boardroom_list(_make_config(), app_token="tok", http_client=mock)
    assert r.success is False and "errCode=10000" in r.error


@pytest.mark.asyncio
async def test_client_reserve_boardroom_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    r = await client.reserve_boardroom(boardroom_id="", name="n", grading_id="g",
                                       reserve_time_start="s", reserve_time_end="e", notice_time="立即提醒")
    assert r.success is False and "boardroom_id is required" in r.error
    await client.close()


def test_boardroom_models_to_dict():
    d = BoardroomReserveResult(success=True, reserve_code="BR1").to_dict()
    assert d["reserve_code"] == "BR1" and "raw_response" not in d
    d2 = BoardroomListResult(success=True, count=2, items=[]).to_dict()
    assert d2["count"] == 2
    failed = BoardroomReserveResult(success=False, error="boom")
    assert failed.to_dict()["error"] == "boom"


def test_boardroom_constants():
    assert BOARDROOM_STATUS_RESERVED == 5
    assert BOARDROOM_RESERVE_TYPE_SINGLE == "0"
    assert BOARDROOM_EDIT_TYPE_CURRENT == "1"
