"""Lansenger contacts/staff API — organization-level staff information operations.

These APIs are available to org bots/apps (not personal bots). They require
appToken for authentication, and some optionally accept userToken for
user-scoped data access.

Endpoints:
1. GET /v1/staffs/:staffid/fetch          — staff basic info
2. GET /v1/staffs/:staffid/infor/fetch    — staff detailed info (needs org/personal auth)
3. GET /v1/staffs/:staffid/departmentancestors/fetch — department ancestor chain
4. GET /v2/staffs/id_mapping/fetch        — map unique identifier (phone/email/etc) to staffId
5. GET /v1/org/:orgid/extrafieldids/fetch — org extra field ID list
6. POST /v2/staffs/search                 — search staff by keyword with department scope
7. GET  /v1/org/:orgid/fetch             — org basic info
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from .config import LansengerConfig
from .url_helpers import build_api_url
from .models import (
    DepartmentAncestorsResult,
    ExtraFieldIdsResult,
    OrgInfoResult,
    StaffBasicInfoResult,
    StaffDetailResult,
    StaffIdMappingResult,
    StaffSearchResult,
)

logger = logging.getLogger("lansenger_sdk.contacts")


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


async def fetch_staff_basic_info(
    config: LansengerConfig,
    app_token: str,
    staff_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> StaffBasicInfoResult:
    """Fetch a staff member's basic information.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        staff_id: Staff openId.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not staff_id:
        return StaffBasicInfoResult(success=False, error="staff_id is required")

    url = build_api_url(config, "staffs", "fetch", app_token, user_token=user_token, staff_id=staff_id)

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return StaffBasicInfoResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StaffBasicInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return StaffBasicInfoResult(
        success=True,
        org_id=d.get("orgId"),
        org_name=d.get("orgName"),
        name=d.get("name"),
        gender=d.get("gender"),
        signature=d.get("signature"),
        avatar_url=d.get("avatarUrl"),
        avatar_id=d.get("avatarId"),
        status=d.get("status"),
        departments=d.get("departments"),
        raw_response=data,
    )


async def fetch_staff_detail(
    config: LansengerConfig,
    app_token: str,
    staff_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> StaffDetailResult:
    """Fetch a staff member's detailed information (requires org/personal auth).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        staff_id: Staff openId.
        user_token: Optional userToken (recommended for personal auth).
        http_client: Optional httpx client.
    """
    if not staff_id:
        return StaffDetailResult(success=False, error="staff_id is required")

    url = build_api_url(config, "staffs", "detail_fetch", app_token, user_token=user_token, staff_id=staff_id)

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return StaffDetailResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StaffDetailResult(success=False, error=api_err)

    d = data.get("data", {})
    return StaffDetailResult(
        success=True,
        name=d.get("name"),
        signature=d.get("signature"),
        avatar_id=d.get("avatarId"),
        avatar_url=d.get("avatarUrl"),
        status=d.get("status"),
        departments=d.get("departments"),
        gender=d.get("gender"),
        org_id=d.get("orgId"),
        org_name=d.get("orgName"),
        login_name=d.get("loginName"),
        employee_number=d.get("employeeNumber"),
        email=d.get("email"),
        external_id=d.get("externalId"),
        nationality=d.get("nationality"),
        birthdate=d.get("birthdate"),
        id_number=d.get("idNumber"),
        native_place=d.get("nativePlace"),
        duties=d.get("duties"),
        parties=d.get("parties"),
        address=d.get("address"),
        mobile_phone=d.get("mobilePhone"),
        extra_phones=d.get("extraPhones"),
        introduction=d.get("introduction"),
        education=d.get("education"),
        career=d.get("career"),
        login_ways=d.get("loginWays"),
        tags=d.get("tags"),
        extra_field_set=d.get("extraFieldSet"),
        leaders=d.get("leaders"),
        join_date=d.get("joinDate"),
        raw_response=data,
    )


async def fetch_department_ancestors(
    config: LansengerConfig,
    app_token: str,
    staff_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> DepartmentAncestorsResult:
    """Fetch ancestor department chain for a staff member.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        staff_id: Staff openId.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not staff_id:
        return DepartmentAncestorsResult(success=False, error="staff_id is required")

    url = build_api_url(config, "staffs", "department_ancestors", app_token, user_token=user_token, staff_id=staff_id)

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return DepartmentAncestorsResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return DepartmentAncestorsResult(success=False, error=api_err)

    result_data = data.get("data", [])
    ancestor_groups: List[List[Dict[str, str]]] = []
    for entry in result_data:
        ancestors = entry.get("ancestorDepartments", [])
        ancestor_groups.append(ancestors)

    return DepartmentAncestorsResult(
        success=True,
        ancestor_groups=ancestor_groups,
        raw_response=data,
    )


async def fetch_staff_id_mapping(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    id_type: str,
    id_value: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> StaffIdMappingResult:
    """Map a unique identifier (phone/email/employee_number) to staffId.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        org_id: Organization ID.
        id_type: One of: "employ_id", "mobile", "mail", "login", "external_id".
        id_value: The value corresponding to id_type.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not org_id:
        return StaffIdMappingResult(success=False, error="org_id is required")
    if not id_type:
        return StaffIdMappingResult(success=False, error="id_type is required")
    if not id_value:
        return StaffIdMappingResult(success=False, error="id_value is required")

    url = build_api_url(config, "staffs", "id_mapping", app_token, user_token=user_token)
    url += f"&org_id={quote(org_id)}&id_type={quote(id_type)}&id_value={quote(id_value)}"

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return StaffIdMappingResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StaffIdMappingResult(success=False, error=api_err)

    d = data.get("data", {})
    return StaffIdMappingResult(
        success=True,
        staff_id=d.get("staffId"),
        raw_response=data,
    )


async def fetch_org_extra_field_ids(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    *,
    user_token: str = "",
    page: int = 1,
    page_size: int = 1000,
    http_client: Optional[httpx.AsyncClient] = None,
) -> ExtraFieldIdsResult:
    """Fetch organization extra field ID list.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        org_id: Organization ID.
        user_token: Optional userToken.
        page: Page offset (default 1).
        page_size: Per-page count (default 1000, max 100000).
        http_client: Optional httpx client.
    """
    if not org_id:
        return ExtraFieldIdsResult(success=False, error="org_id is required")

    url = build_api_url(config, "org", "extra_field_ids", app_token, user_token=user_token, org_id=org_id)
    url += f"&page={page}&page_size={page_size}"

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return ExtraFieldIdsResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return ExtraFieldIdsResult(success=False, error=api_err)

    d = data.get("data", {})
    return ExtraFieldIdsResult(
        success=True,
        has_more=d.get("hasMore", False),
        total=d.get("total", 0),
        extra_field_ids=d.get("extraFieldIds"),
        raw_response=data,
    )


async def search_staff(
    config: LansengerConfig,
    app_token: str,
    keyword: str,
    *,
    user_token: str = "",
    user_id: str = "",
    recursive: bool = True,
    sector_ids: Optional[List[str]] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> StaffSearchResult:
    """Search staff by keyword with optional department scope.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        keyword: Search keyword.
        user_token: Optional userToken (one of user_token/user_id required for auth).
        user_id: Optional staff openId (one of user_token/user_id required for auth).
        recursive: Whether to search sub-departments (default True).
        sector_ids: Optional department openId list to limit search scope.
        page: Optional page number.
        page_size: Optional page size (max 100).
        http_client: Optional httpx client.
    """
    if not keyword:
        return StaffSearchResult(success=False, error="keyword is required")

    url = build_api_url(config, "staffs", "search", app_token, user_token=user_token, user_id=user_id)
    if page is not None and page_size is not None:
        url += f"&page={page}&page_size={page_size}"

    body: Dict[str, Any] = {
        "keyword": keyword,
        "recursive": recursive,
    }
    if sector_ids:
        body["searchScope"] = {"sectorIds": sector_ids}

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)

    try:
        response = await http_client.post(url, json=body)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return StaffSearchResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StaffSearchResult(success=False, error=api_err)

    d = data.get("data", {})
    return StaffSearchResult(
        success=True,
        has_more=d.get("hasMore", False),
        total=d.get("total", 0),
        staff_info=d.get("staffInfo"),
        raw_response=data,
    )


async def fetch_org_info(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> OrgInfoResult:
    """Fetch organization basic information.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        org_id: Organization ID.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not org_id:
        return OrgInfoResult(success=False, error="org_id is required")

    url = build_api_url(config, "org", "fetch", app_token, user_token=user_token, org_id=org_id)

    data, http_err = await _do_get(config, url, http_client)
    if http_err:
        return OrgInfoResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return OrgInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return OrgInfoResult(
        success=True,
        org_id=d.get("orgId"),
        org_name=d.get("orgName"),
        icon_url=d.get("iconUrl"),
        org_max_member_limit=d.get("orgMaxMemberLimit"),
        org_order_type=d.get("orgOrderType"),
        org_days_limit=d.get("orgDaysLimit"),
        org_billing_date=d.get("orgBillingDate"),
        raw_response=data,
    )