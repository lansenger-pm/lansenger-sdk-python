"""Tests for Lansenger SDK department API module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.departments import (
    fetch_department_detail,
    fetch_department_children,
    fetch_department_staffs,
)
from lansenger_sdk.models import (
    DepartmentDetailResult,
    DepartmentChildrenResult,
    DepartmentStaffsResult,
)

from unittest.mock import AsyncMock, patch, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
    )


@pytest.mark.asyncio
async def test_fetch_department_detail_no_department_id():
    config = _make_config()
    result = await fetch_department_detail(config, app_token="tok", department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_detail_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "id": "524288-0",
            "name": "Root Department",
            "externalId": "ext1",
            "parentId": "0",
            "order": 1.0,
            "hasChildren": True,
            "normalMembers": 50,
            "inactiveMembers": 3,
            "frozenMembers": 1,
            "deletedMembers": 0,
            "tags": ["tag1"],
            "ancestorDepartments": [{"departmentId": "root", "departmentName": "Root"}],
            "leaders": ["leader1"],
            "emails": ["dept@org.com"],
            "phones": ["13800138000"],
            "addresses": ["Building A"],
            "introductions": ["Main department"],
            "deptType": 1,
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_detail(
        config, app_token="tok", department_id="524288-0",
        user_token="ut1", tag_id="tag1", http_client=mock_client,
    )
    assert result.success is True
    assert result.id == "524288-0"
    assert result.name == "Root Department"
    assert result.external_id == "ext1"
    assert result.parent_id == "0"
    assert result.has_children is True
    assert result.normal_members == 50
    assert result.leaders == ["leader1"]
    assert result.dept_type == 1


@pytest.mark.asyncio
async def test_fetch_department_detail_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10001,
        "errMsg": "department not found",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_detail(
        config, app_token="tok", department_id="bad_id", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10001" in result.error


@pytest.mark.asyncio
async def test_fetch_department_detail_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_department_detail(
        config, app_token="tok", department_id="524288-0", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_department_children_no_department_id():
    config = _make_config()
    result = await fetch_department_children(config, app_token="tok", department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_children_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "departments": [
                {"id": "child1", "name": "Child Dept 1"},
                {"id": "child2", "name": "Child Dept 2"},
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_children(
        config, app_token="tok", department_id="524288-0",
        user_token="ut1", http_client=mock_client,
    )
    assert result.success is True
    assert len(result.departments) == 2
    assert result.departments[0]["id"] == "child1"
    assert result.departments[1]["name"] == "Child Dept 2"


@pytest.mark.asyncio
async def test_fetch_department_children_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10002,
        "errMsg": "permission denied",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_children(
        config, app_token="tok", department_id="524288-0", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10002" in result.error


@pytest.mark.asyncio
async def test_fetch_department_children_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_department_children(
        config, app_token="tok", department_id="524288-0", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_department_staffs_no_department_id():
    config = _make_config()
    result = await fetch_department_staffs(config, app_token="tok", department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_staffs_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "hasMore": True,
            "total": 50,
            "staffs": [
                {"staffId": "s1", "name": "Alice"},
                {"staffId": "s2", "name": "Bob"},
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_staffs(
        config, app_token="tok", department_id="524288-0",
        user_token="ut1", page=1, page_size=100, http_client=mock_client,
    )
    assert result.success is True
    assert result.has_more is True
    assert result.total == 50
    assert len(result.staffs) == 2
    assert result.staffs[0]["staffId"] == "s1"


@pytest.mark.asyncio
async def test_fetch_department_staffs_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10003,
        "errMsg": "token expired",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_department_staffs(
        config, app_token="tok", department_id="524288-0", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10003" in result.error


@pytest.mark.asyncio
async def test_fetch_department_staffs_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_department_staffs(
        config, app_token="tok", department_id="524288-0", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error