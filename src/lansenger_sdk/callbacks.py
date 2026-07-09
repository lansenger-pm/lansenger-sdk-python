"""Lansenger callback event parsing and verification.

This module handles parsing and verifying callback payloads sent by the
Lansenger platform to your app's HTTP callback endpoint. It provides event
type categorization, structured data parsing, AES decryption (per 4.10.1.4),
and SHA1 signature verification.

No HTTP calls are made — this is purely data parsing.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import struct
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("lansenger_sdk.callbacks")

CALLBACK_EVENT_TYPES: Dict[str, str] = {
    "account_message": "public_account",
    "account_subscribe": "public_account",
    "account_unsubscribe": "public_account",
    "staff_info": "staff",
    "staff_modify": "staff",
    "staff_create": "staff",
    "staff_delete": "staff",
    "dept_modify": "department",
    "dept_create": "department",
    "dept_delete": "department",
    "tag_member": "tag",
    "app_install_org": "app",
    "app_uninstall_org": "app",
    "bot_private_message": "bot",
    "bot_group_message": "bot",
    "group_create_approve": "group",
    "telephone_track": "notification",
    "ua_cert_create": "certificate",
    "ua_cert_delete": "certificate",
    "report_location": "location",
    "user_logout": "auth",
    "data_scope": "data_scope",
    "wb_visible_config": "workbench",
    "schedule_modify": "calendar",
    "schedule_delete": "calendar",
}


# ── Base event ──────────────────────────────────────────────────────

@dataclass
class CallbackEvent:
    event_id: int
    event_type: str
    category: str
    data: Union[dict, "CallbackEventData"]
    app_id: str
    org_id: str


# ── 1. Public account events ────────────────────────────────────────

@dataclass
class AccountSubscribeData:
    staff_id: str = ""
    create_time: str = ""


@dataclass
class AccountUnsubscribeData:
    staff_id: str = ""
    create_time: str = ""


# ── 2. Staff events ──────────────────────────────────────────────────

@dataclass
class StaffInfoData:
    staff_id: str = ""
    name: str = ""
    mobile: str = ""
    state: str = ""
    sex: str = ""
    email: str = ""
    employee_id: str = ""
    avatar_id: str = ""
    timestamp: str = ""


@dataclass
class StaffModifyData:
    staff_id: str = ""
    timestamp: str = ""


@dataclass
class StaffCreateData:
    staff_id: str = ""
    timestamp: str = ""


@dataclass
class StaffDeleteData:
    staff_id: str = ""
    timestamp: str = ""


# ── 3. Telephone track ───────────────────────────────────────────────

@dataclass
class TelephoneTrackCallerData:
    staff_id: str = ""
    country_code: str = ""
    number: str = ""


@dataclass
class TelephoneTrackData:
    transaction_id: str = ""
    attach: str = ""
    caller: TelephoneTrackCallerData = field(default_factory=TelephoneTrackCallerData)
    callee: TelephoneTrackCallerData = field(default_factory=TelephoneTrackCallerData)
    confirm_type: int = 0
    timestamp: str = ""


# ── 4. Department events ──────────────────────────────────────────────

@dataclass
class DeptCreateData:
    dept_id: str = ""
    timestamp: str = ""


@dataclass
class DeptModifyData:
    dept_id: str = ""
    timestamp: str = ""


@dataclass
class DeptDeleteData:
    dept_id: str = ""
    timestamp: str = ""


# ── 5. App install/uninstall ──────────────────────────────────────────

@dataclass
class AppInstallData:
    org_id: str = ""
    org_name: str = ""
    timestamp: str = ""


@dataclass
class AppUninstallData:
    org_id: str = ""
    org_name: str = ""
    timestamp: str = ""


# ── 6. Certificate events ────────────────────────────────────────────

@dataclass
class UaCertCreateData:
    staff_id: str = ""
    device_id: str = ""
    ua_cert: str = ""
    timestamp: str = ""


@dataclass
class UaCertDeleteData:
    staff_id: str = ""
    device_id: str = ""
    timestamp: str = ""


# ── 7. Location report ────────────────────────────────────────────────

@dataclass
class ReportLocationData:
    location_info: Dict[str, str] = field(default_factory=dict)


# ── 8. User logout ────────────────────────────────────────────────────

@dataclass
class UserLogoutData:
    staff_id: str = ""
    device_id: str = ""
    timestamp: str = ""


# ── 9. Data scope ──────────────────────────────────────────────────────

@dataclass
class DataScopeData:
    dept_ids: List[str] = field(default_factory=list)
    timestamp: str = ""


# ── 10. Bot message events ────────────────────────────────────────────

@dataclass
class BotPrivateMessageData:
    from_id: str = ""
    entry_id: str = ""
    msg_type: str = ""
    msg_data: dict = field(default_factory=dict)
    msg_id: str = ""
    reference_msg: Optional[dict] = None


@dataclass
class BotGroupMessageData:
    from_id: str = ""
    entry_id: str = ""
    msg_type: str = ""
    msg_data: dict = field(default_factory=dict)
    group_id: str = ""
    from_type: int = 0
    group_name: str = ""
    bot_creator: str = ""
    msg_id: str = ""
    bot_id: str = ""
    is_at_me: bool = False
    is_at_all: bool = False
    bots: List[dict] = field(default_factory=list)
    staffs: List[dict] = field(default_factory=list)
    magic: str = ""
    reference_msg: Optional[dict] = None


# ── 11. Workbench visible config ───────────────────────────────────────

@dataclass
class WbVisibleConfigData:
    entry_id: str = ""
    department_ids: List[str] = field(default_factory=list)
    staff_ids: List[str] = field(default_factory=list)
    timestamp: str = ""
    is_test_mode_on: bool = False


# ── 12. Group create approve ───────────────────────────────────────────

@dataclass
class GroupCreateApproveData:
    apply_request_id: str = ""
    group_id: str = ""
    timestamp: str = ""


# ── 13. Schedule events ────────────────────────────────────────────────

@dataclass
class ScheduleModifyData:
    primary_schedule_id: str = ""
    schedule_id: str = ""
    summary: str = ""
    description: str = ""
    operation_type: str = ""
    current_time: int = 0
    repeat_type: str = ""
    expire_date_type: str = ""
    all_day: str = ""
    rule: str = ""
    rule_start_time: int = 0
    rule_end_time: int = 0
    start_time: dict = field(default_factory=dict)
    end_time: dict = field(default_factory=dict)
    operator: str = ""
    attendees: List[dict] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class ScheduleDeleteData:
    primary_schedule_id: str = ""
    schedule_id: str = ""
    summary: str = ""
    description: str = ""
    operation_type: str = ""
    current_time: int = 0
    repeat_type: str = ""
    expire_date_type: str = ""
    all_day: str = ""
    rule: str = ""
    rule_start_time: int = 0
    rule_end_time: int = 0
    start_time: dict = field(default_factory=dict)
    end_time: dict = field(default_factory=dict)
    operator: str = ""
    timestamp: str = ""


# ── Tag member (platform not implemented) ────────────────────────────

@dataclass
class TagMemberData:
    tag_id: str = ""
    timestamp: str = ""


# ── Union type for all structured data ────────────────────────────────

CallbackEventData = Union[
    AccountSubscribeData,
    AccountUnsubscribeData,
    StaffInfoData,
    StaffModifyData,
    StaffCreateData,
    StaffDeleteData,
    TelephoneTrackData,
    DeptCreateData,
    DeptModifyData,
    DeptDeleteData,
    AppInstallData,
    AppUninstallData,
    UaCertCreateData,
    UaCertDeleteData,
    ReportLocationData,
    UserLogoutData,
    DataScopeData,
    BotPrivateMessageData,
    BotGroupMessageData,
    WbVisibleConfigData,
    GroupCreateApproveData,
    ScheduleModifyData,
    ScheduleDeleteData,
    TagMemberData,
]


EVENT_DATA_PARSERS: Dict[str, Any] = {
    "account_subscribe": AccountSubscribeData,
    "account_unsubscribe": AccountUnsubscribeData,
    "staff_info": StaffInfoData,
    "staff_modify": StaffModifyData,
    "staff_create": StaffCreateData,
    "staff_delete": StaffDeleteData,
    "telephone_track": TelephoneTrackData,
    "dept_create": DeptCreateData,
    "dept_modify": DeptModifyData,
    "dept_delete": DeptDeleteData,
    "app_install_org": AppInstallData,
    "app_uninstall_org": AppUninstallData,
    "ua_cert_create": UaCertCreateData,
    "ua_cert_delete": UaCertDeleteData,
    "report_location": ReportLocationData,
    "user_logout": UserLogoutData,
    "data_scope": DataScopeData,
    "bot_private_message": BotPrivateMessageData,
    "bot_group_message": BotGroupMessageData,
    "wb_visible_config": WbVisibleConfigData,
    "group_create_approve": GroupCreateApproveData,
    "schedule_modify": ScheduleModifyData,
    "schedule_delete": ScheduleDeleteData,
    "tag_member": TagMemberData,
}

FIELD_MAPS: Dict[str, Dict[str, str]] = {
    "account_subscribe": {"staffId": "staff_id", "createTime": "create_time"},
    "account_unsubscribe": {"staffId": "staff_id", "createTime": "create_time"},
    "staff_info": {"staffId": "staff_id", "name": "name", "mobile": "mobile", "state": "state", "sex": "sex", "email": "email", "employId": "employee_id", "employeeId": "employee_id", "avatarId": "avatar_id", "timestamp": "timestamp"},
    "staff_modify": {"staffId": "staff_id", "timestamp": "timestamp"},
    "staff_create": {"staffId": "staff_id", "timestamp": "timestamp"},
    "staff_delete": {"staffId": "staff_id", "timestamp": "timestamp"},
    "telephone_track": {"transactionId": "transaction_id", "attach": "attach", "confirmType": "confirm_type", "timestamp": "timestamp"},
    "dept_create": {"deptId": "dept_id", "timestamp": "timestamp"},
    "dept_modify": {"deptId": "dept_id", "timestamp": "timestamp"},
    "dept_delete": {"deptId": "dept_id", "timestamp": "timestamp"},
    "app_install_org": {"orgId": "org_id", "orgName": "org_name", "timestamp": "timestamp"},
    "app_uninstall_org": {"orgId": "org_id", "orgName": "org_name", "timestamp": "timestamp"},
    "ua_cert_create": {"staffId": "staff_id", "deviceId": "device_id", "uaCert": "ua_cert", "timestamp": "timestamp"},
    "ua_cert_delete": {"staffId": "staff_id", "deviceId": "device_id", "timestamp": "timestamp"},
    "report_location": {},
    "user_logout": {"staffId": "staff_id", "deviceId": "device_id", "timestamp": "timestamp"},
    "data_scope": {"deptIds": "dept_ids", "timestamp": "timestamp"},
    "bot_private_message": {"from": "from_id", "entryId": "entry_id", "msgType": "msg_type", "msgData": "msg_data", "msgId": "msg_id", "referenceMsg": "reference_msg"},
    "bot_group_message": {"from": "from_id", "entryId": "entry_id", "msgType": "msg_type", "msgData": "msg_data", "groupId": "group_id", "fromType": "from_type", "groupName": "group_name", "botCreator": "bot_creator", "msgId": "msg_id", "botId": "bot_id", "referenceMsg": "reference_msg", "magic": "magic"},
    "wb_visible_config": {"entryId": "entry_id", "departmentIds": "department_ids", "staffIds": "staff_ids", "timestamp": "timestamp", "isTestModeOn": "is_test_mode_on"},
    "group_create_approve": {"applyRequestId": "apply_request_id", "groupId": "group_id", "timestamp": "timestamp"},
    "schedule_modify": {"primaryScheduleId": "primary_schedule_id", "scheduleId": "schedule_id", "summary": "summary", "description": "description", "operationType": "operation_type", "currentTime": "current_time", "repeatType": "repeat_type", "expireDateType": "expire_date_type", "allDay": "all_day", "rule": "rule", "ruleStartTime": "rule_start_time", "ruleEndTime": "rule_end_time", "startTime": "start_time", "endTime": "end_time", "operator": "operator", "attendees": "attendees", "timestamp": "timestamp"},
    "schedule_delete": {"primaryScheduleId": "primary_schedule_id", "scheduleId": "schedule_id", "summary": "summary", "description": "description", "operationType": "operation_type", "currentTime": "current_time", "repeatType": "repeat_type", "expireDateType": "expire_date_type", "allDay": "all_day", "rule": "rule", "ruleStartTime": "rule_start_time", "ruleEndTime": "rule_end_time", "startTime": "start_time", "endTime": "end_time", "operator": "operator", "timestamp": "timestamp"},
    "tag_member": {"tagId": "tag_id", "timestamp": "timestamp"},
}


def _parse_event_data(event_type: str, raw_data: dict) -> Union[dict, CallbackEventData]:
    parser_cls = EVENT_DATA_PARSERS.get(event_type)
    if not parser_cls:
        return raw_data

    field_map = FIELD_MAPS.get(event_type, {})
    kwargs: Dict[str, Any] = {}

    for api_key, python_key in field_map.items():
        value = raw_data.get(api_key)
        if value is not None:
            kwargs[python_key] = value

    if event_type == "telephone_track":
        caller_raw = raw_data.get("caller", {})
        callee_raw = raw_data.get("callee", {})
        caller_info = caller_raw.get("mobilePhone", {}) if isinstance(caller_raw, dict) else {}
        callee_info = callee_raw.get("mobilePhone", {}) if isinstance(callee_raw, dict) else {}
        kwargs["caller"] = TelephoneTrackCallerData(
            staff_id=caller_raw.get("staffId", ""),
            country_code=caller_info.get("countryCode", ""),
            number=caller_info.get("number", ""),
        )
        kwargs["callee"] = TelephoneTrackCallerData(
            staff_id=callee_raw.get("staffId", ""),
            country_code=callee_info.get("countryCode", ""),
            number=callee_info.get("number", ""),
        )

    if event_type == "report_location":
        kwargs["location_info"] = raw_data.get("locationInfo", {})

    if event_type == "bot_group_message":
        reminder = raw_data.get("reminder", {})
        if isinstance(reminder, dict):
            kwargs["is_at_me"] = reminder.get("isAtMe", False)
            kwargs["is_at_all"] = reminder.get("isAtAll", False)
            bots_raw = reminder.get("bots")
            if isinstance(bots_raw, list):
                kwargs["bots"] = bots_raw
            staffs_raw = reminder.get("staffs")
            if isinstance(staffs_raw, list):
                kwargs["staffs"] = staffs_raw

    return parser_cls(**kwargs)


def parse_callback_payload(
    encrypted_data: str,
    *,
    encoding_key: str = "",
    verify_signature: bool = False,
    timestamp: str = "",
    nonce: str = "",
    signature: str = "",
    callback_token: str = "",
    known_app_id: str = "",
) -> list[CallbackEvent]:
    """Parse a callback payload into a list of CallbackEvent objects.

    Each event's data field is parsed into a structured dataclass when
    the event_type is recognized, otherwise left as a raw dict.

    Supports two formats:
    1. Plain JSON — pass the JSON string directly (no encoding_key needed)
    2. AES encrypted — pass the dataEncrypt value and encoding_key for
       decryption per 4.10.1.4

    Args:
        encrypted_data: The callback payload (encrypted dataEncrypt value
            if encoding_key is provided, otherwise raw JSON).
        encoding_key: Base64-encoded AES key for decrypting the payload.
            When provided, encrypted_data is treated as AES-encrypted.
        verify_signature: Whether to verify the payload signature.
        timestamp: Timestamp from callback URL query params (for sig verify).
        nonce: Nonce from callback URL query params (for sig verify).
        signature: Expected signature for verification.
        callback_token: Token for signature verification (from developer
            center callback config). Falls back to encoding_key.
    """
    if encoding_key and encrypted_data.strip().startswith("{"):
        try:
            json.loads(encrypted_data)
        except json.JSONDecodeError:
            pass
        else:
            payload_inner = json.loads(encrypted_data)
            data_encrypt = payload_inner.get("dataEncrypt", "")
            if isinstance(data_encrypt, str) and data_encrypt:
                encrypted_data = data_encrypt
            else:
                payload = payload_inner
                if verify_signature:
                    if not verify_callback_signature(
                        timestamp, nonce, signature, encoding_key,
                        data_encrypt=encrypted_data,
                        callback_token=callback_token,
                    ):
                        raise ValueError("Callback signature verification failed")
                return _parse_decrypted_payload(payload)

    if encoding_key:
        if verify_signature:
            data_encrypt = encrypted_data
            if encrypted_data.strip().startswith("{"):
                payload_inner = json.loads(encrypted_data)
                data_encrypt = payload_inner.get("dataEncrypt", "")
            if not verify_callback_signature(
                timestamp, nonce, signature, encoding_key,
                data_encrypt=data_encrypt,
                callback_token=callback_token,
            ):
                raise ValueError("Callback signature verification failed")

        decrypted = decrypt_callback_payload(encrypted_data, encoding_key, known_app_id=known_app_id)
        payload = {
            "orgId": decrypted.get("orgId", ""),
            "appId": decrypted.get("appId", ""),
            "events": decrypted.get("events", []),
        }
        return _parse_decrypted_payload(payload)

    payload = json.loads(encrypted_data)
    if "dataEncrypt" in payload and not encoding_key:
        raise ValueError("Encrypted callback payload requires encoding_key for decryption")
    if verify_signature and not verify_callback_signature(
        timestamp, nonce, signature, encoding_key,
        data_encrypt=encrypted_data,
        callback_token=callback_token,
    ):
        raise ValueError("Callback signature verification failed")

    return _parse_decrypted_payload(payload)


def _parse_decrypted_payload(payload: dict) -> list[CallbackEvent]:
    events: list[CallbackEvent] = []
    event_list = payload.get("events", [])
    if isinstance(event_list, dict):
        event_list = [event_list]

    top_app_id = payload.get("appId", "")
    top_org_id = payload.get("orgId", "")

    for entry in event_list:
        event_type = entry.get("eventType", entry.get("type", ""))
        category = CALLBACK_EVENT_TYPES.get(event_type, "unknown")
        raw_data = entry.get("data", {})
        if not raw_data and event_type:
            raw_data = entry
        parsed_data = _parse_event_data(event_type, raw_data)

        events.append(
            CallbackEvent(
                event_id=entry.get("eventId", entry.get("id", 0)),
                event_type=event_type,
                category=category,
                data=parsed_data,
                app_id=entry.get("appId", top_app_id),
                org_id=entry.get("orgId", top_org_id),
            )
        )

    return events


def verify_callback_signature(
    timestamp: str,
    nonce: str,
    signature: str,
    encoding_key: str,
    data_encrypt: str = "",
    *,
    callback_token: str = "",
) -> bool:
    """Verify callback payload signature per 4.10.1.4.

    dev_data_signature = sha1(sort(token, timestamp, nonce, dataEncrypt))

    When callback_token is provided it is used as the token; otherwise
    encoding_key is used as the token (蓝信开发者中心配置回调地址时
    指定的签名参数).

    Args:
        timestamp: Timestamp from callback URL query params.
        nonce: Nonce from callback URL query params.
        signature: Signature from callback URL query params.
        encoding_key: Encoding key for AES decryption.
        data_encrypt: The encrypted data string (dataEncrypt field value).
        callback_token: Token specified when configuring the callback URL
            in the Lansenger developer center. Falls back to encoding_key.

    Returns:
        True if signature matches, False otherwise.
    """
    token = callback_token or encoding_key
    params = [token, timestamp, nonce, data_encrypt]
    params.sort()
    joined = "".join(params)
    computed = hashlib.sha1(joined.encode("utf-8")).hexdigest()
    return computed == signature


def decrypt_callback_payload(
    encrypted_data: str,
    encoding_key: str,
    *,
    known_app_id: str = "",
) -> dict:
    """Decrypt a callback payload per 4.10.1.4.

    AES-256-CBC, key = Base64_Decode(encoding_key), IV = key[:16].
    Decrypted structure: random(16B) + eventsLen(4B) + orgId + appId + events

    Args:
        encrypted_data: The dataEncrypt value from callback body.
        encoding_key: Base64-encoded AES key from developer center.
        known_app_id: Known appId to help split orgId/appId in the middle
            buffer. If empty, orgId and appId will be left as the raw
            concatenated middle string in orgId and appId="" returned.

    Returns:
        Dict with: random, orgId, appId, events (list), length.

    Raises:
        ValueError: If decryption fails or data is malformed.
    """
    aes_key = _decode_aes_key(encoding_key)
    iv = aes_key[:16]
    raw = _aes_decrypt(base64.b64decode(encrypted_data), aes_key, iv)
    raw = _pkcs7_unpad(raw)

    if len(raw) < 20:
        raise ValueError(f"Decrypted data too short: {len(raw)} bytes (need >= 20)")

    random_str = raw[:16]
    events_len = struct.unpack("!I", raw[16:20])[0]

    total_after_header = len(raw) - 20
    if total_after_header < events_len:
        raise ValueError(f"Remaining data ({total_after_header}B) shorter than declared events length ({events_len}B)")

    events_bytes = raw[20 + total_after_header - events_len:]
    middle_bytes = raw[20:20 + total_after_header - events_len]

    events_data = json.loads(events_bytes.decode("utf-8"))
    if not isinstance(events_data, list):
        events_data = [events_data]

    middle_str = middle_bytes.decode("utf-8")
    org_id, app_id = _split_org_app_id(middle_str, known_app_id)

    return {
        "random": random_str.decode("utf-8", errors="replace"),
        "orgId": org_id,
        "appId": app_id,
        "events": events_data,
        "length": events_len,
    }


def _decode_aes_key(encoding_key: str) -> bytes:
    padded = encoding_key + "=" * (-len(encoding_key) % 4)
    aes_key = base64.b64decode(padded)
    if len(aes_key) not in (16, 24, 32):
        raise ValueError(f"Invalid AES key length: {len(aes_key)} bytes (expected 16, 24, or 32)")
    return aes_key


def _aes_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    try:
        from Crypto.Cipher import AES
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(data)
    except ImportError:
        pass
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(data) + decryptor.finalize()
    except ImportError:
        raise ImportError(
            "AES decryption requires either 'pycryptodome' or 'cryptography' package. "
            "Install one: pip install pycryptodome  OR  pip install cryptography"
        )


def _pkcs7_unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 32:
        raise ValueError(f"Invalid PKCS7 padding: {pad_len}")
    for i in range(pad_len):
        if data[-(i + 1)] != pad_len:
            raise ValueError("Invalid PKCS7 padding bytes")
    return data[:-pad_len]


def _split_org_app_id(middle_str: str, known_app_id: str = "") -> tuple[str, str]:
    if not middle_str:
        return "", ""
    if known_app_id and middle_str.endswith(known_app_id):
        org_id = middle_str[:-len(known_app_id)]
        return org_id, known_app_id
    if known_app_id:
        idx = middle_str.find(known_app_id)
        if idx >= 0:
            return middle_str[:idx], known_app_id
    return middle_str, ""


def get_callback_event_types() -> Dict[str, str]:
    """Return the mapping of callback event types to categories."""
    return CALLBACK_EVENT_TYPES