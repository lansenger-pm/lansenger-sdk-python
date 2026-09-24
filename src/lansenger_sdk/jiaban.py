"""Lansenger jiaban API — overtime application V2 (加班 V2).

Endpoints:
- POST /xtra/jiaban/server/openapi/v2/getMaxVersionConfigList
- POST /xtra/jiaban/server/openapi/v2/upload
- POST /xtra/jiaban/server/openapi/v2/submitApprove
- POST /xtra/jiaban/server/openapi/v2/getMyApplyPageInfo
- POST /xtra/jiaban/server/openapi/v2/getGroupInfo
- POST /xtra/jiaban/server/openapi/v2/calculateDuration

Path = gateway (config.api_gateway_url) + fixed path. The fixed path shape is
/xtra/<app>/server/openapi/<version>/<method> — `/server` is the service
identifier segment carried by non-standard ("非通版") deployments, and it sits
BEFORE /openapi, same as boardrooms / notices / questionnaires / personal_todos.
Only the gateway is configurable; everything after it is hard-coded.

Identity: jiaban body fields are staffId / orgId (NOT lxUserId as in
boardrooms). When user_token is supplied on the query string, the gateway
injects identity, making body staffId / orgId optional for most endpoints.
submit_approve uses applyerId (own field) and get_my_apply_page_info uses
creatorId (inside page_vo) — these are passed through explicitly rather than
via the staff_id convention.

Upload step: jiaban `upload` returns a pre-signed S3 URL; the caller must then
PUT the file to that URL with a Content-MD5 header. The PUT step is modeled
separately as `put_jiaban_file` so it is not silently dropped.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import (
    JiabanGroupListResult,
    JiabanCalculateDurationResult,
    JiabanMaxVersionConfigListResult,
    JiabanMyApplyPageResult,
    JiabanSubmitApproveResult,
    JiabanUploadUrlResult,
    JiabanUploadFileResult,
)
from .pagination import parse_v2_page_info
from .url_helpers import build_api_url

JIABAN_UPLOAD_TIMEOUT = 60.0


async def fetch_jiaban_get_max_version_config_list(
    config: LansengerConfig,
    app_token: str,
    *,
    org_id: str,
    staff_id: str,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanMaxVersionConfigListResult:
    """考勤组规则配置列表 (加班 V2 /getMaxVersionConfigList)."""
    if not org_id:
        return JiabanMaxVersionConfigListResult(success=False, error="org_id is required")
    if not staff_id:
        return JiabanMaxVersionConfigListResult(success=False, error="staff_id is required")

    url = build_api_url(config, "jiaban", "get_max_version_config_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"orgId": org_id, "staffId": staff_id}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanMaxVersionConfigListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanMaxVersionConfigListResult(success=False, error=api_err)

    items = (data or {}).get("data") or []
    return JiabanMaxVersionConfigListResult(
        success=True, items=items, total=len(items), raw_response=data,
    )


async def fetch_jiaban_upload_url(
    config: LansengerConfig,
    app_token: str,
    *,
    file_name: str,
    md5: str,
    size: int,
    org_id: str,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanUploadUrlResult:
    """取加班附件预签名上传地址 (加班 V2 /upload)."""
    if not file_name:
        return JiabanUploadUrlResult(success=False, error="file_name is required")
    if not md5:
        return JiabanUploadUrlResult(success=False, error="md5 is required")
    if size is None:
        return JiabanUploadUrlResult(success=False, error="size is required")
    if not org_id:
        return JiabanUploadUrlResult(success=False, error="org_id is required")

    url = build_api_url(config, "jiaban", "upload", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "fileName": file_name,
        "md5": md5,
        "size": size,
        "orgId": org_id,
    }

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanUploadUrlResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanUploadUrlResult(success=False, error=api_err)

    return JiabanUploadUrlResult(
        success=True, value=(data or {}).get("data"), raw_response=data,
    )


async def put_jiaban_file(
    url: str,
    content: str | bytes,
    md5: str,
    *,
    http_client: httpx.AsyncClient | None = None,
    timeout: float = JIABAN_UPLOAD_TIMEOUT,
) -> JiabanUploadFileResult:
    """PUT 文件内容到 fetch_jiaban_upload_url 返回的预签名地址。

    加班附件上传必须带 Content-MD5 头（值为文件 MD5），这一步单独建模，
    避免调用方只取到预签名 URL 就以为上传完成。
    """
    if not url:
        return JiabanUploadFileResult(success=False, error="url is required")
    if not md5:
        return JiabanUploadFileResult(success=False, error="md5 is required")

    headers = {"Content-MD5": md5, "Content-Type": "application/octet-stream"}
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=timeout)
    try:
        response = await http_client.put(url, content=content, headers=headers)
    except Exception as exc:  # network-level failure
        return JiabanUploadFileResult(success=False, error=f"network error: {exc}")
    finally:
        if owns_client:
            await http_client.aclose()

    if response.status_code >= 400:
        return JiabanUploadFileResult(
            success=False,
            error=f"HTTP error {response.status_code} {response.reason_phrase or ''}".strip(),
        )
    return JiabanUploadFileResult(success=True)


async def fetch_jiaban_submit_approve(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    applyer_id: str,
    start_time: int,
    end_time: int,
    memo: str,
    approve_ids: list[str],
    overtime_type: int,
    apply_type: int,
    apply_vo: dict[str, Any] | None = None,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanSubmitApproveResult:
    """提交加班申请 (加班 V2 /submitApprove)."""
    if not cmc_code:
        return JiabanSubmitApproveResult(success=False, error="cmc_code is required")
    if not applyer_id:
        return JiabanSubmitApproveResult(success=False, error="applyer_id is required")
    if start_time is None:
        return JiabanSubmitApproveResult(success=False, error="start_time is required")
    if end_time is None:
        return JiabanSubmitApproveResult(success=False, error="end_time is required")
    if not memo:
        return JiabanSubmitApproveResult(success=False, error="memo is required")
    if not approve_ids:
        return JiabanSubmitApproveResult(success=False, error="approve_ids is required")
    if overtime_type is None:
        return JiabanSubmitApproveResult(success=False, error="overtime_type is required")
    if apply_type is None:
        return JiabanSubmitApproveResult(success=False, error="apply_type is required")

    url = build_api_url(config, "jiaban", "submit_approve", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "cmcCode": cmc_code,
        "applyerId": applyer_id,
        "startTime": start_time,
        "endTime": end_time,
        "memo": memo,
        "approveIds": approve_ids,
        "overtimeType": overtime_type,
        "applyType": apply_type,
    }
    if apply_vo:
        body.update(apply_vo)

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanSubmitApproveResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanSubmitApproveResult(success=False, error=api_err)

    return JiabanSubmitApproveResult(
        success=True, value=(data or {}).get("data"), raw_response=data,
    )


async def fetch_jiaban_get_my_apply_page_info(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    page_vo: dict[str, Any],
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanMyApplyPageResult:
    """我的加班申请分页 (加班 V2 /getMyApplyPageInfo)."""
    if not cmc_code:
        return JiabanMyApplyPageResult(success=False, error="cmc_code is required")
    if not page_vo:
        return JiabanMyApplyPageResult(success=False, error="page_vo is required")

    url = build_api_url(config, "jiaban", "get_my_apply_page_info", app_token, user_token=user_token)
    body: dict[str, Any] = {"cmcCode": cmc_code}
    body.update(page_vo)

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanMyApplyPageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanMyApplyPageResult(success=False, error=api_err)

    return JiabanMyApplyPageResult(
        success=True, raw_response=data,
        **parse_v2_page_info((data or {}).get("data")),
    )


async def fetch_jiaban_get_group_info(
    config: LansengerConfig,
    app_token: str,
    *,
    staff_id: str,
    org_id: str,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanGroupListResult:
    """员工所在考勤组 (加班 V2 /getGroupInfo)."""
    if not staff_id:
        return JiabanGroupListResult(success=False, error="staff_id is required")
    if not org_id:
        return JiabanGroupListResult(success=False, error="org_id is required")

    url = build_api_url(config, "jiaban", "get_group_info", app_token, user_token=user_token)
    body: dict[str, Any] = {"staffId": staff_id, "orgId": org_id}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanGroupListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanGroupListResult(success=False, error=api_err)

    items = (data or {}).get("data") or []
    return JiabanGroupListResult(
        success=True, items=items, total=len(items), raw_response=data,
    )


async def fetch_jiaban_calculate_duration(
    config: LansengerConfig,
    app_token: str,
    *,
    cmc_code: str,
    begin_time: int,
    end_time: int,
    group_code: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> JiabanCalculateDurationResult:
    """计算加班时长 (加班 V2 /calculateDuration)."""
    if not cmc_code:
        return JiabanCalculateDurationResult(success=False, error="cmc_code is required")
    if begin_time is None:
        return JiabanCalculateDurationResult(success=False, error="begin_time is required")
    if end_time is None:
        return JiabanCalculateDurationResult(success=False, error="end_time is required")

    url = build_api_url(config, "jiaban", "calculate_duration", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "cmcCode": cmc_code,
        "beginTime": begin_time,
        "endTime": end_time,
    }
    if group_code:
        body["groupCode"] = group_code

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return JiabanCalculateDurationResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data or {})
    if not ok:
        return JiabanCalculateDurationResult(success=False, error=api_err)

    return JiabanCalculateDurationResult(
        success=True, value=(data or {}).get("data"), raw_response=data,
    )
