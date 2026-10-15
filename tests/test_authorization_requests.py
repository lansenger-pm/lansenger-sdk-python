"""Tests for the 4.6.4.14 authorizationReq message body."""

import pytest

from lansenger_sdk import LansengerClient
from lansenger_sdk.authorization_requests import authorization_req_payload
from lansenger_sdk.constants import (
    AUTHORIZATION_TYPE_LOCATION,
    MSG_TYPE_AUTHORIZATION_REQ,
)
from lansenger_sdk.models import SendMessageResult


def test_payload_matches_the_documented_shape():
    assert MSG_TYPE_AUTHORIZATION_REQ == "authorizationReq"
    assert AUTHORIZATION_TYPE_LOCATION == 1
    assert authorization_req_payload() == {"authorizationType": 1}
    assert authorization_req_payload(AUTHORIZATION_TYPE_LOCATION) == {
        "authorizationType": AUTHORIZATION_TYPE_LOCATION
    }


def test_unknown_authorization_type_is_rejected():
    with pytest.raises(ValueError):
        authorization_req_payload(9)


@pytest.mark.asyncio
async def test_client_sends_it_over_the_bot_private_channel(monkeypatch):
    """The platform rejects authorizationReq on the account channel."""
    client = LansengerClient(app_id="id", app_secret="sec")
    calls = {}

    async def fake_send_private(chat_id, msg_type, msg_data, *, ref_msg_id=""):
        calls.update(
            chat_id=chat_id, msg_type=msg_type, msg_data=msg_data, ref_msg_id=ref_msg_id
        )
        return SendMessageResult(success=True, message_id="m-9")

    monkeypatch.setattr(client, "_send_private", fake_send_private)

    result = await client.send_authorization_request("staff-1")
    await client.close()

    assert result.success is True
    assert calls["chat_id"] == "staff-1"
    assert calls["msg_type"] == MSG_TYPE_AUTHORIZATION_REQ
    assert calls["msg_data"] == {"authorizationType": 1}
    assert calls["ref_msg_id"] == ""


@pytest.mark.asyncio
async def test_client_rejects_an_unknown_type_before_sending(monkeypatch):
    client = LansengerClient(app_id="id", app_secret="sec")
    sent = []

    async def fake_send_private(*args, **kwargs):
        sent.append(args)
        return SendMessageResult(success=True)

    monkeypatch.setattr(client, "_send_private", fake_send_private)

    result = await client.send_authorization_request("staff-1", authorization_type=9)
    await client.close()

    assert result.success is False
    assert "authorization_type" in (result.error or "")
    assert sent == []
