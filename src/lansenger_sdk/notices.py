"""Lansenger notice API — send official-account notices and query notice accounts (通知系统).

Endpoints:
- POST /xtra/notice/server/openapi/v1/send           — send a notice via an official account
- POST /xtra/notice/server/openapi/v1/notice/account — list official accounts of an organization

All endpoints use POST with app_token query param. user_token optional:
when provided, body identity fields (createMobile / createUserId) may be
omitted. Paths carry a ``/server`` segment (production stage; dev/test
environments serve the same API without it).

The notice module has no revoke/delete interface: ``noticeStatus=3``
(revoked) exists in payloads but cannot be produced through this API.
Validation errors from the server may arrive concatenated without
separators (e.g. "官方账号不存在类型只能填写1或2" is two messages).
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import NoticeAccountListResult, NoticeSendResult
from .url_helpers import build_api_url

NOTICE_CONTENT_TYPE_TEXT = 1
NOTICE_CONTENT_TYPE_LINK = 2

NOTICE_USER_TYPE_PHONE = 1   # target users by mobile number (phoneUserRange)
NOTICE_USER_TYPE_OPENID = 2  # target users by staffId/department (openUserRange)

NOTICE_RANGE_OBJ_TYPE_STAFF = 1
NOTICE_RANGE_OBJ_TYPE_DEPARTMENT = 2

NOTICE_PHONE_RANGE_MAX = 10   # releaseRangeList / ccRangeList phone limit
NOTICE_OPEN_RANGE_MAX = 200   # releaseRangeList / ccRangeList staff limit

NOTICE_REMIND_AFTER_NEVER = "never"
NOTICE_REMIND_AFTER_UN_OPERATE = "unOperate"
NOTICE_REMIND_AFTER_COUNT = "count"

NOTICE_REMIND_RANGE_ALL = "all"
NOTICE_REMIND_RANGE_RECEIVER = "receiver"
NOTICE_REMIND_RANGE_PARTIAL = "partialRemind"
NOTICE_REMIND_RANGE_NOT_REMINDER = "notReminder"

NOTICE_REMIND_AFTER_TYPES = (
    NOTICE_REMIND_AFTER_NEVER, NOTICE_REMIND_AFTER_UN_OPERATE, NOTICE_REMIND_AFTER_COUNT,
)
NOTICE_REMIND_RANGE_TYPES = (
    NOTICE_REMIND_RANGE_ALL, NOTICE_REMIND_RANGE_RECEIVER,
    NOTICE_REMIND_RANGE_PARTIAL, NOTICE_REMIND_RANGE_NOT_REMINDER,
)


async def send_notice(
    config: LansengerConfig,
    app_token: str,
    title: str,
    content_type: int,
    account_code: str,
    user_type: int,
    *,
    content: str = "",
    notice_link: str = "",
    notice_location: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    release_phones: list[str] | None = None,
    cc_phones: list[str] | None = None,
    release_range: list[dict[str, Any]] | None = None,
    cc_staff_ids: list[str] | None = None,
    create_mobile: str = "",
    create_user_id: str = "",
    resource_list: list[dict[str, Any]] | None = None,
    extend_id: str = "",
    confirm_flag: int | None = None,
    forward_flag: int | None = None,
    reply_flag: int | None = None,
    anonymous_flag: int | None = None,
    remind_status: int | None = None,
    remind_msg_type: str = "",
    at_once_flag: int | None = None,
    remind_after_type: str = "",
    remind_max_count: int | None = None,
    remind_interval_time: int | None = None,
    remind_interval_time_duration: str = "",
    remind_range_type: str = "",
    remind_range_staff_ids: list[str] | None = None,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> NoticeSendResult:
    """Send a notice via an official account (通知系统 /v1/send).

    Args:
        title: Notice title.
        content_type: 1=text (content required), 2=link (notice_link required).
        account_code: Official account CODE — fetch via fetch_notice_accounts().
        user_type: 1=phone targeting (release_phones), 2=staffId/department
            targeting (release_range of {objId, objName, objType} dicts).
        release_phones: Receiver mobile numbers, max NOTICE_PHONE_RANGE_MAX.
        cc_phones: CC mobile numbers, max NOTICE_PHONE_RANGE_MAX.
        release_range: Receiver range items, max NOTICE_OPEN_RANGE_MAX;
            each ``{"objId": ..., "objName": ..., "objType": 1|2}``
            (1=staff, 2=department).
        cc_staff_ids: CC staff IDs, max NOTICE_OPEN_RANGE_MAX.
        create_mobile: Operator mobile (user_type=1); may be omitted when
            user_token is provided.
        create_user_id: Creator staff ID (user_type=2); may be omitted when
            user_token is provided.
        resource_list: Attachment items (ResourceBaseInfo dicts, camelCase).
        confirm_flag/forward_flag/reply_flag/anonymous_flag: 1=yes, 0=no;
            omitted → server default (1).
        remind_status: 1=remind, 0=don't. Omitted → SDK sends 0 (the
            server raises errCode=-1 when the field is absent entirely).
        remind_msg_type: Comma-separated: mobile, sms, app.
        at_once_flag: 1=remind immediately.
        remind_after_type: never / unOperate / count.
        remind_max_count: Max remind count (remind_after_type=count).
        remind_interval_time + remind_interval_time_duration: Interval value
            and unit (minutes/hour/day).
        remind_range_type: all / receiver / partialRemind / notReminder.
        remind_range_staff_ids: Staff IDs excluded from reminding.
    """
    if not title:
        return NoticeSendResult(success=False, error="title is required")
    if content_type not in (NOTICE_CONTENT_TYPE_TEXT, NOTICE_CONTENT_TYPE_LINK):
        return NoticeSendResult(success=False, error="content_type must be 1 (text) or 2 (link)")
    if content_type == NOTICE_CONTENT_TYPE_TEXT and not content:
        return NoticeSendResult(success=False, error="content is required when content_type is 1 (text)")
    if content_type == NOTICE_CONTENT_TYPE_LINK and not notice_link:
        return NoticeSendResult(success=False, error="notice_link is required when content_type is 2 (link)")
    if not account_code:
        return NoticeSendResult(success=False, error="account_code is required")
    if user_type not in (NOTICE_USER_TYPE_PHONE, NOTICE_USER_TYPE_OPENID):
        return NoticeSendResult(success=False, error="user_type must be 1 (phone) or 2 (openid)")

    if user_type == NOTICE_USER_TYPE_PHONE:
        if not release_phones:
            return NoticeSendResult(success=False, error="release_phones is required when user_type is 1 (phone)")
        if len(release_phones) > NOTICE_PHONE_RANGE_MAX:
            return NoticeSendResult(success=False, error=f"release_phones allows at most {NOTICE_PHONE_RANGE_MAX} numbers")
        if cc_phones and len(cc_phones) > NOTICE_PHONE_RANGE_MAX:
            return NoticeSendResult(success=False, error=f"cc_phones allows at most {NOTICE_PHONE_RANGE_MAX} numbers")
        if not create_mobile and not user_token:
            return NoticeSendResult(success=False, error="create_mobile is required when user_type is 1 (phone) and user_token is not provided")
    if user_type == NOTICE_USER_TYPE_OPENID:
        if not release_range:
            return NoticeSendResult(success=False, error="release_range is required when user_type is 2 (openid)")
        if len(release_range) > NOTICE_OPEN_RANGE_MAX:
            return NoticeSendResult(success=False, error=f"release_range allows at most {NOTICE_OPEN_RANGE_MAX} items")
        if cc_staff_ids and len(cc_staff_ids) > NOTICE_OPEN_RANGE_MAX:
            return NoticeSendResult(success=False, error=f"cc_staff_ids allows at most {NOTICE_OPEN_RANGE_MAX} items")
        if not create_user_id and not user_token:
            return NoticeSendResult(success=False, error="create_user_id is required when user_type is 2 (openid) and user_token is not provided")

    if remind_after_type and remind_after_type not in NOTICE_REMIND_AFTER_TYPES:
        return NoticeSendResult(success=False, error=f"remind_after_type must be one of: {', '.join(NOTICE_REMIND_AFTER_TYPES)}")
    if remind_range_type and remind_range_type not in NOTICE_REMIND_RANGE_TYPES:
        return NoticeSendResult(success=False, error=f"remind_range_type must be one of: {', '.join(NOTICE_REMIND_RANGE_TYPES)}")

    url = build_api_url(config, "notices", "send", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "title": title,
        "contentType": content_type,
        "accountCode": account_code,
        "userType": user_type,
    }
    if content:
        body["content"] = content
    if notice_link:
        body["noticeLink"] = notice_link
    if notice_location:
        body["noticeLocation"] = notice_location
    if latitude is not None:
        body["latitude"] = latitude
    if longitude is not None:
        body["longitude"] = longitude
    if user_type == NOTICE_USER_TYPE_PHONE:
        # 实测（stage 2026-09-17）：range 对象内缺失 ccRangeList 时服务端抛
        # errCode=-1 unknown exception（NPE），与 remindStatus 缺失同因，强制下发。
        body["phoneUserRange"] = {
            "releaseRangeList": release_phones,
            "ccRangeList": cc_phones or [],
        }
    if user_type == NOTICE_USER_TYPE_OPENID:
        body["openUserRange"] = {
            "releaseRangeList": release_range,
            "ccRangeList": cc_staff_ids or [],
        }
    if create_mobile:
        body["createMobile"] = create_mobile
    if create_user_id:
        body["createUserId"] = create_user_id
    if resource_list:
        body["resourceList"] = resource_list
    if extend_id:
        body["extendId"] = extend_id
    if confirm_flag is not None:
        body["confirmFlag"] = confirm_flag
    if forward_flag is not None:
        body["forwardFlag"] = forward_flag
    if reply_flag is not None:
        body["replyFlag"] = reply_flag
    if anonymous_flag is not None:
        body["anonymousFlag"] = anonymous_flag
    if remind_status is not None:
        body["remindStatus"] = remind_status
    else:
        # 实测（stage 2026-09-17）：缺失 remindStatus 时服务端抛
        # errCode=-1 unknown exception（NPE），兜底为 0（不提醒）。
        body["remindStatus"] = 0
    if remind_msg_type:
        body["remindMsgType"] = remind_msg_type
    if at_once_flag is not None:
        body["atOnceFlag"] = at_once_flag
    if remind_after_type:
        body["remindAfterType"] = remind_after_type
    if remind_max_count is not None:
        body["remindMaxCount"] = remind_max_count
    if remind_interval_time is not None:
        body["remindIntervalTime"] = remind_interval_time
    if remind_interval_time_duration:
        body["remindIntervalTimeDuration"] = remind_interval_time_duration
    if remind_range_type:
        body["remindRangeType"] = remind_range_type
    if remind_range_staff_ids:
        body["remindRangeStaffIds"] = remind_range_staff_ids

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return NoticeSendResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return NoticeSendResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return NoticeSendResult(
        success=True,
        notice_code=d.get("code"),
        notice_id=d.get("id"),
        title=d.get("title"),
        notice_type=d.get("noticeType"),
        content_type=d.get("contentType"),
        content_abstract=d.get("contentAbstract"),
        notice_link=d.get("noticeLink"),
        notice_status=d.get("noticeStatus"),
        confirm_status=d.get("confirmStatus"),
        publish_time=d.get("publishTime"),
        publish_user_id=d.get("publishUserId"),
        publish_user_name=d.get("publishUserName"),
        raw_response=data,
    )


async def fetch_notice_accounts(
    config: LansengerConfig,
    app_token: str,
    *,
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> NoticeAccountListResult:
    """List official accounts of an organization (通知系统 /v1/notice/account).

    Args:
        org_id: Organization ID. Optional per the API spec; the returned
            ``code`` field of each account is the accountCode needed by
            send_notice().
    """
    url = build_api_url(config, "notices", "accounts_fetch", app_token, user_token=user_token)
    body: dict[str, Any] = {}
    if org_id:
        body["orgId"] = org_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return NoticeAccountListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return NoticeAccountListResult(success=False, error=api_err)

    accounts = data.get("data", []) or []
    return NoticeAccountListResult(
        success=True,
        total=len(accounts),
        accounts=accounts,
        raw_response=data,
    )
