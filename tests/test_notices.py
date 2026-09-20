"""Tests for Lansenger SDK notice (通知系统) module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.notices import (
    send_notice,
    fetch_notice_accounts,
    NOTICE_CONTENT_TYPE_TEXT,
    NOTICE_CONTENT_TYPE_LINK,
    NOTICE_USER_TYPE_PHONE,
    NOTICE_USER_TYPE_OPENID,
    NOTICE_RANGE_OBJ_TYPE_STAFF,
    NOTICE_RANGE_OBJ_TYPE_DEPARTMENT,
    NOTICE_PHONE_RANGE_MAX,
    NOTICE_OPEN_RANGE_MAX,
    NOTICE_REMIND_AFTER_TYPES,
    NOTICE_REMIND_RANGE_TYPES,
)
from lansenger_sdk.models import (
    NoticeSendResult,
    NoticeAccountListResult,
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


def _phone_kwargs():
    return dict(
        content="升级维护通知",
        release_phones=["13800138000", "13800138001"],
        create_mobile="13800138000",
    )


@pytest.mark.asyncio
async def test_send_notice_no_title():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="", content_type=1, account_code="ACC001", user_type=1, **_phone_kwargs())
    assert result.success is False
    assert "title is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_invalid_content_type():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=3, account_code="ACC001", user_type=1, **_phone_kwargs())
    assert result.success is False
    assert "content_type must be 1 (text) or 2 (link)" in result.error


@pytest.mark.asyncio
async def test_send_notice_text_requires_content():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, content="", release_phones=["1"], create_mobile="1")
    assert result.success is False
    assert "content is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_link_requires_notice_link():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=2, account_code="ACC001", user_type=1, notice_link="", release_phones=["1"], create_mobile="1")
    assert result.success is False
    assert "notice_link is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_no_account_code():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="", user_type=1, **_phone_kwargs())
    assert result.success is False
    assert "account_code is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_invalid_user_type():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=3, **_phone_kwargs())
    assert result.success is False
    assert "user_type must be 1 (phone) or 2 (openid)" in result.error


@pytest.mark.asyncio
async def test_send_notice_phone_requires_release_phones():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, content="c", release_phones=None, create_mobile="1")
    assert result.success is False
    assert "release_phones is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_phone_limit():
    config = _make_config()
    result = await send_notice(
        config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1,
        content="c", release_phones=[f"138{i:08d}" for i in range(NOTICE_PHONE_RANGE_MAX + 1)], create_mobile="1",
    )
    assert result.success is False
    assert "release_phones allows at most 10" in result.error


@pytest.mark.asyncio
async def test_send_notice_phone_requires_creator_identity():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, content="c", release_phones=["13800138000"], create_mobile="")
    assert result.success is False
    assert "create_mobile or create_user_id is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_openid_requires_release_range():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=2, content="c", release_range=None, create_user_id="staff-001")
    assert result.success is False
    assert "release_range is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_openid_requires_creator_identity():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=2, content="c", release_range=[{"objId": "s1", "objName": "张三", "objType": 1}], create_user_id="")
    assert result.success is False
    assert "create_mobile or create_user_id is required" in result.error


@pytest.mark.asyncio
async def test_send_notice_openid_user_token_does_not_replace_creator_identity():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"code": "NTC001", "noticeStatus": 2}})
    result = await send_notice(
        config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=2,
        content="c", release_range=[{"objId": "s1", "objName": "张三", "objType": 1}], create_user_id="",
        user_token="utok", http_client=mock_client,
    )
    assert result.success is False
    assert "create_mobile or create_user_id is required" in result.error
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_notice_invalid_remind_after_type():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, remind_after_type="hourly", **_phone_kwargs())
    assert result.success is False
    assert "remind_after_type must be one of" in result.error


@pytest.mark.asyncio
async def test_send_notice_invalid_remind_range_type():
    config = _make_config()
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, remind_range_type="some", **_phone_kwargs())
    assert result.success is False
    assert "remind_range_type must be one of" in result.error


@pytest.mark.asyncio
async def test_send_notice_success_phone():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "errMsg": "success",
        "data": {
            "code": "NTC20260917001",
            "id": 1001,
            "title": "系统升级通知",
            "noticeType": 1,
            "contentType": 1,
            "noticeStatus": 2,
            "confirmStatus": 0,
            "publishUserId": "staff-001",
            "publishUserName": "张三",
            "publishTime": 1672531200000,
        },
    })
    result = await send_notice(
        config, app_token="tok", title="系统升级通知", content_type=NOTICE_CONTENT_TYPE_TEXT,
        account_code="ACC001", user_type=NOTICE_USER_TYPE_PHONE,
        content="系统将于本周六进行升级维护",
        release_phones=["13800138000", "13800138001"],
        cc_phones=["13800138002"],
        create_mobile="13800138000",
        confirm_flag=1, remind_status=1, remind_msg_type="mobile", at_once_flag=1,
        http_client=mock_client,
    )
    assert result.success is True
    assert result.notice_code == "NTC20260917001"
    assert result.notice_status == 2
    assert result.publish_user_name == "张三"

    body = mock_client.post.call_args.kwargs["json"]
    assert body["phoneUserRange"]["releaseRangeList"] == ["13800138000", "13800138001"]
    assert body["phoneUserRange"]["ccRangeList"] == ["13800138002"]
    assert body["confirmFlag"] == 1
    assert "openUserRange" not in body


@pytest.mark.asyncio
async def test_send_notice_success_openid():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"code": "NTC002", "noticeStatus": 2}})
    result = await send_notice(
        config, app_token="tok", title="t", content_type=1, account_code="ACC001",
        user_type=NOTICE_USER_TYPE_OPENID, content="c",
        release_range=[{"objId": "dept-1", "objName": "研发部", "objType": NOTICE_RANGE_OBJ_TYPE_DEPARTMENT}],
        cc_staff_ids=["staff-002"],
        create_user_id="staff-001",
        http_client=mock_client,
    )
    assert result.success is True
    body = mock_client.post.call_args.kwargs["json"]
    assert body["openUserRange"]["releaseRangeList"][0]["objType"] == 2
    assert body["openUserRange"]["ccRangeList"] == ["staff-002"]
    assert "phoneUserRange" not in body


@pytest.mark.asyncio
async def test_send_notice_default_remind_status():
    """实测：缺失 remindStatus 服务端抛 errCode=-1，SDK 必须兜底填 0。"""
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"code": "NTC1"}})
    result = await send_notice(
        config, app_token="tok", title="t", content_type=1, account_code="ACC001",
        user_type=1, content="c", release_phones=["13800138000"], create_mobile="13800138000",
        http_client=mock_client,
    )
    assert result.success is True
    body = mock_client.post.call_args.kwargs["json"]
    assert body["remindStatus"] == 0
    # 实测：ccRangeList 缺失同样触发服务端 NPE，必须强制下发
    assert body["phoneUserRange"]["ccRangeList"] == []


@pytest.mark.asyncio
async def test_send_notice_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 3123, "errMsg": "人员不存在"})
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, **_phone_kwargs(), http_client=mock_client)
    assert result.success is False
    assert "errCode=3123" in result.error


@pytest.mark.asyncio
async def test_send_notice_http_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0})
    mock_client.post.side_effect = httpx.ConnectError("boom")
    result = await send_notice(config, app_token="tok", title="t", content_type=1, account_code="ACC001", user_type=1, **_phone_kwargs(), http_client=mock_client)
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_notice_accounts_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": [
            {"roleName": "行政通知", "officialNumberId": "1001", "code": "ACC001"},
            {"roleName": "安全通知", "officialNumberId": "1002", "code": "ACC002"},
        ],
    })
    result = await fetch_notice_accounts(config, app_token="tok", org_id="org-001", http_client=mock_client)
    assert result.success is True
    assert result.total == 2
    assert result.accounts[0]["code"] == "ACC001"

    body = mock_client.post.call_args.kwargs["json"]
    assert body == {"orgId": "org-001"}


@pytest.mark.asyncio
async def test_fetch_notice_accounts_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 40001, "errMsg": "Invalid token"})
    result = await fetch_notice_accounts(config, app_token="tok", http_client=mock_client)
    assert result.success is False
    assert "errCode=40001" in result.error


@pytest.mark.asyncio
async def test_client_send_notice_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.send_notice(title="", content_type=1, account_code="ACC001", user_type=1, content="c", release_phones=["1"], create_mobile="1")
    assert result.success is False
    assert "title is required" in result.error
    await client.close()


def test_notice_models_to_dict():
    result = NoticeSendResult(success=True, notice_code="NTC001", notice_status=2)
    d = result.to_dict()
    assert d["success"] is True
    assert d["notice_code"] == "NTC001"
    assert d["notice_status"] == 2
    assert "title" not in d
    assert "raw_response" not in d

    accounts = NoticeAccountListResult(success=True, total=1, accounts=[{"code": "ACC001"}])
    d2 = accounts.to_dict()
    assert d2["total"] == 1
    assert d2["accounts"] == [{"code": "ACC001"}]

    failed = NoticeSendResult(success=False, error="boom")
    assert failed.to_dict()["error"] == "boom"


def test_notice_constants():
    assert NOTICE_CONTENT_TYPE_TEXT == 1
    assert NOTICE_CONTENT_TYPE_LINK == 2
    assert NOTICE_USER_TYPE_PHONE == 1
    assert NOTICE_USER_TYPE_OPENID == 2
    assert NOTICE_RANGE_OBJ_TYPE_STAFF == 1
    assert NOTICE_RANGE_OBJ_TYPE_DEPARTMENT == 2
    assert NOTICE_PHONE_RANGE_MAX == 10
    assert NOTICE_OPEN_RANGE_MAX == 200
    assert set(NOTICE_REMIND_AFTER_TYPES) == {"never", "unOperate", "count"}
    assert set(NOTICE_REMIND_RANGE_TYPES) == {"all", "receiver", "partialRemind", "notReminder"}
