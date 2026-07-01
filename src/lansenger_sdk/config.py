"""Lansenger SDK configuration — env var + direct parameter resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .exceptions import LansengerConfigError


DEFAULT_API_GATEWAY_URL = "https://open.e.lanxin.cn/open/apigw"


@dataclass
class LansengerConfig:
    """SDK configuration — resolved from env vars or direct params.

    Resolution order:
    1. Direct params passed to LansengerConfig.create()
    2. LANSENGER_APP_ID / LANSENGER_APP_SECRET / LANSENGER_API_GATEWAY_URL
       LANSENGER_PASSPORT_URL / LANSENGER_REDIRECT_URI /
       LANSENGER_ENCODING_KEY / LANSENGER_CALLBACK_TOKEN /
       LANSENGER_APP_TOKEN / LANSENGER_USER_TOKEN
       env vars
    """

    app_id: str
    app_secret: str
    api_gateway_url: str = DEFAULT_API_GATEWAY_URL
    passport_url: str = ""
    redirect_uri: str = ""
    http_timeout: float = 30.0
    encoding_key: str = ""
    callback_token: str = ""
    app_token: str = ""
    user_token: str = ""

    @classmethod
    def create(
        cls,
        app_id: str | None = None,
        app_secret: str | None = None,
        api_gateway_url: str | None = None,
        passport_url: str | None = None,
        redirect_uri: str | None = None,
        http_timeout: float | None = None,
        encoding_key: str | None = None,
        callback_token: str | None = None,
        app_token: str | None = None,
        user_token: str | None = None,
    ) -> LansengerConfig:
        """Create config from params with env var fallback.

        Raises LansengerConfigError if credentials are missing.
        When app_token is provided, app_id/app_secret are optional.
        """
        resolved_app_id = app_id or os.environ.get("LANSENGER_APP_ID", "").strip()
        resolved_app_secret = app_secret or os.environ.get("LANSENGER_APP_SECRET", "").strip()
        resolved_gateway = api_gateway_url or os.environ.get(
            "LANSENGER_API_GATEWAY_URL", DEFAULT_API_GATEWAY_URL
        ).strip()
        resolved_passport = passport_url or os.environ.get(
            "LANSENGER_PASSPORT_URL", ""
        ).strip()
        resolved_redirect_uri = redirect_uri or os.environ.get(
            "LANSENGER_REDIRECT_URI", ""
        ).strip()
        resolved_timeout = http_timeout if http_timeout is not None else 30.0
        resolved_encoding_key = encoding_key or os.environ.get(
            "LANSENGER_ENCODING_KEY", ""
        ).strip()
        resolved_callback_token = callback_token or os.environ.get(
            "LANSENGER_CALLBACK_TOKEN", ""
        ).strip()
        resolved_app_token = app_token or os.environ.get(
            "LANSENGER_APP_TOKEN", ""
        ).strip()
        resolved_user_token = user_token or os.environ.get(
            "LANSENGER_USER_TOKEN", ""
        ).strip()

        # In external mode (app_token provided), app_id/app_secret are optional
        if not resolved_app_token and (not resolved_app_id or not resolved_app_secret):
            raise LansengerConfigError(
                "Lansenger credentials not configured. "
                "Set LANSENGER_APP_ID and LANSENGER_APP_SECRET env vars, "
                "or pass app_id/app_secret directly, "
                "or provide LANSENGER_APP_TOKEN for external token mode."
            )

        return cls(
            app_id=resolved_app_id,
            app_secret=resolved_app_secret,
            api_gateway_url=resolved_gateway,
            passport_url=resolved_passport,
            redirect_uri=resolved_redirect_uri,
            http_timeout=resolved_timeout,
            encoding_key=resolved_encoding_key,
            callback_token=resolved_callback_token,
            app_token=resolved_app_token,
            user_token=resolved_user_token,
        )

    @classmethod
    def from_env(cls) -> LansengerConfig:
        """Create config purely from environment variables."""
        return cls.create()

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_secret)

    def is_external_mode(self) -> bool:
        """Return True when app_token is provided externally (no auto-refresh)."""
        return bool(self.app_token)

    def has_passport_url(self) -> bool:
        """Check if passport_url is configured (needed for OAuth2 flows)."""
        return bool(self.passport_url)