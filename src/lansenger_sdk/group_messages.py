"""Lansenger group message API — send messages in a group chat (4.6.2).

Messages sent via this channel appear in the group conversation where all
members can see them. This is the ONLY channel that supports @mentions
(reminder).

Endpoint: POST /v1/messages/group/create?app_token=TOKEN&user_token=TOKEN

Sender identity is determined by auth:
- With user_token: message appears from the human user (must be in the group)
- Without user_token, with senderId: message appears from the specified person
- Without both: message appears from the application bot (requires bot capability)

Supported msgType: all developer-accessible types (text, formatText, oacard, appCard, linkCard, appArticles, verifyCard, i18nAppCard, i18nSystemAction, i18nSystem)

Key fields:
- groupId: target group openId (required)
- senderId: sender openId (required if no user_token, optional if user_token present)
- outlines: group notification digest text (optional)
- uuid: deduplication key (optional)
- entryId: app entry selector for multi-entry apps (optional)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS
from .models import SendMessageResult

logger = logging.getLogger("lansenger_sdk.group_messages")


async def send_group_message(
    config: LansengerConfig,
    app_token: str,
    group_id: str,
    msg_type: str,
    msg_data: dict,
    *,
    user_token: str = "",
    sender_id: str = "",
    outlines: str = "",
    uuid: str = "",
    entry_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> SendMessageResult:
    """Send a message in a group chat (4.6.2).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        group_id: Group openId (required).
        msg_type: Message type — text or oacard only.
        msg_data: Message body dict (msgData field).
        user_token: Optional userToken — determines sender identity as human.
        sender_id: Optional sender openId — used if no user_token.
        outlines: Optional group notification digest text.
        uuid: Optional deduplication key.
        entry_id: Optional app entry selector.
        http_client: Optional httpx client.
    """
    if not msg_type:
        return SendMessageResult(success=False, error="msg_type is required")
    if not group_id:
        return SendMessageResult(success=False, error="group_id is required")
    if not msg_data:
        return SendMessageResult(success=False, error="msg_data is required")

    path = API_ENDPOINTS["smart_bot"]["group_message"]
    url = f"{config.api_gateway_url}{path}?app_token={app_token}"
    if user_token:
        url += f"&user_token={user_token}"

    payload: Dict[str, Any] = {
        "groupId": group_id,
        "msgType": msg_type,
        "msgData": msg_data,
    }
    if sender_id:
        payload["senderId"] = sender_id
    if outlines:
        payload["outlines"] = outlines
    if uuid:
        payload["uuid"] = uuid
    if entry_id:
        payload["entryId"] = entry_id

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
        return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return SendMessageResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return SendMessageResult(
            success=False, error=f"API error (errCode={err_code}): {msg}", retryable=True
        )

    d = data.get("data", {})
    return SendMessageResult(
        success=True,
        message_id=d.get("msgId"),
        msg_type=msg_type,
        operation="group_message",
        raw_response=data,
    )