"""Tests for the OAuth2 device flow (device_authorization / device_token)."""

import asyncio
import json

import httpx
import pytest

from lansenger_sdk import __version__
from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.models import DeviceAuthorizationResult, DevicePollResult
from lansenger_sdk.oauth import (
    DEVICE_SOURCE_WHITELIST,
    poll_device_token,
    request_device_authorization,
)

CONFIG = LansengerConfig(
    app_id="1234-5678",
    app_secret="test-secret",
    passport_url="https://pp.example.com",
    api_gateway_url="https://gw.example.com",
)

AUTH_OK = {
    "deviceCode": "a" * 40,
    "userCode": "WDJB-MJHT",
    "verificationUriComplete": "https://pp.example.com/oauth/device_verify?user_code=WDJB-MJHT",
    "interval": 5,
    "expiresIn": 600,
    "expiresAt": 1791864291,
    "openApiDomain": "https://gw.example.com",
}


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _run(coro):
    return asyncio.run(coro)


def test_authorization_success_maps_fields():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=AUTH_OK)

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert isinstance(result, DeviceAuthorizationResult)
    assert result.success
    assert result.device_code == "a" * 40
    assert result.user_code == "WDJB-MJHT"
    assert result.verification_uri_complete.startswith("https://pp.example.com/oauth/device_verify")
    assert result.interval == 5
    assert result.expires_in == 600
    assert result.expires_at == 1791864291
    assert result.open_api_domain == "https://gw.example.com"
    assert result.error is None and result.error_type is None
    assert seen["url"] == "https://pp.example.com/oauth2/device_authorization"
    assert seen["body"]["responseType"] == "device_code"
    assert seen["body"]["scope"] == "basic_userinfor"
    assert seen["body"]["appId"] == "1234-5678"
    assert seen["body"]["from"] == "CLI"
    assert seen["body"]["version"] == __version__


def test_authorization_client_id_defaults_to_app_id():
    def handler(request: httpx.Request) -> httpx.Response:
        seen = json.loads(request.content)
        assert seen["clientId"] == "1234-5678"
        return httpx.Response(200, json=AUTH_OK)

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert result.success


def test_authorization_custom_source_and_version():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["from"] == "MCP"
        assert body["version"] == "9.9.9"
        return httpx.Response(200, json=AUTH_OK)

    result = _run(
        request_device_authorization(
            CONFIG, source="MCP", version="9.9.9", http_client=_client(handler)
        )
    )
    assert result.success


def test_authorization_invalid_app_id_rejected_before_http():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("HTTP must not be called on validation failure")

    config = LansengerConfig(app_id="badid", app_secret="test-secret", passport_url="https://pp.example.com")
    result = _run(request_device_authorization(config, http_client=_client(handler)))
    assert not result.success
    assert result.error is not None and "appId" in result.error


def test_authorization_invalid_source_rejected():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("HTTP must not be called on validation failure")

    result = _run(
        request_device_authorization(CONFIG, source="WorkBuddy", http_client=_client(handler))
    )
    assert not result.success
    assert "WorkBuddy" in result.error
    assert DEVICE_SOURCE_WHITELIST == ("AutoClaw", "CLI", "OpenClaw", "MCP")


def test_authorization_404_classified_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="")

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"
    assert "404" in result.error


def test_authorization_errcode_envelope_classified_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errCode": -5, "errMsg": "API 请求路径错误(4981)"})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"
    assert "-5" in result.error


def test_authorization_error_envelope_is_api_error_not_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"code": 9000, "message": "参数错误", "detail": None}})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type is None
    assert "9000" in result.error


def test_authorization_redirect_classified_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "https://pp.example.com/login"})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_authorization_html_body_classified_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>login page</html>")

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_poll_pending_is_success_without_code():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body == {"deviceCode": "a" * 40, "clientId": "1234-5678"}
        return httpx.Response(200, json={"state": "authorization_pending"})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert isinstance(result, DevicePollResult)
    assert result.success
    assert result.state == "authorization_pending"
    assert result.oauth2_code is None


def test_poll_approved_returns_oauth2_code():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"oauth2Code": "c" * 36, "state": "access_approved"})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert result.success
    assert result.state == "access_approved"
    assert result.oauth2_code == "c" * 36


def test_poll_denied_is_failure_with_state():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "access_denied"})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert result.state == "access_denied"
    assert result.error_type is None


def test_poll_expired_requests_reauthorization():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "expired_token"})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert result.state == "expired_token"


def test_poll_unknown_state_is_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "something_new"})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert "something_new" in result.error


def test_poll_9004_is_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"code": 9004, "message": "请求不合法"}})

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert result.error_type is None
    assert "9004" in result.error


def test_poll_404_classified_unsupported():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="")

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_poll_requires_device_code():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("HTTP must not be called on validation failure")

    result = _run(poll_device_token(CONFIG, "", http_client=_client(handler)))
    assert not result.success
    assert "device_code" in result.error


def test_sync_client_validation_short_circuit():
    from lansenger_sdk import LansengerSyncClient

    client = LansengerSyncClient(
        app_id="badid", app_secret="test-secret", passport_url="https://pp.example.com"
    )
    result = client.request_device_authorization()
    assert not result.success
    assert result.error is not None


def test_sync_ephemeral_call_passes_passport_url(monkeypatch):
    """P0 regression: _ephemeral_call must forward passport_url, else the
    stored-credential path (CLI get_client) loses the device base URL."""
    from lansenger_sdk import sync_client as sc

    captured = {}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def request_device_authorization(self, **kwargs):
            return DeviceAuthorizationResult(success=True, device_code="d" * 40)

        async def close(self):
            pass

    monkeypatch.setattr(sc, "LansengerClient", FakeAsyncClient)
    client = sc.LansengerSyncClient(
        app_id="1234-5678", app_secret="test-secret", passport_url="https://pp.example.com"
    )
    result = client.request_device_authorization()
    assert result.success
    assert captured.get("passport_url") == "https://pp.example.com"


def test_authorization_conflict_shape_errcode_wins_over_devicecode():
    """200 + deviceCode + errCode simultaneously → errCode priority → unsupported."""
    def handler(request: httpx.Request) -> httpx.Response:
        body = dict(AUTH_OK)
        body["errCode"] = -1
        return httpx.Response(200, json=body)

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_authorization_200_with_error_envelope_is_unsupported():
    """Row 6: HTTP 200 + {error:{...}} without deviceCode → conservative unsupported."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": {"code": 9000, "message": "参数错误"}})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_authorization_unknown_error_code_is_unsupported():
    """400 + unknown code (not in the known set) → row 6, not row 5."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"code": 9999, "message": "mystery"}})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"


def test_poll_debug_log_never_contains_oauth2_code(caplog):
    import logging

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"oauth2Code": "c" * 36, "state": "access_approved"})

    with caplog.at_level(logging.DEBUG, logger="lansenger_sdk.oauth"):
        _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert ("c" * 36) not in caplog.text


def test_debug_log_never_contains_device_code(caplog):
    import logging

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=AUTH_OK)

    with caplog.at_level(logging.DEBUG, logger="lansenger_sdk.oauth"):
        _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert ("a" * 40) not in caplog.text
    assert "WDJB-MJHT" not in caplog.text


@pytest.mark.parametrize(
    "body",
    [{"error": "invalid_client"}, {"error": None}, {"error": ["x"]}],
    ids=["string", "null", "list"],
)
def test_authorization_standard_oauth_error_body_is_api_error_not_crash(body):
    """RFC 6749 §5.2 puts a plain string in `error`; must not raise AttributeError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=body)

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type is None
    assert "API error" in result.error
    assert result.device_code is None


@pytest.mark.parametrize(
    "body",
    [{"error": "invalid_client"}, {"error": None}, {"error": ["x"]}],
    ids=["string", "null", "list"],
)
def test_poll_standard_oauth_error_body_is_api_error_not_crash(body):
    """Same guard on the poll side: a string/null/list `error` must not raise."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=body)

    result = _run(poll_device_token(CONFIG, "a" * 40, http_client=_client(handler)))
    assert not result.success
    assert result.error_type is None
    assert "API error" in result.error


def test_authorization_400_without_error_key_stays_unsupported():
    """Row 6 unchanged: a JSON body with no `error` key stays in the conservative bucket."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "bad request"})

    result = _run(request_device_authorization(CONFIG, http_client=_client(handler)))
    assert not result.success
    assert result.error_type == "deviceflow_unsupported"
