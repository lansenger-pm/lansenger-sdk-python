"""Lansenger SDK credential and token persistence.

Stores app credentials, appToken, and userToken in a JSON file
so they survive process restarts. Default path: ~/.lansenger/sdk_state.json

The file is created with 0600 permissions (owner-only read/write).
"""

from __future__ import annotations

import json
import logging
import os
import stat
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("lansenger_sdk.persistence")

DEFAULT_STATE_DIR = os.path.join(os.path.expanduser("~"), ".lansenger")
DEFAULT_STATE_FILE = "sdk_state.json"


class CredentialStore:
    """File-based persistence for Lansenger SDK credentials and tokens.

    Stores:
    - app_id, app_secret (credentials)
    - app_token, app_token_expiry (appToken + epoch expiry time)
    - user_token, refresh_token, user_token_expiry (OAuth2 user tokens)
    """

    def __init__(self, path: Optional[str] = None):
        if path:
            self._path = Path(path)
        else:
            self._path = Path(DEFAULT_STATE_DIR) / DEFAULT_STATE_FILE

    @property
    def path(self) -> str:
        return str(self._path)

    def load(self) -> Dict[str, Any]:
        """Load state from file. Returns empty dict if file doesn't exist."""
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            logger.debug("Loaded SDK state from %s", self._path)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load SDK state from %s: %s", self._path, e)
            return {}

    def save(self, state: Dict[str, Any]) -> None:
        """Save state to file with 0600 permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        try:
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.warning("Failed to set file permissions on %s", self._path)
        logger.debug("Saved SDK state to %s", self._path)

    def load_credentials(self) -> Dict[str, str]:
        """Load app_id, app_secret, api_gateway_url, passport_url from store."""
        state = self.load()
        return {
            "app_id": state.get("app_id", ""),
            "app_secret": state.get("app_secret", ""),
            "api_gateway_url": state.get("api_gateway_url", ""),
            "passport_url": state.get("passport_url", ""),
        }

    def save_credentials(
        self,
        app_id: str,
        app_secret: str,
        api_gateway_url: str = "",
        passport_url: str = "",
    ) -> None:
        """Save app_id, app_secret, api_gateway_url, passport_url to store."""
        state = self.load()
        state["app_id"] = app_id
        state["app_secret"] = app_secret
        if api_gateway_url:
            state["api_gateway_url"] = api_gateway_url
        if passport_url:
            state["passport_url"] = passport_url
        self.save(state)

    def load_app_token(self) -> Optional[str]:
        """Load cached appToken if not expired. Returns None if expired or missing."""
        state = self.load()
        token = state.get("app_token")
        expiry = state.get("app_token_expiry", 0)
        if token and expiry > time.time():
            logger.debug("Loaded cached appToken (expires in %ds)", int(expiry - time.time()))
            return token
        if token:
            logger.debug("Cached appToken expired, will refresh")
        return None

    def save_app_token(self, token: str, expires_in: int = 7200, margin: int = 300) -> None:
        """Save appToken with computed expiry time."""
        state = self.load()
        state["app_token"] = token
        state["app_token_expiry"] = time.time() + expires_in - margin
        self.save(state)

    def load_user_token(self) -> Dict[str, Any]:
        """Load userToken and refreshToken from store."""
        state = self.load()
        return {
            "user_token": state.get("user_token", ""),
            "refresh_token": state.get("refresh_token", ""),
            "user_token_expiry": state.get("user_token_expiry", 0),
        }

    def save_user_token(
        self,
        user_token: str,
        refresh_token: str = "",
        expires_in: int = 0,
    ) -> None:
        """Save userToken and refreshToken to store."""
        state = self.load()
        state["user_token"] = user_token
        state["refresh_token"] = refresh_token
        if expires_in:
            state["user_token_expiry"] = time.time() + expires_in
        self.save(state)

    def clear(self) -> None:
        """Delete the state file."""
        if self._path.exists():
            self._path.unlink()
            logger.debug("Cleared SDK state file %s", self._path)

    def has_credentials(self) -> bool:
        """Check if stored credentials (app_id + app_secret) exist."""
        creds = self.load_credentials()
        return bool(creds["app_id"] and creds["app_secret"])

    def has_full_config(self) -> bool:
        """Check if stored credentials AND URLs exist."""
        creds = self.load_credentials()
        return bool(creds["app_id"] and creds["app_secret"] and creds["api_gateway_url"])