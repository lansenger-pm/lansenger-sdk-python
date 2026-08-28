"""Tests for Lansenger SDK credential and token persistence."""

import json
import os
import time
import tempfile
import pytest

from lansenger_sdk.persistence import CredentialStore


@pytest.fixture
def tmp_store():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    store = CredentialStore(path=path)
    yield store
    if os.path.exists(path):
        os.unlink(path)


def test_credential_store_init(tmp_store):
    assert tmp_store.path.endswith(".json")


def test_credential_store_save_and_load_credentials(tmp_store):
    tmp_store.save_credentials("app123", "secret456", api_gateway_url="https://gw.example.com", passport_url="https://passport.example.com")
    creds = tmp_store.load_credentials()
    assert creds["app_id"] == "app123"
    assert creds["app_secret"] == "secret456"
    assert creds["api_gateway_url"] == "https://gw.example.com"
    assert creds["passport_url"] == "https://passport.example.com"


def test_credential_store_has_credentials(tmp_store):
    assert tmp_store.has_credentials() is False
    tmp_store.save_credentials("app123", "secret456")
    assert tmp_store.has_credentials() is True
    assert tmp_store.has_full_config() is False
    tmp_store.save_credentials("app123", "secret456", api_gateway_url="https://gw.example.com")
    assert tmp_store.has_full_config() is True


def test_credential_store_load_empty(tmp_store):
    state = tmp_store.load()
    assert state == {}


def test_credential_store_app_token_save_and_load(tmp_store):
    tmp_store.save_app_token("token_abc", expires_in=7200, margin=300)
    loaded = tmp_store.load_app_token()
    assert loaded == "token_abc"


def test_credential_store_app_token_expired(tmp_store):
    tmp_store.save_app_token("token_expired", expires_in=100, margin=100)
    loaded = tmp_store.load_app_token()
    assert loaded is None


def test_credential_store_app_token_no_file(tmp_store):
    if os.path.exists(tmp_store.path):
        os.unlink(tmp_store.path)
    loaded = tmp_store.load_app_token()
    assert loaded is None


def test_credential_store_user_token_save_and_load(tmp_store):
    tmp_store.save_user_token("ut_xyz", refresh_token="rt_xyz", expires_in=86400)
    data = tmp_store.load_user_token()
    assert data["user_token"] == "ut_xyz"
    assert data["refresh_token"] == "rt_xyz"


def test_credential_store_clear(tmp_store):
    tmp_store.save_credentials("app", "secret")
    assert os.path.exists(tmp_store.path)
    tmp_store.clear()
    assert not os.path.exists(tmp_store.path)


def test_credential_store_file_permissions(tmp_store):
    tmp_store.save_credentials("app", "secret")
    st = os.stat(tmp_store.path)
    mode = st.st_mode & 0o777
    assert mode == 0o600


def test_credential_store_preserves_state(tmp_store):
    tmp_store.save_credentials("app1", "secret1", api_gateway_url="https://gw.example.com", passport_url="https://pp.example.com")
    tmp_store.save_app_token("token1", expires_in=7200)
    creds = tmp_store.load_credentials()
    assert creds["app_id"] == "app1"
    assert creds["app_secret"] == "secret1"
    assert creds["api_gateway_url"] == "https://gw.example.com"
    assert creds["passport_url"] == "https://pp.example.com"
    token = tmp_store.load_app_token()
    assert token == "token1"


def test_credential_store_custom_path():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "custom.json")
        store = CredentialStore(path=path)
        store.save_credentials("a", "b")
        assert os.path.exists(path)
        creds = store.load_credentials()
        assert creds["app_id"] == "a"


def test_credential_store_corrupt_file(tmp_store):
    with open(tmp_store.path, "w") as f:
        f.write("not valid json")
    state = tmp_store.load()
    assert state == {}


def test_client_with_store_path():
    from lansenger_sdk import LansengerClient
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    client = LansengerClient(app_id="id", app_secret="secret", store_path=path)
    assert client._store is not None
    assert client._store.path == path
    if os.path.exists(path):
        os.unlink(path)


def test_client_from_env_with_store_path():
    from lansenger_sdk import LansengerClient
    os.environ["LANSENGER_APP_ID"] = "env_id"
    os.environ["LANSENGER_APP_SECRET"] = "env_secret"
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    client = LansengerClient.from_env(store_path=path)
    assert client._store is not None
    if os.path.exists(path):
        os.unlink(path)


def test_client_without_store():
    from lansenger_sdk import LansengerClient
    client = LansengerClient(app_id="id", app_secret="secret")
    assert client._store is None


def test_credential_store_save_and_load_encoding_key(tmp_store):
    tmp_store.save_credentials("app123", "secret456", encoding_key="NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM", callback_token="48D32458EB80C61EBB08C7E86CB5BFB1")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
    assert creds["callback_token"] == "48D32458EB80C61EBB08C7E86CB5BFB1"


def test_credential_store_encoding_key_only(tmp_store):
    tmp_store.save_credentials("app123", "secret456", encoding_key="NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
    assert creds["callback_token"] == ""


def test_credential_store_callback_token_only(tmp_store):
    tmp_store.save_credentials("app123", "secret456", callback_token="48D32458EB80C61EBB08C7E86CB5BFB1")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == ""
    assert creds["callback_token"] == "48D32458EB80C61EBB08C7E86CB5BFB1"


def test_credential_store_clear_encoding_key_via_save_credentials(tmp_store):
    tmp_store.save_credentials("app123", "secret456", encoding_key="myKey", callback_token="myToken")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == "myKey"
    assert creds["callback_token"] == "myToken"
    tmp_store.save_credentials("app123", "secret456", encoding_key="", callback_token="")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == ""
    assert creds["callback_token"] == ""


def test_credential_store_save_callback_config(tmp_store):
    tmp_store.save_credentials("app123", "secret456")
    tmp_store.save_callback_config(encoding_key="NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM", callback_token="48D32458EB80C61EBB08C7E86CB5BFB1")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
    assert creds["callback_token"] == "48D32458EB80C61EBB08C7E86CB5BFB1"
    assert creds["app_id"] == "app123"


def test_credential_store_clear_callback_config(tmp_store):
    tmp_store.save_credentials("app123", "secret456", encoding_key="myKey", callback_token="myToken")
    tmp_store.save_callback_config(encoding_key="", callback_token="")
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == ""
    assert creds["callback_token"] == ""
    assert creds["app_id"] == "app123"


def test_credential_store_preserves_encoding_key(tmp_store):
    tmp_store.save_credentials("app1", "secret1", encoding_key="myKey", callback_token="myToken")
    tmp_store.save_app_token("token1", expires_in=7200)
    creds = tmp_store.load_credentials()
    assert creds["encoding_key"] == "myKey"
    assert creds["callback_token"] == "myToken"


def test_sync_client_from_store_with_encoding_key():
    from lansenger_sdk import LansengerSyncClient
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    store = CredentialStore(path=path)
    store.save_credentials("app123", "secret456", encoding_key="NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM", callback_token="48D32458EB80C61EBB08C7E86CB5BFB1")
    client = LansengerSyncClient.from_store(profile="default", path=path)
    assert client._encoding_key == "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
    assert client._callback_token == "48D32458EB80C61EBB08C7E86CB5BFB1"
    if os.path.exists(path):
        os.unlink(path)


def test_async_client_from_store_with_encoding_key():
    from lansenger_sdk import LansengerClient
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    store = CredentialStore(path=path)
    store.save_credentials("app123", "secret456", encoding_key="NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM", callback_token="48D32458EB80C61EBB08C7E86CB5BFB1")
    client = LansengerClient.from_store(profile="default", path=path)
    assert client._config.encoding_key == "NEVFNjNFREZDNUU4QzMxMUQ5MTgzMkI5NTVBMzJFODM"
    assert client._config.callback_token == "48D32458EB80C61EBB08C7E86CB5BFB1"
    assert client._store is not None
    if os.path.exists(path):
        os.unlink(path)


# ── delete_profile_by_name ──────────────────────────────────────

def test_delete_profile_by_name_deletes_and_returns_true():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    try:
        store = CredentialStore(path=path)
        store.save_credentials("app1", "secret1")
        assert store.delete_profile_by_name("default") is True
        assert "default" not in store.list_profiles()
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_delete_profile_by_name_nonexistent_returns_false():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    try:
        store = CredentialStore(path=path)
        store.save_credentials("app1", "secret1")
        assert store.delete_profile_by_name("ghost") is False
        assert "default" in store.list_profiles()
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_delete_profile_by_name_preserves_other_profiles():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    try:
        store_a = CredentialStore(path=path, profile="alpha")
        store_b = CredentialStore(path=path, profile="beta")
        store_a.save_credentials("appA", "secA")
        store_b.save_credentials("appB", "secB")
        profiles = store_a.list_profiles()
        assert "alpha" in profiles
        assert "beta" in profiles
        assert store_a.delete_profile_by_name("alpha") is True
        profiles = store_b.list_profiles()
        assert "alpha" not in profiles
        assert "beta" in profiles
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_delete_profile_by_name_active_falls_back_to_default():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)
    try:
        store = CredentialStore(path=path)
        store.set_active_profile("staging")
        store_a = CredentialStore(path=path, profile="staging")
        store_a.save_credentials("appX", "secX")
        assert store.get_active_profile() == "staging"
        assert store.delete_profile_by_name("staging") is True
        assert store.get_active_profile() == "default"
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── Multi-user userToken isolation ────────────────────────────────

_NOW = int(time.time())


def test_user_token_multi_user_isolation(tmp_store):
    """Two users in the same profile do not overwrite each other."""
    tmp_store.save_user_token(
        "token-a", refresh_token="rt-a", expires_in=7200,
        refresh_expires_in=2592000, staff_id="staff-a",
    )
    tmp_store.save_user_token(
        "token-b", refresh_token="rt-b", expires_in=7200,
        refresh_expires_in=2592000, staff_id="staff-b",
    )

    # Load by staff_id — each gets their own tokens
    a = tmp_store.load_user_token("staff-a")
    b = tmp_store.load_user_token("staff-b")
    assert a["user_token"] == "token-a"
    assert a["refresh_token"] == "rt-a"
    assert a["staff_id"] == "staff-a"
    assert b["user_token"] == "token-b"
    assert b["refresh_token"] == "rt-b"
    assert b["staff_id"] == "staff-b"


def test_user_token_isolation_prevents_overwrite(tmp_store):
    """Saving staff-b does NOT wipe staff-a's tokens."""
    tmp_store.save_user_token("token-a", "rt-a", 7200, staff_id="staff-a")
    tmp_store.save_user_token("token-b", "rt-b", 7200, staff_id="staff-b")

    a = tmp_store.load_user_token("staff-a")
    assert a["user_token"] == "token-a", "staff-a should still have its own token after staff-b save"


def test_user_token_cross_staff_independence(tmp_store):
    """Updating staff-a's token does NOT affect staff-b."""
    tmp_store.save_user_token("token-a-v1", "rt-a", 7200, staff_id="staff-a")
    tmp_store.save_user_token("token-b", "rt-b", 7200, staff_id="staff-b")

    # Update staff-a with a new token
    tmp_store.save_user_token("token-a-v2", "rt-a-v2", 7200, staff_id="staff-a")

    a = tmp_store.load_user_token("staff-a")
    b = tmp_store.load_user_token("staff-b")
    assert a["user_token"] == "token-a-v2"
    assert b["user_token"] == "token-b", "staff-b must be untouched"


def test_user_token_backward_compat_legacy_flat(tmp_store):
    """Legacy flat userToken fields are auto-migrated on first access."""
    # 1. Write legacy flat format manually
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    data["user_token"] = "legacy-ut"
    data["refresh_token"] = "legacy-rt"
    data["staff_id"] = "legacy-staff"
    data["user_token_expiry"] = _NOW + 7200
    data["refresh_token_expiry"] = _NOW + 2592000
    state = tmp_store._set_profile_data(state, data)
    tmp_store.save(state)

    # Verify raw file has flat fields
    raw = json.loads(open(tmp_store.path).read())
    profile = raw["profiles"]["default"]
    assert profile["user_token"] == "legacy-ut"
    assert profile["staff_id"] == "legacy-staff"

    # First access triggers auto-migration in _get_profile_data
    got = tmp_store.load_user_token("")
    assert got["user_token"] == "legacy-ut"
    assert got["staff_id"] == "legacy-staff"

    # After load, flat fields should be migrated away
    raw2 = json.loads(open(tmp_store.path).read())
    profile2 = raw2["profiles"]["default"]
    assert "user_token" not in profile2, "flat user_token should be migrated away"
    assert "staff_id" not in profile2, "flat staff_id should be migrated away"
    assert profile2["user_tokens"]["legacy-staff"]["user_token"] == "legacy-ut"


def test_user_token_auto_migration_on_save(tmp_store):
    """Saving with staff_id migrates flat fields away and into nested."""
    # 1. Write legacy flat format manually
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    data["user_token"] = "legacy-ut"
    data["staff_id"] = "legacy-staff"
    state = tmp_store._set_profile_data(state, data)
    tmp_store.save(state)

    # 2. Verify flat is readable
    got = tmp_store.load_user_token("")
    assert got["user_token"] == "legacy-ut"
    assert got["staff_id"] == "legacy-staff"

    # 3. Now do a nested save for a *different* user — this triggers migration
    tmp_store.save_user_token("nested-ut", "nested-rt", 7200, staff_id="nested-staff")

    # 4. After migration, flat fields should be gone
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    assert "user_token" not in data, "flat user_token should be cleaned after migration"
    assert "staff_id" not in data, "flat staff_id should be cleaned after migration"

    # 5. Legacy user should now be accessible via nested
    legacy = tmp_store.load_user_token("legacy-staff")
    assert legacy["user_token"] == "legacy-ut"

    # 6. New user should also be accessible
    nested = tmp_store.load_user_token("nested-staff")
    assert nested["user_token"] == "nested-ut"


def test_user_token_no_staff_id_fallback(tmp_store):
    """load_user_token('') returns first available user from nested store
    when flat fields are empty (post-migration scenario)."""
    tmp_store.save_user_token("t1", refresh_token="r1", expires_in=7200, staff_id="staff1")
    tmp_store.save_user_token("t2", refresh_token="r2", expires_in=7200, staff_id="staff2")

    # No staff_id → falls back to first entry from nested
    fallback = tmp_store.load_user_token("")
    assert fallback["user_token"] == "t2" or fallback["user_token"] == "t1"

    # But with exact staff_id, we get the specific one
    one = tmp_store.load_user_token("staff1")
    two = tmp_store.load_user_token("staff2")
    assert one["user_token"] == "t1"
    assert two["user_token"] == "t2"


def test_user_token_nonexistent_staff_id(tmp_store):
    """load_user_token with a non-existent staff_id falls back to available tokens.

    This is the graceful-degradation behavior: when the exact staff_id is not
    found, the store returns what's available (first user from nested, or flat).
    This ensures UserTokenManager (which may not know its staff_id at init time)
    always gets the best available token.
    """
    tmp_store.save_user_token("t1", staff_id="staff1")
    got = tmp_store.load_user_token("ghost-staff")
    # Fallback returns first available user (or empty if nothing at all)
    assert got["user_token"] in ("", "t1")
    assert got["staff_id"] in ("ghost-staff", "staff1")


def test_user_token_raw_state_structure(tmp_store):
    """Verify the raw JSON structure has user_tokens nested per staff_id."""
    tmp_store.save_user_token("t-a", "r-a", 7200, staff_id="staff-a")
    tmp_store.save_user_token("t-b", "r-b", 7200, staff_id="staff-b")

    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    nested = data.get("user_tokens")
    assert isinstance(nested, dict), "user_tokens should be a dict"
    assert "staff-a" in nested
    assert "staff-b" in nested
    assert nested["staff-a"]["user_token"] == "t-a"
    assert nested["staff-b"]["user_token"] == "t-b"


def test_user_token_no_staff_id_still_writes_flat(tmp_store):
    """save_user_token without staff_id writes flat fields (backward compat)."""
    tmp_store.save_user_token("flat-ut", "flat-rt", 7200)
    got = tmp_store.load_user_token("")
    assert got["user_token"] == "flat-ut"
    assert got["refresh_token"] == "flat-rt"


def test_user_token_migration_cleans_stale_flat(tmp_store):
    """Issue #2: flat fields written by old SDK after migration are cleaned.

    1. SDK 1.6.14 writes nested user_tokens (no flat)
    2. Old SDK writes flat user_token + staff_id
    3. _migrate_user_tokens should merge flat into existing nested + clean flat
    """
    # 1. Normal nested save
    tmp_store.save_user_token("nested-ut", "nested-rt", 7200, staff_id="staff-1")

    # 2. Simulate old SDK writing flat fields on top of nested
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    data["user_token"] = "old-sdk-ut"
    data["refresh_token"] = "old-sdk-rt"
    data["staff_id"] = "staff-1"
    data["user_token_expiry"] = _NOW + 3600
    data["refresh_token_expiry"] = _NOW + 86400
    state = tmp_store._set_profile_data(state, data)
    tmp_store.save(state)

    # 3. Access triggers _migrate_user_tokens → should merge & clean
    got = tmp_store.load_user_token("staff-1")
    assert got["user_token"] == "old-sdk-ut", "flat value should override nested"
    assert got["refresh_token"] == "old-sdk-rt"

    # 4. Verify flat fields are gone from raw file
    state2 = tmp_store.load()
    data2 = tmp_store._get_profile_data(state2)
    assert "user_token" not in data2, "flat user_token should be cleaned"
    assert "staff_id" not in data2, "flat staff_id should be cleaned"

    # 5. nested entry should have the merged (flat) value
    nested = data2["user_tokens"]["staff-1"]
    assert nested["user_token"] == "old-sdk-ut"


def test_user_token_migration_noop_when_no_flat(tmp_store):
    """_migrate_user_tokens returns False and does nothing when no flat fields."""
    tmp_store.save_user_token("t-a", staff_id="staff-a")
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    # Force _migrate_user_tokens to run — nothing should change
    result = tmp_store._migrate_user_tokens(data)
    assert result is False, "no flat fields → no migration needed"


# ── list_user_tokens ──────────────────────────────────────────────

def test_list_user_tokens_empty(tmp_store):
    """list_user_tokens returns empty list when no users stored."""
    users = tmp_store.list_user_tokens()
    assert users == []


def test_list_user_tokens_single_user(tmp_store):
    """list_user_tokens returns single staff_id."""
    tmp_store.save_user_token("token1", "rt1", 7200, staff_id="staff1")
    users = tmp_store.list_user_tokens()
    assert "staff1" in users


def test_list_user_tokens_multiple_users(tmp_store):
    """list_user_tokens returns all staff_ids."""
    tmp_store.save_user_token("token1", "rt1", 7200, staff_id="staff1")
    tmp_store.save_user_token("token2", "rt2", 7200, staff_id="staff2")
    tmp_store.save_user_token("token3", "rt3", 7200, staff_id="staff3")
    users = tmp_store.list_user_tokens()
    assert len(users) == 3
    assert "staff1" in users
    assert "staff2" in users
    assert "staff3" in users


def test_list_user_tokens_legacy_flat_migrated(tmp_store):
    """list_user_tokens includes legacy flat user after auto-migration."""
    state = tmp_store.load()
    data = tmp_store._get_profile_data(state)
    data["user_token"] = "legacy-ut"
    data["staff_id"] = "legacy-staff"
    state = tmp_store._set_profile_data(state, data)
    tmp_store.save(state)

    tmp_store.load_user_token("")

    users = tmp_store.list_user_tokens()
    assert "legacy-staff" in users


def test_list_user_tokens_profile_isolation(tmp_store):
    """list_user_tokens only returns users from current profile."""
    store_alpha = CredentialStore(path=tmp_store.path, profile="alpha")
    store_beta = CredentialStore(path=tmp_store.path, profile="beta")

    store_alpha.save_user_token("t1", "rt1", 7200, staff_id="staff-a")
    store_beta.save_user_token("t2", "rt2", 7200, staff_id="staff-b")

    alpha_users = store_alpha.list_user_tokens()
    beta_users = store_beta.list_user_tokens()

    assert "staff-a" in alpha_users
    assert "staff-b" not in alpha_users
    assert "staff-b" in beta_users
    assert "staff-a" not in beta_users


# ── client get_user_token with staff_id ──────────────────────────

@pytest.mark.asyncio
async def test_client_get_user_token_with_staff_id():
    """Client can get user_token for specific staff_id."""
    import tempfile
    import os
    from lansenger_sdk import LansengerClient

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        store = CredentialStore(path=path)
        store.save_credentials("app123", "secret456")
        store.save_user_token("token-a", "rt-a", 7200, staff_id="staff-a")
        store.save_user_token("token-b", "rt-b", 7200, staff_id="staff-b")

        client = LansengerClient.from_store(path=path)

        token_a = await client.get_user_token(staff_id="staff-a")
        token_b = await client.get_user_token(staff_id="staff-b")

        assert token_a == "token-a"
        assert token_b == "token-b"
    finally:
        if os.path.exists(path):
            os.unlink(path)


@pytest.mark.asyncio
async def test_client_get_user_token_no_staff_id_backward_compat():
    """get_user_token() without staff_id returns first available token."""
    import tempfile
    import os
    from lansenger_sdk import LansengerClient

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        store = CredentialStore(path=path)
        store.save_credentials("app123", "secret456")
        store.save_user_token("token1", "rt1", 7200, staff_id="staff1")

        client = LansengerClient.from_store(path=path)

        token = await client.get_user_token()
        assert token == "token1"
    finally:
        if os.path.exists(path):
            os.unlink(path)


@pytest.mark.asyncio
async def test_client_set_user_tokens_with_staff_id():
    """Client can set user_token for specific staff_id."""
    import tempfile
    import os
    from lansenger_sdk import LansengerClient

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        store = CredentialStore(path=path)
        store.save_credentials("app123", "secret456")

        client = LansengerClient.from_store(path=path)
        client.set_user_tokens("token-c", "rt-c", 7200, staff_id="staff-c")

        loaded = store.load_user_token("staff-c")
        assert loaded["user_token"] == "token-c"
        assert loaded["refresh_token"] == "rt-c"
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ── identity_type persistence ────────────────────────────────────


def test_identity_type_round_trip(tmp_store):
    """save_identity_type / load_identity_type round-trip for all valid values."""
    assert tmp_store.load_identity_type() == ""
    for value in ("personal-bot", "org-app", "org-bot"):
        tmp_store.save_identity_type(value)
        assert tmp_store.load_identity_type() == value


def test_identity_type_invalid_raises_value_error(tmp_store):
    """save_identity_type rejects values outside VALID_IDENTITY_TYPES."""
    with pytest.raises(ValueError):
        tmp_store.save_identity_type("bad-value")
    assert tmp_store.load_identity_type() == ""


def test_identity_type_empty_string_clears(tmp_store):
    """Saving an empty string removes the field; load returns empty."""
    tmp_store.save_identity_type("org-app")
    tmp_store.save_identity_type("")
    assert tmp_store.load_identity_type() == ""
    state = tmp_store.load()
    assert "identity_type" not in state["profiles"]["default"]


def test_load_credentials_includes_identity_type(tmp_store):
    """load_credentials() returns an identity_type key (empty when unset)."""
    tmp_store.save_credentials("app123", "secret456")
    creds = tmp_store.load_credentials()
    assert creds["identity_type"] == ""
    tmp_store.save_identity_type("org-bot")
    creds = tmp_store.load_credentials()
    assert creds["identity_type"] == "org-bot"


def test_save_credentials_preserves_identity_type(tmp_store):
    """Rewriting credentials does not lose the stored identity_type."""
    tmp_store.save_identity_type("personal-bot")
    tmp_store.save_credentials("app-new", "secret-new", api_gateway_url="https://gw.example.com")
    assert tmp_store.load_identity_type() == "personal-bot"
    creds = tmp_store.load_credentials()
    assert creds["app_id"] == "app-new"
    assert creds["identity_type"] == "personal-bot"


def test_valid_identity_types_exported():
    """VALID_IDENTITY_TYPES is importable from the package root."""
    from lansenger_sdk import VALID_IDENTITY_TYPES
    assert VALID_IDENTITY_TYPES == ("personal-bot", "org-app", "org-bot")
