"""Lansenger SDK token management — get/refresh app access token and user token with file persistence."""

from __future__ import annotations

import logging
import time
from urllib.parse import quote
from typing import Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS
from .exceptions import LansengerAuthError, LansengerNetworkError
from .models import UserTokenResult
from .persistence import CredentialStore
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.auth")

_TOKEN_REFRESH_MARGIN = 300  # Refresh 5 minutes before expiry
_USER_TOKEN_REFRESH_MARGIN = 300


class TokenManager:
    """Manages Lansenger app access token lifecycle.

    The appToken is obtained via GET /v1/apptoken/create with
    app_id + app_secret. It has a 2-hour expiry (7200s) and
    is refreshed 5 minutes before expiry automatically.

    If a CredentialStore is provided, tokens are persisted to disk
    so they survive process restarts.
    """

    def __init__(
        self,
        config: LansengerConfig,
        http_client: httpx.AsyncClient,
        store: Optional[CredentialStore] = None,
    ):
        self._config = config
        self._http_client = http_client
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._store = store

        if self._store:
            cached = self._store.load_app_token()
            if cached:
                self._token = cached
                state = self._store.load()
                self._token_expiry = state.get("app_token_expiry", 0)
                logger.debug("Restored cached appToken from %s", self._store.path)

    async def get_token(self) -> str:
        """Get a valid app access token, refreshing if expired.

        Raises LansengerAuthError if token cannot be obtained.
        """
        if self._token and time.time() < self._token_expiry:
            return self._token

        url = f"{self._config.api_gateway_url}{API_ENDPOINTS['app_token']['create']}"
        params = {
            "grant_type": "client_credential",
            "appid": self._config.app_id,
            "secret": self._config.app_secret,
        }

        try:
            response = await self._http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise LansengerNetworkError(f"Token request failed: {e}") from e

        err_code = data.get("errCode", -1)
        if err_code != 0:
            msg = data.get("errMsg", "Unknown token error")
            raise LansengerAuthError(
                f"Token error (errCode={err_code}): {msg}",
                err_code=err_code,
            )

        token_data = data.get("data", {})
        self._token = token_data.get("appToken")
        expires_in = token_data.get("expiresIn", 7200)
        self._token_expiry = time.time() + expires_in - _TOKEN_REFRESH_MARGIN

        if not self._token:
            raise LansengerAuthError("Token response missing appToken field")

        logger.debug("Got new Lansenger appToken (expires_in=%ds)", expires_in)

        if self._store:
            self._store.save_app_token(self._token, expires_in=expires_in, margin=_TOKEN_REFRESH_MARGIN)

        return self._token

    def invalidate(self) -> None:
        """Force token refresh on next get_token() call."""
        self._token = None
        self._token_expiry = 0


class UserTokenManager:
    """Manages Lansenger userToken lifecycle with auto-refresh.

    userToken expires in 2 hours. refreshToken is long-lived (30 days)
    and single-use (rotated on each refresh). This manager:
    - Proactively refreshes userToken before expiry
    - Persists new tokens after refresh (refreshToken rotation)
    - Falls back to requiring re-authorization if refreshToken is expired

    Requires a TokenManager instance to obtain appToken for API calls.
    """

    def __init__(
        self,
        config: LansengerConfig,
        http_client: httpx.AsyncClient,
        app_token_manager: TokenManager,
        store: Optional[CredentialStore] = None,
    ):
        self._config = config
        self._http_client = http_client
        self._app_token_manager = app_token_manager
        self._store = store
        self._user_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._user_token_expiry: float = 0
        self._refresh_token_expiry: float = 0
        self._staff_id: Optional[str] = None

        if self._store:
            cached = self._store.load_user_token()
            ut = cached.get("user_token", "")
            rt = cached.get("refresh_token", "")
            expiry = cached.get("user_token_expiry", 0)
            refresh_expiry = cached.get("refresh_token_expiry", 0)

            # Load userToken (only if still valid, accounting for refresh margin)
            if ut and expiry > time.time():
                self._user_token = ut
                self._user_token_expiry = expiry
                logger.debug("Restored cached userToken (expires in %ds)", int(expiry - time.time()))

            # Load refreshToken independently — it stays valid (30 days)
            # even after userToken (2h) has expired. Previously we only
            # loaded it inside the ut-expiry guard, so a process restart
            # after userToken expiry would lose the still-valid refreshToken.
            if rt and refresh_expiry > time.time():
                self._refresh_token = rt
                self._refresh_token_expiry = refresh_expiry
                logger.debug("Restored cached refreshToken (valid until %s)", 
                             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(refresh_expiry)))

    async def get_token(self) -> str:
        """Get a valid userToken, refreshing if expired.

        Raises LansengerAuthError if token cannot be obtained
        (e.g. refreshToken expired — must re-authorize).
        """
        if self._user_token and time.time() < self._user_token_expiry:
            return self._user_token

        if not self._refresh_token:
            raise LansengerAuthError(
                "No userToken available and no refreshToken for auto-refresh. "
                "Run OAuth2 authorize flow: build_authorize_url → exchange_code."
            )

        # Check if refreshToken has actually expired before calling the API.
        # Without this, the SDK would call the API with an expired token and
        # return a confusing "invalid CODE" error (errCode=40036).
        if self._refresh_token_expiry > 0 and time.time() >= self._refresh_token_expiry:
            raise LansengerAuthError(
                "RefreshToken has expired. "
                "Re-run OAuth2 authorize flow: build_authorize_url → exchange_code."
            )

        app_token = await self._app_token_manager.get_token()
        url = build_api_url(self._config, "oauth2", "refresh_token_create", app_token)
        url += f"&grant_type=refresh_token&refresh_token={quote(self._refresh_token, safe='')}"

        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise LansengerNetworkError(f"userToken refresh failed: {e}") from e

        err_code = data.get("errCode", -1)
        if err_code != 0:
            msg = data.get("errMsg", "Unknown refresh error")
            raise LansengerAuthError(
                f"userToken refresh error (errCode={err_code}): {msg}",
                err_code=err_code,
            )

        token_data = data.get("data", {})
        self._user_token = token_data.get("userToken")
        expires_in = token_data.get("expiresIn", 7200)
        new_refresh_token = token_data.get("refreshToken")
        if new_refresh_token:
            self._refresh_token = new_refresh_token
        refresh_expires_in = token_data.get("refreshExpiresIn", 0)
        if refresh_expires_in:
            self._refresh_token_expiry = time.time() + refresh_expires_in
        self._staff_id = token_data.get("staffId")
        self._user_token_expiry = time.time() + expires_in - _USER_TOKEN_REFRESH_MARGIN

        if not self._user_token:
            raise LansengerAuthError("Refresh response missing userToken field")

        logger.debug("Refreshed userToken (expires_in=%ds, refreshExpiresIn=%ds)", expires_in, refresh_expires_in)

        if self._store:
            self._store.save_user_token(
                user_token=self._user_token,
                refresh_token=self._refresh_token or "",
                expires_in=expires_in,
                margin=_USER_TOKEN_REFRESH_MARGIN,
                refresh_expires_in=refresh_expires_in,
            )

        return self._user_token

    def set_tokens(
        self,
        user_token: str,
        refresh_token: str,
        expires_in: int = 7200,
        staff_id: str = "",
        refresh_expires_in: int = 0,
    ) -> None:
        """Set userToken + refreshToken after a successful exchange_code or manual authorization.

        Call this after exchange_code() to register the tokens for auto-refresh.
        """
        self._user_token = user_token
        self._refresh_token = refresh_token
        self._user_token_expiry = time.time() + expires_in - _USER_TOKEN_REFRESH_MARGIN
        if refresh_expires_in:
            self._refresh_token_expiry = time.time() + refresh_expires_in
        if staff_id:
            self._staff_id = staff_id

        if self._store:
            self._store.save_user_token(
                user_token=user_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                margin=_USER_TOKEN_REFRESH_MARGIN,
                refresh_expires_in=refresh_expires_in,
            )

        logger.debug("Registered userToken (expires_in=%ds)", expires_in)

    @property
    def staff_id(self) -> Optional[str]:
        """Return staffId associated with the current userToken."""
        return self._staff_id

    @property
    def refresh_token(self) -> Optional[str]:
        """Return the current refreshToken (for diagnostics only)."""
        return self._refresh_token

    @property
    def refresh_token_expiry(self) -> float:
        """Return the absolute expiry time of the refreshToken (epoch seconds)."""
        return self._refresh_token_expiry

    def invalidate(self) -> None:
        """Force userToken refresh on next get_token() call."""
        self._user_token = None
        self._user_token_expiry = 0