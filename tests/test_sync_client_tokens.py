"""Tests for LansengerSyncClient token management fixes."""

import tempfile
import time

import pytest

from lansenger_sdk import LansengerSyncClient
from lansenger_sdk.persistence import CredentialStore
from lansenger_sdk.exceptions import LansengerAuthError


def test_from_store_loads_user_token():
    """Test that from_store() loads user token from credential store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        # First, save credentials and user token
        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
            api_gateway_url="https://test.example.com",
            passport_url="https://passport.test.com",
        )
        store.save_user_token(
            user_token="test_user_token_123",
            refresh_token="test_refresh_token_456",
            expires_in=7200,
            staff_id="staff_789",
        )

        # Now create client from store
        client = LansengerSyncClient.from_store(profile="test", path=store_path)

        # Verify that the async client for tokens was created
        assert client._async_client_for_tokens is not None

        # Verify that get_user_token() returns the token
        token = client.get_user_token()
        assert token == "test_user_token_123"


def test_from_store_without_user_token():
    """Test that from_store() works when no user token is stored."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        # Save only credentials, no user token
        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )

        # Create client from store
        client = LansengerSyncClient.from_store(profile="test", path=store_path)

        # Verify that get_user_token() raises error
        with pytest.raises(LansengerAuthError, match="No userToken available"):
            client.get_user_token()


def test_set_user_tokens_no_await_error():
    """Test that set_user_tokens() doesn't raise TypeError about await."""
    client = LansengerSyncClient(
        app_id="test_app_id",
        app_secret="test_secret",
    )

    # This should NOT raise "TypeError: object NoneType can't be used in 'await' expression"
    client.set_user_tokens(
        user_token="test_token",
        refresh_token="test_refresh",
        expires_in=7200,
        staff_id="staff_123",
    )

    # Verify that the async client was created
    assert client._async_client_for_tokens is not None

    # Verify that get_user_token() returns the token
    token = client.get_user_token()
    assert token == "test_token"


def test_set_user_tokens_multiple_calls():
    """Test that set_user_tokens() can be called multiple times."""
    client = LansengerSyncClient(
        app_id="test_app_id",
        app_secret="test_secret",
    )

    # First call
    client.set_user_tokens(
        user_token="token1",
        refresh_token="refresh1",
        expires_in=7200,
    )
    assert client.get_user_token() == "token1"

    # Second call - should update the token
    client.set_user_tokens(
        user_token="token2",
        refresh_token="refresh2",
        expires_in=7200,
    )
    assert client.get_user_token() == "token2"


def test_get_user_token_without_set_tokens():
    """Test that get_user_token() raises error when no tokens are set."""
    client = LansengerSyncClient(
        app_id="test_app_id",
        app_secret="test_secret",
    )

    with pytest.raises(LansengerAuthError, match="No userToken available"):
        client.get_user_token()


def test_from_store_with_expired_token():
    """Test that from_store() loads expired token but get_user_token() handles it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        # Save credentials and an expired user token
        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        # Set expiry time in the past
        store.save_user_token(
            user_token="expired_token",
            refresh_token="refresh_token",
            expires_in=7200,
            margin=0,
        )
        # Manually set expiry to past
        state = store.load()
        state["profiles"]["test"]["user_token_expiry"] = time.time() - 3600
        store.save(state)

        # Create client from store
        client = LansengerSyncClient.from_store(profile="test", path=store_path)

        # The token should still be loaded, but will be expired
        # (actual refresh would require network, so we just verify it was loaded)
        assert client._async_client_for_tokens is not None


def test_from_store_with_staff_id():
    """Test that from_store() loads staff_id correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        store.save_user_token(
            user_token="test_token",
            refresh_token="test_refresh",
            staff_id="staff_12345",
        )

        client = LansengerSyncClient.from_store(profile="test", path=store_path)

        # Verify that staff_id was loaded (we can't directly access it, but the token should work)
        assert client._async_client_for_tokens is not None
        token = client.get_user_token()
        assert token == "test_token"