"""Lansenger callback event parsing and verification.

This module handles parsing and verifying callback payloads sent by the
Lansenger platform to your app's HTTP callback endpoint. It provides event
type categorization, structured data parsing, and signature verification
(placeholder).

No HTTP calls are made — this is purely data parsing.
"""

from __future__ import annotations

import json
import logging
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
    "staff_info": {"staffId": "staff_id", "name": "name", "mobile": "mobile", "state": "state", "sex": "sex", "email": "email", "employId": "employee_id", "avatarId": "avatar_id", "timestamp": "timestamp"},
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
    "bot_private_message": {"from": "from_id", "entryId": "entry_id", "msgType": "msg_type", "msgData": "msg_data"},
    "bot_group_message": {"from": "from_id", "entryId": "entry_id", "msgType": "msg_type", "msgData": "msg_data", "groupId": "group_id", "fromType": "from_type", "groupName": "group_name", "botCreator": "bot_creator", "msgId": "msg_id", "botId": "bot_id", "isAtMe": "is_at_me", "isAtAll": "is_at_all"},
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

    return parser_cls(**kwargs)


def parse_callback_payload(
    encrypted_data: str,
    *,
    encoding_key: str = "",
    verify_signature: bool = False,
    timestamp: str = "",
    nonce: str = "",
    signature: str = "",
) -> list[CallbackEvent]:
    """Parse a callback payload into a list of CallbackEvent objects.

    Each event's data field is parsed into a structured dataclass when
    the event_type is recognized, otherwise left as a raw dict.

    Args:
        encrypted_data: The callback payload (encrypted if encoding_key is
            provided, otherwise raw JSON).
        encoding_key: Key for decrypting the payload (placeholder — raises
            NotImplementedError if provided).
        verify_signature: Whether to verify the payload signature.
        timestamp: Timestamp for signature verification.
        nonce: Nonce for signature verification.
        signature: Expected signature for verification.
    """
    if encoding_key:
        raise NotImplementedError(
            "Payload decryption is not yet implemented. "
            "Pass the already-decrypted JSON string as encrypted_data."
        )

    if verify_signature and not verify_callback_signature(
        timestamp, nonce, signature, encoding_key
    ):
        raise ValueError("Callback signature verification failed")

    payload = json.loads(encrypted_data)

    events: list[CallbackEvent] = []
    event_list = payload.get("events", [])
    if isinstance(event_list, dict):
        event_list = [event_list]

    for entry in event_list:
        event_type = entry.get("eventType", "")
        category = CALLBACK_EVENT_TYPES.get(event_type, "unknown")
        raw_data = entry.get("data", {})
        parsed_data = _parse_event_data(event_type, raw_data)

        events.append(
            CallbackEvent(
                event_id=entry.get("eventId", 0),
                event_type=event_type,
                category=category,
                data=parsed_data,
                app_id=entry.get("appId", ""),
                org_id=entry.get("orgId", ""),
            )
        )

    return events


def verify_callback_signature(
    timestamp: str,
    nonce: str,
    signature: str,
    encoding_key: str,
) -> bool:
    """Verify callback payload signature.

    Placeholder implementation — always returns True. The actual verification
    algorithm requires the encryption spec from section 4.10.1.4 of the
    Lansenger API documentation.
    """
    return True


def get_callback_event_types() -> Dict[str, str]:
    """Return the mapping of callback event types to categories."""
    return CALLBACK_EVENT_TYPES