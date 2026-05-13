"""Tests for Lansenger SDK exceptions."""

from lansenger_sdk.exceptions import (
    LansengerError,
    LansengerAuthError,
    LansengerConfigError,
    LansengerAPIError,
    LansengerNetworkError,
    LansengerFileError,
)


def test_base_error():
    err = LansengerError("base error")
    assert str(err) == "base error"
    assert err.err_code is None
    assert err.retryable is False


def test_auth_error():
    err = LansengerAuthError("auth failed", err_code=401)
    assert str(err) == "auth failed"
    assert err.err_code == 401
    assert err.retryable is False


def test_config_error():
    err = LansengerConfigError("missing credentials")
    assert str(err) == "missing credentials"
    assert err.retryable is False


def test_api_error():
    err = LansengerAPIError("api error", err_code=10001, retryable=True)
    assert str(err) == "api error"
    assert err.err_code == 10001
    assert err.retryable is True


def test_network_error():
    err = LansengerNetworkError("timeout", retryable=True)
    assert str(err) == "timeout"
    assert err.retryable is True


def test_file_error():
    err = LansengerFileError("file not found")
    assert str(err) == "file not found"
    assert err.retryable is False


def test_exception_hierarchy():
    assert issubclass(LansengerAuthError, LansengerError)
    assert issubclass(LansengerConfigError, LansengerError)
    assert issubclass(LansengerAPIError, LansengerError)
    assert issubclass(LansengerNetworkError, LansengerError)
    assert issubclass(LansengerFileError, LansengerError)