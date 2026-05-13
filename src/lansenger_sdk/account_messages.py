"""Lansenger account message API — send messages via public account channel (4.6.1).

Messages sent via this channel appear as if from the application's Public
Account (公号). The sender identity is determined by accountId (which public
account) or entryId (which app entry's associated public account).

Endpoint: POST /v1/messages/create?app_token=TOKEN&user_token=TOKEN

Supported msgType: text, oacard, linkCard, appCard, verifyCard

Key fields:
- userIdList / departmentIdList / tagUnitList: recipient targeting
- accountId: which public account to send as
- entryId: app entry ID (alternative to accountId)
- attach: extra data for blueprint app context
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS
from .models import AccountMessageResult

logger = logging.getLogger("lansenger_sdk.account_messages")


async def send_account_message(
    config: LansengerConfig,
    app_token: str,
    msg_type: str,
    msg_data: dict,
    *,
    chat_ids: Optional[List[str]] = None,
    department_ids: Optional[List[str]] = None,
    account_id: str = "",
    entry_id: str = "",
    attach: str = "",
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> AccountMessageResult:
    """Send a message via the public account channel (4.6.1).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        msg_type: Message type — text, oacard, linkCard, appCard, verifyCard.
        msg_data: Message body dict (msgData field).
        chat_ids: Recipient user openId list.
        department_ids: Recipient department openId list.
        account_id: Public account ID to send as.
        entry_id: App entry ID (selects associated public account).
        attach: Extra data string for blueprint app context.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    valid_msg_types = ("text", "oacard", "linkCard", "appCard", "verifyCard")
    if msg_type not in valid_msg_types:
        return AccountMessageResult(
            success=False, error=f"msg_type must be one of: {', '.join(valid_msg_types)}"
        )
    if not chat_ids and not department_ids:
        return AccountMessageResult(
            success=False, error="at least one of chat_ids or department_ids is required"
        )
    if not msg_data:
        return AccountMessageResult(success=False, error="msg_data is required")

    path = API_ENDPOINTS["account_message"]["create"]
    url = f"{config.api_gateway_url}{path}?app_token={app_token}"
    if user_token:
        url += f"&user_token={user_token}"

    payload: Dict[str, Any] = {
        "userIdList": chat_ids or [],
        "departmentIdList": department_ids or [],
        "msgType": msg_type,
        "msgData": msg_data,
    }
    if account_id:
        payload["accountId"] = account_id
    if entry_id:
        payload["entryId"] = entry_id
    if attach:
        payload["attach"] = attach

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
        return AccountMessageResult(success=False, error=f"HTTP error: {e}")
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return AccountMessageResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return AccountMessageResult(
            success=False, error=f"API error (errCode={err_code}): {msg}"
        )

    d = data.get("data", {})
    return AccountMessageResult(
        success=True,
        message_id=d.get("msgId"),
        invalid_staff=d.get("invalidStaff"),
        invalid_department=d.get("invalidDepartment"),
        raw_response=data,
    )