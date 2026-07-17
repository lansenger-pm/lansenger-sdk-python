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
