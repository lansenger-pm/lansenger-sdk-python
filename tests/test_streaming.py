"""Tests for Lansenger SDK streaming (SSE) message API module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.streaming import (
    create_stream_message,
    fetch_stream_message,
)
from lansenger_sdk.models import StreamMessageResult

from unittest.mock import AsyncMock, patch, MagicMock


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
    )


@pytest.mark.asyncio
async def test_create_stream_message_no_receiver_id():
    config = _make_config()
    result = await create_stream_message(
        config, app_token="tok", receiver_id="", receiver_type="staff", stream_id="s1",
    )
    assert result.success is False
    assert "receiver_id is required" in result.error


@pytest.mark.asyncio
async def test_create_stream_message_no_receiver_type():
    config = _make_config()
    result = await create_stream_message(
        config, app_token="tok", receiver_id="r1", receiver_type="", stream_id="s1",
    )
    assert result.success is False
    assert "receiver_type is required" in result.error


@pytest.mark.asyncio
async def test_create_stream_message_no_stream_id():
    config = _make_config()
    result = await create_stream_message(
        config, app_token="tok", receiver_id="r1", receiver_type="staff", stream_id="",
    )
    assert result.success is False
    assert "stream_id is required" in result.error


@pytest.mark.asyncio
async def test_create_stream_message_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "msg_stream_1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await create_stream_message(
        config, app_token="tok", receiver_id="r1",
        receiver_type="staff", stream_id="stream1",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "msg_stream_1"

    call_args = mock_client.post.call_args
    body = call_args.kwargs.get("json") or call_args[1].get("json")
    assert body["receiverId"] == "r1"
    assert body["receiverType"] == "staff"
    assert body["streamId"] == "stream1"


@pytest.mark.asyncio
async def test_create_stream_message_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10001,
        "errMsg": "stream creation failed",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await create_stream_message(
        config, app_token="tok", receiver_id="r1",
        receiver_type="staff", stream_id="stream1",
        http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10001" in result.error


@pytest.mark.asyncio
async def test_create_stream_message_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await create_stream_message(
        config, app_token="tok", receiver_id="r1",
        receiver_type="staff", stream_id="stream1",
        http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_fetch_stream_message_no_msg_id():
    config = _make_config()
    result = await fetch_stream_message(config, app_token="tok", msg_id="")
    assert result.success is False
    assert "msg_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_stream_message_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "msg_fetch_1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_stream_message(
        config, app_token="tok", msg_id="msg1", http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "msg_fetch_1"

    call_args = mock_client.post.call_args
    body = call_args.kwargs.get("json") or call_args[1].get("json")
    assert body["msgId"] == "msg1"


@pytest.mark.asyncio
async def test_fetch_stream_message_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 10002,
        "errMsg": "message not found",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await fetch_stream_message(
        config, app_token="tok", msg_id="bad_msg", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10002" in result.error


@pytest.mark.asyncio
async def test_fetch_stream_message_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    result = await fetch_stream_message(
        config, app_token="tok", msg_id="msg1", http_client=mock_client,
    )
    assert result.success is False
    assert "HTTP error" in result.error


@pytest.mark.asyncio
async def test_client_create_stream_message_no_receiver_id():
    from lansenger_sdk import LansengerClient
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.create_stream_message(
        receiver_id="", receiver_type="staff", stream_id="s1",
    )
    assert result.success is False
    assert "receiver_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_create_stream_message_invalid_receiver_type():
    from lansenger_sdk import LansengerClient
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.create_stream_message(
        receiver_id="r1", receiver_type="invalid", stream_id="s1",
    )
    assert result.success is False
    assert "receiver_type must be 'staff' or 'group'" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_create_stream_message_no_stream_id():
    from lansenger_sdk import LansengerClient
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.create_stream_message(
        receiver_id="r1", receiver_type="staff", stream_id="",
    )
    assert result.success is False
    assert "stream_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_fetch_stream_message_no_msg_id():
    from lansenger_sdk import LansengerClient
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_stream_message(msg_id="")
    assert result.success is False
    assert "msg_id is required" in result.error
    await client.close()
