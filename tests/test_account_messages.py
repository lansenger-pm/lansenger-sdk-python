"""Tests for Lansenger SDK account message channel (4.6.1 公号通道)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.account_messages import send_account_message
from lansenger_sdk import LansengerClient, LansengerConfig, AccountMessageResult


def _make_config():
    return LansengerConfig(app_id="id", app_secret="secret")


@pytest.mark.asyncio
async def test_send_account_message_no_chat_ids_or_department_ids():
    config = _make_config()
    result = await send_account_message(
        config, app_token="token",
        msg_type="text", msg_data={"text": {"content": "hi"}},
        chat_ids=None, department_ids=None,
    )
    assert result.success is False
    assert "at least one of chat_ids or department_ids" in result.error


@pytest.mark.asyncio
async def test_send_account_message_no_msg_type():
    config = _make_config()
    result = await send_account_message(
        config, app_token="token",
        msg_type="", msg_data={"text": {"content": "hi"}},
        chat_ids=["user1"],
    )
    assert result.success is False
    assert "msg_type is required" in result.error


@pytest.mark.asyncio
async def test_send_account_message_no_msg_data():
    config = _make_config()
    result = await send_account_message(
        config, app_token="token",
        msg_type="text", msg_data=None,
        chat_ids=["user1"],
    )
    assert result.success is False
    assert "msg_data is required" in result.error


@pytest.mark.asyncio
async def test_send_account_message_success():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {
            "msgId": "msg123",
            "invalidStaff": [],
            "invalidDepartment": [],
        },
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_account_message(
        config, app_token="token",
        msg_type="text", msg_data={"text": {"content": "通知"}},
        chat_ids=["user1", "user2"],
        department_ids=["dept1"],
        account_id="524288-xxxx",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.message_id == "msg123"
    assert result.invalid_staff == []
    assert result.invalid_department == []


@pytest.mark.asyncio
async def test_send_account_message_api_error():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 40001,
        "errMsg": "invalid parameter",
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    result = await send_account_message(
        config, app_token="token",
        msg_type="text", msg_data={"text": {"content": "hi"}},
        chat_ids=["user1"],
        http_client=mock_client,
    )
    assert result.success is False
    assert "API error (errCode=40001)" in result.error


@pytest.mark.asyncio
async def test_send_account_message_http_error():
    config = _make_config()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=Exception("connection failed"))

    result = await send_account_message(
        config, app_token="token",
        msg_type="text", msg_data={"text": {"content": "hi"}},
        chat_ids=["user1"],
        http_client=mock_client,
    )
    assert result.success is False
    assert "connection failed" in result.error


@pytest.mark.asyncio
async def test_client_send_account_message_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_account_message(
        msg_type="text", msg_data={"text": {"content": "hi"}},
        chat_ids=None, department_ids=None,
    )
    assert result.success is False
    assert "at least one of chat_ids or department_ids" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_send_account_message_no_msg_type():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_account_message(
        msg_type="", msg_data={"text": {"content": "hi"}},
        chat_ids=["user1"],
    )
    assert result.success is False
    assert "msg_type is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_account_message_result_to_dict():
    result = AccountMessageResult(
        success=True, message_id="msg123",
        invalid_staff=["bad1"], invalid_department=["bad2"],
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["message_id"] == "msg123"
    assert d["invalid_staff"] == ["bad1"]
    assert d["invalid_department"] == ["bad2"]