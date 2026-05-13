"""Tests for Lansenger SDK callback event parsing and verification."""

import json
import pytest

from lansenger_sdk.callbacks import (
    CALLBACK_EVENT_TYPES,
    CallbackEvent,
    parse_callback_payload,
    verify_callback_signature,
    get_callback_event_types,
)
from lansenger_sdk import LansengerClient


def test_callback_event_types_count():
    assert len(CALLBACK_EVENT_TYPES) == 26


def test_callback_event_types_specific_values():
    assert CALLBACK_EVENT_TYPES["account_message"] == "public_account"
    assert CALLBACK_EVENT_TYPES["account_subscribe"] == "public_account"
    assert CALLBACK_EVENT_TYPES["account_unsubscribe"] == "public_account"
    assert CALLBACK_EVENT_TYPES["staff_info"] == "staff"
    assert CALLBACK_EVENT_TYPES["staff_modify"] == "staff"
    assert CALLBACK_EVENT_TYPES["staff_create"] == "staff"
    assert CALLBACK_EVENT_TYPES["staff_delete"] == "staff"
    assert CALLBACK_EVENT_TYPES["dept_modify"] == "department"
    assert CALLBACK_EVENT_TYPES["dept_create"] == "department"
    assert CALLBACK_EVENT_TYPES["dept_delete"] == "department"
    assert CALLBACK_EVENT_TYPES["tag_member"] == "tag"
    assert CALLBACK_EVENT_TYPES["app_install_org"] == "app"
    assert CALLBACK_EVENT_TYPES["app_uninstall_org"] == "app"
    assert CALLBACK_EVENT_TYPES["bot_private_message"] == "bot"
    assert CALLBACK_EVENT_TYPES["bot_group_message"] == "bot"
    assert CALLBACK_EVENT_TYPES["group_create_approve"] == "group"
    assert CALLBACK_EVENT_TYPES["telephone_track"] == "notification"
    assert CALLBACK_EVENT_TYPES["ua_cert_create"] == "certificate"
    assert CALLBACK_EVENT_TYPES["ua_cert_modify"] == "certificate"
    assert CALLBACK_EVENT_TYPES["ua_cert_delete"] == "certificate"
    assert CALLBACK_EVENT_TYPES["report_location"] == "location"
    assert CALLBACK_EVENT_TYPES["user_logout"] == "auth"
    assert CALLBACK_EVENT_TYPES["data_scope"] == "data_scope"
    assert CALLBACK_EVENT_TYPES["wb_visible_config"] == "workbench"
    assert CALLBACK_EVENT_TYPES["schedule_modify"] == "calendar"
    assert CALLBACK_EVENT_TYPES["schedule_delete"] == "calendar"


def test_callback_event_dataclass():
    event = CallbackEvent(
        event_id=1,
        event_type="account_message",
        category="public_account",
        data={"content": "hello"},
        app_id="app1",
        org_id="org1",
    )
    assert event.event_id == 1
    assert event.event_type == "account_message"
    assert event.category == "public_account"
    assert event.data == {"content": "hello"}
    assert event.app_id == "app1"
    assert event.org_id == "org1"


def test_parse_callback_payload_plain_json():
    payload = json.dumps({
        "events": [
            {
                "eventId": 100,
                "eventType": "account_message",
                "data": {"content": "test message"},
                "appId": "my_app",
                "orgId": "my_org",
            },
            {
                "eventId": 101,
                "eventType": "staff_modify",
                "data": {"staffId": "s1"},
                "appId": "my_app",
                "orgId": "my_org",
            },
        ],
    })
    events = parse_callback_payload(payload)
    assert len(events) == 2
    assert events[0].event_id == 100
    assert events[0].event_type == "account_message"
    assert events[0].category == "public_account"
    assert events[1].event_type == "staff_modify"
    assert events[1].category == "staff"


def test_parse_callback_payload_single_event_dict():
    payload = json.dumps({
        "events": {
            "eventId": 200,
            "eventType": "bot_private_message",
            "data": {"msg": "hi"},
            "appId": "app2",
            "orgId": "org2",
        },
    })
    events = parse_callback_payload(payload)
    assert len(events) == 1
    assert events[0].event_type == "bot_private_message"
    assert events[0].category == "bot"


def test_parse_callback_payload_encryption_raises():
    with pytest.raises(NotImplementedError):
        parse_callback_payload("encrypted_data", encoding_key="some_key")


def test_parse_callback_payload_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_callback_payload("not valid json{}")


def test_parse_callback_payload_unknown_event_type():
    payload = json.dumps({
        "events": [
            {
                "eventId": 300,
                "eventType": "unknown_event_type",
                "data": {},
                "appId": "app3",
                "orgId": "org3",
            },
        ],
    })
    events = parse_callback_payload(payload)
    assert len(events) == 1
    assert events[0].category == "unknown"


def test_verify_callback_signature_returns_true():
    result = verify_callback_signature("ts", "nonce", "sig", "key")
    assert result is True


def test_get_callback_event_types_returns_dict():
    result = get_callback_event_types()
    assert isinstance(result, dict)
    assert result is CALLBACK_EVENT_TYPES


def test_client_parse_callback_payload():
    payload = json.dumps({
        "events": [
            {
                "eventId": 1,
                "eventType": "account_message",
                "data": {},
                "appId": "app1",
                "orgId": "org1",
            },
        ],
    })
    events = LansengerClient.parse_callback_payload(payload)
    assert len(events) == 1
    assert events[0].event_type == "account_message"


def test_client_verify_callback_signature():
    result = LansengerClient.verify_callback_signature("ts", "nonce", "sig", "key")
    assert result is True


def test_client_get_callback_event_types():
    result = LansengerClient.get_callback_event_types()
    assert isinstance(result, dict)
    assert "account_message" in result