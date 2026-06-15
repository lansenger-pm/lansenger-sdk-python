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