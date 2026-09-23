"""Tests for the videoconference (视频会议开放能力) SDK domain."""

import inspect
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from lansenger_sdk.client import LansengerClient
from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.models import (
    VideoconferenceListResult,
    VideoconferenceOpResult,
)
from lansenger_sdk.sync_client import LansengerSyncClient
from lansenger_sdk.videoconferences import (
    VC_OPS,
    cancel_meeting,
    control_member,
    create_meeting,
    modify_meeting,
    fetch_meeting_list,
    fetch_meeting_status,
    fetch_org_conf,
    fetch_vod_download_urls,
    fetch_vod_list,
    subscribe_meeting_events,
)


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
    mock.aclose = AsyncMock()
    return mock


MEMBERS = [
    {"staffId": "u1", "employeeName": "张三", "role": "participant"},
    {"staffId": "u2", "employeeName": "李四", "role": "admin"},
]


@pytest.mark.asyncio
async def test_create_meeting_requires_subject_and_host(monkeypatch):
    c = LansengerClient(_make_config())
    monkeypatch.setattr(c, "_get_token", AsyncMock(return_value="tok"))
    r = await c.create_meeting(subject="", start_time=100, members=MEMBERS, org_id="524288")
    assert r.success is False and "subject is required" in r.error

    no_host = [m for m in MEMBERS if m["role"] != "admin"]
    r = await c.create_meeting(subject="s", start_time=100, members=no_host, org_id="524288")
    assert r.success is False and "exactly one member must have role='admin'" in r.error

    two_hosts = MEMBERS + [{"staffId": "u3", "employeeName": "王五", "role": "admin"}]
    r = await c.create_meeting(subject="s", start_time=100, members=two_hosts, org_id="524288")
    assert r.success is False and "exactly one member must have role='admin'" in r.error


@pytest.mark.asyncio
async def test_create_meeting_module_body_and_url():
    mock = _mock_http_client({"errCode": 0, "data": {"id": 3204, "meetingNumber": "9100"}})
    r = await create_meeting(
        _make_config(), app_token="tok", subject="周会", start_time=1000,
        members=MEMBERS, org_id="524288", auto_record=1,
        conf_password="123456", user_token="ut1", http_client=mock,
    )
    assert r.success is True and r.mid == 3204 and r.meeting_number == "9100"
    body = mock.post.call_args.kwargs["json"]
    assert body["orgId"] == 524288 and body["autoRecord"] == 1
    assert body["member"] == MEMBERS
    url = mock.post.call_args.args[0]
    assert "/xtra/videoconference/openapi/v1/meeting/create" in url
    assert "app_token=tok" in url and "user_token=ut1" in url


@pytest.mark.asyncio
async def test_cancel_meeting_uses_cancle_endpoint():
    mock = _mock_http_client({"errCode": 0, "data": {"code": 0, "message": "success"}})
    r = await cancel_meeting(
        _make_config(), app_token="tok", mid=3204, org_id="524288",
        operator="u1", user_token="ut1", http_client=mock,
    )
    assert r.success is True and r.done is True
    url = mock.post.call_args.args[0]
    # server keeps the historical "cancle" spelling
    assert "/meeting/cancle" in url


@pytest.mark.asyncio
async def test_control_member_passes_op_code_through():
    # 不再做客户端硬校验：未知 op_code 也原样透传给服务端（服务端才是权威）
    mock = _mock_http_client({"errCode": 0, "data": {"code": 0, "message": "success"}})
    r = await control_member(
        _make_config(), app_token="tok", mid=1, staff_id="u1", op_code="not_an_op",
        operator="u2", org_id="524288", user_token="ut1", http_client=mock,
    )
    assert r.success is True
    assert mock.post.call_args.kwargs["json"]["opCode"] == "not_an_op"


def test_vc_ops_is_reference_only():
    # VC_OPS 现在只是「已知取值」参考表，不再用于拦截；保留实测修正
    assert "mute" in VC_OPS and "applyAudio" not in VC_OPS


@pytest.mark.asyncio
async def test_control_member_body():
    mock = _mock_http_client({"errCode": 0, "data": {"code": 0, "message": "success"}})
    r = await control_member(
        _make_config(), app_token="tok", mid=1, staff_id="u1", op_code="mute",
        operator="u2", org_id="524288", user_token="ut1", http_client=mock,
    )
    assert r.success is True and r.done is True
    body = mock.post.call_args.kwargs["json"]
    assert body["opCode"] == "mute" and body["mid"] == 1 and body["staffId"] == "u1"


@pytest.mark.asyncio
async def test_modify_meeting_passes_user_stop_time():
    mock = _mock_http_client({"errCode": 0, "data": {"code": 0, "message": "success"}})
    r = await modify_meeting(
        _make_config(), app_token="tok", mid=1, subject="更新后的会议",
        start_time=1700000000000, members=MEMBERS, org_id="524288",
        operator="u2", user_stop_time=1700003600000, http_client=mock,
    )
    assert r.success is True
    body = mock.post.call_args.kwargs["json"]
    assert body["userStopTime"] == 1700003600000
    # 不传 user_stop_time 时，body 里不应出现该字段
    mock2 = _mock_http_client({"errCode": 0, "data": {"code": 0, "message": "success"}})
    r2 = await modify_meeting(
        _make_config(), app_token="tok", mid=1, subject="更新后的会议",
        start_time=1700000000000, members=MEMBERS, org_id="524288",
        operator="u2", http_client=mock2,
    )
    assert r2.success is True
    assert "userStopTime" not in mock2.post.call_args.kwargs["json"]


@pytest.mark.asyncio
async def test_modify_meeting_done_true_on_meeting_object_response():
    """modify 返回的是会议对象（没有内层 code），done 不应恒为 False。

    响应形状取自 2026-09-23 对 /meeting/modify 的实测抓包。
    """
    meeting = {
        "admin": "u2", "adminName": "李四", "autoRecord": 0, "confPassword": "",
        "controlPassword": "", "createSource": 1, "ctime": 1790145779263,
        "haveVodRecord": 0, "id": 1380079, "meetingNumber": "", "mtime": 1790148033630,
        "startTime": 1790233200000, "status": 0, "stopTime": 0,
        "subject": "测试预约 sdkvfy01 已改", "type": 1,
    }
    mock = _mock_http_client({"errCode": 0, "errMsg": "OK", "data": meeting})
    r = await modify_meeting(
        _make_config(), app_token="tok", mid=1380079, subject="测试预约 sdkvfy01 已改",
        start_time=1790233200000, members=MEMBERS, org_id="14803712",
        operator="u2", http_client=mock,
    )
    assert r.success is True
    assert r.done is True


@pytest.mark.asyncio
async def test_op_done_false_when_inner_code_non_zero():
    """有内层 code 的端点仍按 code == 0 判 done（保留原语义）。"""
    mock = _mock_http_client({"errCode": 0, "data": {"code": 105213, "message": "会议未开始或已结束"}})
    r = await cancel_meeting(
        _make_config(), app_token="tok", mid=1, org_id="524288",
        operator="u1", http_client=mock,
    )
    assert r.success is True
    assert r.done is False
    assert r.message == "会议未开始或已结束"


@pytest.mark.asyncio
async def test_op_done_true_when_no_payload():
    """成功但完全没有 data 负载：三个 SDK 一致判为完成。

    Go 的 fillVCOp / TS 的 _op 同义（此前 Go 会留下 Done=False）。
    """
    mock = _mock_http_client({"errCode": 0, "errMsg": "OK"})
    r = await cancel_meeting(
        _make_config(), app_token="tok", mid=1, org_id="524288",
        operator="u1", http_client=mock,
    )
    assert r.success is True
    assert r.done is True


@pytest.mark.asyncio
async def test_op_done_true_on_subscribe_events_shape():
    """2026-09-23 实测 /meeting/events/subscribe 抓包：内层带 code，仍按 code == 0 判。"""
    mock = _mock_http_client({
        "errCode": 0, "errMsg": "OK",
        "data": {"code": 0, "errCode": 0, "message": ""},
    })
    r = await subscribe_meeting_events(
        _make_config(), app_token="tok", mid=1, org_id="524288",
        events=[{"eventType": "meeting.start"}], http_client=mock,
    )
    assert r.success is True
    assert r.done is True


@pytest.mark.asyncio
async def test_client_modify_meeting_forwards_user_stop_time(monkeypatch):
    c = LansengerClient(_make_config())
    monkeypatch.setattr(c, "_get_token", AsyncMock(return_value="tok"))
    captured = {}

    async def _fake_modify(config, app_token, **kwargs):
        captured.update(kwargs)
        return VideoconferenceOpResult(success=True)

    monkeypatch.setattr("lansenger_sdk.videoconferences.modify_meeting", _fake_modify)
    r = await c.modify_meeting(
        mid=1, subject="更新后的会议", start_time=1700000000000, members=MEMBERS,
        org_id="524288", operator="u2", user_stop_time=1700003600000,
    )
    assert r.success is True
    assert captured["user_stop_time"] == 1700003600000


@pytest.mark.asyncio
async def test_fetch_meeting_list_person_requires_staff_id():
    r = await fetch_meeting_list(
        _make_config(), app_token="tok", org_id="524288",
        start_time=1, end_time=2, fetch_range="person",
    )
    assert r.success is False and "staff_id is required" in r.error


@pytest.mark.asyncio
async def test_fetch_meeting_list_parses_page():
    mock = _mock_http_client({"errCode": 0, "data": {"offset": 0, "total": 2, "items": [{"id": 1}, {"id": 2}]}})
    r = await fetch_meeting_list(
        _make_config(), app_token="tok", org_id="524288",
        start_time=1, end_time=2, user_token="ut1", http_client=mock,
    )
    assert r.success is True and r.total == 2 and len(r.items) == 2
    assert isinstance(r, VideoconferenceListResult)


@pytest.mark.asyncio
async def test_fetch_meeting_status_requires_mids():
    r = await fetch_meeting_status(_make_config(), app_token="tok", org_id="524288", mids=[])
    assert r.success is False and "mids is required" in r.error


@pytest.mark.asyncio
async def test_fetch_vod_download_urls_max_three():
    r = await fetch_vod_download_urls(_make_config(), app_token="tok", vods=[], org_id="524288", operator="u1")
    assert r.success is False and "1..3" in r.error

    r = await fetch_vod_download_urls(
        _make_config(), app_token="tok", vods=[{"vodId": i} for i in range(4)],
        org_id="524288", operator="u1",
    )
    assert r.success is False and "1..3" in r.error


@pytest.mark.asyncio
async def test_fetch_vod_list_parses_items():
    mock = _mock_http_client({"errCode": 0, "data": {"items": [{"vodId": 1, "playUrl": "x"}]}})
    r = await fetch_vod_list(
        _make_config(), app_token="tok", mid=1, org_id="524288",
        operator="u1", user_token="ut1", http_client=mock,
    )
    assert r.success is True and r.items[0]["vodId"] == 1


@pytest.mark.asyncio
async def test_fetch_org_conf_maps_fields():
    mock = _mock_http_client({"errCode": 0, "data": {"maxPerson": 50, "allowedRecordFlag": 1}})
    r = await fetch_org_conf(_make_config(), app_token="tok", org_id="524288", http_client=mock)
    assert r.success is True and r.max_person == 50 and r.allowed_record_flag == 1


def test_sync_client_exposes_videoconference():
    sync = LansengerSyncClient(_make_config())
    assert hasattr(sync, "create_meeting")
    assert hasattr(sync, "modify_meeting")
    assert hasattr(sync, "fetch_meeting_list")
    assert hasattr(sync, "control_member")
    assert hasattr(sync, "fetch_org_videoconference_conf")
    # sync 封装的 modify_meeting 必须接受 user_stop_time（与 create_meeting 一致）
    assert "user_stop_time" in inspect.signature(sync.modify_meeting).parameters


@pytest.mark.asyncio
async def test_api_error_surfaces_in_error():
    mock = _mock_http_client({"errCode": 105107, "errMsg": "组织会议最大人数发生变更，请重新加入会议"})
    r = await cancel_meeting(
        _make_config(), app_token="tok", mid=1, org_id="524288",
        operator="u1", http_client=mock,
    )
    assert r.success is False and "105107" in (r.error or "") or r.error
