"""Tests for Lansenger SDK bot message channel client validation."""

import pytest

from lansenger_sdk import LansengerClient


@pytest.mark.asyncio
async def test_send_bot_message_no_chat_ids_or_department_ids():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_bot_message(
        msg_type="text", msg_data={"text": {"content": "hi"}},
        chat_ids=None, department_ids=None,
    )
    assert result.success is False
    assert "at least one of chat_ids or department_ids is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_send_bot_message_no_msg_type():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_bot_message(
        msg_type="", msg_data={"text": {"content": "hi"}},
        chat_ids=["user1"],
    )
    assert result.success is False
    assert "msg_type is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_send_bot_message_no_msg_data():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_bot_message(
        msg_type="text", msg_data=None,
        chat_ids=["user1"],
    )
    assert result.success is False
    assert "msg_data is required" in result.error
    await client.close()