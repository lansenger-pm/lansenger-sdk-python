"""Tests for Lansenger SDK groups V2 API module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.groups import (
    create_group,
    fetch_group_info,
    fetch_group_members,
    fetch_group_list,
    check_is_in_group,
)
from lansenger_sdk.models import (
    CreateGroupResult,
    GroupInfoResult,
    GroupListResult,
    GroupMemberResult,
    IsInGroupResult,
)

from unittest.mock import AsyncMock, patch, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
    )


@pytest.mark.asyncio
async def test_create_group_no_name():
    config = _make_config()
    result = await create_group(config, app_token="tok", name="", org_id="org1")
    assert result.success is False
    assert "name is required" in result.error


@pytest.mark.asyncio
async def test_create_group_no_org_id():
    config = _make_config()
    result = await create_group(config, app_token="tok", name="MyGroup", org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_create_group_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "groupId": "grp1",
            "totalMembers": 5,
            "invalidStaff": ["bad_staff1"],
            "invalidDepartment": ["bad_dept1"],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await create_group(
        config, app_token="tok", name="MyGroup", org_id="org1",
        staff_id_list=["s1", "s2"], department_id_list=["d1"],
        http_client=mock_client,
    )
    assert result.success is True
    assert result.group_id == "grp1"
    assert result.total_members == 5
    assert result.invalid_staff == ["bad_staff1"]
    assert result.invalid_department == ["bad_dept1"]


@pytest.mark.asyncio
async def test_create_group_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10001,
        "errMsg": "group creation failed",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await create_group(
        config, app_token="tok", name="MyGroup", org_id="org1",
        http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10001" in result.error


@pytest.mark.asyncio
async def test_create_group_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await create_group(
        config, app_token="tok", name="MyGroup", org_id="org1",
        http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_group_info_no_group_id():
    config = _make_config()
    result = await fetch_group_info(config, app_token="tok", group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_group_info_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "name": "TestGroup",
            "description": "A test group",
            "avatarId": "av1",
            "avatarUrl": "https://avatar.url",
            "owner": {"staffId": "owner1"},
            "creator": {"staffId": "creator1"},
            "state": 1,
            "manageMode": 0,
            "locationShare": 0,
            "needsConfirm": 0,
            "isPublic": 0,
            "maxMembers": 500,
            "maxHistoryMsgCount": 1000,
            "totalMembers": 10,
            "remindAll": True,
            "sendMsgStatus": True,
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_info(
        config, app_token="tok", group_id="grp1", http_client=mock_client,
    )
    assert result.success is True
    assert result.name == "TestGroup"
    assert result.description == "A test group"
    assert result.total_members == 10
    assert result.state == 1


@pytest.mark.asyncio
async def test_fetch_group_info_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10002,
        "errMsg": "group not found",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_info(
        config, app_token="tok", group_id="bad_grp", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10002" in result.error


@pytest.mark.asyncio
async def test_fetch_group_info_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_group_info(
        config, app_token="tok", group_id="grp1", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_group_members_no_group_id():
    config = _make_config()
    result = await fetch_group_members(config, app_token="tok", group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_group_members_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "totalMembers": 3,
            "members": [
                {"staffId": "s1", "name": "Alice"},
                {"staffId": "s2", "name": "Bob"},
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_members(
        config, app_token="tok", group_id="grp1",
        page_offset=0, page_size=100, http_client=mock_client,
    )
    assert result.success is True
    assert result.total_members == 3
    assert len(result.members) == 2
    assert result.members[0]["staffId"] == "s1"


@pytest.mark.asyncio
async def test_fetch_group_members_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10003,
        "errMsg": "permission denied",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_members(
        config, app_token="tok", group_id="grp1", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10003" in result.error


@pytest.mark.asyncio
async def test_fetch_group_members_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_group_members(
        config, app_token="tok", group_id="grp1", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_group_list_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "totalGroupIds": 2,
            "groupIds": ["grp1", "grp2"],
        },
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_list(
        config, app_token="tok", page_offset=0, page_size=100,
        http_client=mock_client,
    )
    assert result.success is True
    assert result.total_group_ids == 2
    assert result.group_ids == ["grp1", "grp2"]


@pytest.mark.asyncio
async def test_fetch_group_list_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10004,
        "errMsg": "token expired",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await fetch_group_list(
        config, app_token="tok", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10004" in result.error


@pytest.mark.asyncio
async def test_fetch_group_list_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_group_list(
        config, app_token="tok", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_check_is_in_group_no_group_id():
    config = _make_config()
    result = await check_is_in_group(config, app_token="tok", group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_check_is_in_group_true():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"isInGroup": True},
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await check_is_in_group(
        config, app_token="tok", group_id="grp1",
        staff_id="s1", http_client=mock_client,
    )
    assert result.success is True
    assert result.is_in_group is True


@pytest.mark.asyncio
async def test_check_is_in_group_false():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"isInGroup": False},
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await check_is_in_group(
        config, app_token="tok", group_id="grp1",
        staff_id="s_unknown", http_client=mock_client,
    )
    assert result.success is True
    assert result.is_in_group is False


@pytest.mark.asyncio
async def test_check_is_in_group_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10005,
        "errMsg": "invalid group",
    })
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)

    result = await check_is_in_group(
        config, app_token="tok", group_id="bad_grp", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10005" in result.error


@pytest.mark.asyncio
async def test_check_is_in_group_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await check_is_in_group(
        config, app_token="tok", group_id="grp1", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error