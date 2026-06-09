"""Lansenger unified todo/task API — create, modify, query, and manage todo tasks (4.33).

Todo status codes:
- 11: pending-read (待阅)
- 12: read (已阅)
- 21: pending-do (待办)
- 22: done (已办)

Todo type codes:
- 1: notification (通知)
- 2: approval (审批)

All endpoints use POST with app_token query param. user_token optional.

Endpoints:
1. POST /xtra/task/unified/v1/todotask/create               — create todo
2. POST /xtra/task/unified/v1/todotask/info/update           — modify todo
3. POST /xtra/task/unified/v1/todotask/status/update         — update status
4. POST /xtra/task/unified/v1/sender/todotask/delete         — creator delete
5. POST /xtra/task/unified/v1/todotask/list/fetch            — query all todos
6. POST /xtra/task/unified/v1/todotask/info/fetchbysourceid  — query by sourceId
7. POST /xtra/task/unified/v1/todotask/info/fetch            — query by todotaskId
8. POST /xtra/task/unified/v1/staff/application/fetch        — query user app info
9. POST /xtra/task/unified/v1/todotask/status/countList/fetch— status counts
10. POST /xtra/task/unified/v1/todotask/executor/status/update— update executor status
11. POST /xtra/task/unified/v1/todotask/executor/create       — add executors
12. POST /xtra/task/unified/v1/todotask/executor/delete       — delete executors
13. POST /xtra/task/unified/v1/todotask/executor/list/fetch   — get executor list
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import LansengerConfig
from .models import (
    TodoTaskCreateResult,
    TodoTaskInfoResult,
    TodoTaskListResult,
    TodoTaskStatusCountResult,
    TodoTaskExecutorListResult,
)
from .url_helpers import build_api_url
from .api_utils import do_post, parse_api_response

TODO_TODO_STATUS_PENDING_READ = "11"
TODO_TODO_STATUS_READ = "12"
TODO_TODO_STATUS_PENDING_DO = "21"
TODO_TODO_STATUS_DONE = "22"

TODO_TYPE_NOTIFICATION = 1
TODO_TYPE_APPROVAL = 2


async def create_todo_task(
    config: LansengerConfig,
    app_token: str,
    title: str,
    link: str,
    pc_link: str,
    executor_ids: List[str],
    org_id: str,
    type: int = 1,
    *,
    source_id: str = "",
    desc: str = "",
    sender_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not title:
        return TodoTaskCreateResult(success=False, error="title is required")
    if not link:
        return TodoTaskCreateResult(success=False, error="link is required")
    if not pc_link:
        return TodoTaskCreateResult(success=False, error="pc_link is required")
    if not executor_ids:
        return TodoTaskCreateResult(success=False, error="executor_ids is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "create", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "title": title,
        "type": type,
        "link": link,
        "pcLink": pc_link,
        "executorIds": executor_ids,
        "orgId": org_id,
    }
    if source_id:
        body["sourceId"] = source_id
    if desc:
        body["desc"] = desc
    if sender_id:
        body["senderId"] = sender_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return TodoTaskCreateResult(
        success=True,
        todotask_id=d.get("todotaskId"),
        raw_response=data,
    )


async def update_todo_task(
    config: LansengerConfig,
    app_token: str,
    todotask_id: str,
    title: str,
    link: str,
    pc_link: str,
    org_id: str,
    *,
    desc: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not todotask_id:
        return TodoTaskCreateResult(success=False, error="todotask_id is required")
    if not title:
        return TodoTaskCreateResult(success=False, error="title is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "info_update", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "todotaskId": todotask_id,
        "title": title,
        "link": link,
        "pcLink": pc_link,
        "orgId": org_id,
    }
    if desc:
        body["desc"] = desc

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def update_todo_task_status(
    config: LansengerConfig,
    app_token: str,
    todotask_id: str,
    status: str,
    org_id: str,
    *,
    staff_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    valid_statuses = ("11", "12", "21", "22")
    if status not in valid_statuses:
        return TodoTaskCreateResult(success=False, error=f"status must be one of: {', '.join(valid_statuses)}")
    if not todotask_id:
        return TodoTaskCreateResult(success=False, error="todotask_id is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "status_update", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "todotaskId": todotask_id,
        "status": status,
        "orgId": org_id,
    }
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def delete_todo_task(
    config: LansengerConfig,
    app_token: str,
    todotask_id: str,
    org_id: str,
    *,
    staff_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not todotask_id:
        return TodoTaskCreateResult(success=False, error="todotask_id is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "sender_delete", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "todotaskId": todotask_id,
        "orgId": org_id,
    }
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def fetch_todo_task_list(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    *,
    app_ids: Optional[List[str]] = None,
    staff_id: str = "",
    status_list: Optional[List[str]] = None,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskListResult:
    if not org_id:
        return TodoTaskListResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "list_fetch", app_token, user_token=user_token)
    body: Dict[str, Any] = {"orgId": org_id}
    if app_ids:
        body["appIds"] = app_ids
    if staff_id:
        body["staffId"] = staff_id
    if status_list:
        body["statusList"] = status_list

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskListResult(success=False, error=api_err)

    d = data.get("data", {})
    return TodoTaskListResult(
        success=True,
        total=d.get("total", 0),
        todotask_list=d.get("todotaskList"),
        raw_response=data,
    )


async def fetch_todo_task_by_source_id(
    config: LansengerConfig,
    app_token: str,
    source_id: str,
    org_id: str,
    *,
    staff_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskInfoResult:
    if not source_id:
        return TodoTaskInfoResult(success=False, error="source_id is required")
    if not org_id:
        return TodoTaskInfoResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "info_fetch_by_source_id", app_token, user_token=user_token)
    body: Dict[str, Any] = {"sourceId": source_id, "orgId": org_id}
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return TodoTaskInfoResult(
        success=True,
        todotask_id=d.get("todotaskId"),
        source_id=d.get("sourceId"),
        title=d.get("title"),
        desc=d.get("desc"),
        status=d.get("status"),
        type=d.get("type"),
        link=d.get("link"),
        pc_link=d.get("pcLink"),
        sender_id=d.get("senderId"),
        executor_ids=d.get("executorIds"),
        create_time=d.get("createTime"),
        app_id=d.get("appId"),
        raw_response=data,
    )


async def fetch_todo_task_by_id(
    config: LansengerConfig,
    app_token: str,
    todotask_id: str,
    org_id: str,
    *,
    staff_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskInfoResult:
    if not todotask_id:
        return TodoTaskInfoResult(success=False, error="todotask_id is required")
    if not org_id:
        return TodoTaskInfoResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "info_fetch", app_token, user_token=user_token)
    body: Dict[str, Any] = {"todotaskId": todotask_id, "orgId": org_id}
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return TodoTaskInfoResult(
        success=True,
        todotask_id=d.get("todotaskId"),
        source_id=d.get("sourceId"),
        title=d.get("title"),
        desc=d.get("desc"),
        status=d.get("status"),
        type=d.get("type"),
        link=d.get("link"),
        pc_link=d.get("pcLink"),
        sender_id=d.get("senderId"),
        executor_ids=d.get("executorIds"),
        create_time=d.get("createTime"),
        app_id=d.get("appId"),
        raw_response=data,
    )


async def fetch_todo_task_status_counts(
    config: LansengerConfig,
    app_token: str,
    staff_id: str,
    org_id: str,
    *,
    app_id: str = "",
    status_list: Optional[List[str]] = None,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskStatusCountResult:
    if not staff_id:
        return TodoTaskStatusCountResult(success=False, error="staff_id is required")
    if not org_id:
        return TodoTaskStatusCountResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "status_count_list_fetch", app_token, user_token=user_token)
    body: Dict[str, Any] = {"staffId": staff_id, "orgId": org_id}
    if app_id:
        body["appId"] = app_id
    if status_list:
        body["status"] = status_list

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskStatusCountResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskStatusCountResult(success=False, error=api_err)

    d = data.get("data", [])
    return TodoTaskStatusCountResult(
        success=True,
        status_counts=d,
        raw_response=data,
    )


async def update_executor_status(
    config: LansengerConfig,
    app_token: str,
    executor_status_list: List[Dict[str, str]],
    org_id: str,
    *,
    todotask_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not executor_status_list:
        return TodoTaskCreateResult(success=False, error="executor_status_list is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "executor_status_update", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "executorStatusList": executor_status_list,
        "orgId": org_id,
    }
    if todotask_id:
        body["todotaskId"] = todotask_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def add_executors(
    config: LansengerConfig,
    app_token: str,
    executor_ids: List[str],
    org_id: str,
    *,
    todotask_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not executor_ids:
        return TodoTaskCreateResult(success=False, error="executor_ids is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "executor_create", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "executorIds": executor_ids,
        "orgId": org_id,
    }
    if todotask_id:
        body["todotaskId"] = todotask_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def delete_executors(
    config: LansengerConfig,
    app_token: str,
    executor_ids: List[str],
    org_id: str,
    *,
    todotask_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskCreateResult:
    if not executor_ids:
        return TodoTaskCreateResult(success=False, error="executor_ids is required")
    if not org_id:
        return TodoTaskCreateResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "executor_delete", app_token, user_token=user_token)
    body: Dict[str, Any] = {
        "executorIds": executor_ids,
        "orgId": org_id,
    }
    if todotask_id:
        body["todotaskId"] = todotask_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskCreateResult(success=False, error=api_err)

    return TodoTaskCreateResult(success=True, todotask_id=todotask_id, raw_response=data)


async def fetch_executor_list(
    config: LansengerConfig,
    app_token: str,
    todotask_id: str,
    org_id: str,
    *,
    staff_id: str = "",
    status_list: Optional[List[str]] = None,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> TodoTaskExecutorListResult:
    if not todotask_id:
        return TodoTaskExecutorListResult(success=False, error="todotask_id is required")
    if not org_id:
        return TodoTaskExecutorListResult(success=False, error="org_id is required")

    url = build_api_url(config, "todo", "executor_list_fetch", app_token, user_token=user_token)
    body: Dict[str, Any] = {"todotaskId": todotask_id, "orgId": org_id}
    if staff_id:
        body["staffId"] = staff_id
    if status_list:
        body["statusList"] = status_list

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return TodoTaskExecutorListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return TodoTaskExecutorListResult(success=False, error=api_err)

    d = data.get("data", {})
    return TodoTaskExecutorListResult(
        success=True,
        total=d.get("total", 0),
        executor_list=d.get("executorList"),
        raw_response=data,
    )