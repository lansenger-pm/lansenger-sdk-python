"""Tests for the jiaban (加班 V2) SDK domain."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from lansenger_sdk.constants import API_ENDPOINTS
from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.jiaban import (
    fetch_jiaban_calculate_duration,
    fetch_jiaban_get_group_info,
    fetch_jiaban_get_max_version_config_list,
    fetch_jiaban_get_my_apply_page_info,
    fetch_jiaban_submit_approve,
    fetch_jiaban_upload_url,
    put_jiaban_file,
)
from lansenger_sdk.models import (
    JiabanGroupListResult,
    JiabanCalculateDurationResult,
    JiabanMaxVersionConfigListResult,
    JiabanMyApplyPageResult,
    JiabanSubmitApproveResult,
    JiabanUploadUrlResult,
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


def _mock_put_client(status_code=200, raises=None):
    mock = AsyncMock(spec=httpx.AsyncClient)
    if raises is not None:
        mock.put.side_effect = raises
    else:
        resp = MagicMock()
        resp.status_code = status_code
        resp.reason_phrase = "Bad Request" if status_code >= 400 else "OK"
        mock.put.return_value = resp
    mock.aclose = AsyncMock()
    return mock


def test_jiaban_paths_carry_server_segment():
    for key in ("get_max_version_config_list", "upload", "submit_approve",
                "get_my_apply_page_info", "get_group_info", "calculate_duration"):
        path = API_ENDPOINTS["jiaban"][key]
        assert path.startswith("/xtra/jiaban/server/openapi/v2/"), path


@pytest.mark.asyncio
async def test_get_max_version_config_list_requires_fields():
    r = await fetch_jiaban_get_max_version_config_list(
        _make_config(), app_token="tok", org_id="", staff_id="s1",
    )
    assert r.success is False and "org_id is required" in r.error

    r = await fetch_jiaban_get_max_version_config_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="",
    )
    assert r.success is False and "staff_id is required" in r.error


@pytest.mark.asyncio
async def test_get_max_version_config_list():
    mock = _mock_http_client({"errCode": 0, "data": [{"cmcCode": "C1"}]})
    r = await fetch_jiaban_get_max_version_config_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="s1",
        http_client=mock,
    )
    assert isinstance(r, JiabanMaxVersionConfigListResult)
    assert r.success is True and r.total == 1
    assert "/xtra/jiaban/server/openapi/v2/getMaxVersionConfigList" in mock.post.call_args[0][0]
    assert mock.post.call_args[1]["json"] == {"orgId": "org1", "staffId": "s1"}


@pytest.mark.asyncio
async def test_upload_url_requires_fields():
    r = await fetch_jiaban_upload_url(
        _make_config(), app_token="tok", file_name="", md5="m", size=1, org_id="o",
    )
    assert r.success is False and "file_name is required" in r.error

    r = await fetch_jiaban_upload_url(
        _make_config(), app_token="tok", file_name="a.pdf", md5="m", size=1, org_id="",
    )
    assert r.success is False and "org_id is required" in r.error


@pytest.mark.asyncio
async def test_upload_url_returns_value():
    mock = _mock_http_client({"errCode": 0, "data": "https://s3/upload"})
    r = await fetch_jiaban_upload_url(
        _make_config(), app_token="tok", file_name="a.pdf", md5="m1", size=12,
        org_id="org1", http_client=mock,
    )
    assert isinstance(r, JiabanUploadUrlResult)
    assert r.success is True and r.value == "https://s3/upload"
    assert mock.post.call_args[1]["json"] == {
        "fileName": "a.pdf", "md5": "m1", "size": 12, "orgId": "org1",
    }


@pytest.mark.asyncio
async def test_put_jiaban_file_sends_content_md5():
    mock = _mock_put_client()
    ok, err = await put_jiaban_file(
        "https://s3/upload", b"hello", "5d41402abc4b2a76b9719d911017c592",
        http_client=mock,
    )
    assert ok is True and err is None
    kwargs = mock.put.call_args[1]
    assert kwargs["headers"]["Content-MD5"] == "5d41402abc4b2a76b9719d911017c592"
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
    assert kwargs["content"] == b"hello"


@pytest.mark.asyncio
async def test_put_jiaban_file_requires_args():
    ok, err = await put_jiaban_file("", b"hello", "m1")
    assert ok is False and err == "url is required"

    ok, err = await put_jiaban_file("https://s3/upload", b"hello", "")
    assert ok is False and err == "md5 is required"


@pytest.mark.asyncio
async def test_put_jiaban_file_http_error():
    mock = _mock_put_client(status_code=400)
    ok, err = await put_jiaban_file("https://s3/upload", b"hello", "m1", http_client=mock)
    assert ok is False and "HTTP error 400" in err


@pytest.mark.asyncio
async def test_put_jiaban_file_network_error():
    mock = _mock_put_client(raises=RuntimeError("connection reset"))
    ok, err = await put_jiaban_file("https://s3/upload", b"hello", "m1", http_client=mock)
    assert ok is False and "network error" in err


@pytest.mark.asyncio
async def test_submit_approve_requires_fields():
    base = dict(
        cmc_code="C1", applyer_id="s1", start_time=1, end_time=2, memo="m",
        approve_ids=["a1"], overtime_type=1, apply_type=1,
    )
    for field, msg in (
        ("cmc_code", "cmc_code is required"),
        ("applyer_id", "applyer_id is required"),
        ("memo", "memo is required"),
        ("approve_ids", "approve_ids is required"),
    ):
        kwargs = dict(base)
        kwargs[field] = "" if field != "approve_ids" else []
        r = await fetch_jiaban_submit_approve(_make_config(), app_token="tok", **kwargs)
        assert r.success is False and msg in r.error


@pytest.mark.asyncio
async def test_submit_approve_body():
    mock = _mock_http_client({"errCode": 0, "data": "APPLY001"})
    r = await fetch_jiaban_submit_approve(
        _make_config(), app_token="tok", cmc_code="C1", applyer_id="s1",
        start_time=100, end_time=200, memo="加班", approve_ids=["a1"],
        overtime_type=1, apply_type=2, apply_vo={"reason": "x"}, http_client=mock,
    )
    assert isinstance(r, JiabanSubmitApproveResult)
    assert r.success is True and r.value == "APPLY001"
    body = mock.post.call_args[1]["json"]
    assert body["cmcCode"] == "C1" and body["applyerId"] == "s1"
    assert body["startTime"] == 100 and body["endTime"] == 200
    assert body["approveIds"] == ["a1"] and body["overtimeType"] == 1
    assert body["applyType"] == 2 and body["reason"] == "x"


@pytest.mark.asyncio
async def test_get_my_apply_page_info_parses_v2_page():
    data = {
        "errCode": 0,
        "data": {
            "pageNo": 2,
            "pageSize": 20,
            "pages": 4,
            "total": 60,
            "result": [{"code": "A1"}],
            "hasNextPage": False,
        },
    }
    mock = _mock_http_client(data)
    r = await fetch_jiaban_get_my_apply_page_info(
        _make_config(), app_token="tok", cmc_code="C1",
        page_vo={"pageNo": 2, "creatorId": "s1"}, http_client=mock,
    )
    assert isinstance(r, JiabanMyApplyPageResult)
    assert r.success is True
    assert r.page_no == 2 and r.page_size == 20 and r.total == 60
    assert r.items == [{"code": "A1"}] and r.has_next_page is False
    body = mock.post.call_args[1]["json"]
    assert body == {"cmcCode": "C1", "pageNo": 2, "creatorId": "s1"}


@pytest.mark.asyncio
async def test_get_my_apply_page_info_requires_fields():
    r = await fetch_jiaban_get_my_apply_page_info(
        _make_config(), app_token="tok", cmc_code="", page_vo={},
    )
    assert r.success is False and "cmc_code is required" in r.error


@pytest.mark.asyncio
async def test_get_group_info():
    mock = _mock_http_client({"errCode": 0, "data": [{"groupCode": "G1"}]})
    r = await fetch_jiaban_get_group_info(
        _make_config(), app_token="tok", staff_id="s1", org_id="org1",
        http_client=mock,
    )
    assert isinstance(r, JiabanGroupListResult)
    assert r.success is True and r.total == 1
    assert "/xtra/jiaban/server/openapi/v2/getGroupInfo" in mock.post.call_args[0][0]
    assert mock.post.call_args[1]["json"] == {"staffId": "s1", "orgId": "org1"}


@pytest.mark.asyncio
async def test_get_group_info_requires_fields():
    r = await fetch_jiaban_get_group_info(
        _make_config(), app_token="tok", staff_id="", org_id="org1",
    )
    assert r.success is False and "staff_id is required" in r.error


@pytest.mark.asyncio
async def test_calculate_duration():
    mock = _mock_http_client({"errCode": 0, "data": 3.5})
    r = await fetch_jiaban_calculate_duration(
        _make_config(), app_token="tok", cmc_code="C1", begin_time=100,
        end_time=200, group_code="G1", http_client=mock,
    )
    assert isinstance(r, JiabanCalculateDurationResult)
    assert r.success is True and r.value == 3.5
    assert mock.post.call_args[1]["json"] == {
        "cmcCode": "C1", "beginTime": 100, "endTime": 200, "groupCode": "G1",
    }


@pytest.mark.asyncio
async def test_calculate_duration_requires_fields():
    r = await fetch_jiaban_calculate_duration(
        _make_config(), app_token="tok", cmc_code="", begin_time=1, end_time=2,
    )
    assert r.success is False and "cmc_code is required" in r.error


@pytest.mark.asyncio
async def test_api_error_is_surfaced():
    mock = _mock_http_client({"errCode": 500, "errMsg": "boom"})
    r = await fetch_jiaban_calculate_duration(
        _make_config(), app_token="tok", cmc_code="C1", begin_time=1, end_time=2,
        http_client=mock,
    )
    assert r.success is False and "errCode=500" in r.error
