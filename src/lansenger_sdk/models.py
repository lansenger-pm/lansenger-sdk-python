"""Data models for Lansenger SDK — framework-independent result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SendMessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None
    platform: str = "lansenger"
    msg_type: str | None = None
    operation: str | None = None
    raw_response: dict[str, Any] | None = None
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "platform": self.platform}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffBasicInfoResult:
    success: bool
    org_id: str | None = None
    org_name: str | None = None
    name: str | None = None
    gender: int | None = None
    signature: str | None = None
    avatar_url: str | None = None
    avatar_id: str | None = None
    status: int | None = None
    departments: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("org_id", "org_name", "name", "gender", "signature",
                     "avatar_url", "avatar_id", "status", "departments"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffDetailResult:
    success: bool
    name: str | None = None
    signature: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    status: int | None = None
    departments: list[dict[str, Any]] | None = None
    gender: int | None = None
    org_id: str | None = None
    org_name: str | None = None
    login_name: str | None = None
    employee_number: str | None = None
    email: str | None = None
    external_id: str | None = None
    nationality: str | None = None
    birthdate: str | None = None
    id_number: str | None = None
    native_place: str | None = None
    duties: str | None = None
    parties: str | None = None
    address: str | None = None
    mobile_phone: dict[str, str] | None = None
    extra_phones: list[dict[str, str]] | None = None
    introduction: dict[str, Any] | None = None
    education: list[dict[str, Any]] | None = None
    career: list[dict[str, Any]] | None = None
    login_ways: list[int] | None = None
    tags: list[str] | None = None
    extra_field_set: dict[str, str] | None = None
    leaders: list[str] | None = None
    join_date: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("name", "signature", "avatar_id", "avatar_url", "status",
                     "departments", "gender", "org_id", "org_name", "login_name",
                     "employee_number", "email", "external_id", "nationality",
                     "birthdate", "id_number", "native_place", "duties", "parties",
                     "address", "mobile_phone", "extra_phones", "introduction",
                     "education", "career", "login_ways", "tags", "extra_field_set",
                     "leaders", "join_date"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentAncestorsResult:
    success: bool
    ancestor_groups: list[list[dict[str, str]]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.ancestor_groups is not None:
            d["ancestor_groups"] = self.ancestor_groups
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffIdMappingResult:
    success: bool
    staff_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.staff_id is not None:
            d["staff_id"] = self.staff_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class OrgInfoResult:
    success: bool
    org_id: str | None = None
    org_name: str | None = None
    icon_url: str | None = None
    org_max_member_limit: int | None = None
    org_order_type: int | None = None
    org_days_limit: int | None = None
    org_billing_date: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("org_id", "org_name", "icon_url", "org_max_member_limit",
                     "org_order_type", "org_days_limit", "org_billing_date"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ExtraFieldIdsResult:
    success: bool
    has_more: bool = False
    total: int = 0
    extra_field_ids: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
        if self.extra_field_ids is not None:
            d["extra_field_ids"] = self.extra_field_ids
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffSearchResult:
    success: bool
    has_more: bool = False
    total: int = 0
    staff_info: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
        if self.staff_info is not None:
            d["staff_info"] = self.staff_info
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QueryGroupsResult:
    success: bool
    total_group_ids: int = 0
    group_ids: list[str] = field(default_factory=list)
    error: str | None = None
    platform: str = "lansenger"
    operation: str = "query_groups"
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "success": self.success,
            "total_group_ids": self.total_group_ids,
            "group_ids": self.group_ids,
            "platform": self.platform,
            "operation": self.operation,
        }
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UploadMediaResult:
    success: bool
    media_id: str | None = None
    created_time: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.media_id is not None:
            d["media_id"] = self.media_id
        if self.created_time is not None:
            d["created_time"] = self.created_time
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DownloadMediaResult:
    success: bool
    data: bytes | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            d["size"] = len(self.data)
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class MediaPathResult:
    success: bool
    media_path: str | None = None
    name: str | None = None
    type: str | None = None
    size: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("media_path", "name", "type", "size"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class AppCardParams:
    body_title: str
    chat_id: str = ""
    head_title: str = ""
    body_sub_title: str = ""
    body_content: str = ""
    signature: str = ""
    fields: list[dict[str, str]] | None = None
    links: list[dict[str, str]] | None = None
    card_link: str = ""
    pc_card_link: str = ""
    pad_card_link: str = ""
    is_dynamic: bool = False
    head_status_info: dict[str, str] | None = None
    staff_id: str = ""
    head_icon_url: str = ""
    is_group: bool = False
    user_token: str = ""
    sender_id: str = ""


@dataclass
class LinkCardParams:
    chat_id: str = ""
    title: str = ""
    link: str = ""
    description: str = ""
    icon_link: str = ""
    pc_link: str = ""
    pad_link: str = ""
    from_name: str = ""
    from_icon_link: str = ""
    is_group: bool = False
    user_token: str = ""
    sender_id: str = ""


@dataclass
class OaCardParams:
    chat_id: str = ""
    head: str = ""
    title: str = ""
    sub_title: str = ""
    staff_id: str = ""
    fields: list[dict[str, str]] | None = None
    link: str = ""
    pc_link: str = ""
    pad_link: str = ""
    card_action: dict[str, Any] | None = None
    is_group: bool = False
    user_token: str = ""
    sender_id: str = ""


@dataclass
class DynamicCardUpdateParams:
    msg_id: str
    head_status_info: dict[str, str] | None = None
    links: list[dict[str, str]] | None = None
    is_last_update: bool = False


@dataclass
class ApproveCardParams:
    """ApproveCard (审批卡片) parameters — 4.6.4.13."""
    chat_id: str = ""
    body_title: str = ""  # required
    body_content: str = ""  # required, markdown text
    # head
    head_title: str = ""
    head_icon_link: str = ""
    head_icon_id: str = ""
    head_status_describe: str = ""
    head_status_icon: int = 0  # 1=实心圆
    head_status_icon_link: str = ""
    head_status_colour: str = ""
    # body
    body_format_type: int = 1  # 1=MARK_DOWN
    fields: list[dict[str, str]] | None = None  # [{"key","value"},...]
    # reminder
    reminder_all: bool = False
    reminder_user_ids: list[str] | None = None
    reminder_bot_ids: list[str] | None = None
    # card link
    card_link: str = ""
    card_link_for_pc: str = ""
    card_link_for_pad: str = ""
    # buttons
    buttons: list[dict[str, Any]] | None = None
    # expire
    expire_time: int = 0  # seconds, max 30 days; 0=default 7 days
    # channel
    is_group: bool = False
    user_token: str = ""
    sender_id: str = ""
    is_bot_channel: bool = False  # True → bot channel, False → smart_bot channel


@dataclass
class ApproveCardUpdateParams:
    """Dynamic update params for approveCard — 4.6.4.12."""
    msg_id: str
    # headStatus
    head_status_describe: str = ""
    head_status_icon: int = 0
    head_status_icon_link: str = ""
    head_status_colour: str = ""
    # buttons
    buttons: list[dict[str, Any]] | None = None


@dataclass
class UserTokenResult:
    success: bool
    user_token: str | None = None
    expires_in: int = 7200
    refresh_token: str | None = None
    refresh_expires_in: int = 2592000
    staff_id: str | None = None
    scope: str | None = None
    state: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.user_token is not None:
            d["user_token"] = self.user_token
            d["expires_in"] = self.expires_in
        if self.refresh_token is not None:
            d["refresh_token"] = self.refresh_token
            d["refresh_expires_in"] = self.refresh_expires_in
        if self.staff_id is not None:
            d["staff_id"] = self.staff_id
        if self.scope is not None:
            d["scope"] = self.scope
        if self.state is not None:
            d["state"] = self.state
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UserInfoResult:
    success: bool
    staff_id: str | None = None
    name: str | None = None
    org_id: str | None = None
    org_name: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    mobile_phone: dict[str, str] | None = None
    email: str | None = None
    employee_number: str | None = None
    login_name: str | None = None
    external_id: str | None = None
    department: list[dict[str, str]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.staff_id is not None:
            d["staff_id"] = self.staff_id
        if self.name is not None:
            d["name"] = self.name
        if self.org_id is not None:
            d["org_id"] = self.org_id
        if self.org_name is not None:
            d["org_name"] = self.org_name
        if self.avatar_url is not None:
            d["avatar_url"] = self.avatar_url
        if self.email is not None:
            d["email"] = self.email
        if self.employee_number is not None:
            d["employee_number"] = self.employee_number
        if self.login_name is not None:
            d["login_name"] = self.login_name
        if self.external_id is not None:
            d["external_id"] = self.external_id
        if self.mobile_phone is not None:
            d["mobile_phone"] = self.mobile_phone
        if self.department is not None:
            d["department"] = self.department
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class AccountMessageResult:
    success: bool
    message_id: str | None = None
    invalid_staff: list[str] | None = None
    invalid_department: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.invalid_staff is not None:
            d["invalid_staff"] = self.invalid_staff
        if self.invalid_department is not None:
            d["invalid_department"] = self.invalid_department
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UserMessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BotMessageResult:
    success: bool
    message_id: str | None = None
    invalid_staff: list[str] | None = None
    invalid_department: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.invalid_staff is not None:
            d["invalid_staff"] = self.invalid_staff
        if self.invalid_department is not None:
            d["invalid_department"] = self.invalid_department
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StreamMessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class GroupCreateInfo:
    name: str
    org_id: str
    owner_id: str = ""
    description: str = ""
    avatar_id: str = ""
    staff_id_list: list[str] | None = None
    department_id_list: list[str] | None = None
    apply_request_id: str = ""
    apply_notes: str = ""
    apply_global_unique_id: str = ""
    apply_session_unique_id: str = ""


@dataclass
class CreateGroupResult:
    success: bool
    group_id: str | None = None
    total_members: int = 0
    invalid_staff: list[str] | None = None
    invalid_department: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.group_id is not None:
            d["group_id"] = self.group_id
        d["total_members"] = self.total_members
        if self.invalid_staff is not None:
            d["invalid_staff"] = self.invalid_staff
        if self.invalid_department is not None:
            d["invalid_department"] = self.invalid_department
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class GroupInfoResult:
    success: bool
    name: str | None = None
    description: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    owner: dict[str, str] | None = None
    creator: dict[str, str] | None = None
    state: int | None = None
    manage_mode: int | None = None
    location_share: int | None = None
    needs_confirm: int | None = None
    is_public: int | None = None
    max_members: int | None = None
    max_history_msg_count: int | None = None
    total_members: int | None = None
    remind_all: bool | None = None
    send_msg_status: bool | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("name", "description", "avatar_id", "avatar_url", "owner",
                     "creator", "state", "manage_mode", "location_share",
                     "needs_confirm", "is_public", "max_members",
                     "max_history_msg_count", "total_members", "remind_all",
                     "send_msg_status"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class GroupMemberResult:
    success: bool
    total_members: int = 0
    members: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total_members": self.total_members}
        if self.members is not None:
            d["members"] = self.members
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UpdateGroupResult:
    success: bool
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UpdateGroupMembersResult:
    success: bool
    total_members: int = 0
    added_staff_count: int = 0
    deleted_staff_count: int = 0
    invalid_staff: list[str] | None = None
    invalid_department: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total_members": self.total_members,
                             "added_staff_count": self.added_staff_count,
                             "deleted_staff_count": self.deleted_staff_count}
        if self.invalid_staff is not None:
            d["invalid_staff"] = self.invalid_staff
        if self.invalid_department is not None:
            d["invalid_department"] = self.invalid_department
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class GroupListResult:
    success: bool
    total_group_ids: int = 0
    group_ids: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total_group_ids": self.total_group_ids}
        if self.group_ids is not None:
            d["group_ids"] = self.group_ids
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class IsInGroupResult:
    success: bool
    is_in_group: bool = False
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "is_in_group": self.is_in_group}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentDetailResult:
    success: bool
    id: str | None = None
    name: str | None = None
    external_id: str | None = None
    parent_id: str | None = None
    order: float | None = None
    has_children: bool | None = None
    normal_members: int | None = None
    inactive_members: int | None = None
    frozen_members: int | None = None
    deleted_members: int | None = None
    tags: list[str] | None = None
    ancestor_departments: list[dict[str, str]] | None = None
    leaders: list[str] | None = None
    emails: list[str] | None = None
    phones: list[str] | None = None
    addresses: list[str] | None = None
    introductions: list[str] | None = None
    dept_type: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("id", "name", "external_id", "parent_id", "order",
                     "has_children", "normal_members", "inactive_members",
                     "frozen_members", "deleted_members", "tags",
                     "ancestor_departments", "leaders", "emails", "phones",
                     "addresses", "introductions", "dept_type"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentChildrenResult:
    success: bool
    departments: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.departments is not None:
            d["departments"] = self.departments
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskCreateResult:
    success: bool
    todotask_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.todotask_id is not None:
            d["todotask_id"] = self.todotask_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskInfoResult:
    success: bool
    todotask_id: str | None = None
    source_id: str | None = None
    title: str | None = None
    desc: str | None = None
    status: str | None = None
    type: int | None = None
    link: str | None = None
    pc_link: str | None = None
    sender_id: str | None = None
    executor_ids: list[str] | None = None
    create_time: str | None = None
    app_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("todotask_id", "source_id", "title", "desc", "status",
                     "type", "link", "pc_link", "sender_id", "executor_ids",
                     "create_time", "app_id"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskListResult:
    success: bool
    total: int = 0
    todotask_list: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.todotask_list is not None:
            d["todotask_list"] = self.todotask_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskStatusCountResult:
    success: bool
    status_counts: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.status_counts is not None:
            d["status_counts"] = self.status_counts
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskExecutorListResult:
    success: bool
    total: int = 0
    executor_list: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.executor_list is not None:
            d["executor_list"] = self.executor_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalTodoSaveResult:
    success: bool
    todo_code: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.todo_code is not None:
            d["todo_code"] = self.todo_code
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalTodoListResult:
    success: bool
    page_no: int = 0
    page_size: int = 0
    pages: int = 0
    total: int = 0
    has_more: bool = False
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "success": self.success,
            "page_no": self.page_no,
            "page_size": self.page_size,
            "pages": self.pages,
            "total": self.total,
            "has_more": self.has_more,
        }
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalTodoResourceResult:
    success: bool
    file_name: str | None = None
    mime_type: str | None = None
    suffix: str | None = None
    size: int | None = None
    md5: str | None = None
    extension_info: str | None = None
    resource_id: str | None = None
    download_url: str | None = None
    image_thumbnail_list: dict[str, Any] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in (
            "file_name", "mime_type", "suffix", "size", "md5",
            "extension_info", "resource_id", "download_url",
            "image_thumbnail_list",
        ):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalTodoUrlResult:
    success: bool
    url: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.url is not None:
            d["url"] = self.url
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class CalendarPrimaryResult:
    success: bool
    calendar_id: str | None = None
    summary: str | None = None
    description: str | None = None
    permissions: str | None = None
    color: str | None = None
    type: str | None = None
    role: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("calendar_id", "summary", "description", "permissions",
                      "color", "type", "role"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleCreateResult:
    success: bool
    schedule_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.schedule_id is not None:
            d["schedule_id"] = self.schedule_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleInfoResult:
    success: bool
    schedule_id: str | None = None
    summary: str | None = None
    description: str | None = None
    repeat_type: str | None = None
    all_day: str | None = None
    start_time: dict[str, Any] | None = None
    end_time: dict[str, Any] | None = None
    creator: dict[str, Any] | None = None
    rsvp_status: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("schedule_id", "summary", "description", "repeat_type",
                      "all_day", "start_time", "end_time", "creator",
                      "rsvp_status"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleListResult:
    success: bool
    schedule_list: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.schedule_list is not None:
            d["schedule_list"] = self.schedule_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleAttendeesResult:
    success: bool
    total: int = 0
    attendees: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.attendees is not None:
            d["attendees"] = self.attendees
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleUpdateResult:
    success: bool
    schedule_ids: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.schedule_ids is not None:
            d["schedule_ids"] = self.schedule_ids
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleAttendeeMetaResult:
    success: bool
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleAttendeesUpdateResult:
    """4.23.19 — batch add/delete schedule attendees in one call."""
    success: bool
    schedule_ids: list[str] | None = None
    failed_attendees: list[str] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.schedule_ids is not None:
            d["schedule_ids"] = self.schedule_ids
        if self.failed_attendees is not None:
            d["failed_attendees"] = self.failed_attendees
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BotCommandResult:
    """4.37 — bot command create/delete result."""
    success: bool
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BotCommandQueryResult:
    """4.37.2 — query bot commands result."""
    success: bool
    scope_type: int | None = None
    chat_id: str | None = None
    chat_type: str | None = None
    staff_id: str | None = None
    commands: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("scope_type", "chat_id", "chat_type", "staff_id"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.commands is not None:
            d["commands"] = self.commands
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalAppCreateResult:
    """4.38.1 — create personal app result."""
    success: bool
    app_id: str | None = None
    secret: str | None = None
    apigw_addr: str | None = None
    passport_addr: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("app_id", "secret", "apigw_addr", "passport_addr"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalAppInfoResult:
    """4.38.3 — fetch personal app info result."""
    success: bool
    app_id: str | None = None
    name: str | None = None
    avatar_id: str | None = None
    description: str | None = None
    apigw_addr: str | None = None
    passport_addr: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("app_id", "name", "avatar_id", "description",
                      "apigw_addr", "passport_addr"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class PersonalAppListResult:
    """4.38.5 — list personal apps result."""
    success: bool
    app_list: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.app_list is not None:
            d["app_list"] = self.app_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentStaffsResult:
    success: bool
    has_more: bool = False
    total: int = 0
    staffs: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
        if self.staffs is not None:
            d["staffs"] = self.staffs
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ChatStaffInfo:
    staff_id: str = ""
    staff_name: str = ""
    sector_names: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"staff_id": self.staff_id, "staff_name": self.staff_name}
        if self.sector_names is not None:
            d["sector_names"] = self.sector_names
        return d


@dataclass
class ChatGroupInfo:
    group_id: str = ""
    group_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"group_id": self.group_id, "group_name": self.group_name}
        return d


@dataclass
class ChatListResult:
    success: bool
    staff_infos: list[ChatStaffInfo] | None = None
    group_infos: list[ChatGroupInfo] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.staff_infos is not None:
            d["staff_infos"] = [s.to_dict() for s in self.staff_infos]
        if self.group_infos is not None:
            d["group_infos"] = [g.to_dict() for g in self.group_infos]
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ChatMessageInfo:
    send_time: str = ""
    sender: str = ""
    message_type: str = ""
    content: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"send_time": self.send_time, "sender": self.sender, "message_type": self.message_type}
        if self.content is not None:
            d["content"] = self.content
        return d

    def plain_text(self) -> str:
        if self.content is None:
            return ""
        if isinstance(self.content, str):
            return self.content
        if isinstance(self.content, dict):
            format_text = self.content.get("formatText")
            if isinstance(format_text, dict):
                return format_text.get("content", "")
            text = self.content.get("text")
            if isinstance(text, str):
                return text
        return ""


@dataclass
class ChatMessagesResult:
    success: bool
    has_more: bool = False
    total: int = 0
    last_version: str = ""
    name: str = ""
    chat_type: str = ""
    retryable: bool = False
    messages: list[ChatMessageInfo] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total, "last_version": self.last_version, "name": self.name, "chat_type": self.chat_type}
        if self.messages is not None:
            d["messages"] = [m.to_dict() for m in self.messages]
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class NoticeSendResult:
    """通知系统 /xtra/notice/server/openapi/v1/send — send notice result."""

    success: bool
    notice_code: str | None = None
    notice_id: int | None = None
    title: str | None = None
    notice_type: int | None = None
    content_type: int | None = None
    content_abstract: str | None = None
    notice_link: str | None = None
    notice_status: int | None = None
    confirm_status: int | None = None
    publish_time: int | None = None
    publish_user_id: str | None = None
    publish_user_name: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in (
            "notice_code", "notice_id", "title", "notice_type", "content_type",
            "content_abstract", "notice_link", "notice_status", "confirm_status",
            "publish_time", "publish_user_id", "publish_user_name",
        ):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class NoticeAccountListResult:
    """通知系统 /xtra/notice/server/openapi/v1/notice/account — official account list result."""

    success: bool
    total: int = 0
    accounts: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.accounts is not None:
            d["accounts"] = self.accounts
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireSaveResult:
    """问卷系统 /v1/saveQuestionnaire — create/update questionnaire result."""

    success: bool
    questionnaire_code: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.questionnaire_code is not None:
            d["questionnaire_code"] = self.questionnaire_code
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireQuestionSaveResult:
    """问卷系统 /v1/saveQuestionList — batch save questions result."""

    success: bool
    saved_count: int = 0
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "saved_count": self.saved_count}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireQuestionDeleteResult:
    """问卷系统 /v1/deleteQuestion — delete question result."""

    success: bool
    deleted: bool = False
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "deleted": self.deleted}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireOpResult:
    """问卷系统 /v1/publish|withdraw|finish|delete — boolean operation result."""

    success: bool
    done: bool = False
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "done": self.done}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireDetailResult:
    """问卷系统 /v1/detail 与 /v1/detailWithoutAuth（brief，questions=None）— detail result."""

    success: bool
    questionnaire_id: int | None = None
    code: str | None = None
    title: str | None = None
    status: int | None = None
    account_type: int | None = None
    account_code: str | None = None
    answer_user_count: int | None = None
    answer_user_times: int | None = None
    question_count: int | None = None
    questions: list[dict[str, Any]] | None = None
    publish_time: int | None = None
    publish_user_name: str | None = None
    create_user_name: str | None = None
    create_time: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in (
            "questionnaire_id", "code", "title", "status", "account_type", "account_code",
            "answer_user_count", "answer_user_times", "question_count", "questions",
            "publish_time", "publish_user_name", "create_user_name", "create_time",
        ):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireAnswerUrlResult:
    """问卷系统 /v1/getAnswerUrl — answer page URL result."""

    success: bool
    url: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.url is not None:
            d["url"] = self.url
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireCopyResult:
    """问卷系统 /v1/copy — copy result."""

    success: bool
    new_code: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.new_code is not None:
            d["new_code"] = self.new_code
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireQueryListResult:
    """问卷系统 /v1/queryList — batch query by codes result."""

    success: bool
    total: int = 0
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireAccountListResult:
    """问卷系统 /v1/userOfficeAccountList — manageable office accounts result."""

    success: bool
    total: int = 0
    accounts: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.accounts is not None:
            d["accounts"] = self.accounts
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnairePageResult:
    """问卷系统 /v1/createList|myCreateList|participationList|answerList|answerData — PageResult."""

    success: bool
    page_no: int = 0
    page_size: int = 0
    pages: int = 0
    total: int = 0
    has_more: bool = False
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "success": self.success, "page_no": self.page_no, "page_size": self.page_size,
            "pages": self.pages, "total": self.total, "has_more": self.has_more,
        }
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireAnswerDetailResult:
    """问卷系统 /v1/answerDetail 与 /v1/lastAnswerDetail — answer detail result."""

    success: bool
    answer_code: str | None = None
    answer_user_id: str | None = None
    answer_user_name: str | None = None
    answer_status: int | None = None
    answer_type: int | None = None
    answer_use_time: int | None = None
    answer_question_count: int | None = None
    answer_commit_time: int | None = None
    questionnaire: dict[str, Any] | None = None
    questions: list[dict[str, Any]] | None = None
    answers: dict[str, Any] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in (
            "answer_code", "answer_user_id", "answer_user_name", "answer_status", "answer_type",
            "answer_use_time", "answer_question_count", "answer_commit_time",
            "questionnaire", "questions", "answers",
        ):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireRecordResult:
    """问卷系统 /v1/lastAnswerRecord — last answer record (main table) result."""

    success: bool
    record_id: int | None = None
    record_code: str | None = None
    answer_user_id: str | None = None
    answer_user_name: str | None = None
    answer_status: int | None = None
    answer_type: int | None = None
    answer_use_time: int | None = None
    answer_question_count: int | None = None
    answer_commit_time: int | None = None
    stats_status: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in (
            "record_id", "record_code", "answer_user_id", "answer_user_name", "answer_status",
            "answer_type", "answer_use_time", "answer_question_count", "answer_commit_time",
            "stats_status",
        ):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QuestionnaireUploadUrlResult:
    """问卷系统 /v1/upload — presigned upload URL result."""

    success: bool
    url: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.url is not None:
            d["url"] = self.url
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomListResult:
    """会议室预定 V2 /v2/roomList 与 /v2/myReserveList — PageInfo 结果。"""

    success: bool
    count: int = 0
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "count": self.count}
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomDetailResult:
    """会议室预定 V2 /v2/roomDetail — 会议室详情（字段子集，其余见 raw_response）。"""

    success: bool
    room_id: str | None = None
    name: str | None = None
    status: str | None = None
    people_num: int | None = None
    can_reserve_flag: str | None = None
    address: str | None = None
    area_name: str | None = None
    grading_id: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("room_id", "name", "status", "people_num", "can_reserve_flag", "address", "area_name", "grading_id"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomScheduleResult:
    """会议室预定 V2 /v2/roomSchedule — 当日预订与停用信息。"""

    success: bool
    room_id: str | None = None
    name: str | None = None
    people_num: int | None = None
    can_reserve_flag: str | None = None
    reserves: list[dict[str, Any]] | None = None
    deactivations: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("room_id", "name", "people_num", "can_reserve_flag", "reserves", "deactivations"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomReserveDetailResult:
    """会议室预定 V2 /v2/reserveDetail — 预订详情（字段子集，参会人/审批流见 raw_response）。"""

    success: bool
    reserve_id: str | None = None
    boardroom_name: str | None = None
    meeting_name: str | None = None
    status: str | None = None
    reserve_time_start: str | None = None
    reserve_time_end: str | None = None
    reserve_time: str | None = None
    reserve_user_name: str | None = None
    people_number: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("reserve_id", "boardroom_name", "meeting_name", "status", "reserve_time_start", "reserve_time_end", "reserve_time", "reserve_user_name", "people_number"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomReserveResult:
    """会议室预定 V2 /v2/reserveRoom 与 /v2/editReserve — 预订/修改结果。"""

    success: bool
    reserve_id: str | None = None
    reserve_code: str | None = None
    boardroom_name: str | None = None
    meeting_name: str | None = None
    status: str | None = None
    reserve_time_start: str | None = None
    reserve_time_end: str | None = None
    reserve_time: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for key in ("reserve_id", "reserve_code", "boardroom_name", "meeting_name", "status", "reserve_time_start", "reserve_time_end", "reserve_time"):
            v = getattr(self, key)
            if v is not None:
                d[key] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomOpResult:
    """会议室预定 V2 /v2/reserveCancel 与 /v2/confirmSign — Boolean 操作结果。"""

    success: bool
    done: bool = False
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "done": self.done}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomGradingListResult:
    """会议室预定 V2 /v2/gradingList — 可见分级列表（id 即 gradingId）。"""

    success: bool
    total: int = 0
    gradings: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.gradings is not None:
            d["gradings"] = self.gradings
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BoardroomAreaListResult:
    """会议室预定 V2 /v2/areaOfficeList — 分级下办公区列表。"""

    success: bool
    total: int = 0
    areas: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "total": self.total}
        if self.areas is not None:
            d["areas"] = self.areas
        if self.error is not None:
            d["error"] = self.error
        return d


# ── Videoconference (视频会议开放能力) ──────────────────────────────────


@dataclass
class VideoconferenceOpResult:
    """视频会议 Boolean 操作（create 系列 op 端点：取消/结束/会控/邀请/事件订阅）。"""

    success: bool
    done: bool = False
    message: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "done": self.done}
        if self.message is not None:
            d["message"] = self.message
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceDetailResult:
    """视频会议 /meeting/create、/meeting/detail — 会议详情。"""

    success: bool
    mid: int | None = None
    subject: str | None = None
    meeting_number: str | None = None
    start_time: int | None = None
    stop_time: int | None = None
    type: int | None = None
    status: int | None = None
    admin: str | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for k in ("mid", "subject", "meeting_number", "start_time", "stop_time",
                  "type", "status", "admin"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceListResult:
    """视频会议分页列表（meeting/list、record/list、simplerecord、fixroom、history、active、member/list）。"""

    success: bool
    offset: int = 0
    total: int = 0
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success, "offset": self.offset, "total": self.total}
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceStatusListResult:
    """视频会议 /meeting/status/fetchmore — 批量会议状态。"""

    success: bool
    statuses: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.statuses is not None:
            d["statuses"] = self.statuses
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceParamResult:
    """视频会议 /meeting/param/fetch — 会议参数信息。"""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            d["data"] = self.data
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceVodListResult:
    """视频会议 /meeting/vod/list — 会议录像列表。"""

    success: bool
    items: list[dict[str, Any]] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.items is not None:
            d["items"] = self.items
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceVodUrlResult:
    """视频会议 /vod/url/download/fetch — 录像下载链接（最多 3 个）。"""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        if self.data is not None:
            d["data"] = self.data
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class VideoconferenceConfResult:
    """视频会议 /conf/fetch — 组织视频会议配置（PRS ≥3.8）。"""

    success: bool
    max_person: int | None = None
    default_max_person: int | None = None
    allowed_record_flag: int | None = None
    force_passwd_flag: int | None = None
    space_size: int | None = None
    error: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"success": self.success}
        for k in ("max_person", "default_max_person", "allowed_record_flag",
                  "force_passwd_flag", "space_size"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        if self.error is not None:
            d["error"] = self.error
        return d
