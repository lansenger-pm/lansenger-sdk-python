"""Lansenger SDK credential and token persistence.

Stores app credentials, appToken, and userToken in a JSON file
so they survive process restarts. Default path: ~/.lansenger/sdk_state.json

Supports multiple named profiles, each with its own credentials and tokens.
The file format is:

{
  "profiles": {
    "default": { "app_id": "...", "app_secret": "...", "api_gateway_url": "...", ... },
    "prod":    { "app_id": "...", ... },
    "staging": { "app_id": "...", ... }
  },
  "active_profile": "default"
}

Legacy single-credential format (flat dict with app_id at top level) is
auto-migrated to the "default" profile on first load.

The file is created with 0600 permissions (owner-only read/write).
"""

from __future__ import annotations

import json
import logging
import os
import stat
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lansenger_sdk.persistence")

DEFAULT_STATE_DIR = os.path.join(os.path.expanduser("~"), ".lansenger")
DEFAULT_STATE_FILE = "sdk_state.json"

DEFAULT_PROFILE = "default"

_LEGACY_KEYS = {"app_id", "app_secret", "api_gateway_url", "passport_url",
                "encoding_key", "callback_token",
                "app_token", "app_token_expiry", "user_token", "refresh_token",
                "user_token_expiry"}


class CredentialStore:
    """File-based persistence for Lansenger SDK credentials and tokens.

    Supports multiple named profiles. Each profile stores its own
    app_id, app_secret, api_gateway_url, passport_url, and tokens.
    """

    def __init__(self, path: Optional[str] = None, profile: str = DEFAULT_PROFILE):
        if path:
            self._path = Path(path)
        else:
            self._path = Path(DEFAULT_STATE_DIR) / DEFAULT_STATE_FILE
        self._profile = profile

    @property
    def path(self) -> str:
        return str(self._path)

    @property
    def profile(self) -> str:
        return self._profile

    def _migrate_legacy(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate flat dict format to multi-profile format."""
        if "profiles" in state:
            return state
        legacy_data = {k: v for k, v in state.items() if k in _LEGACY_KEYS}
        if not legacy_data.get("app_id"):
            return state
        new_state = {
            "profiles": {DEFAULT_PROFILE: legacy_data},
            "active_profile": DEFAULT_PROFILE,
        }
        logger.info("Migrated legacy credential store to multi-profile format (profile='default')")
        self.save(new_state)
        return new_state

    def load(self) -> Dict[str, Any]:
        """Load state from file. Returns empty dict if file doesn't exist."""
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            data = self._migrate_legacy(data)
            logger.debug("Loaded SDK state from %s", self._path)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load SDK state from %s: %s", self._path, e)
            return {}

    def save(self, state: Dict[str, Any]) -> None:
        """Save state to file with 0600 permissions."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.warning("Failed to set file permissions on %s", self._path)
        logger.debug("Saved SDK state to %s", self._path)

    def _get_profile_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the data dict for the current profile."""
        profiles = state.get("profiles", {})
        return profiles.get(self._profile, {})

    def _set_profile_data(self, state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Set the data dict for the current profile and return updated state."""
        if "profiles" not in state:
            state["profiles"] = {}
        state["profiles"][self._profile] = data
        if "active_profile" not in state:
            state["active_profile"] = DEFAULT_PROFILE
        return state

    def load_credentials(self) -> Dict[str, str]:
        """Load app_id, app_secret, api_gateway_url, passport_url, encoding_key, callback_token for current profile."""
        state = self.load()
        data = self._get_profile_data(state)
        return {
            "app_id": data.get("app_id", ""),
            "app_secret": data.get("app_secret", ""),
            "api_gateway_url": data.get("api_gateway_url", ""),
            "passport_url": data.get("passport_url", ""),
            "encoding_key": data.get("encoding_key", ""),
            "callback_token": data.get("callback_token", ""),
        }

    def save_credentials(
        self,
        app_id: str,
        app_secret: str,
        api_gateway_url: str = "",
        passport_url: str = "",
        encoding_key: str = "",
        callback_token: str = "",
    ) -> None:
        """Save app_id, app_secret, api_gateway_url, passport_url, encoding_key, callback_token for current profile."""
        state = self.load()
        data = self._get_profile_data(state)
        data["app_id"] = app_id
        data["app_secret"] = app_secret
        if api_gateway_url:
            data["api_gateway_url"] = api_gateway_url
        if passport_url:
            data["passport_url"] = passport_url
        if encoding_key:
            data["encoding_key"] = encoding_key
        if callback_token:
            data["callback_token"] = callback_token
        state = self._set_profile_data(state, data)
        self.save(state)

    def load_app_token(self) -> Optional[str]:
        """Load cached appToken for current profile if not expired."""
        state = self.load()
        data = self._get_profile_data(state)
        token = data.get("app_token")
        expiry = data.get("app_token_expiry", 0)
        if token and expiry > time.time():
            logger.debug("Loaded cached appToken for profile '%s' (expires in %ds)",
                         self._profile, int(expiry - time.time()))
            return token
        if token:
            logger.debug("Cached appToken for profile '%s' expired, will refresh", self._profile)
        return None

    def save_app_token(self, token: str, expires_in: int = 7200, margin: int = 300) -> None:
        """Save appToken for current profile with computed expiry time."""
        state = self.load()
        data = self._get_profile_data(state)
        data["app_token"] = token
        data["app_token_expiry"] = time.time() + expires_in - margin
        state = self._set_profile_data(state, data)
        self.save(state)

    def load_user_token(self) -> Dict[str, Any]:
        """Load userToken and refreshToken for current profile."""
        state = self.load()
        data = self._get_profile_data(state)
        return {
            "user_token": data.get("user_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "user_token_expiry": data.get("user_token_expiry", 0),
        }

    def save_user_token(
        self,
        user_token: str,
        refresh_token: str = "",
        expires_in: int = 0,
    ) -> None:
        """Save userToken and refreshToken for current profile."""
        state = self.load()
        data = self._get_profile_data(state)
        data["user_token"] = user_token
        data["refresh_token"] = refresh_token
        if expires_in:
            data["user_token_expiry"] = time.time() + expires_in
        state = self._set_profile_data(state, data)
        self.save(state)

    def clear_profile(self) -> None:
        """Clear the current profile's data from the store file."""
        state = self.load()
        profiles = state.get("profiles", {})
        if self._profile in profiles:
            del profiles[self._profile]
            self.save(state)
            logger.debug("Cleared profile '%s'", self._profile)

    def clear(self) -> None:
        """Delete the entire state file."""
        if self._path.exists():
            self._path.unlink()
            logger.debug("Cleared SDK state file %s", self._path)

    def list_profiles(self) -> List[str]:
        """List all profile names in the store."""
        state = self.load()
        return list(state.get("profiles", {}).keys())

    def get_active_profile(self) -> str:
        """Get the active profile name."""
        state = self.load()
        return state.get("active_profile", DEFAULT_PROFILE)

    def set_active_profile(self, profile: str) -> None:
        """Set the active profile name."""
        state = self.load()
        state["active_profile"] = profile
        self.save(state)

    def has_credentials(self) -> bool:
        """Check if stored credentials (app_id + app_secret) exist for current profile."""
        creds = self.load_credentials()
        return bool(creds["app_id"] and creds["app_secret"])

    def has_full_config(self) -> bool:
        """Check if stored credentials AND URLs exist for current profile."""
        creds = self.load_credentials()
        return bool(creds["app_id"] and creds["app_secret"] and creds["api_gateway_url"])