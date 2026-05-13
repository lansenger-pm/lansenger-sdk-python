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
    state = tmp_store.load()
    assert state["app_id"] == "app1"
    assert state["app_secret"] == "secret1"
    assert state["api_gateway_url"] == "https://gw.example.com"
    assert state["passport_url"] == "https://pp.example.com"
    assert state["app_token"] == "token1"


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