"""Lansenger SDK credential and token persistence.

Stores app credentials, appToken, and userToken in a JSON file
so they survive process restarts. Default path: ~/.lansenger/sdk_state.json

Supports multiple named profiles, each with its own credentials and tokens.
userTokens are stored per-staff_id so multiple users can coexist in
the same profile without overwriting each other.

The file format is:

{
  "profiles": {
    "default": {
      "app_id": "...",
      "app_secret": "...",
      "api_gateway_url": "...",
      "user_tokens": {
        "staff-id-a": { "user_token": "...", "refresh_token": "...", ... },
        "staff-id-b": { "user_token": "...", "refresh_token": "...", ... }
      }
    }
  },
  "active_profile": "default"
}

Legacy single-credential format (flat dict with app_id at top level) and
legacy flat userToken fields (user_token / refresh_token / staff_id at
profile level) are auto-migrated on first load.

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
                "redirect_uri", "encoding_key", "callback_token",
                "app_token", "app_token_expiry", "user_token", "refresh_token",
                "user_token_expiry", "staff_id"}


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

    def _migrate_user_tokens(self, data: Dict[str, Any]) -> bool:
        """Migrate flat userToken fields into user_tokens[staff_id] nested structure.

        Returns True if a migration or cleanup was performed (caller must persist).
        Modifies *data* in place.

        If ``staff_id`` already exists in ``user_tokens``, flat fields are merged
        into the existing entry (newer flat data wins), then flat is cleaned.
        This handles the case where an old SDK rewrites flat after migration.
        """
        staff_id = (data.get("staff_id") or "").strip()
        user_token = (data.get("user_token") or "").strip()
        if not staff_id or not user_token:
            return False

        nested = data.get("user_tokens")
        if not isinstance(nested, dict):
            nested = {}
            data["user_tokens"] = nested

        # Merge flat into nested — either create new or update existing entry
        entry = nested.get(staff_id, {})
        changed = False
        for key in ("user_token", "refresh_token", "user_token_expiry", "refresh_token_expiry"):
            if key in data:
                entry[key] = data.pop(key)
                changed = True
        data.pop("staff_id", None)
        if changed:
            nested[staff_id] = entry
            logger.debug("Migrated/merged flat userToken for staff_id=%s", staff_id)
        return changed

    def _get_profile_data(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the data dict for the current profile, migrating flat userTokens on access."""
        profiles = state.get("profiles", {})
        data = profiles.get(self._profile, {})
        if self._migrate_user_tokens(data):
            self.save(state)
        return data

    def _set_profile_data(self, state: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Set the data dict for the current profile and return updated state."""
        if "profiles" not in state:
            state["profiles"] = {}
        state["profiles"][self._profile] = data
        if "active_profile" not in state:
            state["active_profile"] = DEFAULT_PROFILE
        return state

    def load_credentials(self) -> Dict[str, str]:
        """Load app_id, app_secret, api_gateway_url, passport_url, redirect_uri, encoding_key, callback_token for current profile."""
        state = self.load()
        data = self._get_profile_data(state)
        return {
            "app_id": data.get("app_id", ""),
            "app_secret": data.get("app_secret", ""),
            "api_gateway_url": data.get("api_gateway_url", ""),
            "passport_url": data.get("passport_url", ""),
            "redirect_uri": data.get("redirect_uri", ""),
            "encoding_key": data.get("encoding_key", ""),
            "callback_token": data.get("callback_token", ""),
        }

    def save_credentials(
        self,
        app_id: str,
        app_secret: str,
        api_gateway_url: str = "",
        passport_url: str = "",
        redirect_uri: str = "",
        encoding_key: str = "",
        callback_token: str = "",
    ) -> None:
        """Save app_id, app_secret, api_gateway_url, passport_url, redirect_uri, encoding_key, callback_token for current profile.

        encoding_key, callback_token and redirect_uri are always written (even empty strings)
        so they can be explicitly cleared.
        """
        state = self.load()
        data = self._get_profile_data(state)
        data["app_id"] = app_id
        data["app_secret"] = app_secret
        if api_gateway_url:
            data["api_gateway_url"] = api_gateway_url
        if passport_url:
            data["passport_url"] = passport_url
        data["redirect_uri"] = redirect_uri
        data["encoding_key"] = encoding_key
        data["callback_token"] = callback_token
        state = self._set_profile_data(state, data)
        self.save(state)

    def save_callback_config(
        self,
        encoding_key: str,
        callback_token: str = "",
    ) -> None:
        """Save or clear encoding_key and callback_token for current profile.

        This method always writes the values, allowing explicit clearing
        by passing empty strings.
        """
        state = self.load()
        data = self._get_profile_data(state)
        data["encoding_key"] = encoding_key
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

    def load_user_token(self, staff_id: str = "") -> Dict[str, Any]:
        """Load userToken and refreshToken for current profile.

        If staff_id is provided, reads from the per-user nested store
        ``data["user_tokens"][staff_id]``.  Otherwise falls back to the
        legacy flat fields (``data["user_token"]``, …) for backward
        compatibility.  Flat fields are auto-migrated to nested on load.
        """
        state = self.load()
        data = self._get_profile_data(state)
        if staff_id:
            nested = data.get("user_tokens")
            if isinstance(nested, dict):
                entry = nested.get(staff_id)
                if isinstance(entry, dict):
                    return {
                        "user_token": entry.get("user_token", ""),
                        "refresh_token": entry.get("refresh_token", ""),
                        "user_token_expiry": entry.get("user_token_expiry", 0),
                        "refresh_token_expiry": entry.get("refresh_token_expiry", 0),
                        "staff_id": staff_id,
                    }
        # Fallback: legacy flat fields (backward compat with old store format
        # before migration runs). If flat is empty, try the first entry from
        # the nested store (post-migration, when no staff_id is specified).
        flat = {
            "user_token": data.get("user_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "user_token_expiry": data.get("user_token_expiry", 0),
            "refresh_token_expiry": data.get("refresh_token_expiry", 0),
            "staff_id": data.get("staff_id", ""),
        }
        if flat["user_token"] and flat["staff_id"]:
            return flat

        nested = data.get("user_tokens")
        if isinstance(nested, dict) and nested:
            first_sid = next(iter(nested))
            first_entry = nested.get(first_sid, {})
            if isinstance(first_entry, dict):
                return {
                    "user_token": first_entry.get("user_token", ""),
                    "refresh_token": first_entry.get("refresh_token", ""),
                    "user_token_expiry": first_entry.get("user_token_expiry", 0),
                    "refresh_token_expiry": first_entry.get("refresh_token_expiry", 0),
                    "staff_id": first_sid,
                }

        return flat

    def save_user_token(
        self,
        user_token: str,
        refresh_token: str = "",
        expires_in: int = 0,
        margin: int = 300,
        refresh_expires_in: int = 0,
        staff_id: str = "",
    ) -> None:
        """Save userToken and refreshToken into per-user nested store.

        Writes into ``data["user_tokens"][staff_id]`` so multiple users
        can coexist in the same profile without overwriting each other.
        Falls back to legacy flat fields when no staff_id is provided
        (backward compatibility).
        """
        state = self.load()
        data = self._get_profile_data(state)

        if not staff_id:
            # Legacy flat path — no staff_id to key on
            data["user_token"] = user_token
            data["refresh_token"] = refresh_token
            if expires_in:
                data["user_token_expiry"] = time.time() + expires_in - margin
            if refresh_expires_in:
                data["refresh_token_expiry"] = time.time() + refresh_expires_in
            data.pop("staff_id", None)
        else:
            nested = data.get("user_tokens")
            if not isinstance(nested, dict):
                nested = {}
                data["user_tokens"] = nested

            entry = nested.get(staff_id, {})
            entry["user_token"] = user_token
            entry["refresh_token"] = refresh_token
            if expires_in:
                entry["user_token_expiry"] = time.time() + expires_in - margin
            if refresh_expires_in:
                entry["refresh_token_expiry"] = time.time() + refresh_expires_in
            nested[staff_id] = entry

            # Clean up legacy flat fields after first nested save
            data.pop("user_token", None)
            data.pop("refresh_token", None)
            data.pop("user_token_expiry", None)
            data.pop("refresh_token_expiry", None)
            data.pop("staff_id", None)

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

    def delete_profile_by_name(self, name: str) -> bool:
        """Delete a profile by name from the store.

        If the deleted profile is the active profile, automatically
        falls back to ``"default"``.

        Returns:
            True if the profile was found and deleted, False otherwise.
        """
        state = self.load()
        profiles = state.get("profiles", {})
        if name not in profiles:
            return False
        del profiles[name]
        if state.get("active_profile") == name:
            state["active_profile"] = DEFAULT_PROFILE
        self.save(state)
        logger.debug("Deleted profile '%s'", name)
        return True

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