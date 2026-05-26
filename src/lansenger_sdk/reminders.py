"""Lansenger reminder API — send urgent reminders for previously sent messages (4.6.14).

Endpoint: POST /v1/messages/reminder/create?app_token=TOKEN

reminderTypes values:
  0 = NONE (no reminder)
  1 = Pop-up message reminder
  2 = SMS reminder
  3 = Phone call reminder

userIdList must be recipients of the original message. Max 100 people.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .models import SendMessageResult
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.reminders")

REMINDER_TYPE_NONE = 0
REMINDER_TYPE_POPUP = 1
REMINDER_TYPE_SMS = 2
REMINDER_TYPE_PHONE = 3


async def send_reminder(
    config: LansengerConfig,
    app_token: str,
    msg_id: str,
    reminder_types: List[int],
    user_id_list: List[str],
    *,
    http_client: Optional[httpx.AsyncClient] = None,
) -> SendMessageResult:
    """Send an urgent reminder for a previously sent message (4.6.14).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        msg_id: The message ID to remind about.
        reminder_types: List of reminder type ints (1=popup, 2=SMS, 3=phone).
        user_id_list: List of staff openIds to remind (max 100).
        http_client: Optional httpx client.
    """
    if not msg_id:
        return SendMessageResult(success=False, error="msg_id is required")
    if not reminder_types:
        return SendMessageResult(success=False, error="reminder_types is required")
    if not user_id_list:
        return SendMessageResult(success=False, error="user_id_list is required")

    url = build_api_url(config, "message", "reminder_create", app_token)

    body: Dict[str, Any] = {
        "msgId": msg_id,
        "reminderTypes": reminder_types,
        "userIdList": user_id_list,
    }

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
            success=False,
            error=f"API error (errCode={err_code}): {msg}",
            operation="send_reminder",
            retryable=True,
        )

    return SendMessageResult(
        success=True,
        operation="send_reminder",
        raw_response=data,
    )