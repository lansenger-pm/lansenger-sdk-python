"""Lansenger OAuth2 authorization helpers — user authentication flow.

Lansenger uses OAuth2 for user identity verification. When an org bot/app
needs to identify a Lansenger user (not the bot itself), it must:

1. Redirect the user to the Lansenger passport OAuth2 authorize page
2. User logs in on the Lansenger side
3. Lansenger redirects back to redirect_uri with code + state
4. App exchanges the code for a userToken + refreshToken via /v2/user_token/create

Key difference from appToken auth:
- appToken: authenticates the bot/app itself (for sending messages, etc.)
- OAuth2 userToken: authenticates a specific Lansenger user (for user-level ops)

Authentication hierarchy:
- appToken: bot's own credential → used for bot-level API calls
- userToken: user's credential → used for user-level API calls (contacts, etc.)
- refreshToken: long-lived (30 days) → used to refresh expired userToken
"""

from __future__ import annotations

import logging
import uuid
from urllib.parse import urlencode, quote
from typing import Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS, OAUTH2_SCOPE_BASIC_USER_INFO, OAUTH2_SCOPES
from .exceptions import LansengerAuthError, LansengerConfigError, LansengerNetworkError
from .models import UserTokenResult

logger = logging.getLogger("lansenger_sdk.oauth")


def build_authorize_url(
    config: LansengerConfig,
    redirect_uri: str,
    *,
    scope: str | list[str] | None = None,
    state: str | None = None,
) -> str:
    """Build the OAuth2 authorize URL for user authentication.

    The generated URL should be presented to the Lansenger user (e.g.
    redirect in browser, or send as a link card). After the user
    authorizes, Lansenger will redirect to redirect_uri with code + state.

    Args:
        config: LansengerConfig with passport_url set.
        redirect_uri: The URL Lansenger will redirect to after authorization.
            Must be URL-encoded and its domain must be in the app's trusted
            domain list.
        scope: OAuth2 scope(s). Can be a single scope string, a list, or
            None (defaults to "basic_userinfor"). Supported scopes:
            - "basic_userinfor": basic user information
        state: CSRF protection random string. If None, auto-generated UUID.

    Returns:
        The full authorize URL string.

    Raises:
        LansengerConfigError: if passport_url is not configured.
    """
    if not config.passport_url:
        raise LansengerConfigError(
            "passport_url is required for OAuth2 flows. "
            "Set LANSENGER_PASSPORT_URL env var or pass passport_url in config."
        )

    if state is None:
        state = uuid.uuid1().hex

    if scope is None:
        scope_str = OAUTH2_SCOPE_BASIC_USER_INFO
    elif isinstance(scope, list):
        scope_str = ",".join(scope)
    else:
        scope_str = scope

    params = {
        "appid": config.app_id,
        "response_type": "code",
        "scope": scope_str,
        "state": state,
        "redirect_uri": redirect_uri,
    }

    base_url = config.passport_url.rstrip("/") + API_ENDPOINTS["oauth2"]["authorize"]
    url = f"{base_url}?{urlencode(params, quote_via=quote)}"

    logger.debug("OAuth2 authorize URL built: %s", url[:80])
    return url


async def exchange_code_for_user_token(
    config: LansengerConfig,
    app_token: str,
    code: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
    redirect_uri: str = "",
) -> UserTokenResult:
    """Exchange an OAuth2 authorization code for a userToken + refreshToken.

    Uses GET /v2/user_token/create with appToken + code. The appToken
    authenticates the bot/app, while the code proves the user authorized.
    The returned userToken authenticates the specific Lansenger user.

    Args:
        config: LansengerConfig with api_gateway_url.
        app_token: The bot's appToken (obtained via /v1/apptoken/create).
        code: The authorization code from the OAuth2 authorize callback.
        http_client: Optional httpx.AsyncClient. If None, creates ephemeral.
        redirect_uri: Optional redirect_uri (same as used in authorize URL).

    Returns:
        UserTokenResult with userToken, refreshToken, staffId, etc.
    """
    if not code:
        return UserTokenResult(success=False, error="code is required")
    if not app_token:
        return UserTokenResult(success=False, error="app_token is required")

    url = (
        f"{config.api_gateway_url}"
        f"{API_ENDPOINTS['oauth2']['user_token_create']}"
        f"?app_token={app_token}"
        f"&grant_type=authorization_code"
        f"&code={code}"
    )
    if redirect_uri:
        url += f"&redirect_uri={quote(redirect_uri)}"

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
        return UserTokenResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return UserTokenResult(
            success=False,
            error=f"API error (errCode={err_code}): {msg}",
        )

    token_data = data.get("data", {})
    return UserTokenResult(
        success=True,
        user_token=token_data.get("userToken"),
        expires_in=token_data.get("expiresIn", 7200),
        refresh_token=token_data.get("refreshToken"),
        refresh_expires_in=token_data.get("refreshExpiresIn", 2592000),
        staff_id=token_data.get("staffId"),
        scope=token_data.get("scope"),
        state=token_data.get("state"),
        raw_response=data,
    )


async def refresh_user_token(
    config: LansengerConfig,
    app_token: str,
    refresh_token: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
    scope: str = "",
) -> UserTokenResult:
    """Refresh a userToken using a refreshToken.

    Uses GET /v1/refresh_token/create with appToken + refreshToken.
    The returned refreshToken replaces the old one (old becomes invalid).
    Total refreshToken validity does NOT extend — it's the remaining time
    from the original 30-day grant.

    If refreshToken has expired, must re-initiate OAuth2 authorize flow.

    Args:
        config: LansengerConfig with api_gateway_url.
        app_token: The bot's appToken.
        refresh_token: The refreshToken from a previous exchange_code or refresh.
        http_client: Optional httpx.AsyncClient. If None, creates ephemeral.
        scope: Optional scope (can only narrow, not widen, from original grant).

    Returns:
        UserTokenResult with new userToken, new refreshToken, staffId, etc.
        IMPORTANT: The new refreshToken replaces the old one. Always use
        the returned refreshToken for subsequent refreshes.
    """
    if not refresh_token:
        return UserTokenResult(success=False, error="refresh_token is required")
    if not app_token:
        return UserTokenResult(success=False, error="app_token is required")

    url = (
        f"{config.api_gateway_url}"
        f"{API_ENDPOINTS['oauth2']['refresh_token_create']}"
        f"?app_token={app_token}"
        f"&grant_type=refresh_token"
        f"&refresh_token={refresh_token}"
    )
    if scope:
        url += f"&scope={quote(scope)}"

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
        return UserTokenResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return UserTokenResult(
            success=False,
            error=f"API error (errCode={err_code}): {msg}",
        )

    token_data = data.get("data", {})
    return UserTokenResult(
        success=True,
        user_token=token_data.get("userToken"),
        expires_in=token_data.get("expiresIn", 7200),
        refresh_token=token_data.get("refreshToken"),
        refresh_expires_in=token_data.get("refreshExpiresIn", 2592000),
        staff_id=token_data.get("staffId"),
        scope=token_data.get("scope"),
        state=token_data.get("state"),
        raw_response=data,
    )


def parse_authorize_callback(
    query_string: str | dict,
) -> dict:
    """Parse the redirect callback from Lansenger OAuth2 authorize.

    After the user authorizes, Lansenger redirects to redirect_uri with
    code and state parameters. This helper parses them.

    Args:
        query_string: Either a dict (from parsed query params) or a raw
            query string like "code=XXX&state=YYY".

    Returns:
        Dict with:
        - code: The authorization code (5 min validity, one-time use)
        - state: The state value (should match what was sent)
        - error: Error code if authorization failed (optional)
        - error_description: Error description (optional)
    """
    if isinstance(query_string, dict):
        params = query_string
    else:
        params = {}
        for part in query_string.lstrip("?").split("&"):
            if "=" in part:
                key, value = part.split("=", 1)
                params[key] = value

    result = {
        "code": params.get("code", ""),
        "state": params.get("state", ""),
    }
    if "error" in params:
        result["error"] = params["error"]
    if "error_description" in params:
        result["error_description"] = params["error_description"]

    return result


def validate_callback_state(
    callback_state: str,
    expected_state: str,
) -> bool:
    """Validate that the callback state matches the expected state.

    Per OAuth2 spec, this prevents CSRF attacks.

    Args:
        callback_state: The state value received in the callback.
        expected_state: The state value that was sent in the authorize request.

    Returns:
        True if they match, False otherwise.
    """
    return callback_state == expected_state