"""Lansenger user information — fetch user profile via userToken.

Uses GET /v1/users/fetch with appToken + userToken to retrieve the
Lansenger user's basic information (name, org, department, phone, email, etc).

This API requires both tokens:
- appToken: authenticates the bot/app
- userToken: authenticates the specific user (obtained via OAuth2 flow)
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from .config import LansengerConfig
from .url_helpers import build_api_url
from .models import UserInfoResult

logger = logging.getLogger("lansenger_sdk.users")


async def fetch_user_info(
    config: LansengerConfig,
    app_token: str,
    user_token: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
) -> UserInfoResult:
    """Fetch a Lansenger user's basic information.

    Uses GET /v1/users/fetch with appToken + userToken.

    Args:
        config: LansengerConfig with api_gateway_url.
        app_token: The bot's appToken (obtained via /v1/apptoken/create).
        user_token: The user's userToken (obtained via OAuth2 code exchange).
        http_client: Optional httpx.AsyncClient. If None, creates ephemeral.

    Returns:
        UserInfoResult with staffId, name, org, department, email, phone, etc.
    """
    if not user_token:
        return UserInfoResult(success=False, error="user_token is required")
    if not app_token:
        return UserInfoResult(success=False, error="app_token is required")

    url = build_api_url(config, "users", "fetch", app_token, user_token=user_token)

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)

    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return UserInfoResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return UserInfoResult(
            success=False,
            error=f"API error (errCode={err_code}): {msg}",
        )

    user_data = data.get("data", {})
    return UserInfoResult(
        success=True,
        staff_id=user_data.get("staffId"),
        name=user_data.get("name"),
        org_id=user_data.get("orgId"),
        org_name=user_data.get("orgid") or user_data.get("orgName") or user_data.get("orgname"),
        avatar_id=user_data.get("avatarId"),
        avatar_url=user_data.get("avatarUrl"),
        mobile_phone=user_data.get("mobilePhone"),
        email=user_data.get("email"),
        employee_number=user_data.get("employeeNumber"),
        login_name=user_data.get("loginName"),
        external_id=user_data.get("externalId"),
        department=user_data.get("department"),
        raw_response=data,
    )