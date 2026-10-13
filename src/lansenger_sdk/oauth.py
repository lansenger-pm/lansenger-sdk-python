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

import json
import logging
import re
import uuid
from urllib.parse import quote, urlencode

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS, OAUTH2_SCOPE_BASIC_USER_INFO
from .exceptions import LansengerConfigError
from .models import DeviceAuthorizationResult, DevicePollResult, UserTokenResult
from .url_helpers import build_api_url

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

    if not redirect_uri:
        redirect_uri = config.redirect_uri
    if not redirect_uri:
        raise LansengerConfigError(
            "redirect_uri is required for OAuth2 authorize flow. "
            "Set LANSENGER_REDIRECT_URI env var, pass redirect_uri to config, "
            "or pass it directly to build_authorize_url()."
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
    http_client: httpx.AsyncClient | None = None,
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

    url = build_api_url(config, "oauth2", "user_token_create", app_token)
    url += f"&grant_type=authorization_code&code={quote(code)}"
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
    http_client: httpx.AsyncClient | None = None,
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

    url = build_api_url(config, "oauth2", "refresh_token_create", app_token)
    url += f"&grant_type=refresh_token&refresh_token={quote(refresh_token)}"
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


# --- OAuth2 Device Authorization Grant (新版开平；旧版无此路由，见 unsupported 分类) ---

DEVICE_SOURCE_WHITELIST = ("AutoClaw", "CLI", "OpenClaw", "MCP")
_DEVICE_UNSUPPORTED = "deviceflow_unsupported"
_APP_ID_PATTERN = re.compile(r"\d+-\d+")
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
# Known OAuth2-service error codes (interface doc); 200-with-error-envelope or
# unknown codes fall through to the conservative unsupported bucket (§4.1 row 6).
_DEVICE_KNOWN_CODES = {9000, 9003, 9004, 9100, 9101, 10001, 10002}


def _device_api_error_status(status: int) -> bool:
    """4xx/5xx other than 404 (legacy open platform): a JSON `error` body there means the route answered."""
    return 400 <= status < 600 and status != 404


def _device_base_url(config: LansengerConfig) -> str:
    """Device endpoints live on the passport base (verified on stage: T1)."""
    if not config.passport_url:
        raise LansengerConfigError(
            "passport_url is required for device flow. "
            "Set LANSENGER_PASSPORT_URL env var or pass passport_url in config."
        )
    return config.passport_url.rstrip("/")


def _device_body_summary(data: object) -> str:
    if isinstance(data, dict):
        return json.dumps(data, ensure_ascii=False)[:200]
    return f"non-JSON body ({len(str(data))} bytes)"


def _unsupported_auth(status: int, data: object, reason: str) -> DeviceAuthorizationResult:
    return DeviceAuthorizationResult(
        success=False,
        error=f"deviceflow unavailable (HTTP {status}): {reason}",
        error_type=_DEVICE_UNSUPPORTED,
        raw_response=data if isinstance(data, dict) else None,
    )


def _classify_authorization(status: int, data: object) -> DeviceAuthorizationResult:
    # Priority order mirrors evaluation.md §4.1 rows 0-6.
    if status == 200 and isinstance(data, dict) and data.get("deviceCode") and "errCode" not in data:
        return DeviceAuthorizationResult(
            success=True,
            device_code=data["deviceCode"],
            user_code=data.get("userCode"),
            verification_uri_complete=data.get("verificationUriComplete"),
            interval=data.get("interval", 5),
            expires_in=data.get("expiresIn", 600),
            expires_at=data.get("expiresAt"),
            open_api_domain=data.get("openApiDomain"),
            raw_response=data,
        )
    if isinstance(data, dict) and "errCode" in data:  # row 1: gateway path error (T5a/P3)
        return _unsupported_auth(
            status,
            data,
            f"gateway path error (errCode={data.get('errCode')}): {data.get('errMsg', '')}",
        )
    if status == 404:  # row 2: legacy open platform (beta11 P1/T5b)
        return _unsupported_auth(status, data, "route not found (404) — legacy open platform without deviceflow")
    if status in _REDIRECT_STATUSES:  # row 3
        return _unsupported_auth(status, data, "redirected (non-JSON) — check passport_url / path.prefix")
    if _device_api_error_status(status) and isinstance(data, dict) and "error" in data:  # row 5
        err = data["error"]
        if isinstance(err, dict) and err.get("code") in _DEVICE_KNOWN_CODES:
            return DeviceAuthorizationResult(
                success=False,
                error=f"API error (code={err.get('code')}): {err.get('message', '')}",
                raw_response=data,
            )
        if not isinstance(err, dict):
            # RFC 6749 §5.2 error is a plain string: the route answered, so this is an API error, not a missing route
            return DeviceAuthorizationResult(
                success=False,
                error=f"API error (HTTP {status}): {_device_body_summary(data)}",
                raw_response=data,
            )
    # rows 4 (200+HTML) & 6 (unknown shapes): conservative unsupported bucket
    return _unsupported_auth(status, data, f"unexpected response: {_device_body_summary(data)}")


def _classify_poll(status: int, data: object) -> DevicePollResult:
    if status == 200 and isinstance(data, dict) and "state" in data and "errCode" not in data:
        state = data["state"]
        if state == "authorization_pending":
            return DevicePollResult(success=True, state=state, raw_response=data)
        if state == "access_approved":
            return DevicePollResult(success=True, state=state, oauth2_code=data.get("oauth2Code"), raw_response=data)
        if state == "access_denied":
            return DevicePollResult(success=False, state=state, error="user denied authorization (access_denied)", raw_response=data)
        if state == "expired_token":
            return DevicePollResult(
                success=False,
                state=state,
                error="authorization expired (expired_token) — request a new device code",
                raw_response=data,
            )
        return DevicePollResult(success=False, error=f"unknown state: {state}", raw_response=data)
    if status == 404:
        return DevicePollResult(
            success=False,
            error="deviceflow unavailable (HTTP 404): route not found",
            error_type=_DEVICE_UNSUPPORTED,
        )
    if isinstance(data, dict) and "errCode" in data:
        return DevicePollResult(
            success=False,
            error=f"deviceflow unavailable: gateway path error (errCode={data.get('errCode')})",
            error_type=_DEVICE_UNSUPPORTED,
        )
    if status in _REDIRECT_STATUSES:
        return DevicePollResult(
            success=False,
            error="deviceflow unavailable: redirected (non-JSON) — check passport_url / path.prefix",
            error_type=_DEVICE_UNSUPPORTED,
        )
    if _device_api_error_status(status) and isinstance(data, dict) and "error" in data:
        err = data["error"]
        if isinstance(err, dict) and err.get("code") in _DEVICE_KNOWN_CODES:
            return DevicePollResult(success=False, error=f"API error (code={err.get('code')}): {err.get('message', '')}", raw_response=data)
        if not isinstance(err, dict):
            # RFC 6749 §5.2 error is a plain string: the route answered, so this is an API error, not a missing route
            return DevicePollResult(success=False, error=f"API error (HTTP {status}): {_device_body_summary(data)}", raw_response=data)
    return DevicePollResult(
        success=False,
        error=f"deviceflow unavailable (HTTP {status}): {_device_body_summary(data)}",
        error_type=_DEVICE_UNSUPPORTED,
    )


async def request_device_authorization(
    config: LansengerConfig,
    *,
    client_id: str = "",
    app_id: str | None = None,
    source: str = "CLI",
    version: str | None = None,
    scope: str = OAUTH2_SCOPE_BASIC_USER_INFO,
    http_client: httpx.AsyncClient | None = None,
) -> DeviceAuthorizationResult:
    """Request a device code (OAuth2 device flow, step 1).

    POST {passport_url}/oauth2/device_authorization. The route lives on the
    passport base; servers without the route are classified as
    ``error_type="deviceflow_unsupported"`` (legacy open platforms).

    Args:
        config: LansengerConfig with passport_url set.
        client_id: OAuth2 client id; defaults to app_id (accepted by server).
        app_id: App id in ``数字-数字`` form; defaults to config.app_id.
        source: Client source, one of DEVICE_SOURCE_WHITELIST (default "CLI").
        version: Client version; defaults to this SDK's __version__.
        scope: Fixed to basic_userinfor by the server; kept as a parameter.
        http_client: Optional httpx.AsyncClient; ephemeral if None.

    Returns:
        DeviceAuthorizationResult with device_code/user_code/
        verification_uri_complete/interval/expires_in/expires_at,
        or success=False with error_type="deviceflow_unsupported".
    """
    resolved_app_id = app_id or config.app_id
    if not resolved_app_id:
        return DeviceAuthorizationResult(success=False, error="app_id is required")
    if not _APP_ID_PATTERN.fullmatch(resolved_app_id):
        return DeviceAuthorizationResult(success=False, error=f"invalid appId format: expect 数字-数字, got length {len(resolved_app_id)}")
    if source not in DEVICE_SOURCE_WHITELIST:
        return DeviceAuthorizationResult(success=False, error=f"invalid source: {source!r} not in {DEVICE_SOURCE_WHITELIST}")
    if version is None:
        from . import __version__

        version = __version__
    if not version:
        return DeviceAuthorizationResult(success=False, error="version is required")

    url = _device_base_url(config) + API_ENDPOINTS["oauth2"]["device_authorization"]
    payload = {
        "clientId": client_id or resolved_app_id,
        "responseType": "device_code",
        "scope": scope,
        "appId": resolved_app_id,
        "from": source,
        "version": version,
    }

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=payload)
        try:
            data = response.json()
        except ValueError:
            data = None
        logger.debug("device_authorization HTTP %s", response.status_code)
    except httpx.HTTPError as e:
        return DeviceAuthorizationResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    return _classify_authorization(response.status_code, data)


async def poll_device_token(
    config: LansengerConfig,
    device_code: str,
    *,
    client_id: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> DevicePollResult:
    """Poll once for the device authorization outcome (device flow, step 2).

    POST {passport_url}/oauth2/device_token. Callers poll every
    ``interval`` seconds (from step 1) until state becomes
    ``access_approved`` (take oauth2_code) or a terminal state.

    Returns:
        DevicePollResult: success=True for pending/approved (oauth2_code on
        approved); success=False for denied/expired/errors. HTTP-level
        missing-route shapes carry error_type="deviceflow_unsupported".
    """
    if not device_code:
        return DevicePollResult(success=False, error="device_code is required")
    client_id = client_id or config.app_id
    if not client_id:
        return DevicePollResult(success=False, error="client_id is required")

    url = _device_base_url(config) + API_ENDPOINTS["oauth2"]["device_token"]
    payload = {"deviceCode": device_code, "clientId": client_id}

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.post(url, json=payload)
        try:
            data = response.json()
        except ValueError:
            data = None
        logger.debug("device_token HTTP %s", response.status_code)
    except httpx.HTTPError as e:
        return DevicePollResult(success=False, error=f"HTTP error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    return _classify_poll(response.status_code, data)
