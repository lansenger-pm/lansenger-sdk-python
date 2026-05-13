"""Lansenger user message API — send private chat message impersonating a user (4.6.3).

Messages sent via this channel appear as if from a real human user. The
sender identity is derived from userToken (obtained via OAuth2). The
message appears in a 1:1 private chat conversation — as if the person
typed it themselves.

Endpoint: POST /v1/messages/chat/create?app_token=TOKEN&user_token=TOKEN

**user_token is REQUIRED** — must be obtained via OAuth2 flow to identify
the current user.

Key fields:
- receiverId: single recipient openId (1:1 private chat)
- msgType: message type
- msgData: includes "common" sub-object alongside type-specific content
- uuid: optional deduplication key
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS
from .models import UserMessageResult

logger = logging.getLogger("lansenger_sdk.user_messages")


async def send_user_message(
    config: LansengerConfig,
    app_token: str,
    user_token: str,
    receiver_id: str,
    msg_type: str,
    msg_data: dict,
    *,
    common: Optional[dict] = None,
    uuid: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> UserMessageResult:
    """Send a private chat message impersonating a user (4.6.3).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        user_token: User's userToken (REQUIRED — obtained via OAuth2).
        receiver_id: Single recipient's openId.
        msg_type: Message type (text, formatText, appCard, etc.).
        msg_data: Message body dict (type-specific content).
        common: Optional "common" sub-object in msgData.
        uuid: Optional deduplication UUID string.
        http_client: Optional httpx client.
    """
    if not user_token:
        return UserMessageResult(
            success=False, error="user_token is required for user private chat messages"
        )
    if not receiver_id:
        return UserMessageResult(success=False, error="receiver_id is required")
    if not msg_type:
        return UserMessageResult(success=False, error="msg_type is required")
    if not msg_data:
        return UserMessageResult(success=False, error="msg_data is required")

    path = API_ENDPOINTS["user_message"]["create"]
    url = f"{config.api_gateway_url}{path}?app_token={app_token}&user_token={user_token}"

    final_msg_data: Dict[str, Any] = dict(msg_data)
    if common:
        final_msg_data["common"] = common

    payload: Dict[str, Any] = {
        "receiverId": receiver_id,
        "msgType": msg_type,
        "msgData": final_msg_data,
    }
    if uuid:
        payload["uuid"] = uuid

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
        return UserMessageResult(success=False, error=f"HTTP error: {e}")
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return UserMessageResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return UserMessageResult(
            success=False, error=f"API error (errCode={err_code}): {msg}"
        )

    d = data.get("data", {})
    return UserMessageResult(
        success=True,
        message_id=d.get("msgId"),
        raw_response=data,
    )