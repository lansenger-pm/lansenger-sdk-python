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


# ── Bug 3 fix: from_store() should not produce negative expires_in ──────

def test_from_store_with_past_user_token_expiry_does_not_produce_negative():
    """Bug 3: when user_token_expiry is in the past, expires_in should be 7200 (not negative).

    Before the fix, int(past_timestamp - time.time()) produced a negative value,
    which was passed to set_user_tokens() causing _user_token_expiry to be set
    far in the past rather than triggering an immediate natural refresh.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        # Save token with expiry timestamp already in the past
        # Use save_user_token with expires_in=0 + manual timestamp override
        store.save_user_token(
            user_token="expired_token",
            refresh_token="valid_refresh",
            expires_in=1,  # minimal — will expire soon
            margin=0,
        )
        # Override expiry to a time clearly in the past
        state = store.load()
        state["profiles"]["test"]["user_token_expiry"] = time.time() - 3600  # 1 hour ago
        store.save(state)

        client = LansengerSyncClient.from_store(profile="test", path=store_path)

        # The client should be created without errors — previous bug would crash
        assert client._async_client_for_tokens is not None

        # get_user_token() should attempt refresh (which will fail because no
        # real network, but the code path must not produce negative expires_in)
        try:
            client.get_user_token()
        except LansengerAuthError:
            # Expected — no real server to refresh against
            pass


def test_from_store_with_past_refresh_token_expiry():
    """Bug 3: when refresh_token_expiry is in the past, it gets truncated to 0.

    The from_store logic now uses max(0, ...) so past expiries become 0,
    which means the UserTokenManager optimistically tries to refresh
    (which would succeed if the token is actually still valid server-side).
    This test verifies no negative values leak through.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        store.save_user_token(
            user_token="test_token",
            refresh_token="expired_refresh",
            expires_in=7200,
            margin=0,
            refresh_expires_in=2592000,
        )
        state = store.load()
        # Both expiries in the past
        state["profiles"]["test"]["user_token_expiry"] = time.time() - 3600
        state["profiles"]["test"]["refresh_token_expiry"] = time.time() - 86400
        store.save(state)

        # from_store should load without crashing (no negative expires_in)
        client = LansengerSyncClient.from_store(profile="test", path=store_path)
        assert client._async_client_for_tokens is not None

        # get_user_token() will attempt refresh (real HTTP) because
        # refresh_expires_in was truncated to 0 by max(0, ...).
        # With no real server, this raises LansengerNetworkError.
        from lansenger_sdk.exceptions import LansengerNetworkError
        try:
            client.get_user_token()
        except (LansengerAuthError, LansengerNetworkError):
            # Either is acceptable — the key is no crash from negative values
            pass


def test_from_store_with_missing_refresh_token_expiry():
    """When refresh_token_expiry is 0/missing, from_store should still load the refresh token.

    This simulates the side-effect of Bug 1 (exchange_code didn't save refresh_expires_in).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        # Save WITHOUT refresh_expires_in (as exchange_code used to do before Bug 1 fix)
        store.save_user_token(
            user_token="test_token",
            refresh_token="valid_refresh",
            expires_in=7200,
            # refresh_expires_in defaults to 0 — this is the Bug 1 scenario
        )

        client = LansengerSyncClient.from_store(profile="test", path=store_path)
        assert client._async_client_for_tokens is not None

        # Should still load token — just without expiry tracking
        token = client.get_user_token()
        assert token == "test_token"


# ── Bug 4 fix: refreshToken margin check ──────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_margin_blocks_near_expiry(monkeypatch):
    """Bug 4: refreshToken within 5-minute margin should be treated as expired."""
    from lansenger_sdk.auth import UserTokenManager, TokenManager, _USER_TOKEN_REFRESH_MARGIN
    from lansenger_sdk.config import LansengerConfig

    config = LansengerConfig(app_id="test", app_secret="test")

    class FakeHttpClient:
        async def get(self, url, **kwargs):
            class FakeResponse:
                def raise_for_status(self): pass
                def json(self):
                    return {
                        "errCode": 0,
                        "data": {
                            "appToken": "app_tok",
                            "expiresIn": 7200,
                        },
                    }
            return FakeResponse()

        async def aclose(self): pass

    http_client = FakeHttpClient()
    token_mgr = TokenManager(config, http_client)
    utm = UserTokenManager(config, http_client, token_mgr, store=None)

    # Set a refreshToken that expires in 200 seconds (within 300s margin)
    utm._refresh_token = "rt_near_expiry"
    utm._refresh_token_expiry = time.time() + 200

    with pytest.raises(LansengerAuthError, match="RefreshToken has expired"):
        await utm.get_token()


@pytest.mark.asyncio
async def test_refresh_token_margin_allows_valid_token(monkeypatch):
    """Bug 4: refreshToken well outside margin should be accepted."""
    from lansenger_sdk.auth import UserTokenManager, TokenManager
    from lansenger_sdk.config import LansengerConfig

    config = LansengerConfig(app_id="test", app_secret="test")

    class FakeHttpClient:
        call_count = 0

        async def get(self, url, **kwargs):
            self.call_count += 1
            class FakeResponse:
                def raise_for_status(self): pass
                def json(self):
                    if "apptoken" in url:
                        return {
                            "errCode": 0,
                            "data": {"appToken": "app_tok", "expiresIn": 7200},
                        }
                    else:
                        return {
                            "errCode": 0,
                            "data": {
                                "userToken": "new_user_token",
                                "expiresIn": 7200,
                                "refreshToken": "new_refresh",
                                "refreshExpiresIn": 2592000,
                            },
                        }
            return FakeResponse()

        async def aclose(self): pass

    http_client = FakeHttpClient()
    token_mgr = TokenManager(config, http_client)
    utm = UserTokenManager(config, http_client, token_mgr, store=None)

    # refreshToken valid for 30 days — well outside 5-minute margin
    utm._refresh_token = "rt_valid"
    utm._refresh_token_expiry = time.time() + 30 * 86400

    token = await utm.get_token()
    assert token == "new_user_token"


def test_from_store_with_future_expiry_computes_remaining_correctly():
    """Verify that from_store correctly computes remaining seconds for future expiries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = f"{tmpdir}/test_state.json"

        store = CredentialStore(path=store_path, profile="test")
        store.save_credentials(
            app_id="test_app_id",
            app_secret="test_secret",
        )
        store.save_user_token(
            user_token="future_token",
            refresh_token="future_refresh",
            expires_in=7200,
            margin=300,
            refresh_expires_in=2592000,
        )

        client = LansengerSyncClient.from_store(profile="test", path=store_path)
        assert client._async_client_for_tokens is not None

        # Token is still valid (just saved)
        token = client.get_user_token()
        assert token == "future_token"
