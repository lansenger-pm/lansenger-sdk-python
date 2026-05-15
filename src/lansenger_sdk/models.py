"""Data models for Lansenger SDK — framework-independent result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SendMessageResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    platform: str = "lansenger"
    msg_type: Optional[str] = None
    operation: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "platform": self.platform}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffBasicInfoResult:
    success: bool
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[int] = None
    signature: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_id: Optional[str] = None
    status: Optional[int] = None
    departments: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    name: Optional[str] = None
    signature: Optional[str] = None
    avatar_id: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[int] = None
    departments: Optional[List[Dict[str, Any]]] = None
    gender: Optional[int] = None
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    login_name: Optional[str] = None
    employee_number: Optional[str] = None
    email: Optional[str] = None
    external_id: Optional[str] = None
    nationality: Optional[str] = None
    birthdate: Optional[str] = None
    id_number: Optional[str] = None
    native_place: Optional[str] = None
    duties: Optional[str] = None
    parties: Optional[str] = None
    address: Optional[str] = None
    mobile_phone: Optional[Dict[str, str]] = None
    extra_phones: Optional[List[Dict[str, str]]] = None
    introduction: Optional[Dict[str, Any]] = None
    education: Optional[List[Dict[str, Any]]] = None
    career: Optional[List[Dict[str, Any]]] = None
    login_ways: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    extra_field_set: Optional[Dict[str, str]] = None
    leaders: Optional[List[str]] = None
    join_date: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    ancestor_groups: Optional[List[List[Dict[str, str]]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.ancestor_groups is not None:
            d["ancestor_groups"] = self.ancestor_groups
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class StaffIdMappingResult:
    success: bool
    staff_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.staff_id is not None:
            d["staff_id"] = self.staff_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class OrgInfoResult:
    success: bool
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    icon_url: Optional[str] = None
    org_max_member_limit: Optional[int] = None
    org_order_type: Optional[int] = None
    org_days_limit: Optional[int] = None
    org_billing_date: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    extra_field_ids: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
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
    staff_info: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
        if self.staff_info is not None:
            d["staff_info"] = self.staff_info
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class QueryGroupsResult:
    success: bool
    total_group_ids: int = 0
    group_ids: List[str] = field(default_factory=list)
    error: Optional[str] = None
    platform: str = "lansenger"
    operation: str = "query_groups"
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
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
    media_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.media_id is not None:
            d["media_id"] = self.media_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DownloadMediaResult:
    success: bool
    data: Optional[bytes] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.data is not None:
            d["size"] = len(self.data)
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
    fields: Optional[List[Dict[str, str]]] = None
    links: Optional[List[Dict[str, str]]] = None
    card_link: str = ""
    pc_card_link: str = ""
    pad_card_link: str = ""
    is_dynamic: bool = False
    head_status_info: Optional[Dict[str, str]] = None
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
    fields: Optional[List[Dict[str, str]]] = None
    link: str = ""
    pc_link: str = ""
    pad_link: str = ""
    card_action: Optional[Dict[str, Any]] = None
    is_group: bool = False
    user_token: str = ""
    sender_id: str = ""


@dataclass
class DynamicCardUpdateParams:
    msg_id: str
    head_status_info: Optional[Dict[str, str]] = None
    links: Optional[List[Dict[str, str]]] = None
    is_last_update: bool = False


@dataclass
class UserTokenResult:
    success: bool
    user_token: Optional[str] = None
    expires_in: int = 7200
    refresh_token: Optional[str] = None
    refresh_expires_in: int = 2592000
    staff_id: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    staff_id: Optional[str] = None
    name: Optional[str] = None
    org_id: Optional[str] = None
    org_name: Optional[str] = None
    avatar_id: Optional[str] = None
    avatar_url: Optional[str] = None
    mobile_phone: Optional[Dict[str, str]] = None
    email: Optional[str] = None
    employee_number: Optional[str] = None
    login_name: Optional[str] = None
    external_id: Optional[str] = None
    department: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    message_id: Optional[str] = None
    invalid_staff: Optional[List[str]] = None
    invalid_department: Optional[List[str]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class BotMessageResult:
    success: bool
    message_id: Optional[str] = None
    invalid_staff: Optional[List[str]] = None
    invalid_department: Optional[List[str]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.message_id is not None:
            d["message_id"] = self.message_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class GroupCreateInfo:
    name: str
    org_id: int
    owner_id: str = ""
    description: str = ""
    avatar_id: str = ""
    staff_id_list: Optional[List[str]] = None
    department_id_list: Optional[List[str]] = None
    apply_request_id: str = ""
    apply_notes: str = ""
    apply_global_unique_id: str = ""
    apply_session_unique_id: str = ""


@dataclass
class CreateGroupResult:
    success: bool
    group_id: Optional[str] = None
    total_members: int = 0
    invalid_staff: Optional[List[str]] = None
    invalid_department: Optional[List[str]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_id: Optional[str] = None
    avatar_url: Optional[str] = None
    owner: Optional[Dict[str, str]] = None
    creator: Optional[Dict[str, str]] = None
    state: Optional[int] = None
    manage_mode: Optional[int] = None
    location_share: Optional[int] = None
    needs_confirm: Optional[int] = None
    is_public: Optional[int] = None
    max_members: Optional[int] = None
    max_history_msg_count: Optional[int] = None
    total_members: Optional[int] = None
    remind_all: Optional[bool] = None
    send_msg_status: Optional[bool] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    members: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total_members": self.total_members}
        if self.members is not None:
            d["members"] = self.members
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UpdateGroupResult:
    success: bool
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UpdateGroupMembersResult:
    success: bool
    total_members: int = 0
    added_staff_count: int = 0
    deleted_staff_count: int = 0
    invalid_staff: Optional[List[str]] = None
    invalid_department: Optional[List[str]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total_members": self.total_members,
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
    group_ids: Optional[List[str]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total_group_ids": self.total_group_ids}
        if self.group_ids is not None:
            d["group_ids"] = self.group_ids
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class IsInGroupResult:
    success: bool
    is_in_group: bool = False
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "is_in_group": self.is_in_group}
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentDetailResult:
    success: bool
    id: Optional[str] = None
    name: Optional[str] = None
    external_id: Optional[str] = None
    parent_id: Optional[str] = None
    order: Optional[float] = None
    has_children: Optional[bool] = None
    normal_members: Optional[int] = None
    inactive_members: Optional[int] = None
    frozen_members: Optional[int] = None
    deleted_members: Optional[int] = None
    tags: Optional[List[str]] = None
    ancestor_departments: Optional[List[Dict[str, str]]] = None
    leaders: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    phones: Optional[List[str]] = None
    addresses: Optional[List[str]] = None
    introductions: Optional[List[str]] = None
    dept_type: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    departments: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.departments is not None:
            d["departments"] = self.departments
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskCreateResult:
    success: bool
    todotask_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.todotask_id is not None:
            d["todotask_id"] = self.todotask_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskInfoResult:
    success: bool
    todotask_id: Optional[str] = None
    source_id: Optional[str] = None
    title: Optional[str] = None
    desc: Optional[str] = None
    status: Optional[str] = None
    type: Optional[int] = None
    link: Optional[str] = None
    pc_link: Optional[str] = None
    sender_id: Optional[str] = None
    executor_ids: Optional[List[str]] = None
    create_time: Optional[str] = None
    app_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    todotask_list: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total": self.total}
        if self.todotask_list is not None:
            d["todotask_list"] = self.todotask_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskStatusCountResult:
    success: bool
    status_counts: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.status_counts is not None:
            d["status_counts"] = self.status_counts
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class TodoTaskExecutorListResult:
    success: bool
    total: int = 0
    executor_list: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total": self.total}
        if self.executor_list is not None:
            d["executor_list"] = self.executor_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class CalendarPrimaryResult:
    success: bool
    calendar_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[str] = None
    color: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    schedule_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.schedule_id is not None:
            d["schedule_id"] = self.schedule_id
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleInfoResult:
    success: bool
    schedule_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    repeat_type: Optional[str] = None
    all_day: Optional[str] = None
    start_time: Optional[Dict[str, Any]] = None
    end_time: Optional[Dict[str, Any]] = None
    creator: Optional[Dict[str, Any]] = None
    rsvp_status: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
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
    schedule_list: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success}
        if self.schedule_list is not None:
            d["schedule_list"] = self.schedule_list
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ScheduleAttendeesResult:
    success: bool
    total: int = 0
    attendees: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "total": self.total}
        if self.attendees is not None:
            d["attendees"] = self.attendees
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class DepartmentStaffsResult:
    success: bool
    has_more: bool = False
    total: int = 0
    staffs: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"success": self.success, "has_more": self.has_more, "total": self.total}
        if self.staffs is not None:
            d["staffs"] = self.staffs
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class ChatStaffInfo:
    staff_id: str = ""
    staff_name: str = ""
    sector_names: Optional[List[str]] = None


@dataclass
class ChatGroupInfo:
    group_id: str = ""
    group_name: str = ""


@dataclass
class ChatListResult:
    success: bool
    staff_infos: Optional[List[ChatStaffInfo]] = None
    group_infos: Optional[List[ChatGroupInfo]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessageInfo:
    send_time: str = ""
    sender: str = ""
    message_type: str = ""
    content: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessagesResult:
    success: bool
    has_more: bool = False
    total: int = 0
    last_version: str = ""
    name: str = ""
    chat_type: str = ""
    messages: Optional[List[ChatMessageInfo]] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None