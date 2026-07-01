"""Tests for Lansenger SDK config module."""

import os

import pytest

from lansenger_sdk.config import LansengerConfig, DEFAULT_API_GATEWAY_URL
from lansenger_sdk.exceptions import LansengerConfigError


def test_config_from_direct_params():
    config = LansengerConfig.create(app_id="test_id", app_secret="test_secret")
    assert config.app_id == "test_id"
    assert config.app_secret == "test_secret"
    assert config.api_gateway_url == DEFAULT_API_GATEWAY_URL
    assert config.http_timeout == 30.0


def test_config_from_direct_params_with_gateway():
    config = LansengerConfig.create(
        app_id="test_id",
        app_secret="test_secret",
        api_gateway_url="https://custom.gateway.com/api",
        http_timeout=60.0,
    )
    assert config.api_gateway_url == "https://custom.gateway.com/api"
    assert config.http_timeout == 60.0


def test_config_from_env_vars():
    os.environ["LANSENGER_APP_ID"] = "env_id"
    os.environ["LANSENGER_APP_SECRET"] = "env_secret"
    try:
        config = LansengerConfig.from_env()
        assert config.app_id == "env_id"
        assert config.app_secret == "env_secret"
    finally:
        os.environ.pop("LANSENGER_APP_ID", None)
        os.environ.pop("LANSENGER_APP_SECRET", None)


def test_config_missing_credentials_raises():
    os.environ.pop("LANSENGER_APP_ID", None)
    os.environ.pop("LANSENGER_APP_SECRET", None)
    with pytest.raises(LansengerConfigError):
        LansengerConfig.create()


def test_config_env_overridden_by_direct_params():
    os.environ["LANSENGER_APP_ID"] = "env_id"
    os.environ["LANSENGER_APP_SECRET"] = "env_secret"
    try:
        config = LansengerConfig.create(app_id="direct_id", app_secret="direct_secret")
        assert config.app_id == "direct_id"
        assert config.app_secret == "direct_secret"
    finally:
        os.environ.pop("LANSENGER_APP_ID", None)
        os.environ.pop("LANSENGER_APP_SECRET", None)


def test_config_is_configured():
    config = LansengerConfig.create(app_id="test_id", app_secret="test_secret")
    assert config.is_configured() is True

    empty_config = LansengerConfig(app_id="", app_secret="")
    assert empty_config.is_configured() is False


def test_external_mode_with_app_token_only():
    """External mode: app_token alone is sufficient, no app_id/app_secret needed."""
    config = LansengerConfig.create(app_token="external_token_123")
    assert config.app_token == "external_token_123"
    assert config.is_external_mode() is True
    assert config.is_configured() is False  # no app_id/app_secret
    assert config.api_gateway_url == DEFAULT_API_GATEWAY_URL


def test_external_mode_with_app_token_env_var():
    """LANSENGER_APP_TOKEN env var triggers external mode."""
    os.environ["LANSENGER_APP_TOKEN"] = "env_token"
    try:
        config = LansengerConfig.create()
        assert config.app_token == "env_token"
        assert config.is_external_mode() is True
    finally:
        os.environ.pop("LANSENGER_APP_TOKEN", None)


def test_external_mode_optional_credentials():
    """app_token + app_id/app_secret together: external mode is True, is_configured is also True."""
    config = LansengerConfig.create(app_id="a", app_secret="s", app_token="tok")
    assert config.is_external_mode() is True
    assert config.is_configured() is True


def test_user_token_field():
    config = LansengerConfig.create(app_id="a", app_secret="s", user_token="user_tok_123")
    assert config.user_token == "user_tok_123"


def test_user_token_env_var():
    os.environ["LANSENGER_USER_TOKEN"] = "env_user"
    try:
        config = LansengerConfig.create(app_id="a", app_secret="s")
        assert config.user_token == "env_user"
    finally:
        os.environ.pop("LANSENGER_USER_TOKEN", None)


def test_still_requires_credentials_without_app_token():
    """Without app_token, missing app_id/app_secret still raises."""
    os.environ.pop("LANSENGER_APP_ID", None)
    os.environ.pop("LANSENGER_APP_SECRET", None)
    os.environ.pop("LANSENGER_APP_TOKEN", None)
    with pytest.raises(LansengerConfigError):
        LansengerConfig.create()