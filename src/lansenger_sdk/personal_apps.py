"""Lansenger personal apps API — manage personal apps/bots (4.38).

Endpoints:
- 4.38.1 POST /v1/personal/apps/create        — create personal app
- 4.38.2 POST /v1/personal/apps/:app_id/update — update personal app
- 4.38.3 GET  /v1/personal/apps/:app_id/fetch  — query personal app
- 4.38.4 POST /v1/personal/apps/:app_id/delete — delete personal app
- 4.38.5 GET  /v1/personal/apps/list/fetch     — list personal apps

All endpoints require both app_token and user_token.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_get, do_post, parse_api_response
from .config import LansengerConfig
from .models import PersonalAppCreateResult, PersonalAppInfoResult, PersonalAppListResult
from .url_helpers import build_api_url


async def create_personal_app(
    config: LansengerConfig,
    app_token: str,
    *,
    user_token: str,
    name: str = "",
    avatar_id: str = "",
    description: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalAppCreateResult:
    """Create a personal app (4.38.1).

    Args:
        user_token: User token from OAuth2 (required).
        name: App name.
        avatar_id: Avatar media ID from upload.
        description: App description.
    """
    if not user_token:
        return PersonalAppCreateResult(success=False, error="user_token is required")

    url = build_api_url(config, "personal_apps", "create", app_token, user_token=user_token)

    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if avatar_id:
        body["avatarId"] = avatar_id
    if description:
        body["description"] = description

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalAppCreateResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return PersonalAppCreateResult(success=False, error=api_err)

    d = data.get("data", {})
    return PersonalAppCreateResult(
        success=True,
        app_id=d.get("id"),
        secret=d.get("secret"),
        apigw_addr=d.get("apigwAddr"),
        passport_addr=d.get("passportAddr"),
        raw_response=data,
    )


async def update_personal_app(
    config: LansengerConfig,
    app_token: str,
    app_id: str,
    *,
    user_token: str,
    name: str,
    avatar_id: str = "",
    description: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> PersonalAppInfoResult:
    """Update a personal app (4.38.2).

    Args:
        app_id: App ID (required).
        user_token: User token from OAuth2 (required).
        name: App name (required, max 10 characters).
        avatar_id: Avatar media ID from upload.
        description: App description (max 20 characters).
    """
    if not app_id:
        return PersonalAppInfoResult(success=False, error="app_id is required")
    if not user_token:
        return PersonalAppInfoResult(success=False, error="user_token is required")
    if not name:
        return PersonalAppInfoResult(success=False, error="name is required")

    url = build_api_url(
        config, "personal_apps", "update", app_token,
        user_token=user_token, app_id=app_id,
    )

    body: dict[str, Any] = {"name": name}
    if avatar_id:
        body["avatarId"] = avatar_id
    if description:
        body["description"] = description

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return PersonalAppInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return PersonalAppInfoResult(success=False, error=api_err)

    return PersonalAppInfoResult(success=True, app_id=app_id, raw_response=data)


async def fetch_personal_app(
    config: LansengerConfig,
    app_token: str,
    app_id: str,
    *,
    user_token: str,
    http_client: httpx.AsyncClient | None = None,
) -> PersonalAppInfoResult:
    """Fetch personal app info (4.38.3).

    Args:
        app_id: App ID (required).
        user_token: User token from OAuth2 (required).
    """
    if not app_id:
        return PersonalAppInfoResult(success=False, error="app_id is required")
    if not user_token:
        return PersonalAppInfoResult(success=False, error="user_token is required")

    url = build_api_url(
        config, "personal_apps", "fetch", app_token,
        user_token=user_token, app_id=app_id,
    )

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return PersonalAppInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return PersonalAppInfoResult(success=False, error=api_err)

    d = data.get("data", {})
    return PersonalAppInfoResult(
        success=True,
        app_id=app_id,
        name=d.get("name"),
        avatar_id=d.get("avatarId"),
        description=d.get("description"),
        apigw_addr=d.get("apigwAddr"),
        passport_addr=d.get("passportAddr"),
        raw_response=data,
    )


async def delete_personal_app(
    config: LansengerConfig,
    app_token: str,
    app_id: str,
    *,
    user_token: str,
    http_client: httpx.AsyncClient | None = None,
) -> PersonalAppInfoResult:
    """Delete a personal app (4.38.4).

    Args:
        app_id: App ID (required).
        user_token: User token from OAuth2 (required).
    """
    if not app_id:
        return PersonalAppInfoResult(success=False, error="app_id is required")
    if not user_token:
        return PersonalAppInfoResult(success=False, error="user_token is required")

    url = build_api_url(
        config, "personal_apps", "delete", app_token,
        user_token=user_token, app_id=app_id,
    )

    data, http_err = await do_post(config, url, {}, http_client)
    if http_err:
        return PersonalAppInfoResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return PersonalAppInfoResult(success=False, error=api_err)

    return PersonalAppInfoResult(success=True, app_id=app_id, raw_response=data)


async def fetch_personal_app_list(
    config: LansengerConfig,
    app_token: str,
    *,
    user_token: str,
    http_client: httpx.AsyncClient | None = None,
) -> PersonalAppListResult:
    """Fetch personal app list (4.38.5).

    Args:
        user_token: User token from OAuth2 (required).
    """
    if not user_token:
        return PersonalAppListResult(success=False, error="user_token is required")

    url = build_api_url(
        config, "personal_apps", "list_fetch", app_token,
        user_token=user_token,
    )

    data, http_err = await do_get(config, url, http_client)
    if http_err:
        return PersonalAppListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return PersonalAppListResult(success=False, error=api_err)

    d = data.get("data", {})
    app_list = d.get("appList")
    app_list = app_list if isinstance(app_list, list) else None

    return PersonalAppListResult(
        success=True,
        app_list=app_list,
        raw_response=data,
    )
