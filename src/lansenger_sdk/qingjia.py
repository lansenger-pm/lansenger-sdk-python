"""Lansenger qingjia API — leave application V2 (请假 V2).

Endpoints:
- POST /xtra/qingjia/server/openapi/v2/maxVersionConfigList
- POST /xtra/qingjia/server/openapi/v2/times
- POST /xtra/qingjia/server/openapi/v2/upload
- POST /xtra/qingjia/server/openapi/v2/saveApply
- POST /xtra/qingjia/server/openapi/v2/myApplyPageInfo
- POST /xtra/qingjia/server/openapi/v2/personBalance
- POST /xtra/qingjia/server/openapi/v2/attendanceGroupList
- POST /xtra/qingjia/server/openapi/v2/enableLeaveTypeList

Path = gateway (config.api_gateway_url) + fixed path. The fixed path shape is
/xtra/<app>/server/openapi/<version>/<method> — `/server` is the service
identifier segment carried by non-standard ("非通版") deployments, and it sits
BEFORE /openapi, same as boardrooms / notices / questionnaires / personal_todos.
Only the gateway is configurable; everything after it is hard-coded.

Identity: qingjia body fields are staffId / orgId (NOT lxUserId as in
boardrooms). When user_token is supplied on the query string, the gateway
injects identity, making body staffId / orgId optional for most endpoints.
SDK kwargs use staff_id / org_id → injected as staffId / orgId only when the
endpoint's doc actually carries that field.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import (
    QingjiaGroupListResult,
    QingjiaEnableLeaveTypeListResult,
    QingjiaMyApplyPageResult,
    QingjiaPersonBalanceResult,
    QingjiaRuleConfigListResult,
    QingjiaSaveApplyResult,
    QingjiaTimesResult,
    QingjiaUploadUrlResult,
)
from .pagination import parse_v2_page_info
from .url_helpers import build_api_url


async def fetch_qingjia_max_version_config_list(
    config: LansengerConfig,
    app_token: str,
    *,
    org_id: str = "",
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaRuleConfigListResult:
    """考勤组规则配置列表 (请假 V2 /maxVersionConfigList)."""
    url = build_api_url(config, "qingjia", "max_version_config_list", app_token, user_token=user_token)
    body: dict[str, Any] = {}
    if org_id:
        body["orgId"] = org_id
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaRuleConfigListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaRuleConfigListResult(success=False, error=api_err)

    items = (data or {}).get("data") or []
    return QingjiaRuleConfigListResult(
        success=True, items=items, total=len(items), raw_response=data,
    )


async def fetch_qingjia_times(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    times_vo: dict[str, Any],
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaTimesResult:
    """按时间段计算请假时长 (请假 V2 /times)."""
    if not cmc_code:
        return QingjiaTimesResult(success=False, error="cmc_code is required")
    if not times_vo:
        return QingjiaTimesResult(success=False, error="times_vo is required")

    url = build_api_url(config, "qingjia", "times", app_token, user_token=user_token)
    body: dict[str, Any] = {"cmcCode": cmc_code, "timesVO": times_vo}
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaTimesResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaTimesResult(success=False, error=api_err)

    d = (data or {}).get("data") or {}
    return QingjiaTimesResult(
        success=True,
        type_code=d.get("typeCode"),
        apply_start_time=d.get("applyStartTime"),
        apply_end_time=d.get("applyEndTime"),
        effective_hours=d.get("effectiveHours"),
        effective_days=d.get("effectiveDays"),
        effective_timestamp=d.get("effectiveTimestamp"),
        time_str=d.get("timeStr"),
        raw_response=data,
    )


async def fetch_qingjia_upload_url(
    config: LansengerConfig,
    app_token: str,
    *,
    file_name: str,
    md5: str,
    size: int,
    org_id: str = "",
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaUploadUrlResult:
    """取请假附件预签名上传地址 (请假 V2 /upload)."""
    if not file_name:
        return QingjiaUploadUrlResult(success=False, error="file_name is required")
    if not md5:
        return QingjiaUploadUrlResult(success=False, error="md5 is required")
    if size is None:
        return QingjiaUploadUrlResult(success=False, error="size is required")

    url = build_api_url(config, "qingjia", "upload", app_token, user_token=user_token)
    body: dict[str, Any] = {"fileName": file_name, "md5": md5, "size": size}
    if org_id:
        body["orgId"] = org_id
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaUploadUrlResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaUploadUrlResult(success=False, error=api_err)

    return QingjiaUploadUrlResult(
        success=True, value=(data or {}).get("data"), raw_response=data,
    )


async def fetch_qingjia_save_apply(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    is_leave_back: bool,
    apply_vo: dict[str, Any],
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaSaveApplyResult:
    """提交请假申请 (请假 V2 /saveApply)."""
    if not cmc_code:
        return QingjiaSaveApplyResult(success=False, error="cmc_code is required")
    if is_leave_back is None:
        return QingjiaSaveApplyResult(success=False, error="is_leave_back is required")
    if not apply_vo:
        return QingjiaSaveApplyResult(success=False, error="apply_vo is required")

    url = build_api_url(config, "qingjia", "save_apply", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "cmcCode": cmc_code,
        "isLeaveBack": is_leave_back,
        "applyVO": apply_vo,
    }
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaSaveApplyResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaSaveApplyResult(success=False, error=api_err)

    return QingjiaSaveApplyResult(
        success=True, value=(data or {}).get("data"), raw_response=data,
    )


async def fetch_qingjia_my_apply_page_info(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    query_vo: dict[str, Any],
    is_diss: bool | None = None,
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaMyApplyPageResult:
    """我的请假申请分页 (请假 V2 /myApplyPageInfo)."""
    if not cmc_code:
        return QingjiaMyApplyPageResult(success=False, error="cmc_code is required")
    if not query_vo:
        return QingjiaMyApplyPageResult(success=False, error="query_vo is required")

    url = build_api_url(config, "qingjia", "my_apply_page_info", app_token, user_token=user_token)
    body: dict[str, Any] = {"cmcCode": cmc_code, "queryVO": query_vo}
    if is_diss is not None:
        body["isDiss"] = is_diss
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaMyApplyPageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaMyApplyPageResult(success=False, error=api_err)

    return QingjiaMyApplyPageResult(
        success=True, raw_response=data,
        **parse_v2_page_info((data or {}).get("data")),
    )


async def fetch_qingjia_person_balance(
    config: LansengerConfig,
    app_token: str,
    *,
    org_id: str,
    cmc_code: str,
    type_code: str = "",
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaPersonBalanceResult:
    """人员假期余额 (请假 V2 /personBalance)."""
    if not org_id:
        return QingjiaPersonBalanceResult(success=False, error="org_id is required")
    if not cmc_code:
        return QingjiaPersonBalanceResult(success=False, error="cmc_code is required")

    url = build_api_url(config, "qingjia", "person_balance", app_token, user_token=user_token)
    body: dict[str, Any] = {"orgId": org_id, "cmcCode": cmc_code}
    if type_code:
        body["typeCode"] = type_code
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaPersonBalanceResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaPersonBalanceResult(success=False, error=api_err)

    d = (data or {}).get("data") or {}
    return QingjiaPersonBalanceResult(
        success=True,
        staff_id=d.get("staffId"),
        name=d.get("name"),
        phone=d.get("phone"),
        employee_code=d.get("employeeCode"),
        staff_no=d.get("staffNo"),
        dep_name=d.get("depName"),
        balance_list=d.get("balanceList"),
        raw_response=data,
    )


async def fetch_qingjia_attendance_group_list(
    config: LansengerConfig,
    app_token: str,
    *,
    org_id: str = "",
    staff_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaGroupListResult:
    """考勤组列表 (请假 V2 /attendanceGroupList)."""
    if not org_id:
        return QingjiaGroupListResult(success=False, error="org_id is required")

    url = build_api_url(config, "qingjia", "attendance_group_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"orgId": org_id}
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaGroupListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaGroupListResult(success=False, error=api_err)

    items = (data or {}).get("data") or []
    return QingjiaGroupListResult(
        success=True, items=items, total=len(items), raw_response=data,
    )


async def fetch_qingjia_enable_leave_type_list(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QingjiaEnableLeaveTypeListResult:
    """启用的假期类型 (请假 V2 /enableLeaveTypeList)."""
    if not cmc_code:
        return QingjiaEnableLeaveTypeListResult(success=False, error="cmc_code is required")

    url = build_api_url(config, "qingjia", "enable_leave_type_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"cmcCode": cmc_code}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QingjiaEnableLeaveTypeListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return QingjiaEnableLeaveTypeListResult(success=False, error=api_err)

    items = (data or {}).get("data") or []
    return QingjiaEnableLeaveTypeListResult(
        success=True, items=items, total=len(items), raw_response=data,
    )
