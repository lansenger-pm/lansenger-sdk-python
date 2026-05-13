"""Tests for Lansenger SDK callback event parsing and verification."""

import json
import pytest

from lansenger_sdk.callbacks import (
    CALLBACK_EVENT_TYPES,
    CallbackEvent,
    parse_callback_payload,
    verify_callback_signature,
    get_callback_event_types,
    AccountSubscribeData,
    StaffModifyData,
    StaffInfoData,
    BotPrivateMessageData,
    BotGroupMessageData,
    TelephoneTrackData,
    DeptCreateData,
    AppInstallData,
    GroupCreateApproveData,
    ScheduleModifyData,
    ScheduleDeleteData,
    DataScopeData,
    WbVisibleConfigData,
    UserLogoutData,
    ReportLocationData,
)
from lansenger_sdk import LansengerClient


def test_callback_event_types_count():
    assert len(CALLBACK_EVENT_TYPES) == 25


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
    assert CALLBACK_EVENT_TYPES["ua_cert_delete"] == "certificate"
    assert CALLBACK_EVENT_TYPES["report_location"] == "location"
    assert CALLBACK_EVENT_TYPES["user_logout"] == "auth"
    assert CALLBACK_EVENT_TYPES["data_scope"] == "data_scope"
    assert CALLBACK_EVENT_TYPES["wb_visible_config"] == "workbench"
    assert CALLBACK_EVENT_TYPES["schedule_modify"] == "calendar"
    assert CALLBACK_EVENT_TYPES["schedule_delete"] == "calendar"


def test_no_ua_cert_modify():
    assert "ua_cert_modify" not in CALLBACK_EVENT_TYPES


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
                "eventType": "staff_modify",
                "data": {"staffId": "s1", "timestamp": "123456"},
                "appId": "my_app",
                "orgId": "my_org",
            },
            {
                "eventId": 101,
                "eventType": "unknown_type",
                "data": {"someKey": "someValue"},
                "appId": "my_app",
                "orgId": "my_org",
            },
        ],
    })
    events = parse_callback_payload(payload)
    assert len(events) == 2
    assert events[0].event_id == 100
    assert events[0].event_type == "staff_modify"
    assert events[0].category == "staff"
    assert isinstance(events[0].data, StaffModifyData)
    assert events[0].data.staff_id == "s1"
    assert events[0].data.timestamp == "123456"
    assert events[1].event_type == "unknown_type"
    assert events[1].category == "unknown"
    assert isinstance(events[1].data, dict)


def test_parse_callback_payload_single_event_dict():
    payload = json.dumps({
        "events": {
            "eventId": 200,
            "eventType": "bot_private_message",
            "data": {"from": "524288-xxx", "msgType": "text", "msgData": {"text": {"content": "hi"}}},
            "appId": "app2",
            "orgId": "org2",
        },
    })
    events = parse_callback_payload(payload)
    assert len(events) == 1
    assert events[0].event_type == "bot_private_message"
    assert events[0].category == "bot"
    assert isinstance(events[0].data, BotPrivateMessageData)
    assert events[0].data.from_id == "524288-xxx"
    assert events[0].data.msg_type == "text"


def test_parse_bot_group_message():
    payload = json.dumps({
        "events": [{
            "eventId": 300,
            "eventType": "bot_group_message",
            "data": {
                "from": "524288-abc",
                "msgType": "text",
                "msgData": {"text": {"content": "@bot hello"}},
                "groupId": "524288-grp",
                "entryId": "524288-entry",
                "fromType": 0,
                "groupName": "项目讨论",
                "botCreator": "524288-creator",
                "msgId": "524288-msgid",
                "botId": "524288-botid",
                "isAtMe": True,
                "isAtAll": False,
            },
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    assert len(events) == 1
    data = events[0].data
    assert isinstance(data, BotGroupMessageData)
    assert data.from_id == "524288-abc"
    assert data.group_id == "524288-grp"
    assert data.from_type == 0
    assert data.group_name == "项目讨论"
    assert data.bot_creator == "524288-creator"
    assert data.msg_id == "524288-msgid"
    assert data.bot_id == "524288-botid"
    assert data.is_at_me is True
    assert data.is_at_all is False


def test_parse_account_subscribe():
    payload = json.dumps({
        "events": [{
            "eventId": 1,
            "eventType": "account_subscribe",
            "data": {"staffId": "524288-sub", "createTime": "1540377644020456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, AccountSubscribeData)
    assert data.staff_id == "524288-sub"
    assert data.create_time == "1540377644020456"


def test_parse_staff_info():
    payload = json.dumps({
        "events": [{
            "eventId": 2,
            "eventType": "staff_info",
            "data": {"staffId": "524288-s1", "name": "张三", "mobile": "13800138000", "state": "正常", "sex": "保密", "email": "z@lx.com", "employId": "A123", "avatarId": "524288-av", "timestamp": "123456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, StaffInfoData)
    assert data.staff_id == "524288-s1"
    assert data.name == "张三"
    assert data.employee_id == "A123"


def test_parse_telephone_track():
    payload = json.dumps({
        "events": [{
            "eventId": 3,
            "eventType": "telephone_track",
            "data": {
                "transactionId": "524288-tx",
                "attach": "app_data",
                "caller": {"staffId": "524288-caller", "mobilePhone": {"countryCode": "86", "number": "12345678902"}},
                "callee": {"staffId": "524288-callee", "mobilePhone": {"countryCode": "86", "number": "98765432100"}},
                "confirmType": 1,
                "timestamp": "1234567890",
            },
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, TelephoneTrackData)
    assert data.transaction_id == "524288-tx"
    assert data.confirm_type == 1
    assert data.caller.staff_id == "524288-caller"
    assert data.caller.country_code == "86"
    assert data.caller.number == "12345678902"
    assert data.callee.staff_id == "524288-callee"


def test_parse_dept_create():
    payload = json.dumps({
        "events": [{
            "eventId": 4,
            "eventType": "dept_create",
            "data": {"deptId": "524288-dept", "timestamp": "1234567890"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, DeptCreateData)
    assert data.dept_id == "524288-dept"


def test_parse_app_install():
    payload = json.dumps({
        "events": [{
            "eventId": 5,
            "eventType": "app_install_org",
            "data": {"orgId": "234583", "orgName": "组织名称", "timestamp": "12345678899"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, AppInstallData)
    assert data.org_id == "234583"
    assert data.org_name == "组织名称"


def test_parse_group_create_approve():
    payload = json.dumps({
        "events": [{
            "eventId": 6,
            "eventType": "group_create_approve",
            "data": {"applyRequestId": "req1", "groupId": "524288-grp", "timestamp": "123456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, GroupCreateApproveData)
    assert data.apply_request_id == "req1"


def test_parse_schedule_modify():
    payload = json.dumps({
        "events": [{
            "eventId": 7,
            "eventType": "schedule_modify",
            "data": {
                "primaryScheduleId": "524288-psid",
                "scheduleId": "524288-sid",
                "summary": "会议",
                "operationType": "modify_all",
                "startTime": {"time": 1712988000, "timeZone": "Asia/Shanghai"},
                "endTime": {"time": 1712998800, "timeZone": "Asia/Shanghai"},
                "timestamp": "1712655597216842",
            },
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, ScheduleModifyData)
    assert data.schedule_id == "524288-sid"
    assert data.operation_type == "modify_all"
    assert data.start_time["time"] == 1712988000


def test_parse_schedule_delete():
    payload = json.dumps({
        "events": [{
            "eventId": 8,
            "eventType": "schedule_delete",
            "data": {"scheduleId": "sid1", "operationType": "delete_current", "timestamp": "123456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, ScheduleDeleteData)
    assert data.operation_type == "delete_current"


def test_parse_data_scope():
    payload = json.dumps({
        "events": [{
            "eventId": 9,
            "eventType": "data_scope",
            "data": {"deptIds": ["524288-d1", "524288-d2"], "timestamp": "123456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, DataScopeData)
    assert data.dept_ids == ["524288-d1", "524288-d2"]


def test_parse_wb_visible_config():
    payload = json.dumps({
        "events": [{
            "eventId": 10,
            "eventType": "wb_visible_config",
            "data": {"entryId": "entry1", "staffIds": ["s1"], "departmentIds": ["d1"], "timestamp": "123", "isTestModeOn": False},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, WbVisibleConfigData)
    assert data.entry_id == "entry1"
    assert data.is_test_mode_on is False


def test_parse_user_logout():
    payload = json.dumps({
        "events": [{
            "eventId": 11,
            "eventType": "user_logout",
            "data": {"staffId": "s1", "deviceId": "dev1", "timestamp": "123456"},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, UserLogoutData)
    assert data.staff_id == "s1"


def test_parse_report_location():
    payload = json.dumps({
        "events": [{
            "eventId": 12,
            "eventType": "report_location",
            "data": {"locationInfo": {"latitude": "39.9", "longitude": "116.4", "city": "北京"}},
            "appId": "app1",
            "orgId": "org1",
        }],
    })
    events = parse_callback_payload(payload)
    data = events[0].data
    assert isinstance(data, ReportLocationData)
    assert data.location_info["city"] == "北京"


def test_parse_callback_payload_encryption_raises():
    with pytest.raises(NotImplementedError):
        parse_callback_payload("encrypted_data", encoding_key="some_key")


def test_parse_callback_payload_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_callback_payload("not valid json{}")


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
                "eventType": "account_subscribe",
                "data": {"staffId": "524288-xxx", "createTime": "1540377644020456"},
                "appId": "app1",
                "orgId": "org1",
            },
        ],
    })
    events = LansengerClient.parse_callback_payload(payload)
    assert len(events) == 1
    assert events[0].event_type == "account_subscribe"
    assert isinstance(events[0].data, AccountSubscribeData)


def test_client_verify_callback_signature():
    result = LansengerClient.verify_callback_signature("ts", "nonce", "sig", "key")
    assert result is True


def test_client_get_callback_event_types():
    result = LansengerClient.get_callback_event_types()
    assert isinstance(result, dict)
    assert "account_message" in result