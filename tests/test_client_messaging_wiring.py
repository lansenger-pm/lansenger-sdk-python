"""Dual-surface wiring for the 1.13.0 messaging additions (4.6.17 / 4.6.4.14).

The client wrappers must reject bad arguments locally — before a token request —
and the sync wrappers must expose the same two entry points.
"""

import pytest

from lansenger_sdk import LansengerClient, LansengerSyncClient
from lansenger_sdk.message_replies import validate_reply_request


@pytest.mark.asyncio
async def test_client_reply_message_rejects_bad_arguments_locally():
    client = LansengerClient(app_id="id", app_secret="sec")
    try:
        missing = await client.reply_message("", emoji_id="TYPE_OK")
        assert missing.success is False
        assert missing.error == "msg_id is required"

        bad_emoji = await client.reply_message("m-1", emoji_id="TYPE_NOPE")
        assert bad_emoji.success is False
        assert "invalid emoji_id" in (bad_emoji.error or "")

        bad_type = await client.reply_message("m-1", emoji_id="TYPE_OK", reply_type=7)
        assert bad_type.success is False
        assert "invalid reply_type" in (bad_type.error or "")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_client_authorization_request_requires_a_target():
    client = LansengerClient(app_id="id", app_secret="sec")
    try:
        result = await client.send_authorization_request("")
        assert result.success is False
        assert result.error == "chat_id is required"
    finally:
        await client.close()


def test_cancel_also_requires_an_emoji():
    assert validate_reply_request("m-1", "", 2) is not None
    assert validate_reply_request("m-1", "TYPE_OK", 2) is None
    assert validate_reply_request("m-1", "", 1) is not None
    assert validate_reply_request("", "TYPE_OK", 1) is not None


def test_sync_client_exposes_the_same_two_entry_points():
    sync = LansengerSyncClient(app_id="id", app_secret="sec")

    reply = sync.reply_message("", emoji_id="TYPE_OK")
    assert reply.success is False
    assert reply.error == "msg_id is required"

    request = sync.send_authorization_request("")
    assert request.success is False
    assert request.error == "chat_id is required"
