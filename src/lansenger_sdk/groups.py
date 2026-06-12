"""Lansenger groups V2 API — group creation, info, membership, and listing operations.

These APIs are available to org bots/apps (not personal bots). They require
appToken for authentication, and some optionally accept userToken for
user-scoped data access.

Endpoints:
1. POST /v2/groups/create                        — create a new group
2. GET  /v2/groups/{group_id}/info/fetch          — group info
3. GET  /v2/groups/{group_id}/members/fetch       — group members (paginated)
4. GET  /v2/groups/fetch                          — group ID list (paginated)
5. GET  /v2/groups/{group_id}/members/is_in_group — check if staff is in group
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .config import LansengerConfig
from .url_helpers import build_api_url
from .api_utils import do_get, do_post, parse_api_response
from .models import (
    CreateGroupResult,
    GroupInfoResult,
    GroupListResult,
    GroupMemberResult,
    IsInGroupResult,
    UpdateGroupMembersResult,
    UpdateGroupResult,
)


async def create_group(
    config: LansengerConfig,
    app_token: str,
    name: str,
    org_id: str,
    *,
    owner_id: str = "",
    description: str = "",
    avatar_id: str = "",
    staff_id_list: Optional[List[str]] = None,
    department_id_list: Optional[List[str]] = None,
    user_token: str = "",
    apply_request_id: str = "",
    apply_notes: str = "",
    apply_global_unique_id: str = "",
    apply_session_unique_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> CreateGroupResult:
    """Create a new group in an organization.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        name: Group name (required).
        org_id: Organization ID (required).
        owner_id: Group owner staff openId.
        description: Group description.
        avatar_id: Group avatar media ID.
        staff_id_list: Staff openId list to add as members.
        department_id_list: Department openId list to add as members.
        user_token: Optional userToken.
        apply_request_id: Approval request ID.
        apply_notes: Approval notes.
        apply_global_unique_id: Approval global unique ID.
        apply_session_unique_id: Approval session unique ID.
        http_client: Optional httpx client.
    """
    if not name:
        return CreateGroupResult(success=False, error="name is required")
    if not org_id:
        return CreateGroupResult(success=False, error="org_id is required")

    url = build_api_url(config, "groups", "create", app_token, user_token=user_token)

    body: Dict[str, Any] = {
        "name": name,
        "orgId": org_id,
    }
    if owner_id:
        body["ownerId"] = owner_id
    if description:
        body["description"] = description
    if avatar_id:
        body["avatarId"] = avatar_id
    if staff_id_list:
        body["staffIdList"] = staff_id_list
    if department_id_list:
        body["departmentIdList"] = department_id_list
    if apply_request_id:
        body["applyRequestId"] = apply_request_id
    if apply_notes:
        body["applyNotes"] = apply_notes
    if apply_global_unique_id:
        body["applyGlobalUniqueId"] = apply_global_unique_id
    if apply_session_unique_id:
        body["applySessionUniqueId"] = apply_session_unique_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return CreateGroupResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return CreateGroupResult(success=False, error=api_err)

    d = data.get("data", {})
    return CreateGroupResult(
        success=True,
        group_id=d.get("groupId"),
        total_members=d.get("totalMembers", 0),
        invalid_staff=d.get("invalidStaff"),
        invalid_department=d.get("invalidDepartment"),
        raw_response=data,
    )


async def fetch_group_info(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> GroupInfoResult:
    """Fetch a group's detailed information.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not group_id:
        return GroupInfoResult(success=False, error="group_id is required")

    url = build_api_url(config, "groups", "info_fetch", app_token, user_token=user_token, group_id=group_id)

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return GroupInfoResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return GroupInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return GroupInfoResult(
        success=True,
        name=d.get("name"),
        description=d.get("description"),
        avatar_id=d.get("avatarId"),
        avatar_url=d.get("avatarUrl"),
        owner=d.get("owner"),
        creator=d.get("creator"),
        state=d.get("state"),
        manage_mode=d.get("manageMode"),
        location_share=d.get("locationShare"),
        needs_confirm=d.get("needsConfirm"),
        is_public=d.get("isPublic"),
        max_members=d.get("maxMembers"),
        max_history_msg_count=d.get("maxHistoryMsgCount"),
        total_members=d.get("totalMembers"),
        remind_all=d.get("remindAll"),
        send_msg_status=d.get("sendMsgStatus"),
        raw_response=data,
    )


async def fetch_group_members(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    user_token: str = "",
    page_offset: int = 0,
    page_size: int = 100,
    http_client: Optional[httpx.AsyncClient] = None,
) -> GroupMemberResult:
    """Fetch a group's member list (paginated).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        user_token: Optional userToken.
        page_offset: Page offset (default 0).
        page_size: Page size (default 100).
        http_client: Optional httpx client.
    """
    if not group_id:
        return GroupMemberResult(success=False, error="group_id is required")

    url = build_api_url(config, "groups", "members_fetch", app_token, user_token=user_token, group_id=group_id)
    url += f"&page_offset={page_offset}&page_size={page_size}"

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return GroupMemberResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return GroupMemberResult(success=False, error=api_err)

    d = data.get("data", {})
    return GroupMemberResult(
        success=True,
        total_members=d.get("totalMembers", 0),
        members=d.get("members"),
        raw_response=data,
    )


async def fetch_group_list(
    config: LansengerConfig,
    app_token: str,
    *,
    user_token: str = "",
    page_offset: int = 0,
    page_size: int = 100,
    http_client: Optional[httpx.AsyncClient] = None,
) -> GroupListResult:
    """Fetch the list of group IDs the authenticated user/bot belongs to (paginated).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        user_token: Optional userToken.
        page_offset: Page offset (default 0).
        page_size: Page size (default 100).
        http_client: Optional httpx client.
    """
    url = build_api_url(config, "groups", "groups_fetch", app_token, user_token=user_token)
    url += f"&page_offset={page_offset}&page_size={page_size}"

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return GroupListResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return GroupListResult(success=False, error=api_err)

    d = data.get("data", {})
    return GroupListResult(
        success=True,
        total_group_ids=d.get("totalGroupIds", 0),
        group_ids=d.get("groupIds"),
        raw_response=data,
    )


async def check_is_in_group(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    user_token: str = "",
    staff_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> IsInGroupResult:
    """Check whether a staff member is in a group.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        user_token: Optional userToken.
        staff_id: Optional staff openId to check membership for.
        http_client: Optional httpx client.
    """
    if not group_id:
        return IsInGroupResult(success=False, error="group_id is required")

    url = build_api_url(config, "groups", "is_in_group", app_token, user_token=user_token, group_id=group_id)
    if staff_id:
        url += f"&staff_id={quote(staff_id)}"

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return IsInGroupResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return IsInGroupResult(success=False, error=api_err)

    d = data.get("data", {})
    return IsInGroupResult(
        success=True,
        is_in_group=d.get("isInGroup", False),
        raw_response=data,
    )


async def update_group_info(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    name: str = "",
    description: str = "",
    avatar_id: str = "",
    owner_id: str = "",
    assistant: Optional[List[str]] = None,
    demote_assistant: Optional[List[str]] = None,
    manage_mode: Optional[int] = None,
    location_share: Optional[bool] = None,
    needs_confirm: Optional[bool] = None,
    is_public: Optional[bool] = None,
    max_members: Optional[int] = None,
    max_history_msg_count: Optional[int] = None,
    remind_all: Optional[bool] = None,
    send_msg_status: Optional[bool] = None,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> UpdateGroupResult:
    """Update a group's basic information (4.28.2).

    Only sends keys you provide — omit keys you don't want to change.
    App must have robot capability enabled.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        name: New group name.
        description: New group description.
        avatar_id: New group avatar ID.
        owner_id: New owner openId (must be a group member).
        assistant: Staff IDs to add as assistant group owner.
        demote_assistant: Staff IDs to demote from assistant to regular member.
        manage_mode: 0=all manage, 1=owner only.
        location_share: Enable/disable location sharing.
        needs_confirm: Join requires confirmation.
        is_public: Group is public.
        max_members: Max member count (>1).
        max_history_msg_count: History msg count limit.
        remind_all: @mention feature enabled/disabled.
        send_msg_status: Group mute enabled/disabled.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not group_id:
        return UpdateGroupResult(success=False, error="group_id is required")

    url = build_api_url(config, "groups", "info_update", app_token, user_token=user_token, group_id=group_id)

    body: Dict[str, Any] = {}
    if name:
        body["name"] = name
    if description:
        body["description"] = description
    if avatar_id:
        body["avatarId"] = avatar_id
    if owner_id:
        body["ownerId"] = owner_id
    if assistant:
        body["assistant"] = assistant
    if demote_assistant:
        body["demoteAssistant"] = demote_assistant
    if manage_mode is not None:
        body["manageMode"] = manage_mode
    if location_share is not None:
        body["locationShare"] = location_share
    if needs_confirm is not None:
        body["needsConfirm"] = needs_confirm
    if is_public is not None:
        body["isPublic"] = is_public
    if max_members is not None:
        body["maxMembers"] = max_members
    if max_history_msg_count is not None:
        body["maxHistoryMsgCount"] = max_history_msg_count
    if remind_all is not None:
        body["remindAll"] = remind_all
    if send_msg_status is not None:
        body["sendMsgStatus"] = send_msg_status

    if not body:
        return UpdateGroupResult(success=False, error="at least one field to update is required")

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return UpdateGroupResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return UpdateGroupResult(success=False, error=api_err)

    return UpdateGroupResult(success=True, raw_response=data)


async def update_group_members(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    add_user_list: Optional[List[str]] = None,
    del_user_list: Optional[List[str]] = None,
    add_department_id_list: Optional[List[str]] = None,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> UpdateGroupMembersResult:
    """Update group members — add/remove users/departments (4.28.5).

    Robot identity cannot add department members (addDepartmentIdList).
    Group owner can delete any member; non-owner can only delete members they added.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        add_user_list: Staff IDs to add to group.
        del_user_list: Staff IDs to remove from group.
        add_department_id_list: Department IDs to add (not supported with robot identity).
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not group_id:
        return UpdateGroupMembersResult(success=False, error="group_id is required")
    if not add_user_list and not del_user_list and not add_department_id_list:
        return UpdateGroupMembersResult(success=False, error="at least one of add_user_list, del_user_list, or add_department_id_list is required")

    url = build_api_url(config, "groups", "members_update", app_token, user_token=user_token, group_id=group_id)

    body: Dict[str, Any] = {}
    if add_user_list:
        body["addUserList"] = add_user_list
    if del_user_list:
        body["delUserList"] = del_user_list
    if add_department_id_list:
        body["addDepartmentIdList"] = add_department_id_list

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return UpdateGroupMembersResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return UpdateGroupMembersResult(success=False, error=api_err)

    d = data.get("data", {})
    return UpdateGroupMembersResult(
        success=True,
        total_members=d.get("totalMembers", 0),
        added_staff_count=d.get("addedStaffCount", 0),
        deleted_staff_count=d.get("deletedStaffCount", 0),
        invalid_staff=d.get("invalidStaff"),
        invalid_department=d.get("invalidDepartment"),
        raw_response=data,
    )


async def dismiss_group(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> UpdateGroupResult:
    """Dismiss/delete a group (4.28.6).

    Only the group owner can dismiss a group. This is a high-risk operation.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not group_id:
        return UpdateGroupResult(success=False, error="group_id is required")

    url = build_api_url(config, "groups", "delete", app_token, user_token=user_token, group_id=group_id)

    data, http_err = await do_post(config, url, {}, http_client)
    if http_err:
        return UpdateGroupResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return UpdateGroupResult(success=False, error=api_err)

    return UpdateGroupResult(success=True, raw_response=data)
