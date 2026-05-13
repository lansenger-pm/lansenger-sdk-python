"""Tests for Lansenger SDK user message channel (4.6.3 私聊消息)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.user_messages import send_user_message
from lansenger_sdk import LansengerClient, LansengerConfig, UserMessageResult


def _make_config():
    return LansengerConfig(app_id="id", app_secret="secret")


@pytest.mark.asyncio
async def test_send_user_message_no_user_token():
    config = _make_config()
    result = await send_user_message(
        config, app_token="token", user_token="",
        receiver_id="user1", msg_type="text",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "user_token is required" in result.error


@pytest.mark.asyncio
async def test_send_user_message_no_receiver_id():
    config = _make_config()
    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "receiver_id is required" in result.error


@pytest.mark.asyncio
async def test_send_user_message_no_msg_type():
    config = _make_config()
    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="user1", msg_type="",
        msg_data={"text": {"content": "hi"}},
    )
    assert result.success is False
    assert "msg_type is required" in result.error


@pytest.mark.asyncio
async def test_send_user_message_no_msg_data():
    config = _make_config()
    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="user1", msg_type="text",
        msg_data=None,
    )
    assert result.success is False
    assert "msg_data is required" in result.error


@pytest.mark.asyncio
async def test_send_user_message_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "msg456"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="staff456", msg_type="text",
        msg_data={"text": {"content": "你好"}},
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "msg456"


@pytest.mark.asyncio
async def test_send_user_message_with_common():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "msg789"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="staff456", msg_type="appCard",
        msg_data={"appCard": {"bodyTitle": "审批"}},
        common={"notifyType": 1},
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "msg789"

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["msgData"]["common"]["notifyType"] == 1


@pytest.mark.asyncio
async def test_send_user_message_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 50001,
        "errMsg": "user not found",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="staff456", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        http_client=mock_client,
    )
    assert result.success is False
    assert "API error (errCode=50001)" in result.error


@pytest.mark.asyncio
async def test_send_user_message_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("timeout"))

    result = await send_user_message(
        config, app_token="token", user_token="ut123",
        receiver_id="staff456", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        http_client=mock_client,
    )
    assert result.success is False
    assert "timeout" in result.error


@pytest.mark.asyncio
async def test_client_send_user_message_no_user_token():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_user_message(
        receiver_id="staff1", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        user_token="",
    )
    assert result.success is False
    assert "user_token is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_send_user_message_no_receiver_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_user_message(
        receiver_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        user_token="ut123",
    )
    assert result.success is False
    assert "receiver_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_user_message_result_to_dict():
    result = UserMessageResult(success=True, message_id="msg456")
    d = result.to_dict()
    assert d["success"] is True
    assert d["message_id"] == "msg456"