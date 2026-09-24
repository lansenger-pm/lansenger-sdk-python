"""Tests for the qingjia (请假 V2) SDK domain."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from lansenger_sdk.constants import API_ENDPOINTS
from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.models import (
    QingjiaAttendanceGroupListResult,
    QingjiaEnableLeaveTypeListResult,
    QingjiaMyApplyPageResult,
    QingjiaPersonBalanceResult,
    QingjiaRuleConfigListResult,
    QingjiaSaveApplyResult,
    QingjiaTimesResult,
    QingjiaUploadUrlResult,
)
from lansenger_sdk.qingjia import (
    fetch_qingjia_attendance_group_list,
    fetch_qingjia_enable_leave_type_list,
    fetch_qingjia_max_version_config_list,
    fetch_qingjia_my_apply_page_info,
    fetch_qingjia_person_balance,
    fetch_qingjia_save_apply,
    fetch_qingjia_times,
    fetch_qingjia_upload_url,
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


def test_qingjia_paths_carry_server_segment():
    for key in ("max_version_config_list", "times", "upload", "save_apply",
                "my_apply_page_info", "person_balance", "attendance_group_list",
                "enable_leave_type_list"):
        path = API_ENDPOINTS["qingjia"][key]
        assert path.startswith("/xtra/qingjia/server/openapi/v2/"), path


@pytest.mark.asyncio
async def test_max_version_config_list():
    mock = _mock_http_client({"errCode": 0, "data": [{"cmcCode": "C1"}]})
    r = await fetch_qingjia_max_version_config_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="s1",
        user_token="ut1", http_client=mock,
    )
    assert isinstance(r, QingjiaRuleConfigListResult)
    assert r.success is True and r.total == 1
    url = mock.post.call_args[0][0]
    assert "/xtra/qingjia/server/openapi/v2/maxVersionConfigList" in url
    assert "user_token=ut1" in url
    assert mock.post.call_args[1]["json"] == {"orgId": "org1", "staffId": "s1"}


@pytest.mark.asyncio
async def test_times_requires_fields():
    r = await fetch_qingjia_times(
        _make_config(), app_token="tok", cmc_code="", times_vo={"a": 1},
    )
    assert r.success is False and "cmc_code is required" in r.error

    r = await fetch_qingjia_times(
        _make_config(), app_token="tok", cmc_code="C1", times_vo={},
    )
    assert r.success is False and "times_vo is required" in r.error


@pytest.mark.asyncio
async def test_times_parses_result():
    data = {
        "errCode": 0,
        "data": {
            "typeCode": "T1",
            "applyStartTime": 100,
            "applyEndTime": 200,
            "effectiveHours": 8.0,
            "effectiveDays": 1.0,
            "effectiveTimestamp": 300,
            "timeStr": "1天",
        },
    }
    mock = _mock_http_client(data)
    r = await fetch_qingjia_times(
        _make_config(), app_token="tok", cmc_code="C1",
        times_vo={"beginTime": 100}, staff_id="s1", http_client=mock,
    )
    assert isinstance(r, QingjiaTimesResult)
    assert r.success is True and r.type_code == "T1"
    assert r.effective_hours == 8.0 and r.effective_days == 1.0
    assert r.time_str == "1天"
    body = mock.post.call_args[1]["json"]
    assert body["cmcCode"] == "C1" and body["timesVO"] == {"beginTime": 100}
    assert body["staffId"] == "s1"


@pytest.mark.asyncio
async def test_upload_url_requires_fields():
    r = await fetch_qingjia_upload_url(
        _make_config(), app_token="tok", file_name="", md5="m", size=1,
    )
    assert r.success is False and "file_name is required" in r.error

    r = await fetch_qingjia_upload_url(
        _make_config(), app_token="tok", file_name="a.pdf", md5="", size=1,
    )
    assert r.success is False and "md5 is required" in r.error


@pytest.mark.asyncio
async def test_upload_url_returns_value():
    mock = _mock_http_client({"errCode": 0, "data": "https://s3/upload"})
    r = await fetch_qingjia_upload_url(
        _make_config(), app_token="tok", file_name="a.pdf", md5="m1", size=12,
        org_id="org1", http_client=mock,
    )
    assert isinstance(r, QingjiaUploadUrlResult)
    assert r.success is True and r.value == "https://s3/upload"
    body = mock.post.call_args[1]["json"]
    assert body == {"fileName": "a.pdf", "md5": "m1", "size": 12, "orgId": "org1"}


@pytest.mark.asyncio
async def test_save_apply_requires_fields():
    r = await fetch_qingjia_save_apply(
        _make_config(), app_token="tok", cmc_code="", is_leave_back=False,
        apply_vo={"a": 1},
    )
    assert r.success is False and "cmc_code is required" in r.error

    r = await fetch_qingjia_save_apply(
        _make_config(), app_token="tok", cmc_code="C1", is_leave_back=None,
        apply_vo={"a": 1},
    )
    assert r.success is False and "is_leave_back is required" in r.error

    r = await fetch_qingjia_save_apply(
        _make_config(), app_token="tok", cmc_code="C1", is_leave_back=False,
        apply_vo={},
    )
    assert r.success is False and "apply_vo is required" in r.error


@pytest.mark.asyncio
async def test_save_apply_body():
    mock = _mock_http_client({"errCode": 0, "data": "APPLY001"})
    r = await fetch_qingjia_save_apply(
        _make_config(), app_token="tok", cmc_code="C1", is_leave_back=True,
        apply_vo={"startTime": 1}, staff_id="s1", http_client=mock,
    )
    assert isinstance(r, QingjiaSaveApplyResult)
    assert r.success is True and r.value == "APPLY001"
    body = mock.post.call_args[1]["json"]
    assert body["cmcCode"] == "C1" and body["isLeaveBack"] is True
    assert body["applyVO"] == {"startTime": 1} and body["staffId"] == "s1"


@pytest.mark.asyncio
async def test_my_apply_page_info_parses_v2_page():
    data = {
        "errCode": 0,
        "data": {
            "pageNo": 1,
            "pageSize": 10,
            "pages": 3,
            "total": 25,
            "result": [{"code": "A1"}],
            "hasNextPage": True,
        },
    }
    mock = _mock_http_client(data)
    r = await fetch_qingjia_my_apply_page_info(
        _make_config(), app_token="tok", cmc_code="C1",
        query_vo={"pageNo": 1}, is_diss=True, http_client=mock,
    )
    assert isinstance(r, QingjiaMyApplyPageResult)
    assert r.success is True
    assert r.page_no == 1 and r.page_size == 10 and r.pages == 3 and r.total == 25
    assert r.items == [{"code": "A1"}] and r.has_next_page is True
    body = mock.post.call_args[1]["json"]
    assert body["isDiss"] is True and body["queryVO"] == {"pageNo": 1}


@pytest.mark.asyncio
async def test_my_apply_page_info_requires_fields():
    r = await fetch_qingjia_my_apply_page_info(
        _make_config(), app_token="tok", cmc_code="", query_vo={},
    )
    assert r.success is False and "cmc_code is required" in r.error


@pytest.mark.asyncio
async def test_person_balance():
    data = {
        "errCode": 0,
        "data": {
            "staffId": "s1",
            "name": "张三",
            "phone": "13800000000",
            "employeeCode": "E1",
            "staffNo": "N1",
            "depName": "研发部",
            "balanceList": [{"typeCode": "T1", "balance": 5.0}],
        },
    }
    mock = _mock_http_client(data)
    r = await fetch_qingjia_person_balance(
        _make_config(), app_token="tok", org_id="org1", cmc_code="C1",
        type_code="T1", http_client=mock,
    )
    assert isinstance(r, QingjiaPersonBalanceResult)
    assert r.success is True and r.name == "张三" and r.dep_name == "研发部"
    assert r.balance_list == [{"typeCode": "T1", "balance": 5.0}]
    body = mock.post.call_args[1]["json"]
    assert body == {"orgId": "org1", "cmcCode": "C1", "typeCode": "T1"}


@pytest.mark.asyncio
async def test_person_balance_requires_fields():
    r = await fetch_qingjia_person_balance(
        _make_config(), app_token="tok", org_id="", cmc_code="C1",
    )
    assert r.success is False and "org_id is required" in r.error


@pytest.mark.asyncio
async def test_attendance_group_list_requires_org_id():
    r = await fetch_qingjia_attendance_group_list(
        _make_config(), app_token="tok", org_id="",
    )
    assert r.success is False and "org_id is required" in r.error


@pytest.mark.asyncio
async def test_attendance_group_list():
    mock = _mock_http_client({"errCode": 0, "data": [{"groupCode": "G1"}]})
    r = await fetch_qingjia_attendance_group_list(
        _make_config(), app_token="tok", org_id="org1", http_client=mock,
    )
    assert isinstance(r, QingjiaAttendanceGroupListResult)
    assert r.success is True and r.total == 1
    assert "/xtra/qingjia/server/openapi/v2/attendanceGroupList" in mock.post.call_args[0][0]


@pytest.mark.asyncio
async def test_enable_leave_type_list():
    mock = _mock_http_client({"errCode": 0, "data": [{"typeCode": "T1"}]})
    r = await fetch_qingjia_enable_leave_type_list(
        _make_config(), app_token="tok", cmc_code="C1", http_client=mock,
    )
    assert isinstance(r, QingjiaEnableLeaveTypeListResult)
    assert r.success is True and r.items == [{"typeCode": "T1"}]
    assert mock.post.call_args[1]["json"] == {"cmcCode": "C1"}


@pytest.mark.asyncio
async def test_enable_leave_type_list_requires_cmc_code():
    r = await fetch_qingjia_enable_leave_type_list(
        _make_config(), app_token="tok", cmc_code="",
    )
    assert r.success is False and "cmc_code is required" in r.error


@pytest.mark.asyncio
async def test_api_error_is_surfaced():
    mock = _mock_http_client({"errCode": 500, "errMsg": "boom"})
    r = await fetch_qingjia_max_version_config_list(
        _make_config(), app_token="tok", http_client=mock,
    )
    assert r.success is False and "errCode=500" in r.error
