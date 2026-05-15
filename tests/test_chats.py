"""Tests for Lansenger SDK chat APIs (4.24 MCP)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.chats import fetch_chat_list, fetch_chat_messages
from lansenger_sdk import LansengerClient, LansengerConfig


def _make_config():
    return LansengerConfig(app_id="id", app_secret="secret")


@pytest.mark.asyncio
async def test_fetch_chat_messages_no_staff_or_group():
    config = _make_config()
    result = await fetch_chat_messages(config, app_token="token")
    assert result.success is False
    assert "staff_id or group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_chat_messages_no_staff_or_group_via_client():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_chat_messages()
    assert result.success is False
    assert "staff_id or group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_chat_list_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "staffIdInfos": [
                {"staffId": "sid1", "staffName": "Alice", "sectorName": ["Dept A"]},
            ],
            "groupIdInfos": [
                {"groupId": "gid1", "groupName": "Team Chat"},
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_list(
        config, app_token="token", http_client=mock_client,
    )
    assert result.success is True
    assert len(result.staff_infos) == 1
    assert result.staff_infos[0].staff_id == "sid1"
    assert result.staff_infos[0].staff_name == "Alice"
    assert len(result.group_infos) == 1
    assert result.group_infos[0].group_id == "gid1"
    assert result.group_infos[0].group_name == "Team Chat"


@pytest.mark.asyncio
async def test_fetch_chat_list_with_user_token():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "staffIdInfos": [],
            "groupIdInfos": [],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_list(
        config, app_token="token", user_token="ut1", http_client=mock_client,
    )
    assert result.success is True

    call_args = mock_client.post.call_args
    url = call_args.kwargs.get("url") or call_args[0][0] or call_args.args[0]
    assert "user_token=ut1" in url


@pytest.mark.asyncio
async def test_fetch_chat_list_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 63001,
        "errMsg": "获取会话列表失败",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_list(
        config, app_token="token", http_client=mock_client,
    )
    assert result.success is False
    assert "63001" in result.error


@pytest.mark.asyncio
async def test_fetch_chat_messages_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "total": 2,
            "hasMore": False,
            "lastVersion": "v100",
            "name": "Alice",
            "chatType": "private",
            "messageList": [
                {
                    "name": "Alice",
                    "chatType": "private",
                    "messageInfo": {
                        "sendTime": "2025-11-04 10:30:00",
                        "sender": "Alice",
                        "type": "text",
                        "content": {"text": "Hello", "attachments": []},
                    },
                },
                {
                    "name": "Alice",
                    "chatType": "private",
                    "messageInfo": {
                        "sendTime": "2025-11-04 10:31:00",
                        "sender": "Me",
                        "type": "text",
                        "content": {"text": "Hi there"},
                    },
                },
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_messages(
        config, app_token="token", staff_id="sid1", http_client=mock_client,
    )
    assert result.success is True
    assert result.has_more is False
    assert result.total == 2
    assert result.last_version == "v100"
    assert result.name == "Alice"
    assert result.chat_type == "private"
    assert len(result.messages) == 2
    assert result.messages[0].sender == "Alice"
    assert result.messages[0].message_type == "text"
    assert result.messages[0].content["text"] == "Hello"


@pytest.mark.asyncio
async def test_fetch_chat_messages_group():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "total": 1,
            "hasMore": True,
            "lastVersion": "v50",
            "name": "Team Chat",
            "chatType": "group",
            "messageList": [
                {
                    "name": "Team Chat",
                    "chatType": "group",
                    "messageInfo": {
                        "sendTime": "2025-11-04 11:00:00",
                        "sender": "Bob",
                        "type": "text",
                        "content": {"text": "通知"},
                    },
                },
            ],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_messages(
        config, app_token="token", group_id="gid1", http_client=mock_client,
    )
    assert result.success is True
    assert result.has_more is True
    assert result.chat_type == "group"
    assert len(result.messages) == 1

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["groupId"] == "gid1"


@pytest.mark.asyncio
async def test_fetch_chat_messages_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 63002,
        "errMsg": "参数错误",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_chat_messages(
        config, app_token="token", staff_id="sid1", http_client=mock_client,
    )
    assert result.success is False
    assert "63002" in result.error


@pytest.mark.asyncio
async def test_fetch_chat_messages_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("timeout"))

    result = await fetch_chat_messages(
        config, app_token="token", staff_id="sid1", http_client=mock_client,
    )
    assert result.success is False
    assert "timeout" in result.error