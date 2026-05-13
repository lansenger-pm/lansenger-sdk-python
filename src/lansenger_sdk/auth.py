"""Lansenger SDK token management — get/refresh app access token."""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from .config import LansengerConfig
from .constants import API_ENDPOINTS
from .exceptions import LansengerAuthError, LansengerNetworkError

logger = logging.getLogger("lansenger_sdk.auth")

_TOKEN_REFRESH_MARGIN = 300  # Refresh 5 minutes before expiry


class TokenManager:
    """Manages Lansenger app access token lifecycle.

    The appToken is obtained via GET /v1/apptoken/create with
    app_id + app_secret. It has a 2-hour expiry (7200s) and
    is refreshed 5 minutes before expiry automatically.
    """

    def __init__(self, config: LansengerConfig, http_client: httpx.AsyncClient):
        self._config = config
        self._http_client = http_client
        self._token: Optional[str] = None
        self._token_expiry: float = 0

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
        return self._token

    def invalidate(self) -> None:
        """Force token refresh on next get_token() call."""
        self._token = None
        self._token_expiry = 0