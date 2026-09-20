"""Lansenger boardroom API — meeting-room lookup and reservation (会议室预定 V2).

Endpoints:
- POST /xtra/boardroom/server/openapi/v2/roomList        — filter meeting rooms (paged)
- POST /xtra/boardroom/server/openapi/v2/roomDetail      — room detail (equipment, service staff)
- POST /xtra/boardroom/server/openapi/v2/roomSchedule    — a room's bookings + deactivations for a date
- POST /xtra/boardroom/server/openapi/v2/reserveDetail   — reservation detail (attendees, approvals)
- POST /xtra/boardroom/server/openapi/v2/reserveRoom     — reserve (single/repeat; id+editType = edit)
- POST /xtra/boardroom/server/openapi/v2/editReserve     — edit (only non-approval reservations)
- POST /xtra/boardroom/server/openapi/v2/reserveCancel   — cancel (status 0/1/5 only)
- POST /xtra/boardroom/server/openapi/v2/confirmSign     — scan-code confirmation (status 1 only)
- POST /xtra/boardroom/server/openapi/v2/myReserveList   — my reservations (paged)
- POST /xtra/boardroom/server/openapi/v2/gradingList     — visible gradings
- POST /xtra/boardroom/server/openapi/v2/areaOfficeList  — office areas of a grading

All endpoints use POST with app_token query param. user_token optional: when
provided, body identity fields (lxUserId / orgId / reserveUser / cancelUserId)
may be omitted — and per the doc, a non-empty user_token OVERRIDES those body
fields. gradingId is required by many endpoints (missing → error or silently
empty result depending on the endpoint). Paths carry a ``/server`` segment
(production stage; dev/test environments omit it). Note: several fields use
the historical spelling ``Fooler`` (= Floor). Time strings: reserve endpoints
use ``yyyy-MM-dd HH:mm:ss``; roomList filter uses ``yyyy-MM-dd HH:mm``.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import (
    BoardroomAreaListResult,
    BoardroomDetailResult,
    BoardroomGradingListResult,
    BoardroomListResult,
    BoardroomOpResult,
    BoardroomReserveResult,
    BoardroomReserveDetailResult,
    BoardroomScheduleResult,
)
from .url_helpers import build_api_url

BOARDROOM_STATUS_APPROVING = 0
BOARDROOM_STATUS_PENDING_SIGN = 1
BOARDROOM_STATUS_SIGN_TIMEOUT = 2
BOARDROOM_STATUS_REJECTED = 3
BOARDROOM_STATUS_CANCELED = 4
BOARDROOM_STATUS_RESERVED = 5
BOARDROOM_STATUS_FINISHED = 6

BOARDROOM_APPROVE_NONE = 0
BOARDROOM_APPROVE_ONGOING = 1
BOARDROOM_APPROVE_PASSED = 2
BOARDROOM_APPROVE_REJECTED = 3

BOARDROOM_RESERVE_TYPE_SINGLE = "0"
BOARDROOM_RESERVE_TYPE_REPEAT = "1"

BOARDROOM_EDIT_TYPE_CURRENT = "1"
BOARDROOM_EDIT_TYPE_CURRENT_AND_AFTER = "2"

BOARDROOM_CANCEL_TYPE_CURRENT = "1"
BOARDROOM_CANCEL_TYPE_CURRENT_AND_AFTER = "2"
BOARDROOM_CANCEL_TYPE_ALL_UNFINISHED = "3"


def _identity(body: dict[str, Any], lx_user_id: str = "", org_id: str = "") -> None:
    """Append optional identity fields — omitted entirely when empty."""
    if lx_user_id:
        body["lxUserId"] = lx_user_id
    if org_id:
        body["orgId"] = org_id


def _page_info(data: dict | None) -> dict[str, Any]:
    """Extract the shared PageInfo{count, data} fields."""
    d = data or {}
    items = d.get("data") or []
    return {"count": d.get("count", 0), "items": items}


def _reserve_body(
    boardroom_id: str,
    name: str,
    grading_id: str,
    reserve_time_start: str,
    reserve_time_end: str,
    notice_time: str,
    *,
    reserve_user: str = "",
    org_id: str = "",
    toastmaster: str = "",
    leader: str = "",
    leader_attend: str = "",
    people_number: str = "",
    other_demand: str = "",
    is_video: str = "",
    video_name: str = "",
    user_list: list[str] | None = None,
    invitation_user_list: list[str] | None = None,
    table_cards: str = "",
    reserve_type: str = "",
    repeat_type: str = "",
    repeat_days: list[int] | None = None,
    skip: str = "",
    repeat_end_date: str = "",
    reserve_id: str = "",
    edit_type: str = "",
) -> dict[str, Any]:
    """Build the shared reserve/edit body (ExternalReserveRoomVO)."""
    body: dict[str, Any] = {
        "boardRoomId": boardroom_id,
        "name": name,
        "gradingId": grading_id,
        "reserveTimeStartStr": reserve_time_start,
        "reserveTimeEndStr": reserve_time_end,
        "noticeTime": notice_time,
    }
    if reserve_user:
        body["reserveUser"] = reserve_user
    if org_id:
        body["orgId"] = org_id
    if toastmaster:
        body["toastmaster"] = toastmaster
    if leader:
        body["leader"] = leader
    if leader_attend:
        body["leaderAttend"] = leader_attend
    if people_number:
        body["peopleNumber"] = people_number
    if other_demand:
        body["otherDemand"] = other_demand
    if is_video:
        body["isVideo"] = is_video
    if video_name:
        body["videoName"] = video_name
    if user_list:
        body["userList"] = user_list
    if invitation_user_list:
        body["invitationUserList"] = invitation_user_list
    if table_cards:
        body["tableCards"] = table_cards
    if reserve_type:
        body["reserveType"] = reserve_type
    if repeat_type:
        body["repeatType"] = repeat_type
    if repeat_days:
        body["repeatDays"] = repeat_days
    if skip:
        body["skip"] = skip
    if repeat_end_date:
        body["repeatEndDateStr"] = repeat_end_date
    if reserve_id:
        body["id"] = reserve_id
    if edit_type:
        body["editType"] = edit_type
    return body


async def _do_reserve(
    config: LansengerConfig,
    url: str,
    body: dict[str, Any],
    http_client: httpx.AsyncClient | None,
) -> BoardroomReserveResult:
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomReserveResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomReserveResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return BoardroomReserveResult(
        success=True,
        reserve_id=d.get("id"),
        reserve_code=d.get("reserveCode"),
        boardroom_name=d.get("boardRoomName"),
        meeting_name=d.get("name"),
        status=d.get("status"),
        reserve_time_start=d.get("reserveTimeStart"),
        reserve_time_end=d.get("reserveTimeEnd"),
        reserve_time=d.get("reserveTime"),
        raw_response=data,
    )


async def fetch_boardroom_list(
    config: LansengerConfig,
    app_token: str,
    *,
    grading_id: str = "",
    area_office_id: str = "",
    floor_ids: list[str] | None = None,
    equipment: list[str] | None = None,
    reserve_time_start: str = "",
    reserve_time_end: str = "",
    query_date: str = "",
    page: int = 1,
    limit: int = 10,
    lx_user_id: str = "",
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomListResult:
    """Filter meeting rooms by area/floor/equipment/time/capacity (会议室预定 V2 /v2/roomList).

    Args:
        grading_id: Grading (分区) ID — several endpoints fail or return empty without it.
        reserve_time_start/end: ``yyyy-MM-dd HH:mm`` filter for availability.
        query_date: ``yyyy-MM-dd``; server defaults to today; enables deactivation info.
    """
    url = build_api_url(config, "boardrooms", "room_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"page": page, "limit": limit}
    if grading_id:
        body["gradingId"] = grading_id
    if area_office_id:
        body["areaOfficeId"] = area_office_id
    if floor_ids:
        body["areaOfficeFoolerIds"] = floor_ids
    if equipment:
        body["equipment"] = equipment
    if reserve_time_start:
        body["reserveTimeStartStr"] = reserve_time_start
    if reserve_time_end:
        body["reserveTimeEndStr"] = reserve_time_end
    if query_date:
        body["queryDate"] = query_date
    _identity(body, lx_user_id, org_id)

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomListResult(success=False, error=api_err)
    return BoardroomListResult(success=True, raw_response=data, **_page_info(data.get("data") or {}))


async def fetch_boardroom_detail(
    config: LansengerConfig,
    app_token: str,
    room_id: str,
    *,
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomDetailResult:
    """Fetch meeting-room detail incl. equipment and service staff (会议室预定 V2 /v2/roomDetail)."""
    if not room_id:
        return BoardroomDetailResult(success=False, error="room_id is required")

    url = build_api_url(config, "boardrooms", "room_detail", app_token, user_token=user_token)
    body: dict[str, Any] = {"id": room_id}
    if org_id:
        body["orgId"] = org_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return BoardroomDetailResult(
        success=True,
        room_id=d.get("id"),
        name=d.get("name"),
        status=d.get("status"),
        people_num=d.get("peopleNum"),
        can_reserve_flag=d.get("canReserveFlag"),
        address=d.get("address"),
        area_name=d.get("areaName"),
        grading_id=d.get("gradingId"),
        raw_response=data,
    )


async def fetch_boardroom_schedule(
    config: LansengerConfig,
    app_token: str,
    room_id: str,
    query_date: str,
    grading_id: str,
    *,
    reserve_user_id: str = "",
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomScheduleResult:
    """Fetch a room's bookings + deactivation info for a date (会议室预定 V2 /v2/roomSchedule).

    Args:
        query_date: ``yyyy-MM-dd``.
        grading_id: Required by this endpoint.
    """
    if not room_id:
        return BoardroomScheduleResult(success=False, error="room_id is required")
    if not query_date:
        return BoardroomScheduleResult(success=False, error="query_date is required")
    if not grading_id:
        return BoardroomScheduleResult(success=False, error="grading_id is required")

    url = build_api_url(config, "boardrooms", "room_schedule", app_token, user_token=user_token)
    body: dict[str, Any] = {"roomId": room_id, "queryDate": query_date, "gradingId": grading_id}
    if reserve_user_id:
        body["reserveUserId"] = reserve_user_id
    if org_id:
        body["orgId"] = org_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomScheduleResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomScheduleResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return BoardroomScheduleResult(
        success=True,
        room_id=d.get("id"),
        name=d.get("name"),
        people_num=d.get("peopleNum"),
        can_reserve_flag=d.get("canReserveFlag"),
        reserves=d.get("reserveDtoList"),
        deactivations=d.get("deactivatedInfoList"),
        raw_response=data,
    )


async def fetch_boardroom_reserve_detail(
    config: LansengerConfig,
    app_token: str,
    reserve_room_id: str,
    *,
    grading_id: str = "",
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomReserveDetailResult:
    """Fetch reservation detail: room, attendees, approval flow (会议室预定 V2 /v2/reserveDetail)."""
    if not reserve_room_id:
        return BoardroomReserveDetailResult(success=False, error="reserve_room_id is required")

    url = build_api_url(config, "boardrooms", "reserve_detail", app_token, user_token=user_token)
    body: dict[str, Any] = {"reserveRoomId": reserve_room_id}
    if grading_id:
        body["gradingId"] = grading_id
    if org_id:
        body["orgId"] = org_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomReserveDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomReserveDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return BoardroomReserveDetailResult(
        success=True,
        reserve_id=d.get("id"),
        boardroom_name=d.get("boardRoomName"),
        meeting_name=d.get("name"),
        status=d.get("status"),
        reserve_time_start=d.get("reserveTimeStart"),
        reserve_time_end=d.get("reserveTimeEnd"),
        reserve_time=d.get("reserveTime"),
        reserve_user_name=d.get("reserveUserName"),
        people_number=d.get("peopleNumber"),
        raw_response=data,
    )


async def reserve_boardroom(
    config: LansengerConfig,
    app_token: str,
    boardroom_id: str,
    name: str,
    grading_id: str,
    reserve_time_start: str,
    reserve_time_end: str,
    notice_time: str,
    *,
    reserve_user: str = "",
    org_id: str = "",
    toastmaster: str = "",
    leader: str = "",
    leader_attend: str = "",
    people_number: str = "",
    other_demand: str = "",
    is_video: str = "",
    video_name: str = "",
    user_list: list[str] | None = None,
    invitation_user_list: list[str] | None = None,
    table_cards: str = "",
    reserve_type: str = BOARDROOM_RESERVE_TYPE_SINGLE,
    repeat_type: str = "",
    repeat_days: list[int] | None = None,
    skip: str = "",
    repeat_end_date: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomReserveResult:
    """Reserve a meeting room, single or repeating (会议室预定 V2 /v2/reserveRoom).

    Args:
        boardroom_id/name/grading_id/notice_time: Required.
        reserve_time_start/end: ``yyyy-MM-dd HH:mm:ss``.
        notice_time: 不提醒/立即提醒/会前15分钟/会前30分钟/会前1小时/会前2小时/会前1天
            (doc gives no code mapping; pass the documented value string).
        reserve_type: "0"=single, "1"=repeat (repeat needs repeatType/repeatDays).
        leader_attend/is_video/table_cards: doc strings with 0/1 semantics —
            see skill notes (several are inverted: 0=on).
    """
    if not boardroom_id:
        return BoardroomReserveResult(success=False, error="boardroom_id is required")
    if not name:
        return BoardroomReserveResult(success=False, error="name is required")
    if not grading_id:
        return BoardroomReserveResult(success=False, error="grading_id is required")
    if not reserve_time_start:
        return BoardroomReserveResult(success=False, error="reserve_time_start is required")
    if not reserve_time_end:
        return BoardroomReserveResult(success=False, error="reserve_time_end is required")
    if not notice_time:
        return BoardroomReserveResult(success=False, error="notice_time is required")

    url = build_api_url(config, "boardrooms", "reserve_room", app_token, user_token=user_token)
    body = _reserve_body(
        boardroom_id, name, grading_id, reserve_time_start, reserve_time_end, notice_time,
        reserve_user=reserve_user, org_id=org_id, toastmaster=toastmaster, leader=leader,
        leader_attend=leader_attend, people_number=people_number, other_demand=other_demand,
        is_video=is_video, video_name=video_name, user_list=user_list,
        invitation_user_list=invitation_user_list, table_cards=table_cards,
        reserve_type=reserve_type, repeat_type=repeat_type, repeat_days=repeat_days,
        skip=skip, repeat_end_date=repeat_end_date,
    )
    return await _do_reserve(config, url, body, http_client)


async def edit_boardroom_reserve(
    config: LansengerConfig,
    app_token: str,
    reserve_id: str,
    boardroom_id: str,
    name: str,
    grading_id: str,
    reserve_time_start: str,
    reserve_time_end: str,
    notice_time: str,
    *,
    edit_type: str = BOARDROOM_EDIT_TYPE_CURRENT,
    reserve_user: str = "",
    org_id: str = "",
    toastmaster: str = "",
    leader: str = "",
    leader_attend: str = "",
    people_number: str = "",
    other_demand: str = "",
    is_video: str = "",
    video_name: str = "",
    user_list: list[str] | None = None,
    invitation_user_list: list[str] | None = None,
    table_cards: str = "",
    reserve_type: str = BOARDROOM_RESERVE_TYPE_SINGLE,
    repeat_type: str = "",
    repeat_days: list[int] | None = None,
    skip: str = "",
    repeat_end_date: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomReserveResult:
    """Edit a reservation — only non-approval-flow reservations support editing (会议室预定 V2 /v2/editReserve).

    Args:
        edit_type: "1"=edit this booking only, "2"=edit this and all following.
    """
    if not reserve_id:
        return BoardroomReserveResult(success=False, error="reserve_id is required")
    if not boardroom_id:
        return BoardroomReserveResult(success=False, error="boardroom_id is required")
    if not name:
        return BoardroomReserveResult(success=False, error="name is required")
    if not grading_id:
        return BoardroomReserveResult(success=False, error="grading_id is required")
    if not reserve_time_start:
        return BoardroomReserveResult(success=False, error="reserve_time_start is required")
    if not reserve_time_end:
        return BoardroomReserveResult(success=False, error="reserve_time_end is required")
    if not notice_time:
        return BoardroomReserveResult(success=False, error="notice_time is required")

    url = build_api_url(config, "boardrooms", "edit_reserve", app_token, user_token=user_token)
    body = _reserve_body(
        boardroom_id, name, grading_id, reserve_time_start, reserve_time_end, notice_time,
        reserve_user=reserve_user, org_id=org_id, toastmaster=toastmaster, leader=leader,
        leader_attend=leader_attend, people_number=people_number, other_demand=other_demand,
        is_video=is_video, video_name=video_name, user_list=user_list,
        invitation_user_list=invitation_user_list, table_cards=table_cards,
        reserve_type=reserve_type, repeat_type=repeat_type, repeat_days=repeat_days,
        skip=skip, repeat_end_date=repeat_end_date, reserve_id=reserve_id, edit_type=edit_type,
    )
    return await _do_reserve(config, url, body, http_client)


async def cancel_boardroom_reserve(
    config: LansengerConfig,
    app_token: str,
    reserve_id: str,
    *,
    cancel_user_id: str = "",
    org_id: str = "",
    cancel_reason: str = "",
    is_send: bool | None = None,
    notify_user_list: list[str] | None = None,
    cancel_video: str = "",
    cancel_type: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomOpResult:
    """Cancel a reservation — only status 0(审批中)/1(待扫码确认)/5(预定成功) revocable (会议室预定 V2 /v2/reserveCancel).

    Args:
        cancel_type: "1"=this booking, "2"=this and following, "3"=all unfinished.
        is_send: notify attendees (server default false).
    """
    if not reserve_id:
        return BoardroomOpResult(success=False, error="reserve_id is required")

    url = build_api_url(config, "boardrooms", "reserve_cancel", app_token, user_token=user_token)
    body: dict[str, Any] = {"id": reserve_id}
    if cancel_user_id:
        body["cancelUserId"] = cancel_user_id
    if org_id:
        body["orgId"] = org_id
    if cancel_reason:
        body["cancelReason"] = cancel_reason
    if is_send is not None:
        body["isSend"] = is_send
    if notify_user_list:
        body["userList"] = notify_user_list
    if cancel_video:
        body["cancelVideo"] = cancel_video
    if cancel_type:
        body["cancelType"] = cancel_type

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomOpResult(success=False, error=api_err)
    return BoardroomOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def confirm_boardroom_sign(
    config: LansengerConfig,
    app_token: str,
    reserve_id: str,
    *,
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomOpResult:
    """Scan-code confirmation — only status 1(待扫码确认) reservations (会议室预定 V2 /v2/confirmSign)."""
    if not reserve_id:
        return BoardroomOpResult(success=False, error="reserve_id is required")

    url = build_api_url(config, "boardrooms", "confirm_sign", app_token, user_token=user_token)
    body: dict[str, Any] = {"id": reserve_id}
    if org_id:
        body["orgId"] = org_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomOpResult(success=False, error=api_err)
    return BoardroomOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def fetch_my_boardroom_reserves(
    config: LansengerConfig,
    app_token: str,
    grading_id: str,
    *,
    keys: str = "",
    start_time: str = "",
    end_time: str = "",
    boardroom_id: str = "",
    floor_ids: list[str] | None = None,
    page: int = 1,
    limit: int = 10,
    lx_user_id: str = "",
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomListResult:
    """Page my reservations with filters (会议室预定 V2 /v2/myReserveList)."""
    if not grading_id:
        return BoardroomListResult(success=False, error="grading_id is required")

    url = build_api_url(config, "boardrooms", "my_reserve_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"gradingId": grading_id, "page": page, "limit": limit}
    if keys:
        body["keys"] = keys
    if start_time:
        body["startTime"] = start_time
    if end_time:
        body["endTime"] = end_time
    if boardroom_id:
        body["boardRoomId"] = boardroom_id
    if floor_ids:
        body["areaOfficeFoolerIds"] = floor_ids
    _identity(body, lx_user_id, org_id)

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomListResult(success=False, error=api_err)
    return BoardroomListResult(success=True, raw_response=data, **_page_info(data.get("data") or {}))


async def fetch_boardroom_gradings(
    config: LansengerConfig,
    app_token: str,
    *,
    lx_user_id: str = "",
    org_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomGradingListResult:
    """Fetch gradings visible to the user (会议室预定 V2 /v2/gradingList).

    Each item's ``id`` is the gradingId needed by the other endpoints.
    """
    url = build_api_url(config, "boardrooms", "grading_list", app_token, user_token=user_token)
    body: dict[str, Any] = {}
    _identity(body, lx_user_id, org_id)

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomGradingListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomGradingListResult(success=False, error=api_err)

    gradings = data.get("data") or []
    return BoardroomGradingListResult(success=True, total=len(gradings), gradings=gradings, raw_response=data)


async def fetch_boardroom_area_offices(
    config: LansengerConfig,
    app_token: str,
    grading_id: str,
    *,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> BoardroomAreaListResult:
    """Fetch office areas under a grading (会议室预定 V2 /v2/areaOfficeList)."""
    if not grading_id:
        return BoardroomAreaListResult(success=False, error="grading_id is required")

    url = build_api_url(config, "boardrooms", "area_office_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"gradingId": grading_id}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BoardroomAreaListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BoardroomAreaListResult(success=False, error=api_err)

    areas = data.get("data") or []
    return BoardroomAreaListResult(success=True, total=len(areas), areas=areas, raw_response=data)
