"""Lansenger videoconference API — video-meeting open APIs (视频会议开放能力).

Endpoints (all POST, prefix /xtra/videoconference/openapi/v1):
- /meeting/create              — create a meeting (instant or reserved)
- /meeting/modify              — modify a meeting that has not started
- /meeting/cancle              — cancel a meeting that has not started
                                (endpoint keeps the server's historical
                                "cancle" spelling)
- /meeting/stop                — end a running meeting
- /meeting/detail              — meeting detail by mid
- /meeting/list                — meeting list by time range (fetchRange my/all/person)
- /meeting/record/list         — meeting operation record list
- /meeting/member/simplerecord — member join/leave records
- /meeting/fixroom/list        — fixed (cloud) meeting-room list
- /meeting/status/fetchmore    — batch meeting status by mids
- /meeting/events/subscribe    — subscribe meeting status-change events
- /meeting/param/fetch         — meeting params by meetingNumber
- /meeting/history/fetch       — a person's past meetings (paged)
- /meeting/active/fetch        — a person's running/reserved meetings (paged)
- /meeting/member/control      — host controls a member (opCode)
- /meeting/member/invite       — invite members to a running meeting
- /meeting/member/list         — paged member list of a meeting
- /meeting/vod/list            — recording list of a meeting
- /vod/url/download/fetch      — recording download URLs (max 3 vods)
- /conf/fetch                  — org videoconference config

LIVE-VERIFIED (2026-09-21, org 2285568): conf fetch / meeting list /
active fetch / status / detail / create / stop all pass. Enum notes:
type 0=instant meeting, 1=reserved (reserved requires start_time in the
future, errCode 105204); cancel only applies to not-started meetings
(errCode 105224 once started — use stop_meeting instead); member roles
are admin (host) / joinHost / participant (errCode 105230 without an
admin member).

All calls go through the standard app gateway (app_token query param, same
as contacts/groups). Prerequisites per docs: the org has the 视频会议 app
installed (platform ≥3.6), the EMC backend configured the app's external
identifier, and the developer-center 开放能力 switch is on with a service
address. Time values are epoch milliseconds. The member list endpoint is
documented as GET but carries a JSON body — we send it as POST like every
other call on this gateway.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import (
    VideoconferenceConfResult,
    VideoconferenceDetailResult,
    VideoconferenceListResult,
    VideoconferenceOpResult,
    VideoconferenceParamResult,
    VideoconferenceStatusListResult,
    VideoconferenceVodListResult,
    VideoconferenceVodUrlResult,
)
from .url_helpers import build_api_url

VC_MEMBER_ROLE_HOST = "admin"
VC_MEMBER_ROLE_MEMBER = "participant"

# opCode values for member/control (接口枚举字典)
VC_OPS = (
    "kick", "quit", "join", "handup", "openScreenShare", "closeScreenShare",
    "openVideo", "closeVideo", "applyAudio", "applyVideo", "shareVideo",
    "cancelShareVideo", "muteall", "unmuteall", "remove", "call",
    "enforceOpenVideo", "setJoinHost", "cancelJoinHost", "inviteOpenAudio",
    "setHost", "grabHost",
)

VC_FETCH_RANGE_MY = "my"
VC_FETCH_RANGE_ALL = "all"
VC_FETCH_RANGE_PERSON = "person"

# createSource for meeting/record/list
VC_CREATE_SOURCE_CLIENT = 0
VC_CREATE_SOURCE_THIRD_PARTY = 1


def _members(members: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
    return members


def _host_required(members: list[dict[str, Any]] | None) -> str | None:
    """Server requires exactly one member with the host role on create."""
    if not members:
        return "member is required (with exactly one host)"
    hosts = [m for m in members if str(m.get("role", "")) == VC_MEMBER_ROLE_HOST]
    if len(hosts) != 1:
        return "exactly one member must have role='admin'"
    return None


def _page(data: dict | None) -> dict[str, Any]:
    d = data or {}
    return {"offset": d.get("offset", 0), "total": d.get("total", 0),
            "items": d.get("items") or d.get("mids")}


def _op(data: dict | None) -> dict[str, Any]:
    d = (data or {}).get("data") or {}
    return {"done": d.get("code") == 0, "message": d.get("message")}


async def create_meeting(
    config: LansengerConfig,
    app_token: str,
    *,
    subject: str,
    start_time: int,
    members: list[dict[str, Any]],
    org_id: int | str,
    auto_record: int = 0,
    type: int = 1,
    group_new: int = 0,
    conf_password: str = "",
    control_password: str = "",
    mask_type: int = 0,
    ext_attr: str = "",
    join_mute: int | None = None,
    open_mute: int | None = None,
    enable_pre_join: int | None = None,
    user_stop_time: int | None = None,
    invite_admin: int | None = None,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceDetailResult:
    """Create a meeting (instant or reserved) (/meeting/create).

    Args:
        members: [{staffId, employeeName, role}]; exactly one role='admin'.
        start_time: epoch milliseconds; later than now for reserved meetings.
    """
    if not subject:
        return VideoconferenceDetailResult(success=False, error="subject is required")
    err = _host_required(members)
    if err:
        return VideoconferenceDetailResult(success=False, error=err)
    if not start_time:
        return VideoconferenceDetailResult(success=False, error="start_time is required")

    url = build_api_url(config, "videoconferences", "meeting_create", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "subject": subject, "startTime": start_time,
        "autoRecord": auto_record, "type": type, "groupNew": group_new,
        "confPassword": conf_password, "controlPassword": control_password,
        "member": _members(members), "extAttr": ext_attr,
        "maskType": mask_type, "orgId": int(org_id) if str(org_id).isdigit() else org_id,
    }
    for key, val in (("joinMute", join_mute), ("openMute", open_mute),
                     ("enablePreJoin", enable_pre_join),
                     ("userStopTime", user_stop_time), ("inviteAdmin", invite_admin)):
        if val is not None:
            body[key] = val

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceDetailResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return VideoconferenceDetailResult(
        success=True, mid=d.get("id") or d.get("mid"),
        subject=d.get("subject"), meeting_number=d.get("meetingNumber"),
        start_time=d.get("startTime"), type=d.get("type"), status=d.get("status"),
        raw_response=data,
    )


async def modify_meeting(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    subject: str, start_time: int, members: list[dict[str, Any]],
    org_id: int | str, operator: str, auto_record: int = 0,
    type: int = 1, group_new: int = 0, conf_password: str = "",
    control_password: str = "", user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """Modify a meeting that has not started yet (/meeting/modify)."""
    err = _host_required(members)
    if err:
        return VideoconferenceOpResult(success=False, error=err)
    url = build_api_url(config, "videoconferences", "meeting_modify", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id, "operator": operator,
        "mid": int(mid), "subject": subject, "startTime": start_time,
        "autoRecord": auto_record, "type": type, "groupNew": group_new,
        "confPassword": conf_password, "controlPassword": control_password,
        "member": _members(members),
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def cancel_meeting(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """Cancel a meeting that has not started (/meeting/cancle)."""
    url = build_api_url(config, "videoconferences", "meeting_cancel", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "mid": int(mid),
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def stop_meeting(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """End a running meeting (/meeting/stop)."""
    url = build_api_url(config, "videoconferences", "meeting_stop", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "mid": int(mid),
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def fetch_meeting_detail(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceDetailResult:
    """Meeting detail by mid (/meeting/detail)."""
    url = build_api_url(config, "videoconferences", "meeting_detail", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "mid": int(mid),
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceDetailResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return VideoconferenceDetailResult(
        success=True, mid=d.get("id"), subject=d.get("subject"),
        meeting_number=d.get("meetingNumber"), start_time=d.get("startTime"),
        stop_time=d.get("stopTime"), type=d.get("type"), status=d.get("status"),
        admin=d.get("admin"), raw_response=data,
    )


async def fetch_meeting_list(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    start_time: int, end_time: int, fetch_range: str = VC_FETCH_RANGE_ALL,
    staff_id: str = "", limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """Meeting list by time range (/meeting/list).

    Args:
        fetch_range: "my" | "all" | "person" (person requires staff_id).
    """
    if fetch_range == VC_FETCH_RANGE_PERSON and not staff_id:
        return VideoconferenceListResult(success=False, error="staff_id is required when fetch_range='person'")
    url = build_api_url(config, "videoconferences", "meeting_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "limit": limit, "offset": offset,
        "startTime": start_time, "endTime": end_time,
        "fetchRange": fetch_range, "staffId": staff_id,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_meeting_record_list(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    start_time: int, end_time: int, admin: str = "",
    create_source: int = VC_CREATE_SOURCE_CLIENT,
    limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """Meeting operation record list (/meeting/record/list).

    Args:
        create_source: 0=platform client, 1=third-party app.
    """
    url = build_api_url(config, "videoconferences", "meeting_record_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "limit": limit, "offset": offset,
        "startTime": start_time, "endTime": end_time,
        "admin": admin, "createSource": create_source,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_member_simplerecord(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """Member join/leave records of a meeting (/meeting/member/simplerecord)."""
    url = build_api_url(config, "videoconferences", "member_simplerecord", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "mid": int(mid), "operator": operator, "limit": limit, "offset": offset,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_fixroom_list(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    operator: str, limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """Fixed (cloud) meeting-room list (/meeting/fixroom/list)."""
    url = build_api_url(config, "videoconferences", "fixroom_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "limit": limit, "offset": offset,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_meeting_status(
    config: LansengerConfig, app_token: str, *, mids: list[int | str],
    org_id: int | str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceStatusListResult:
    """Batch meeting status by mids (/meeting/status/fetchmore)."""
    if not mids:
        return VideoconferenceStatusListResult(success=False, error="mids is required")
    url = build_api_url(config, "videoconferences", "status_fetchmore", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "mids": [int(m) for m in mids],
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceStatusListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceStatusListResult(success=False, error=api_err)
    d = (data.get("data") or {}).get("mids") or []
    return VideoconferenceStatusListResult(success=True, statuses=d, raw_response=data)


async def subscribe_meeting_events(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, events: list[dict[str, Any]],
    call_back_info: str = "", user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """Subscribe meeting status-change events (/meeting/events/subscribe)."""
    url = build_api_url(config, "videoconferences", "events_subscribe", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "mid": int(mid), "events": events,
    }
    if call_back_info:
        body["callBackInfo"] = call_back_info
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def fetch_meeting_params(
    config: LansengerConfig, app_token: str, *, meeting_number: str,
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceParamResult:
    """Meeting params by meetingNumber; PRS ≥3.8 (/meeting/param/fetch)."""
    if not meeting_number:
        return VideoconferenceParamResult(success=False, error="meeting_number is required")
    url = build_api_url(config, "videoconferences", "param_fetch", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "meetingNumber": meeting_number, "operator": operator,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceParamResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceParamResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return VideoconferenceParamResult(success=True, data=d.get("meetingInfo"), raw_response=data)


async def fetch_history_meetings(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    operator: str, limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """A person's past meetings (/meeting/history/fetch)."""
    url = build_api_url(config, "videoconferences", "history_fetch", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "limit": limit, "offset": offset,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_active_meetings(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    operator: str, limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """A person's running + reserved meetings (/meeting/active/fetch)."""
    url = build_api_url(config, "videoconferences", "active_fetch", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "limit": limit, "offset": offset,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def control_member(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    staff_id: str, op_code: str, operator: str, org_id: int | str,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """Host controls a member (/meeting/member/control).

    Args:
        op_code: one of VC_OPS (kick/join/handup/muteall/setHost/...).
        staff_id: the member the operation applies to.
    """
    if op_code not in VC_OPS:
        return VideoconferenceOpResult(success=False, error=f"op_code must be one of {VC_OPS}")
    url = build_api_url(config, "videoconferences", "member_control", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "staffId": staff_id, "mid": int(mid), "opCode": op_code, "operator": operator,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def invite_members(
    config: LansengerConfig, app_token: str, *, meeting_number: str,
    members: list[dict[str, Any]], org_id: int | str, operator: str,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceOpResult:
    """Invite members to a running meeting (/meeting/member/invite).

    Args:
        members: [{staffId, employeeName, type, audio, video, typeMask?}];
            type 0=platform member, 1=小鱼 device (typeMask: 1=PSTN, 2=小鱼, 3=H323).
    """
    if not members:
        return VideoconferenceOpResult(success=False, error="member is required")
    url = build_api_url(config, "videoconferences", "member_invite", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "meetingNumber": meeting_number,
        "member": members,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceOpResult(success=False, error=api_err)
    return VideoconferenceOpResult(success=True, raw_response=data, **_op(data))


async def fetch_member_list(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, limit: int = 10, offset: int = 0,
    user_token: str = "", http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceListResult:
    """Paged member list of a meeting (/meeting/member/list).

    Documented as GET with a JSON body; this gateway's convention is POST,
    so we send POST like the rest of the module.
    """
    url = build_api_url(config, "videoconferences", "member_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "mid": int(mid), "operator": operator, "limit": limit, "offset": offset,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceListResult(success=False, error=api_err)
    return VideoconferenceListResult(success=True, raw_response=data, **_page(data.get("data") or {}))


async def fetch_vod_list(
    config: LansengerConfig, app_token: str, *, mid: int | str,
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceVodListResult:
    """Recording list of a meeting (/meeting/vod/list)."""
    url = build_api_url(config, "videoconferences", "vod_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "mid": int(mid), "operator": operator,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceVodListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceVodListResult(success=False, error=api_err)
    items = (data.get("data") or {}).get("items") or []
    return VideoconferenceVodListResult(success=True, items=items, raw_response=data)


async def fetch_vod_download_urls(
    config: LansengerConfig, app_token: str, *, vods: list[dict[str, Any]],
    org_id: int | str, operator: str, user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceVodUrlResult:
    """Recording download URLs (/vod/url/download/fetch); max 3 vods per call.

    Args:
        vods: [{vodId}] — up to three entries.
    """
    if not vods or len(vods) > 3:
        return VideoconferenceVodUrlResult(success=False, error="vods must contain 1..3 entries")
    url = build_api_url(config, "videoconferences", "vod_download_url", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
        "operator": operator, "vods": vods,
    }
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceVodUrlResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceVodUrlResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return VideoconferenceVodUrlResult(success=True, data=d, raw_response=data)


async def fetch_org_conf(
    config: LansengerConfig, app_token: str, *, org_id: int | str,
    meeting_number: str = "", operator: str = "", user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> VideoconferenceConfResult:
    """Org videoconference config; PRS ≥3.8 (/conf/fetch).

    Pass meeting_number to get the config of the org owning that meeting.
    """
    url = build_api_url(config, "videoconferences", "conf_fetch", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "orgId": int(org_id) if str(org_id).isdigit() else org_id,
    }
    if meeting_number:
        body["meetingNumber"] = meeting_number
    if operator:
        body["operator"] = operator
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return VideoconferenceConfResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return VideoconferenceConfResult(success=False, error=api_err)
    d = data.get("data", {}) or {}
    return VideoconferenceConfResult(
        success=True, max_person=d.get("maxPerson"), default_max_person=d.get("defaultMaxPerson"),
        allowed_record_flag=d.get("allowedRecordFlag"), force_passwd_flag=d.get("forcePasswdFlag"),
        space_size=d.get("spaceSize"), raw_response=data,
    )
