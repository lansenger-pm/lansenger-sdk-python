"""Tests for Lansenger SDK group message channel (4.6.2 群聊消息)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.group_messages import send_group_message
from lansenger_sdk import LansengerClient, LansengerConfig, SendMessageResult


def _make_config():
    return LansengerConfig(app_id="id", app_secret="secret")


@pytest.mark.asyncio
async def test_send_group_message_no_group_id():
    config = _make_config()
    result = await send_group_message(
        config, app_token="token",
        group_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_send_group_message_no_msg_type():
    config = _make_config()
    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "msg_type is required" in result.error


@pytest.mark.asyncio
async def test_send_group_message_no_msg_data():
    config = _make_config()
    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data=None,
    )
    assert result.success is False
    assert "msg_data is required" in result.error


@pytest.mark.asyncio
async def test_send_group_message_bot_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "grpmsg1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data={"text": {"content": "通知"}},
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "grpmsg1"
    assert result.operation == "group_message"


@pytest.mark.asyncio
async def test_send_group_message_human_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "grpmsg2"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data={"text": {"content": "我来处理"}},
        user_token="ut123",
        sender_id="staff456",
        outlines="[通知]张三: 我来处理",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "grpmsg2"

    call_args = mock_client.post.call_args
    url = call_args.kwargs.get("url") or call_args[0][0]
    assert "user_token=ut123" in url
    payload = call_args.kwargs.get("json")
    assert payload["senderId"] == "staff456"
    assert payload["outlines"] == "[通知]张三: 我来处理"


@pytest.mark.asyncio
async def test_send_group_message_with_reminder():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "grpmsg3"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    msg_data = {
        "text": {
            "content": "重要通知！",
            "reminder": {"all": True, "userIds": []},
        }
    }
    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data=msg_data,
        http_client=mock_client,
    )
    assert result.success is True

    payload = mock_client.post.call_args.kwargs.get("json")
    assert payload["msgData"]["text"]["reminder"]["all"] is True


@pytest.mark.asyncio
async def test_send_group_message_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 30001,
        "errMsg": "not in group",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        http_client=mock_client,
    )
    assert result.success is False
    assert "API error (errCode=30001)" in result.error


@pytest.mark.asyncio
async def test_send_group_message_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("timeout"))

    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        http_client=mock_client,
    )
    assert result.success is False
    assert "timeout" in result.error


@pytest.mark.asyncio
async def test_client_send_group_message_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "group_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_send_group_message_no_msg_type():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="grp1", msg_type="",
        msg_data={"appCard": {"bodyTitle": "hi"}},
    )
    assert result.success is False
    assert "msg_type is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_send_group_message_no_msg_data():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="grp1", msg_type="text",
        msg_data=None,
    )
    assert result.success is False
    assert "msg_data is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_send_group_message_app_card():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "grpmsg4"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_group_message(
        config, app_token="token",
        group_id="grp1", msg_type="appCard",
        msg_data={"appCard": {"bodyTitle": "Approval"}},
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "grpmsg4"