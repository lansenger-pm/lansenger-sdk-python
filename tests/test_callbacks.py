"""Tests for Lansenger SDK callback event parsing and verification."""

import base64
import hashlib
import json
import struct

import pytest

from lansenger_sdk.callbacks import (
    CALLBACK_EVENT_TYPES,
    CallbackEvent,
    decrypt_callback_payload,
    get_callback_event_types,
    parse_callback_payload,
    verify_callback_signature,
    _decode_aes_key,
    _pkcs7_unpad,
    AccountSubscribeData,
    AppInstallData,
    BotGroupMessageData,
    BotPrivateMessageData,
    DataScopeData,
    DeptCreateData,
    GroupCreateApproveData,
    ReportLocationData,
    ScheduleDeleteData,
    ScheduleModifyData,
    StaffInfoData,
    StaffModifyData,
    TelephoneTrackData,
    UserLogoutData,
    WbVisibleConfigData,
)
from lansenger_sdk import LansengerClient

AES_KEY_B64 = "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
CALLBACK_TOKEN = "48D32458EB80C61EBB08C7E86CB5BFB1"


def _encrypt_payload(events_json_str, org_id="3211264", app_id="2285568-12042496", encoding_key=AES_KEY_B64):
    aes_key = base64.b64decode(encoding_key + "=" * (-len(encoding_key) % 4))
    iv = aes_key[:16]
    events_bytes = events_json_str.encode("utf-8")
    events_len = struct.pack("!I", len(events_bytes))
    random_bytes = b"random16bytes!!!"
    plaintext = random_bytes + events_len + org_id.encode() + app_id.encode() + events_bytes
    pad_len = 32 - (len(plaintext) % 32)
    plaintext += bytes([pad_len] * pad_len)
    from Crypto.Cipher import AES
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return base64.b64encode(cipher.encrypt(plaintext)).decode()


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


def test_parse_callback_payload_encrypted_with_key():
    try:
        from Crypto.Cipher import AES
    except ImportError:
        pytest.skip("pycryptodome not installed")

    events_json = json.dumps([{"eventType": "staff_modify", "data": {"staffId": "s1", "timestamp": "123456"}}])
    encrypted = _encrypt_payload(events_json)
    events = parse_callback_payload(encrypted, encoding_key=AES_KEY_B64, known_app_id="2285568-12042496")
    assert len(events) == 1
    assert events[0].event_type == "staff_modify"
    assert isinstance(events[0].data, StaffModifyData)
    assert events[0].data.staff_id == "s1"
    assert events[0].app_id == "2285568-12042496"
    assert events[0].org_id == "3211264"


def test_parse_callback_payload_encrypted_json_wrapper():
    try:
        from Crypto.Cipher import AES
    except ImportError:
        pytest.skip("pycryptodome not installed")

    events_json = json.dumps([{"eventType": "bot_private_message", "data": {"from": "524288-xxx", "msgType": "text", "msgData": {"text": {"content": "hi"}}}}])
    encrypted = _encrypt_payload(events_json)
    wrapper = json.dumps({"dataEncrypt": encrypted})
    events = parse_callback_payload(wrapper, encoding_key=AES_KEY_B64, known_app_id="2285568-12042496")
    assert len(events) == 1
    assert events[0].event_type == "bot_private_message"
    assert isinstance(events[0].data, BotPrivateMessageData)


def test_parse_callback_payload_encrypted_with_signature():
    try:
        from Crypto.Cipher import AES
    except ImportError:
        pytest.skip("pycryptodome not installed")

    events_json = json.dumps([{"eventType": "staff_create", "data": {"staffId": "524288-new", "timestamp": "999"}}])
    encrypted = _encrypt_payload(events_json)
    timestamp = "1710000000"
    nonce = "nonce123"
    params = sorted([CALLBACK_TOKEN, timestamp, nonce, encrypted])
    sig = hashlib.sha1("".join(params).encode()).hexdigest()

    events = parse_callback_payload(
        encrypted,
        encoding_key=AES_KEY_B64,
        known_app_id="2285568-12042496",
        verify_signature=True,
        timestamp=timestamp,
        nonce=nonce,
        signature=sig,
        callback_token=CALLBACK_TOKEN,
    )
    assert len(events) == 1
    assert events[0].event_type == "staff_create"


def test_parse_callback_payload_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_callback_payload("not valid json{}")


def test_verify_callback_signature():
    timestamp = "1710000000"
    nonce = "nonce123"
    data_encrypt = "ENCRYPTED_DATA"
    params = sorted([CALLBACK_TOKEN, timestamp, nonce, data_encrypt])
    computed = hashlib.sha1("".join(params).encode()).hexdigest()
    result = verify_callback_signature(timestamp, nonce, computed, AES_KEY_B64, data_encrypt=data_encrypt, callback_token=CALLBACK_TOKEN)
    assert result is True


def test_verify_callback_signature_wrong_sig():
    result = verify_callback_signature("ts", "nonce", "wrong_sig", "key", data_encrypt="data", callback_token="token")
    assert result is False


def test_verify_callback_signature_fallback_to_encoding_key():
    encoding_key = "my_key"
    timestamp = "1710000000"
    nonce = "nonce123"
    data_encrypt = "ENCRYPTED_DATA"
    params = sorted([encoding_key, timestamp, nonce, data_encrypt])
    computed = hashlib.sha1("".join(params).encode()).hexdigest()
    result = verify_callback_signature(timestamp, nonce, computed, encoding_key, data_encrypt=data_encrypt)
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
    timestamp = "1710000000"
    nonce = "nonce123"
    data_encrypt = "ENCRYPTED_DATA"
    params = sorted([CALLBACK_TOKEN, timestamp, nonce, data_encrypt])
    computed = hashlib.sha1("".join(params).encode()).hexdigest()
    result = LansengerClient.verify_callback_signature(timestamp, nonce, computed, AES_KEY_B64, data_encrypt=data_encrypt, callback_token=CALLBACK_TOKEN)
    assert result is True


def test_client_get_callback_event_types():
    result = LansengerClient.get_callback_event_types()
    assert isinstance(result, dict)
    assert "account_message" in result


def test_decode_aes_key_valid():
    decoded = _decode_aes_key(AES_KEY_B64)
    assert len(decoded) == 32


def test_decode_aes_key_padding():
    key = base64.b64encode(b"aes_key_16bytes_").decode().rstrip("=")
    decoded = _decode_aes_key(key)
    assert len(decoded) == 16


def test_decode_aes_key_invalid_length():
    key = base64.b64encode(b"short5").decode()
    with pytest.raises(ValueError, match="Invalid AES key length"):
        _decode_aes_key(key)


def test_pkcs7_unpad_valid():
    data = b"hello\x03\x03\x03"
    result = _pkcs7_unpad(data)
    assert result == b"hello"


def test_pkcs7_unpad_invalid():
    with pytest.raises(ValueError, match="Invalid PKCS7 padding"):
        _pkcs7_unpad(b"hello\x00")


def test_decrypt_callback_payload_basic():
    try:
        from Crypto.Cipher import AES
    except ImportError:
        pytest.skip("pycryptodome not installed")

    events_json = json.dumps([{"eventType": "staff_create", "data": {"staffId": "524288-new", "timestamp": "999"}}])
    encrypted = _encrypt_payload(events_json)
    result = decrypt_callback_payload(encrypted, AES_KEY_B64, known_app_id="2285568-12042496")
    assert result["orgId"] == "3211264"
    assert result["appId"] == "2285568-12042496"
    assert isinstance(result["events"], list)
    assert result["events"][0]["eventType"] == "staff_create"


def test_decrypt_callback_payload_without_known_app_id():
    try:
        from Crypto.Cipher import AES
    except ImportError:
        pytest.skip("pycryptodome not installed")

    events_json = json.dumps([{"eventType": "staff_create", "data": {"staffId": "524288-new", "timestamp": "999"}}])
    encrypted = _encrypt_payload(events_json)
    result = decrypt_callback_payload(encrypted, AES_KEY_B64)
    assert result["orgId"] == "32112642285568-12042496"
    assert result["appId"] == ""
    assert isinstance(result["events"], list)


def test_config_encoding_key_from_env():
    import os
    os.environ["LANSENGER_APP_ID"] = "test_id"
    os.environ["LANSENGER_APP_SECRET"] = "test_secret"
    os.environ["LANSENGER_ENCODING_KEY"] = "test_encoding_key"
    os.environ["LANSENGER_CALLBACK_TOKEN"] = "test_callback_token"
    try:
        from lansenger_sdk.config import LansengerConfig
        config = LansengerConfig.from_env()
        assert config.encoding_key == "test_encoding_key"
        assert config.callback_token == "test_callback_token"
    finally:
        os.environ.pop("LANSENGER_APP_ID", None)
        os.environ.pop("LANSENGER_APP_SECRET", None)
        os.environ.pop("LANSENGER_ENCODING_KEY", None)
        os.environ.pop("LANSENGER_CALLBACK_TOKEN", None)


def test_config_encoding_key_from_direct_params():
    from lansenger_sdk.config import LansengerConfig
    config = LansengerConfig.create(app_id="id", app_secret="secret", encoding_key="key", callback_token="token")
    assert config.encoding_key == "key"
    assert config.callback_token == "token"