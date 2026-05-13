"""Tests for Lansenger SDK OAuth2 authorization flow."""

import os

import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.constants import OAUTH2_SCOPE_BASIC_USER_INFO
from lansenger_sdk.exceptions import LansengerConfigError
from lansenger_sdk.oauth import (
    build_authorize_url,
    parse_authorize_callback,
    validate_callback_state,
)


def test_build_authorize_url_basic():
    config = LansengerConfig(
        app_id="3064064-123456",
        app_secret="secret",
        passport_url="https://passport-test.test.com",
    )
    url = build_authorize_url(config, redirect_uri="http://localhost:8080")
    assert "passport-test.test.com/oauth2/authorize" in url
    assert "appid=3064064-123456" in url
    assert "response_type=code" in url
    assert "scope=basic_userinfor" in url
    assert "redirect_uri=http" in url
    assert "state=" in url


def test_build_authorize_url_with_state():
    config = LansengerConfig(
        app_id="myapp",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    url = build_authorize_url(
        config,
        redirect_uri="https://myapp.com/callback",
        state="3da9d9f1-6756-11ea-8b95-0242ac115010",
    )
    assert "state=3da9d9f1-6756-11ea-8b95-0242ac115010" in url


def test_build_authorize_url_custom_scope():
    config = LansengerConfig(
        app_id="myapp",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    url = build_authorize_url(
        config,
        redirect_uri="https://myapp.com/callback",
        scope="custom_scope",
    )
    assert "scope=custom_scope" in url


def test_build_authorize_url_multiple_scopes():
    config = LansengerConfig(
        app_id="myapp",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    url = build_authorize_url(
        config,
        redirect_uri="https://myapp.com/callback",
        scope=["basic_userinfor", "custom_scope"],
    )
    assert "scope=basic_userinfor%2Ccustom_scope" in url


def test_build_authorize_url_no_passport_raises():
    config = LansengerConfig(
        app_id="myapp",
        app_secret="secret",
        passport_url="",
    )
    with pytest.raises(LansengerConfigError, match="passport_url"):
        build_authorize_url(config, redirect_uri="https://myapp.com/callback")


def test_build_authorize_url_from_env():
    os.environ["LANSENGER_APP_ID"] = "env_app"
    os.environ["LANSENGER_APP_SECRET"] = "env_secret"
    os.environ["LANSENGER_PASSPORT_URL"] = "https://passport-env.test.com"
    try:
        config = LansengerConfig.from_env()
        url = build_authorize_url(config, redirect_uri="http://localhost:8080")
        assert "passport-env.test.com/oauth2/authorize" in url
        assert "appid=env_app" in url
    finally:
        os.environ.pop("LANSENGER_APP_ID", None)
        os.environ.pop("LANSENGER_APP_SECRET", None)
        os.environ.pop("LANSENGER_PASSPORT_URL", None)


def test_parse_callback_from_dict():
    result = parse_authorize_callback({
        "code": "4d32b46d-3e88-44b2-9c7a-903ac638fcfb",
        "state": "572ca2d8-4383-11eb-96e3-0242ac11e605",
    })
    assert result["code"] == "4d32b46d-3e88-44b2-9c7a-903ac638fcfb"
    assert result["state"] == "572ca2d8-4383-11eb-96e3-0242ac11e605"


def test_parse_callback_from_query_string():
    result = parse_authorize_callback(
        "code=4d32b46d-3e88-44b2-9c7a-903ac638fcfb&state=572ca2d8-4383-11eb-96e3-0242ac11e605"
    )
    assert result["code"] == "4d32b46d-3e88-44b2-9c7a-903ac638fcfb"
    assert result["state"] == "572ca2d8-4383-11eb-96e3-0242ac11e605"


def test_parse_callback_with_leading_question_mark():
    result = parse_authorize_callback(
        "?code=abc123&state=xyz789"
    )
    assert result["code"] == "abc123"
    assert result["state"] == "xyz789"


def test_parse_callback_with_error():
    result = parse_authorize_callback({
        "error": "access_denied",
        "error_description": "User denied authorization",
        "state": "some_state",
    })
    assert result["error"] == "access_denied"
    assert result["error_description"] == "User denied authorization"
    assert result["code"] == ""


def test_validate_callback_state_match():
    assert validate_callback_state("abc123", "abc123") is True


def test_validate_callback_state_no_match():
    assert validate_callback_state("abc123", "different_state") is False


def test_client_build_authorize_url():
    from lansenger_sdk import LansengerClient

    client = LansengerClient(
        app_id="myapp",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")
    assert "passport.example.com/oauth2/authorize" in url
    assert "appid=myapp" in url


def test_client_build_authorize_url_no_passport_raises():
    from lansenger_sdk import LansengerClient

    client = LansengerClient(app_id="myapp", app_secret="secret")
    with pytest.raises(LansengerConfigError):
        client.build_authorize_url(redirect_uri="https://myapp.com/callback")


def test_sync_client_build_authorize_url():
    from lansenger_sdk import LansengerSyncClient

    client = LansengerSyncClient(
        app_id="myapp",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    url = client.build_authorize_url(redirect_uri="https://myapp.com/callback")
    assert "passport.example.com/oauth2/authorize" in url


def test_config_has_passport_url():
    config = LansengerConfig(
        app_id="id",
        app_secret="secret",
        passport_url="https://passport.example.com",
    )
    assert config.has_passport_url() is True

    config_no_passport = LansengerConfig(
        app_id="id",
        app_secret="secret",
        passport_url="",
    )
    assert config_no_passport.has_passport_url() is False


def test_exchange_code_validation_no_code():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(success=False, error="code is required")
    assert result.success is False
    assert "code is required" in result.error


def test_exchange_code_validation_no_app_token():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(success=False, error="app_token is required")
    assert result.success is False
    assert "app_token is required" in result.error


def test_user_token_result_model():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(
        success=True,
        user_token="db501ca9-fe6c-11ec-8747-be04fc88dec5",
        expires_in=7200,
        refresh_token="1cf4a0b2-fe6d-11ec-8b9d-62bb1295b923",
        refresh_expires_in=2592000,
        staff_id="524288-abcedfghigklmn",
        scope="basic_userinfor",
        state="fa8a0a63-fe6c-11ec-9438-162619e741e0",
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["user_token"] == "db501ca9-fe6c-11ec-8747-be04fc88dec5"
    assert d["expires_in"] == 7200
    assert d["refresh_token"] == "1cf4a0b2-fe6d-11ec-8b9d-62bb1295b923"
    assert d["refresh_expires_in"] == 2592000
    assert d["staff_id"] == "524288-abcedfghigklmn"


def test_user_token_result_error():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(
        success=False,
        error="API error (errCode=10001): invalid code",
    )
    d = result.to_dict()
    assert d["success"] is False
    assert d["error"] == "API error (errCode=10001): invalid code"
    assert "user_token" not in d


def test_refresh_token_validation():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(success=False, error="refresh_token is required")
    assert result.success is False
    assert "refresh_token is required" in result.error

    result = UserTokenResult(success=False, error="app_token is required")
    assert result.success is False
    assert "app_token is required" in result.error


def test_refresh_token_success_model():
    from lansenger_sdk.models import UserTokenResult

    result = UserTokenResult(
        success=True,
        user_token="e3474e95-fe6c-11ec-979d-fa55fbd6fc61",
        expires_in=7200,
        refresh_token="db9c959f-fe6c-11ec-8747-be04fc88dec5",
        refresh_expires_in=1792360,
        staff_id="524-ADAFSFD87F",
        scope="scope1,scope2",
        state="STATE0x8765",
    )
    d = result.to_dict()
    assert d["user_token"] == "e3474e95-fe6c-11ec-979d-fa55fbd6fc61"
    assert d["refresh_token"] == "db9c959f-fe6c-11ec-8747-be04fc88dec5"
    assert d["refresh_expires_in"] == 1792360


def test_user_info_result_model():
    from lansenger_sdk.models import UserInfoResult

    result = UserInfoResult(
        success=True,
        staff_id="788-59",
        name="张三",
        org_id="788",
        org_name="组织名称",
        avatar_url="http://路径",
        avatar_id="788-3456",
        mobile_phone={"countryCode": "86", "number": "12345678902"},
        email="email@test.com",
        employee_number="A00001",
        login_name="login001",
        external_id="zhangsan01",
        department=[{"id": "524288-3145728", "name": "core"}],
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["staff_id"] == "788-59"
    assert d["name"] == "张三"
    assert d["org_id"] == "788"
    assert d["org_name"] == "组织名称"
    assert d["email"] == "email@test.com"
    assert d["employee_number"] == "A00001"
    assert d["login_name"] == "login001"
    assert d["external_id"] == "zhangsan01"
    assert d["mobile_phone"]["countryCode"] == "86"
    assert d["department"][0]["name"] == "core"


def test_user_info_result_error():
    from lansenger_sdk.models import UserInfoResult

    result = UserInfoResult(success=False, error="user_token is required")
    d = result.to_dict()
    assert d["success"] is False
    assert d["error"] == "user_token is required"
    assert "staff_id" not in d


def test_constants_oauth2_refresh_endpoint():
    from lansenger_sdk.constants import API_ENDPOINTS

    assert "refresh_token_create" in API_ENDPOINTS["oauth2"]
    assert API_ENDPOINTS["oauth2"]["refresh_token_create"] == "/v1/refresh_token/create"


def test_constants_users_fetch_endpoint():
    from lansenger_sdk.constants import API_ENDPOINTS

    assert "users" in API_ENDPOINTS
    assert "fetch" in API_ENDPOINTS["users"]
    assert API_ENDPOINTS["users"]["fetch"] == "/v1/users/fetch"