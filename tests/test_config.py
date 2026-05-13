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