"""Tests for Lansenger SDK contacts/staff API module functions."""

import json

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.contacts import (
    fetch_staff_basic_info,
    fetch_staff_detail,
    fetch_department_ancestors,
    fetch_staff_id_mapping,
    fetch_org_extra_field_ids,
    search_staff,
)
from lansenger_sdk.models import (
    StaffBasicInfoResult,
    StaffDetailResult,
    DepartmentAncestorsResult,
    StaffIdMappingResult,
    ExtraFieldIdsResult,
    StaffSearchResult,
)

from unittest.mock import AsyncMock, patch, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
    )


@pytest.mark.asyncio
async def test_fetch_staff_basic_info_no_staff_id():
    config = _make_config()
    result = await fetch_staff_basic_info(config, app_token="tok", staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_basic_info_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "orgId": "org1",
            "orgName": "MyOrg",
            "name": "Alice",
            "gender": 1,
            "signature": "Hello",
            "avatarUrl": "https://avatar.url",
            "avatarId": "av1",
            "status": 1,
            "departments": [{"departmentId": "d1"}],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_staff_basic_info(
        config, app_token="tok", staff_id="staff1", http_client=mock_client,
    )
    assert result.success is True
    assert result.org_id == "org1"
    assert result.name == "Alice"
    assert result.gender == 1


@pytest.mark.asyncio
async def test_fetch_staff_basic_info_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10001,
        "errMsg": "staff not found",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_staff_basic_info(
        config, app_token="tok", staff_id="bad_id", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10001" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_detail_no_staff_id():
    config = _make_config()
    result = await fetch_staff_detail(config, app_token="tok", staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_detail_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "name": "Bob",
            "orgId": "org1",
            "orgName": "MyOrg",
            "email": "bob@org.com",
            "employeeNumber": "E001",
            "mobilePhone": {"phoneNumber": "13800138000"},
            "loginName": "bob_login",
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_staff_detail(
        config, app_token="tok", staff_id="staff2", user_token="ut1",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.name == "Bob"
    assert result.email == "bob@org.com"
    assert result.employee_number == "E001"


@pytest.mark.asyncio
async def test_fetch_department_ancestors_no_staff_id():
    config = _make_config()
    result = await fetch_department_ancestors(config, app_token="tok", staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_ancestors_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": [
            {"ancestorDepartments": [
                {"departmentId": "root", "departmentName": "Root Dept"},
                {"departmentId": "sub", "departmentName": "Sub Dept"},
            ]},
        ],
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_ancestors(
        config, app_token="tok", staff_id="staff1", http_client=mock_client,
    )
    assert result.success is True
    assert len(result.ancestor_groups) == 1
    assert len(result.ancestor_groups[0]) == 2
    assert result.ancestor_groups[0][0]["departmentId"] == "root"


@pytest.mark.asyncio
async def test_fetch_staff_id_mapping_validation():
    config = _make_config()
    result = await fetch_staff_id_mapping(config, app_token="tok", org_id="", id_type="mobile", id_value="123")
    assert result.success is False
    assert "org_id is required" in result.error

    result = await fetch_staff_id_mapping(config, app_token="tok", org_id="org1", id_type="", id_value="123")
    assert result.success is False
    assert "id_type is required" in result.error

    result = await fetch_staff_id_mapping(config, app_token="tok", org_id="org1", id_type="mobile", id_value="")
    assert result.success is False
    assert "id_value is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_id_mapping_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"staffId": "mapped_staff1"},
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_staff_id_mapping(
        config, app_token="tok", org_id="org1", id_type="mobile",
        id_value="13800138000", http_client=mock_client,
    )
    assert result.success is True
    assert result.staff_id == "mapped_staff1"


@pytest.mark.asyncio
async def test_fetch_org_extra_field_ids_no_org_id():
    config = _make_config()
    result = await fetch_org_extra_field_ids(config, app_token="tok", org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_org_extra_field_ids_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "hasMore": False,
            "total": 2,
            "extraFieldIds": [
                {"extraFieldId": "ef1"},
                {"extraFieldId": "ef2"},
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_org_extra_field_ids(
        config, app_token="tok", org_id="org1", http_client=mock_client,
    )
    assert result.success is True
    assert result.has_more is False
    assert result.total == 2
    assert len(result.extra_field_ids) == 2


@pytest.mark.asyncio
async def test_search_staff_no_keyword():
    config = _make_config()
    result = await search_staff(config, app_token="tok", keyword="")
    assert result.success is False
    assert "keyword is required" in result.error


@pytest.mark.asyncio
async def test_search_staff_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "hasMore": False,
            "total": 1,
            "staffInfo": [{"staffId": "s1", "name": "Alice"}],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await search_staff(
        config, app_token="tok", keyword="Alice", user_token="ut1",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.total == 1
    assert result.staff_info[0]["staffId"] == "s1"


@pytest.mark.asyncio
async def test_search_staff_with_sector_ids():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"hasMore": False, "total": 0, "staffInfo": []},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await search_staff(
        config, app_token="tok", keyword="Bob",
        user_id="staff1", sector_ids=["d1", "d2"],
        recursive=False, http_client=mock_client,
    )
    assert result.success is True

    call_args = mock_client.post.call_args
    body = call_args.kwargs.get("json") or call_args[1].get("json")
    assert body["keyword"] == "Bob"
    assert body["recursive"] is False
    assert body["searchScope"]["sectorIds"] == ["d1", "d2"]


@pytest.mark.asyncio
async def test_fetch_staff_basic_info_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_staff_basic_info(
        config, app_token="tok", staff_id="staff1", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error