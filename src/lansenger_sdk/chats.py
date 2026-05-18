"""Lansenger chat APIs — fetch chat list and chat messages (4.24 MCP).

Two endpoints for reading conversation data:
- /v1/chats/fetch: query personal chat list (private + group)
- /v1/messages/fetch: fetch messages from a specific conversation

These are POST endpoints that require appToken. userToken is optional
but recommended — it authenticates as a specific human user.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .url_helpers import build_api_url
from .models import (
    ChatGroupInfo,
    ChatListResult,
    ChatMessageInfo,
    ChatMessagesResult,
    ChatStaffInfo,
)

logger = logging.getLogger("lansenger_sdk.chats")


async def fetch_chat_list(
    config: LansengerConfig,
    app_token: str,
    *,
    chat_type: int = 0,
    keyword: str = "",
    start_time: int = 0,
    end_time: int = 0,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ChatListResult:
    """Fetch personal chat list (private + group conversations).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        chat_type: 0=all, 1=private, 2=group (default 0).
        keyword: Search keyword (only works when chat_type is 1 or 2).
        start_time: Filter start time in microseconds.
        end_time: Filter end time in microseconds.
        user_token: Optional userToken for human identity.
        http_client: Optional httpx client.
    """
    url = build_api_url(config, "chats", "fetch", app_token, user_token=user_token)

    payload: Dict[str, Any] = {}
    if chat_type:
        payload["chatType"] = chat_type
    if keyword:
        payload["keyword"] = keyword
    if start_time:
        payload["startTime"] = start_time
    if end_time:
        payload["endTime"] = end_time

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return ChatListResult(success=False, error=f"HTTP error: {e}")
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return ChatListResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return ChatListResult(
            success=False, error=f"API error (errCode={err_code}): {msg}"
        )

    result_data = data.get("data", {})
    staff_infos = []
    for si in result_data.get("staffIdInfos", []):
        staff_infos.append(ChatStaffInfo(
            staff_id=si.get("staffId", ""),
            staff_name=si.get("staffName", ""),
            sector_names=si.get("sectorName") or si.get("sectorNames"),
        ))

    group_infos = []
    for gi in result_data.get("groupIdInfos", []):
        group_infos.append(ChatGroupInfo(
            group_id=gi.get("groupId", ""),
            group_name=gi.get("groupName", ""),
        ))

    return ChatListResult(
        success=True,
        staff_infos=staff_infos,
        group_infos=group_infos,
        raw_response=data,
    )


async def fetch_chat_messages(
    config: LansengerConfig,
    app_token: str,
    *,
    staff_id: str = "",
    group_id: str = "",
    page_size: int = 100,
    base_version: str = "0",
    start_time: int = 0,
    end_time: int = 0,
    sender_id: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> ChatMessagesResult:
    """Fetch messages from a specific conversation.

    staff_id and group_id are mutually exclusive (pick one).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        staff_id: Private chat partner's staffId (for private conversations).
        group_id: Group openId (for group conversations).
        page_size: Per-page count (max 100, default 100).
        base_version: Deep pagination cursor. First call: "0".
        start_time: Filter start time in microseconds.
        end_time: Filter end time in microseconds.
        sender_id: Filter by sender staffId.
        user_token: Optional userToken for human identity.
        http_client: Optional httpx client.
    """
    if not staff_id and not group_id:
        return ChatMessagesResult(
            success=False, error="staff_id or group_id is required"
        )

    url = build_api_url(config, "chats", "messages_fetch", app_token, user_token=user_token)
    url += f"&page_size={page_size}"
    if base_version:
        url += f"&base_version={base_version}"

    payload: Dict[str, Any] = {}
    if staff_id:
        payload["staffId"] = staff_id
    if group_id:
        payload["groupId"] = group_id
    if start_time:
        payload["startTime"] = start_time
    if end_time:
        payload["endTime"] = end_time
    if sender_id:
        payload["senderId"] = sender_id

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return ChatMessagesResult(success=False, error=f"HTTP error: {e}", retryable=True)
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return ChatMessagesResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return ChatMessagesResult(
            success=False, error=f"API error (errCode={err_code}): {msg}"
        )

    result_data = data.get("data", {})
    messages = []
    for msg_item in result_data.get("messageList", []):
        msg_info_raw = msg_item.get("messageInfo") or msg_item.get("messageInfos") or {}
        if isinstance(msg_info_raw, list) and len(msg_info_raw) > 0:
            msg_info_raw = msg_info_raw[0]
        content_raw = msg_info_raw.get("content", {})
        if content_raw is None:
            content_raw = {}
        messages.append(ChatMessageInfo(
            send_time=msg_info_raw.get("sendTime", ""),
            sender=msg_info_raw.get("sender", ""),
            message_type=msg_info_raw.get("type", "") or msg_info_raw.get("messageType", ""),
            content=content_raw,
        ))

    return ChatMessagesResult(
        success=True,
        has_more=result_data.get("hasMore", False),
        total=result_data.get("total", 0),
        last_version=result_data.get("lastVersion", ""),
        name=result_data.get("name", ""),
        chat_type=result_data.get("chatType", ""),
        messages=messages,
        raw_response=data,
    )