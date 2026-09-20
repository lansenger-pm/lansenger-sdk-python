"""Lansenger personal todo API — personal task management (个人待办).

Endpoints:
- POST /xtra/tdtask/server/openapi/v3/taskopt/savePersonalTask
- POST /xtra/tdtask/server/openapi/v3/taskopt/updatePersonalTask
- POST /xtra/tdtask/server/openapi/v3/user/list
- POST /xtra/tdtask/server/openapi/resource/update
- POST /xtra/tdtask/server/openapi/resource/getResourceDownload
- POST /xtra/tdtask/server/openapi/resource/getUploadUrl

All endpoints use POST with app_token query param. user_token is optional.
Unlike the unified application todo API, this module manages personal todos.
The server does not expose complete/delete operations for this API.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post
from .config import LansengerConfig
from .models import (
    PersonalTodoListResult,
    PersonalTodoResourceResult,
    PersonalTodoSaveResult,
    PersonalTodoUrlResult,
)
from .url_helpers import build_api_url

PERSONAL_TODO_TYPE_PERSONAL = 1
PERSONAL_TODO_STATUS_UNFINISHED = 0
PERSONAL_TODO_STATUS_FINISHED = 1

PERSONAL_TODO_PRIORITY_LOW = 0
PERSONAL_TODO_PRIORITY_NORMAL = 1
PERSONAL_TODO_PRIORITY_URGENT = 2
PERSONAL_TODO_PRIORITY_VERY_URGENT = 3

PERSONAL_TODO_PLATFORM_APP = 1
PERSONAL_TODO_PLATFORM_WEB = 2
PERSONAL_TODO_PLATFORM_API = 3

PERSONAL_TODO_RESOURCE_MAX_SIZE = 9 * 1024 * 1024


def _parse_response(data: dict[str, Any]) -> tuple[bool, str | None]:
    """Accept errCode=0 and legacy write success errCode=200."""
    err_code = data.get("errCode", -1)
    if err_code not in (0, 200):
        msg = data.get("errMsg", "Unknown error")
        return False, f"API error (errCode={err_code}): {msg}"
    return True, None


async def save_personal_todo(
    config: LansengerConfig,
    app_token: str,
    subject: str,
    start_time: int,
    due_time: int,
    priority: int,
    create_user_id: str,
    org_id: str,
    appid: str,
    *,
    description: str = "",
    parent_code: str = "",
    group_id: str = "",
    group_category_code: str = "",
    finish_time: int | None = 0,
    status_tag_no: str = "",
    status_tag_yes: str = "",
    app_info_id: int | None = None,
    app_category_id: int | None = None,
    platform: int | None = None,
    subscribe_status: int | None = None,
    user_code: str = "",
    executors: list[dict[str, Any]] | None = None,
    copys: list[dict[str, Any]] | None = None,
    resources: list[dict[str, Any]] | None = None,
    reminds: list[dict[str, Any]] | None = None,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoSaveResult:
    """Create a personal todo (个人待办 /v3/taskopt/savePersonalTask)."""
    if not subject:
        return PersonalTodoSaveResult(success=False, error="subject is required")
    if start_time is None:
        return PersonalTodoSaveResult(success=False, error="start_time is required")
    if due_time is None:
        return PersonalTodoSaveResult(success=False, error="due_time is required")
    if priority not in (0, 1, 2, 3):
        return PersonalTodoSaveResult(success=False, error="priority must be 0, 1, 2, or 3")
    if not create_user_id:
        return PersonalTodoSaveResult(success=False, error="create_user_id is required")
    if not org_id:
        return PersonalTodoSaveResult(success=False, error="org_id is required")
    if not appid:
        return PersonalTodoSaveResult(success=False, error="appid is required")

    url = build_api_url(config, "personal_todos", "save", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "subject": subject,
        "startTime": start_time,
        "dueTime": due_time,
        "finishTime": finish_time if finish_time is not None else 0,
        "priority": priority,
        "type": PERSONAL_TODO_TYPE_PERSONAL,
        "createUserId": create_user_id,
        "orgId": org_id,
        "appid": appid,
    }
    optional: dict[str, Any] = {
        "description": description,
        "parentCode": parent_code,
        "groupId": group_id,
        "groupCategoryCode": group_category_code,
        "statusTagNo": status_tag_no,
        "statusTagYes": status_tag_yes,
        "appInfoId": app_info_id,
        "appCategoryId": app_category_id,
        "platform": platform,
        "subscribeStatus": subscribe_status,
        "userCode": user_code,
        "executors": executors,
        "copys": copys,
        "resources": resources,
        "reminds": reminds,
    }
    for key, value in optional.items():
        if value is not None and value != "":
            body[key] = value

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoSaveResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoSaveResult(success=False, error=api_err)

    d = (data or {}).get("data")
    return PersonalTodoSaveResult(
        success=True,
        todo_code=d if isinstance(d, str) else None,
        raw_response=data,
    )


async def update_personal_todo(
    config: LansengerConfig,
    app_token: str,
    todo_code: str,
    org_id: str,
    update_fields: list[str],
    *,
    subject: str = "",
    description: str = "",
    start_time: int | None = None,
    due_time: int | None = None,
    finish_time: int | None = None,
    priority: int | None = None,
    status_tag_no: str = "",
    status_tag_yes: str = "",
    subscribe_status: int | None = None,
    create_user_id: str = "",
    group_id: str = "",
    group_category_code: str = "",
    appid: str = "",
    executors: list[dict[str, Any]] | None = None,
    copys: list[dict[str, Any]] | None = None,
    resources: list[dict[str, Any]] | None = None,
    reminds: list[dict[str, Any]] | None = None,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoSaveResult:
    """Edit selected fields of a personal todo (个人待办 /v3/taskopt/updatePersonalTask)."""
    if not todo_code:
        return PersonalTodoSaveResult(success=False, error="todo_code is required")
    if not org_id:
        return PersonalTodoSaveResult(success=False, error="org_id is required")
    if not update_fields:
        return PersonalTodoSaveResult(success=False, error="update_fields is required")
    if not create_user_id:
        return PersonalTodoSaveResult(success=False, error="create_user_id is required")
    if not appid:
        return PersonalTodoSaveResult(success=False, error="appid is required")

    update_content: dict[str, Any] = {"code": todo_code}
    candidate_fields: dict[str, Any] = {
        "subject": subject,
        "description": description,
        "startTime": start_time,
        "dueTime": due_time,
        "finishTime": finish_time,
        "priority": priority,
        "statusTagNo": status_tag_no,
        "statusTagYes": status_tag_yes,
        "subscribeStatus": subscribe_status,
        "createUserId": create_user_id,
        "groupId": group_id,
        "groupCategoryCode": group_category_code,
        "appid": appid,
        "executors": executors,
        "copys": copys,
        "resources": resources,
        "reminds": reminds,
    }
    for key, value in candidate_fields.items():
        if key in update_fields and value is not None and value != "":
            update_content[key] = value
    update_content["createUserId"] = create_user_id
    update_content["appid"] = appid

    url = build_api_url(config, "personal_todos", "update", app_token, user_token=user_token)
    body = {
        "orgId": org_id,
        "updateFields": update_fields,
        "updateContent": update_content,
    }

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoSaveResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoSaveResult(success=False, error=api_err)

    return PersonalTodoSaveResult(success=True, todo_code=todo_code, raw_response=data)


def _parse_page(data: dict[str, Any] | None) -> dict[str, Any]:
    d = data or {}
    return {
        "page_no": d.get("pageNo", 0),
        "page_size": d.get("pageSize", 0),
        "pages": d.get("pages", 0),
        "total": d.get("total", 0),
        "has_more": bool(d.get("hasNextPage", False)),
        "items": d.get("result") or [],
    }


async def fetch_personal_todo_list(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    staff_id: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    status: int | None = None,
    app_id: str = "",
    app_category_name: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoListResult:
    """Page a user's personal todos (个人待办 /v3/user/list)."""
    if not org_id:
        return PersonalTodoListResult(success=False, error="org_id is required")
    if not staff_id:
        return PersonalTodoListResult(success=False, error="staff_id is required")
    if status is not None and status not in (0, 1):
        return PersonalTodoListResult(success=False, error="status must be 0 or 1")

    url = build_api_url(config, "personal_todos", "user_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": org_id,
        "staffId": staff_id,
        "pageNo": page_no,
        "pageSize": page_size,
    }
    if status is not None:
        body["status"] = status
    if app_id:
        body["appId"] = app_id
    if app_category_name:
        body["appCategoryName"] = app_category_name

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoListResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoListResult(success=False, error=api_err)

    return PersonalTodoListResult(
        success=True,
        raw_response=data,
        **_parse_page((data or {}).get("data")),
    )


async def upload_personal_todo_resource(
    config: LansengerConfig,
    app_token: str,
    app_id: str,
    size: int,
    file_name: str,
    content_type: str,
    file_data: str,
    org_id: str,
    *,
    extension_info: str = "",
    thumb: bool = False,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoResourceResult:
    """Upload a personal-todo resource as base64 file data (个人待办 /resource/update)."""
    if not app_id:
        return PersonalTodoResourceResult(success=False, error="app_id is required")
    if size <= 0:
        return PersonalTodoResourceResult(success=False, error="size is required")
    if size > PERSONAL_TODO_RESOURCE_MAX_SIZE:
        return PersonalTodoResourceResult(
            success=False,
            error=f"size exceeds the {PERSONAL_TODO_RESOURCE_MAX_SIZE} byte limit",
        )
    if not file_name:
        return PersonalTodoResourceResult(success=False, error="file_name is required")
    if not content_type:
        return PersonalTodoResourceResult(success=False, error="content_type is required")
    if not file_data:
        return PersonalTodoResourceResult(success=False, error="file_data is required")
    if not org_id:
        return PersonalTodoResourceResult(success=False, error="org_id is required")

    url = build_api_url(config, "personal_todos", "resource_update", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "appId": app_id,
        "size": size,
        "fileName": file_name,
        "contentType": content_type,
        "fileData": file_data,
        "orgId": org_id,
        "thumb": thumb,
    }
    if extension_info:
        body["extensionInfo"] = extension_info

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoResourceResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoResourceResult(success=False, error=api_err)

    d = (data or {}).get("data") or {}
    return PersonalTodoResourceResult(
        success=True,
        file_name=d.get("fileName"),
        mime_type=d.get("mimeType"),
        suffix=d.get("suffix"),
        size=d.get("size"),
        md5=d.get("md5"),
        extension_info=d.get("extensionInfo"),
        resource_id=d.get("resourceId"),
        download_url=d.get("downloadUrl"),
        image_thumbnail_list=d.get("imageThumbnailList"),
        raw_response=data,
    )


async def fetch_personal_todo_resource_download_url(
    config: LansengerConfig,
    app_token: str,
    resource_id: str,
    org_id: str,
    *,
    file_name: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoUrlResult:
    """Fetch a resource download URL valid for up to one hour (个人待办 /resource/getResourceDownload)."""
    if not resource_id:
        return PersonalTodoUrlResult(success=False, error="resource_id is required")
    if not org_id:
        return PersonalTodoUrlResult(success=False, error="org_id is required")

    url = build_api_url(config, "personal_todos", "resource_download", app_token, user_token=user_token)
    body: dict[str, Any] = {"resourceId": resource_id, "orgId": org_id}
    if file_name:
        body["fileName"] = file_name

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoUrlResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoUrlResult(success=False, error=api_err)

    d = (data or {}).get("data")
    return PersonalTodoUrlResult(
        success=True,
        url=d if isinstance(d, str) else None,
        raw_response=data,
    )


async def fetch_personal_todo_resource_upload_url(
    config: LansengerConfig,
    app_token: str,
    file_name: str,
    md5: str,
    size: int,
    org_id: str,
    *,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalTodoUrlResult:
    """Fetch a presigned S3 upload URL (个人待办 /resource/getUploadUrl)."""
    if not file_name:
        return PersonalTodoUrlResult(success=False, error="file_name is required")
    if not md5:
        return PersonalTodoUrlResult(success=False, error="md5 is required")
    if size <= 0:
        return PersonalTodoUrlResult(success=False, error="size is required")
    if not org_id:
        return PersonalTodoUrlResult(success=False, error="org_id is required")

    url = build_api_url(config, "personal_todos", "resource_upload_url", app_token, user_token=user_token)
    body = {
        "fileName": file_name,
        "md5": md5,
        "size": size,
        "orgId": org_id,
    }

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalTodoUrlResult(success=False, error=http_err)
    ok, api_err = _parse_response(data or {})
    if not ok:
        return PersonalTodoUrlResult(success=False, error=api_err)

    d = (data or {}).get("data")
    return PersonalTodoUrlResult(
        success=True,
        url=d if isinstance(d, str) else None,
        raw_response=data,
    )
