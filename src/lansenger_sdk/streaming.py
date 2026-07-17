"""Lansenger streaming (SSE) message API — stream message creation and retrieval.

These APIs are used for AI-agent streaming message delivery. They require
appToken for authentication.

Endpoints:
1. POST /v1/sse/msg/create — create a streaming message
2. POST /v1/sse/msg/fetch  — fetch a streaming message status
"""

from __future__ import annotations

from typing import Any

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import StreamMessageResult
from .url_helpers import build_api_url


async def create_stream_message(
    config: LansengerConfig,
    app_token: str,
    receiver_id: str,
    receiver_type: str,
    stream_id: str,
    *,
    http_client: httpx.AsyncClient | None = None,
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

    body: dict[str, Any] = {
        "receiverId": receiver_id,
        "receiverType": receiver_type,
        "streamId": stream_id,
    }

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return StreamMessageResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
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
    http_client: httpx.AsyncClient | None = None,
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

    body: dict[str, Any] = {
        "msgId": msg_id,
    }

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return StreamMessageResult(success=False, error=http_err)

    ok, api_err = parse_api_response(data)
    if not ok:
        return StreamMessageResult(success=False, error=api_err)

    d = data.get("data", {})
    return StreamMessageResult(
        success=True,
        message_id=d.get("msgId"),
        raw_response=data,
    )
