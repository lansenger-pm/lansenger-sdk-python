"""Tests for Lansenger SDK personal apps (4.38) module functions."""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.personal_apps import (
    create_personal_app,
    update_personal_app,
    fetch_personal_app,
    delete_personal_app,
    fetch_personal_app_list,
)
from lansenger_sdk.models import PersonalAppCreateResult, PersonalAppInfoResult, PersonalAppListResult


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://open.e.lanxin.cn/open/apigw",
    )


def _mock_http_client(response_data):
    mock = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"errCode":0}'
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    mock.post.return_value = mock_response
    mock.get.return_value = mock_response
    mock.aclose = AsyncMock()
    return mock


# ── create_personal_app ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_personal_app_no_user_token():
    config = _make_config()
    result = await create_personal_app(config, app_token="tok", user_token="")
    assert result.success is False
    assert "user_token is required" in result.error


@pytest.mark.asyncio
async def test_create_personal_app_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"id": "app1", "secret": "sec1", "apigwAddr": "https://gw", "passportAddr": "https://pp"},
    })
    result = await create_personal_app(
        config, app_token="tok", user_token="utok", name="MyApp",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.app_id == "app1"
    assert result.secret == "sec1"


@pytest.mark.asyncio
async def test_create_personal_app_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 10005, "errMsg": "no permission"})
    result = await create_personal_app(config, app_token="tok", user_token="utok", http_client=mock_client)
    assert result.success is False


# ── update_personal_app ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_personal_app_no_app_id():
    config = _make_config()
    result = await update_personal_app(config, app_token="tok", app_id="", user_token="utok", name="n")
    assert result.success is False
    assert "app_id is required" in result.error


@pytest.mark.asyncio
async def test_update_personal_app_no_name():
    config = _make_config()
    result = await update_personal_app(config, app_token="tok", app_id="app1", user_token="utok", name="")
    assert result.success is False
    assert "name is required" in result.error


@pytest.mark.asyncio
async def test_update_personal_app_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "errMsg": "ok"})
    result = await update_personal_app(
        config, app_token="tok", app_id="app1", user_token="utok", name="NewName",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.app_id == "app1"


# ── fetch_personal_app ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_personal_app_no_app_id():
    config = _make_config()
    result = await fetch_personal_app(config, app_token="tok", app_id="", user_token="utok")
    assert result.success is False


@pytest.mark.asyncio
async def test_fetch_personal_app_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"name": "MyApp", "description": "desc", "apigwAddr": "https://gw", "passportAddr": "https://pp"},
    })
    result = await fetch_personal_app(config, app_token="tok", app_id="app1", user_token="utok", http_client=mock_client)
    assert result.success is True
    assert result.name == "MyApp"
    assert result.apigw_addr == "https://gw"


# ── delete_personal_app ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_personal_app_no_app_id():
    config = _make_config()
    result = await delete_personal_app(config, app_token="tok", app_id="", user_token="utok")
    assert result.success is False


@pytest.mark.asyncio
async def test_delete_personal_app_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "errMsg": "ok"})
    result = await delete_personal_app(config, app_token="tok", app_id="app1", user_token="utok", http_client=mock_client)
    assert result.success is True


# ── fetch_personal_app_list ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_personal_app_list_no_user_token():
    config = _make_config()
    result = await fetch_personal_app_list(config, app_token="tok", user_token="")
    assert result.success is False
    assert "user_token is required" in result.error


@pytest.mark.asyncio
async def test_fetch_personal_app_list_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {"appList": [{"appId": "a1", "appName": "App1", "description": "d1"}]},
    })
    result = await fetch_personal_app_list(config, app_token="tok", user_token="utok", http_client=mock_client)
    assert result.success is True
    assert result.app_list is not None
    assert len(result.app_list) == 1


# ── models to_dict ───────────────────────────────────────────────────

def test_personal_app_models_to_dict():
    r1 = PersonalAppCreateResult(success=True, app_id="a1", secret="s1").to_dict()
    assert r1["success"] is True
    assert r1["app_id"] == "a1"

    r2 = PersonalAppInfoResult(success=True, name="MyApp", apigw_addr="https://gw").to_dict()
    assert r2["success"] is True
    assert r2["name"] == "MyApp"

    r3 = PersonalAppListResult(success=True, app_list=[]).to_dict()
    assert r3["success"] is True
    assert r3["app_list"] == []
