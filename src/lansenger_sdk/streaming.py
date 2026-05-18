"""Lansenger streaming (SSE) message API — stream message creation and retrieval.

These APIs are used for AI-agent streaming message delivery. They require
appToken for authentication.

Endpoints:
1. POST /v1/sse/msg/create — create a streaming message
2. POST /v1/sse/msg/fetch  — fetch a streaming message status
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from .config import LansengerConfig
from .url_helpers import build_api_url
from .models import StreamMessageResult

logger = logging.getLogger("lansenger_sdk.streaming")


def _parse_api_response(data: dict) -> tuple[bool, Optional[str]]:
    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return False, f"API error (errCode={err_code}): {msg}"
    return True, None


async def _do_post(
    config: LansengerConfig,
    url: str,
    body: Dict[str, Any],
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=body)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return None, f"HTTP error: {e}"
    except Exception as e:
        return None, f"Request error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None


async def create_stream_message(
    config: LansengerConfig,
    app_token: str,
    receiver_id: str,
    receiver_type: str,
    stream_id: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
) -> StreamMessageResult:
    """Create a streaming (SSE) message for an AI-agent conversation.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        receiver_id: Target staff or group openId (required).
        receiver_type: "staff" or "group" (required).
        stream_id: Unique stream identifier (required).
        http_client: Optional httpx client.
    """
    if not receiver_id:
        return StreamMessageResult(success=False, error="receiver_id is required")
    if not receiver_type:
        return StreamMessageResult(success=False, error="receiver_type is required")
    if not stream_id:
        return StreamMessageResult(success=False, error="stream_id is required")

    url = build_api_url(config, "sse", "msg_create", app_token)

    body: Dict[str, Any] = {
        "receiverId": receiver_id,
        "receiverType": receiver_type,
        "streamId": stream_id,
    }

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return StreamMessageResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StreamMessageResult(success=False, error=api_err)

    d = data.get("data", {})
    return StreamMessageResult(
        success=True,
        message_id=d.get("msgId"),
        raw_response=data,
    )


async def fetch_stream_message(
    config: LansengerConfig,
    app_token: str,
    msg_id: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
) -> StreamMessageResult:
    """Fetch a streaming (SSE) message by its message ID.

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        msg_id: Message openId (required).
        http_client: Optional httpx client.
    """
    if not msg_id:
        return StreamMessageResult(success=False, error="msg_id is required")

    url = build_api_url(config, "sse", "msg_fetch", app_token)

    body: Dict[str, Any] = {
        "msgId": msg_id,
    }

    data, http_err = await _do_post(config, url, body, http_client)
    if http_err:
        return StreamMessageResult(success=False, error=http_err)

    ok, api_err = _parse_api_response(data)
    if not ok:
        return StreamMessageResult(success=False, error=api_err)

    d = data.get("data", {})
    return StreamMessageResult(
        success=True,
        message_id=d.get("msgId"),
        raw_response=data,
    )