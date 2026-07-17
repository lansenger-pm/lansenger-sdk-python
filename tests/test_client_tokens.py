"""Tests for LansengerClient (async) get_user_token error paths.

These tests cover the async client's get_user_token(staff_id=...) code paths
that were not tested and allowed the missing LansengerAuthError import bug
to slip through.
"""

import os
import tempfile

import pytest

from lansenger_sdk import LansengerClient
from lansenger_sdk.persistence import CredentialStore
from lansenger_sdk.exceptions import LansengerAuthError


@pytest.mark.asyncio
async def test_async_client_get_user_token_no_store():
    """get_user_token(staff_id=...) without a store should raise LansengerAuthError."""
    client = LansengerClient(app_id="test_id", app_secret="test_secret")

    with pytest.raises(LansengerAuthError, match="CredentialStore is required"):
        await client.get_user_token(staff_id="some-user")


@pytest.mark.asyncio
async def test_async_client_get_user_token_no_token():
    """get_user_token(staff_id=...) with store but no token for that staff_id
    should raise LansengerAuthError."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        store = CredentialStore(path=path)
        store.save_credentials("test_app", "test_secret")

        client = LansengerClient.from_store(path=path)

        with pytest.raises(
            LansengerAuthError,
            match="No userToken available",
        ):
            await client.get_user_token(staff_id="missing-user")
    finally:
        if os.path.exists(path):
            os.unlink(path)


@pytest.mark.asyncio
async def test_async_client_get_user_token_with_valid_token():
    """get_user_token(staff_id=...) with a valid (non-expired) user token
    should return the token string."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    os.unlink(path)

    try:
        store = CredentialStore(path=path)
        store.save_credentials("test_app", "test_secret")
        store.save_user_token(
            "valid-user-token",
            refresh_token="valid-refresh",
            expires_in=7200,
            staff_id="valid-user",
        )

        client = LansengerClient.from_store(path=path)

        token = await client.get_user_token(staff_id="valid-user")
        assert token == "valid-user-token"
    finally:
        if os.path.exists(path):
            os.unlink(path)
