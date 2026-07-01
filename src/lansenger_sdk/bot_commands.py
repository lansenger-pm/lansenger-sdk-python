"""Lansenger bot commands API — manage bot slash commands (4.37).

Endpoints:
- 4.37.1 POST /v1/bot/commands/create — create bot commands
- 4.37.2 POST /v1/bot/commands/fetch  — query bot commands
- 4.37.3 POST /v1/bot/commands/delete — delete bot commands

All endpoints require app_token.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .config import LansengerConfig
from .models import BotCommandResult, BotCommandQueryResult
from .url_helpers import build_api_url
from .api_utils import do_post, parse_api_response


async def create_bot_commands(
    config: LansengerConfig,
    app_token: str,
    scope_type: int,
    commands: List[Dict[str, Any]],
    *,
    chat_id: str = "",
    chat_type: str = "",
    staff_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> BotCommandResult:
    """Create bot commands (4.37.1).

    Args:
        scope_type: 1=single member of single group, 2=admin of single group,
            3=single chat, 4=all group admins, 5=all groups, 6=all private chats,
            7=global default.
        commands: List of command objects, each with command, description, icon,
            and optional i18nDescription.
        chat_id: Group/staff openId (required for scope 1/2/3).
        chat_type: "group" or "staff" (required for scope 1/2/3).
        staff_id: Staff openId (required for scope 1).
    """
    if scope_type not in range(1, 8):
        return BotCommandResult(success=False, error="scope_type must be 1-7")
    if not commands:
        return BotCommandResult(success=False, error="commands is required")

    url = build_api_url(config, "bot_commands", "create", app_token)

    body: Dict[str, Any] = {
        "scopeType": scope_type,
        "commands": commands,
    }
    if chat_id:
        body["chatId"] = chat_id
    if chat_type:
        body["chatType"] = chat_type
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BotCommandResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BotCommandResult(success=False, error=api_err)

    return BotCommandResult(success=True, raw_response=data)


async def fetch_bot_commands(
    config: LansengerConfig,
    app_token: str,
    scope_type: int,
    *,
    chat_id: str = "",
    chat_type: str = "",
    staff_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> BotCommandQueryResult:
    """Query bot commands (4.37.2).

    Args:
        scope_type: Command scope (1-7, same as create).
        chat_id: Group/staff openId (required for scope 1/2/3).
        chat_type: "group" or "staff" (required for scope 1/2/3).
        staff_id: Staff openId (required for scope 1).
    """
    if scope_type not in range(1, 8):
        return BotCommandQueryResult(success=False, error="scope_type must be 1-7")

    url = build_api_url(config, "bot_commands", "fetch", app_token)

    body: Dict[str, Any] = {"scopeType": scope_type}
    if chat_id:
        body["chatId"] = chat_id
    if chat_type:
        body["chatType"] = chat_type
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BotCommandQueryResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BotCommandQueryResult(success=False, error=api_err)

    d = data.get("data", {})
    commands = d.get("commands")
    if isinstance(commands, list):
        commands = commands
    else:
        commands = None

    return BotCommandQueryResult(
        success=True,
        scope_type=d.get("scopeType"),
        chat_id=d.get("chatId"),
        chat_type=d.get("chatType"),
        staff_id=d.get("staffId"),
        commands=commands,
        raw_response=data,
    )


async def delete_bot_commands(
    config: LansengerConfig,
    app_token: str,
    scope_type: int,
    *,
    chat_id: str = "",
    chat_type: str = "",
    staff_id: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> BotCommandResult:
    """Delete bot commands (4.37.3).

    Deletes all commands for the given scope.

    Args:
        scope_type: Command scope (1-7, same as create).
        chat_id: Group/staff openId (required for scope 1/2/3).
        chat_type: "group" or "staff" (required for scope 1/2/3).
        staff_id: Staff openId (required for scope 1).
    """
    if scope_type not in range(1, 8):
        return BotCommandResult(success=False, error="scope_type must be 1-7")

    url = build_api_url(config, "bot_commands", "delete", app_token)

    body: Dict[str, Any] = {"scopeType": scope_type}
    if chat_id:
        body["chatId"] = chat_id
    if chat_type:
        body["chatType"] = chat_type
    if staff_id:
        body["staffId"] = staff_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return BotCommandResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return BotCommandResult(success=False, error=api_err)

    return BotCommandResult(success=True, raw_response=data)
