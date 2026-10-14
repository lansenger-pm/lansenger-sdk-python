"""Tests for the 4.6.17 emoji reply API (message_replies)."""

import asyncio
import json

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.constants import EMOJI_IDS
from lansenger_sdk.message_replies import reply_message

CONFIG = LansengerConfig(
    app_id="1234-5678",
    app_secret="sec",
    api_gateway_url="https://gw.example.com",
)


def _run(coro):
    return asyncio.run(coro)


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _ok_handler(seen):
    def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"errCode": 0})

    return handler


def test_reply_message_posts_the_documented_body():
    seen = {}

    async def go():
        async with _client(_ok_handler(seen)) as client:
            return await reply_message(
                CONFIG, "at", "m-1", emoji_id="TYPE_THUMB", http_client=client
            )

    result = _run(go())

    assert result.success is True
    assert result.reply_type == 1
    assert result.emoji_id == "TYPE_THUMB"
    assert "/v1/messages/reply/create" in seen["url"]
    assert seen["body"] == {"replyType": 1, "msgId": "m-1", "emojiId": "TYPE_THUMB"}
    assert result.to_dict()["msg_id"] == "m-1"


def test_cancel_reply_sends_the_emoji_too():
    seen = {}

    async def go():
        async with _client(_ok_handler(seen)) as client:
            return await reply_message(
                CONFIG, "at", "m-2", emoji_id="TYPE_OK", reply_type=2, http_client=client
            )

    result = _run(go())

    assert result.success is True
    assert seen["body"] == {"replyType": 2, "msgId": "m-2", "emojiId": "TYPE_OK"}


def test_cancel_reply_without_emoji_is_rejected():
    cancelled = _run(reply_message(CONFIG, "at", "m-2", emoji_id="", reply_type=2))
    assert cancelled.success is False
    assert "invalid emoji_id" in (cancelled.error or "")

    replied = _run(reply_message(CONFIG, "at", "m-2", emoji_id="", reply_type=1))
    assert replied.success is False
    assert "invalid emoji_id" in (replied.error or "")


@pytest.mark.parametrize("emoji", EMOJI_IDS)
def test_every_documented_emoji_is_accepted(emoji):
    seen = {}

    async def go():
        async with _client(_ok_handler(seen)) as client:
            return await reply_message(
                CONFIG, "at", "m-3", emoji_id=emoji, http_client=client
            )

    result = _run(go())

    assert result.success is True
    assert seen["body"]["emojiId"] == emoji


def test_reply_message_requires_msg_id():
    result = _run(reply_message(CONFIG, "at", "", emoji_id="TYPE_OK"))

    assert result.success is False
    assert result.error == "msg_id is required"


def test_reply_message_rejects_unknown_reply_type():
    result = _run(reply_message(CONFIG, "at", "m-4", emoji_id="TYPE_OK", reply_type=3))

    assert result.success is False
    assert "invalid reply_type" in (result.error or "")


def test_reply_message_rejects_unknown_emoji():
    result = _run(reply_message(CONFIG, "at", "m-5", emoji_id="TYPE_NOPE"))

    assert result.success is False
    assert "invalid emoji_id" in (result.error or "")


def test_reply_message_surfaces_api_error():
    def handler(request):
        return httpx.Response(200, json={"errCode": 40060, "errMsg": "消息为空或格式错误"})

    async def go():
        async with _client(handler) as client:
            return await reply_message(
                CONFIG, "at", "m-6", emoji_id="TYPE_LOVE", http_client=client
            )

    result = _run(go())

    assert result.success is False
    assert "40060" in (result.error or "")


def test_reply_message_surfaces_http_error():
    def handler(request):
        return httpx.Response(500, text="boom")

    async def go():
        async with _client(handler) as client:
            return await reply_message(
                CONFIG, "at", "m-7", emoji_id="TYPE_LOVE", http_client=client
            )

    result = _run(go())

    assert result.success is False
    assert "HTTP error" in (result.error or "")
