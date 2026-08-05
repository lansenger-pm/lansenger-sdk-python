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


@pytest.mark.asyncio
async def test_client_send_text_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_text(chat_id="", content="hi", is_group=True)
    assert result.success is False
    assert "chat_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_markdown_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_markdown(chat_id="", content="**hi**", is_group=True)
    assert result.success is False
    assert "chat_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_link_card_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_link_card(
        chat_id="", title="T", link="L", is_group=True,
        user_token="ut1", sender_id="sid1",
    )
    assert result.success is False
    assert "chat_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_app_articles_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_app_articles(
        chat_id="", articles=[{"title": "T"}], is_group=True,
        user_token="ut1", sender_id="sid1",
    )
    assert result.success is False
    assert "chat_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_app_card_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_app_card(
        chat_id="", body_title="Card", is_group=True,
        user_token="ut1", sender_id="sid1",
    )
    assert result.success is False
    assert "chat_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_group_message_reminder_text_injects():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        reminder_all=True, reminder_user_ids=["u1", "u2"],
    )
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_group_message_reminder_format_text_injects():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="formatText",
        msg_data={"formatText": {"formatType": 1, "text": "hi"}},
        reminder_all=True,
    )
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_group_message_reminder_non_text_no_inject():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="linkCard",
        msg_data={"linkCard": {"title": "T", "link": "L"}},
        reminder_all=True, reminder_user_ids=["u1"],
    )
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_client_send_bot_message_is_group():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_bot_message(
        msg_type="",
        msg_data={"text": {"content": "hi"}},
        chat_ids=["grp1"],
        is_group=True,
    )
    assert result.success is False
    assert "msg_type is required" in result.error


@pytest.mark.asyncio
async def test_client_send_link_card_group_with_mock():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "lcgrp1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=MagicMock(
        status_code=200, raise_for_status=MagicMock(),
        json=MagicMock(return_value={"errCode": 0, "data": {"appToken": "test_token", "expiresIn": 7200}}),
    ))

    client = LansengerClient(app_id="id", app_secret="secret")
    client.attach_http_client(mock_client)
    result = await client.send_link_card(
        chat_id="grp1", title="T", link="L",
        is_group=True, user_token="ut1", sender_id="sid1",
    )
    assert result.success is True
    assert result.message_id == "lcgrp1"

    call_args = mock_client.post.call_args
    url = call_args.kwargs.get("url") or call_args[0][0] or call_args.args[0]
    assert "group" in url or "groupId" in str(call_args)
    payload = call_args.kwargs.get("json")
    assert payload["groupId"] == "grp1"
    assert payload["msgType"] == "linkCard"
    assert payload["senderId"] == "sid1"


@pytest.mark.asyncio
async def test_client_send_app_articles_group_with_mock():
    config = _make_config()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "aagrp1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=MagicMock(
        status_code=200, raise_for_status=MagicMock(),
        json=MagicMock(return_value={"errCode": 0, "data": {"appToken": "test_token", "expiresIn": 7200}}),
    ))

    client = LansengerClient(app_id="id", app_secret="secret")
    client.attach_http_client(mock_client)
    result = await client.send_app_articles(
        chat_id="grp1", articles=[{"title": "T"}],
        is_group=True, user_token="ut1", sender_id="sid1",
    )
    assert result.success is True
    assert result.message_id == "aagrp1"

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["groupId"] == "grp1"
    assert payload["msgType"] == "appArticles"


@pytest.mark.asyncio
async def test_client_send_app_card_group_with_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "acgrp1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=MagicMock(
        status_code=200, raise_for_status=MagicMock(),
        json=MagicMock(return_value={"errCode": 0, "data": {"appToken": "test_token", "expiresIn": 7200}}),
    ))

    client = LansengerClient(app_id="id", app_secret="secret")
    client.attach_http_client(mock_client)
    result = await client.send_app_card(
        chat_id="grp1", body_title="Card",
        is_group=True, user_token="ut1", sender_id="sid1",
    )
    assert result.success is True
    assert result.message_id == "acgrp1"

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["groupId"] == "grp1"
    assert payload["msgType"] == "appCard"
    assert payload["senderId"] == "sid1"


@pytest.mark.asyncio
async def test_client_send_group_message_reminder_text_with_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "rem1"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=MagicMock(
        status_code=200, raise_for_status=MagicMock(),
        json=MagicMock(return_value={"errCode": 0, "data": {"appToken": "test_token", "expiresIn": 7200}}),
    ))

    client = LansengerClient(app_id="id", app_secret="secret")
    client.attach_http_client(mock_client)
    result = await client.send_group_message(
        group_id="grp1", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        reminder_all=True, reminder_user_ids=["u1"],
    )
    assert result.success is True
    assert result.message_id == "rem1"

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["msgData"]["text"]["reminder"]["all"] is True
    assert payload["msgData"]["text"]["reminder"]["userIds"] == ["u1"]


@pytest.mark.asyncio
async def test_client_send_group_message_reminder_formatText_with_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "errCode": 0,
        "data": {"msgId": "rem2"},
    })
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.get = AsyncMock(return_value=MagicMock(
        status_code=200, raise_for_status=MagicMock(),
        json=MagicMock(return_value={"errCode": 0, "data": {"appToken": "test_token", "expiresIn": 7200}}),
    ))

    client = LansengerClient(app_id="id", app_secret="secret")
    client.attach_http_client(mock_client)
    result = await client.send_group_message(
        group_id="grp1", msg_type="formatText",
        msg_data={"formatText": {"formatType": 1, "text": "hi"}},
        reminder_all=True,
    )
    assert result.success is True

    call_args = mock_client.post.call_args
    payload = call_args.kwargs.get("json")
    assert payload["msgData"]["formatText"]["reminder"]["all"] is True


@pytest.mark.asyncio
async def test_client_send_bot_message_is_group_no_chat_ids():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_bot_message(
        msg_type="text",
        msg_data={"text": {"content": "hi"}},
        chat_ids=None,
        is_group=True,
    )
    assert result.success is False
    assert "chat_ids" in result.error
