"""4.6.17 Emoji reply management (创建表情回复消息)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import LansengerConfig
from .constants import EMOJI_IDS, REPLY_TYPE_CANCEL, REPLY_TYPE_REPLY
from .models import ReplyMessageResult
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.message_replies")


def validate_reply_request(
    msg_id: str,
    emoji_id: str,
    reply_type: int,
) -> ReplyMessageResult | None:
    """Return a failed result when the request is invalid, else None.

    Kept separate so callers (the client's dual-surface wrappers) can reject
    bad arguments before spending a token request on them.
    """
    if not msg_id:
        return ReplyMessageResult(success=False, error="msg_id is required")

    if reply_type not in (REPLY_TYPE_REPLY, REPLY_TYPE_CANCEL):
        return ReplyMessageResult(
            success=False,
            error=f"invalid reply_type: {reply_type!r} (1=reply, 2=cancel)",
            reply_type=reply_type,
            msg_id=msg_id,
        )

    if emoji_id not in EMOJI_IDS:
        return ReplyMessageResult(
            success=False,
            error=(
                f"invalid emoji_id: {emoji_id!r}; one of {', '.join(EMOJI_IDS)} "
                "(required for both reply and cancel: cancel needs to know which reply to drop)"
            ),
            reply_type=reply_type,
            msg_id=msg_id,
            emoji_id=emoji_id,
        )

    return None


async def reply_message(
    config: LansengerConfig,
    app_token: str,
    msg_id: str,
    *,
    emoji_id: str,
    reply_type: int = REPLY_TYPE_REPLY,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> ReplyMessageResult:
    """Create or cancel an emoji reply on a message (4.6.17).

    Args:
        config: SDK config (api_gateway_url required).
        app_token: Bot appToken.
        msg_id: ID of the message being replied to (msgId).
        emoji_id: Emoji to attach — TYPE_THUMB (点赞), TYPE_OK (收到),
            TYPE_ADD_ONE (+1), TYPE_FIREWORK (烟火), TYPE_LOVE (爱心),
            TYPE_DOUBT (问号). Required in both modes: with reply_type=2 the
            platform needs it to know which emoji reply to cancel.
        reply_type: 1=reply (default), 2=cancel the existing reply.
        user_token: Optional userToken (the endpoint accepts one).
        http_client: Optional injected client (tests).

    Returns:
        ReplyMessageResult — failures are returned, never raised.
    """
    invalid = validate_reply_request(msg_id, emoji_id, reply_type)
    if invalid is not None:
        return invalid

    url = build_api_url(
        config, "message", "reply_create", app_token, user_token=user_token
    )
    payload: dict[str, Any] = {
        "replyType": reply_type,
        "msgId": msg_id,
        "emojiId": emoji_id,
    }

    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(timeout=30.0)
    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return ReplyMessageResult(
            success=False,
            error=f"HTTP error: {e}",
            reply_type=reply_type,
            msg_id=msg_id,
            emoji_id=emoji_id,
        )
    finally:
        if owns_client:
            await client.aclose()

    logger.debug("reply_create HTTP %s", response.status_code)

    result = ReplyMessageResult(
        success=True,
        reply_type=reply_type,
        msg_id=msg_id,
        emoji_id=emoji_id,
        raw_response=data if isinstance(data, dict) else None,
    )

    if isinstance(data, dict):
        err_code = data.get("errCode", 0)
        if err_code not in (0, None):
            result.success = False
            result.error = f"API error (errCode={err_code}): {data.get('errMsg', '')}"

    return result
