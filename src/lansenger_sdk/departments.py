"""Lansenger department API — organization branch/department operations.

These APIs are available to org bots/apps (not personal bots). They require
appToken for authentication, and optionally accept userToken for user-scoped
data access.

Endpoints:
1. GET /v1/departments/{department_id}/fetch          — department detail
2. GET /v1/departments/{department_id}/children/fetch  — child departments
3. GET /v1/departments/{department_id}/staffs/fetch    — department staff list (paginated)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from .config import LansengerConfig
from .url_helpers import build_api_url
from .models import (
    DepartmentChildrenResult,
    DepartmentDetailResult,
    DepartmentStaffsResult,
)

logger = logging.getLogger("lansenger_sdk.departments")


def _parse_api_response(data: dict) -> tuple[bool, Optional[str]]:
    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return False, f"API error (errCode={err_code}): {msg}"
    return True, None


async def _do_get(
    config: LansengerConfig,
    url: str,
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return None, f"HTTP error: {e}"
    except Exception as e:
        return None, f"Request error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None


async def fetch_department_detail(
    config: LansengerConfig,
    app_token: str,
    department_id: str,
    *,
    user_token: str = "",
    tag_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> DepartmentDetailResult:
    """Fetch a department's detailed information.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        department_id: Department openId (required, e.g. "524288-0" for root).
        user_token: Optional userToken.
        tag_id: Optional tag ID filter.
        http_client: Optional httpx client.
    """
    if not department_id:
        return DepartmentDetailResult(success=False, error="department_id is required")

    url = build_api_url(config, "departments", "fetch", app_token, user_token=user_token, department_id=department_id)
    if tag_id:
        url += f"&tag_id={quote(tag_id)}"

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return DepartmentDetailResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return DepartmentDetailResult(success=False, error=api_err)

    d = data.get("data", {})
    return DepartmentDetailResult(
        success=True,
        id=d.get("id"),
        name=d.get("name"),
        external_id=d.get("externalId"),
        parent_id=d.get("parentId"),
        order=d.get("order"),
        has_children=d.get("hasChildren"),
        normal_members=d.get("normalMembers"),
        inactive_members=d.get("inactiveMembers"),
        frozen_members=d.get("frozenMembers"),
        deleted_members=d.get("deletedMembers"),
        tags=d.get("tags"),
        ancestor_departments=d.get("ancestorDepartments"),
        leaders=d.get("leaders"),
        emails=d.get("emails"),
        phones=d.get("phones"),
        addresses=d.get("addresses"),
        introductions=d.get("introductions"),
        dept_type=d.get("deptType"),
        raw_response=data,
    )


async def fetch_department_children(
    config: LansengerConfig,
    app_token: str,
    department_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> DepartmentChildrenResult:
    """Fetch a department's child departments.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        department_id: Department openId (required).
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not department_id:
        return DepartmentChildrenResult(success=False, error="department_id is required")

    url = build_api_url(config, "departments", "children_fetch", app_token, user_token=user_token, department_id=department_id)

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return DepartmentChildrenResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return DepartmentChildrenResult(success=False, error=api_err)

    d = data.get("data", {})
    return DepartmentChildrenResult(
        success=True,
        departments=d.get("departments"),
        raw_response=data,
    )


async def fetch_department_staffs(
    config: LansengerConfig,
    app_token: str,
    department_id: str,
    *,
    user_token: str = "",
    page: int = 1,
    page_size: int = 100,
    http_client: Optional[httpx.AsyncClient] = None,
) -> DepartmentStaffsResult:
    """Fetch staff members in a department (paginated).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        department_id: Department openId (required).
        user_token: Optional userToken.
        page: Page number (default 1).
        page_size: Page size (default 100).
        http_client: Optional httpx client.
    """
    if not department_id:
        return DepartmentStaffsResult(success=False, error="department_id is required")

    url = build_api_url(config, "departments", "staffs_fetch", app_token, user_token=user_token, department_id=department_id)
    url += f"&page={page}&page_size={page_size}"

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return DepartmentStaffsResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return DepartmentStaffsResult(success=False, error=api_err)

    d = data.get("data", {})
    return DepartmentStaffsResult(
        success=True,
        has_more=d.get("hasMore", False),
        total=d.get("total", 0),
        staffs=d.get("staffs"),
        raw_response=data,
    )