"""4.10.1.3 bot message callbacks: fromName / osType (prs5.10.0)."""

import json

from lansenger_sdk.callbacks import (
    BotGroupMessageData,
    BotPrivateMessageData,
    parse_callback_payload,
)


def _parse(event_type, data):
    payload = json.dumps({
        "events": [{
            "eventId": 201,
            "eventType": event_type,
            "data": data,
            "appId": "app-1",
            "orgId": "org-1",
        }],
    })
    return parse_callback_payload(payload)[0].data


def test_private_message_maps_from_name_and_os_type():
    parsed = _parse("bot_private_message", {
        "from": "524288-xxx",
        "fromName": "张三",
        "msgType": "text",
        "msgData": {"text": {"content": "hi"}},
        "msgId": "m-1",
        "osType": "ios",
    })

    assert isinstance(parsed, BotPrivateMessageData)
    assert parsed.from_id == "524288-xxx"
    assert parsed.from_name == "张三"
    assert parsed.os_type == "ios"
    assert parsed.msg_id == "m-1"


def test_group_message_maps_from_name_and_os_type():
    parsed = _parse("bot_group_message", {
        "from": "524288-xxx",
        "fromName": "李四",
        "entryId": "entry-1",
        "msgType": "text",
        "msgData": {"text": {"content": "hi"}},
        "groupId": "g-1",
        "groupName": "项目群",
        "msgId": "m-2",
        "botId": "bot-1",
        "osType": "Windows PC",
    })

    assert isinstance(parsed, BotGroupMessageData)
    assert parsed.from_name == "李四"
    assert parsed.os_type == "Windows PC"
    assert parsed.group_id == "g-1"


def test_missing_new_fields_stay_empty_for_older_servers():
    parsed = _parse("bot_private_message", {
        "from": "524288-xxx",
        "msgType": "text",
        "msgData": {"text": {"content": "hi"}},
    })

    assert parsed.from_name == ""
    assert parsed.os_type == ""
