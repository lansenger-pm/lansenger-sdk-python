"""Tests for Lansenger SDK bot commands (4.37) module functions."""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.bot_commands import create_bot_commands, fetch_bot_commands, delete_bot_commands
from lansenger_sdk.models import BotCommandResult, BotCommandQueryResult


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
    mock.aclose = AsyncMock()
    return mock


# ── create_bot_commands ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_bot_commands_no_commands():
    config = _make_config()
    result = await create_bot_commands(config, app_token="tok", scope_type=7, commands=[])
    assert result.success is False
    assert "commands is required" in result.error


@pytest.mark.asyncio
async def test_create_bot_commands_bad_scope():
    config = _make_config()
    result = await create_bot_commands(config, app_token="tok", scope_type=0, commands=[{"command": "test"}])
    assert result.success is False
    assert "scope_type must be 1-7" in result.error


@pytest.mark.asyncio
async def test_create_bot_commands_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "errMsg": "ok"})
    result = await create_bot_commands(
        config, app_token="tok", scope_type=7,
        commands=[{"command": "add", "description": "add something"}],
        http_client=mock_client,
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_bot_commands_with_chat():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "errMsg": "ok"})
    result = await create_bot_commands(
        config, app_token="tok", scope_type=1,
        commands=[{"command": "add"}],
        chat_id="524288-xxx", chat_type="group", staff_id="524288-yyy",
        http_client=mock_client,
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_create_bot_commands_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 10000, "errMsg": "API service unavailable"})
    result = await create_bot_commands(
        config, app_token="tok", scope_type=7,
        commands=[{"command": "test"}],
        http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=10000" in result.error


# ── fetch_bot_commands ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fetch_bot_commands_bad_scope():
    config = _make_config()
    result = await fetch_bot_commands(config, app_token="tok", scope_type=8)
    assert result.success is False
    assert "scope_type must be 1-7" in result.error


@pytest.mark.asyncio
async def test_fetch_bot_commands_success():
    config = _make_config()
    mock_client = _mock_http_client({
        "errCode": 0,
        "data": {
            "scopeType": 7,
            "commands": [{"command": "add", "description": "desc"}],
        },
    })
    result = await fetch_bot_commands(config, app_token="tok", scope_type=7, http_client=mock_client)
    assert result.success is True
    assert result.scope_type == 7
    assert result.commands is not None
    assert len(result.commands) == 1


@pytest.mark.asyncio
async def test_fetch_bot_commands_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 10000, "errMsg": "error"})
    result = await fetch_bot_commands(config, app_token="tok", scope_type=7, http_client=mock_client)
    assert result.success is False


# ── delete_bot_commands ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_bot_commands_bad_scope():
    config = _make_config()
    result = await delete_bot_commands(config, app_token="tok", scope_type=8)
    assert result.success is False
    assert "scope_type must be 1-7" in result.error


@pytest.mark.asyncio
async def test_delete_bot_commands_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "errMsg": "ok"})
    result = await delete_bot_commands(config, app_token="tok", scope_type=7, http_client=mock_client)
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_bot_commands_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 10000, "errMsg": "error"})
    result = await delete_bot_commands(config, app_token="tok", scope_type=7, http_client=mock_client)
    assert result.success is False


# ── models to_dict ───────────────────────────────────────────────────

def test_bot_command_models_to_dict():
    r1 = BotCommandResult(success=True).to_dict()
    assert r1["success"] is True

    r2 = BotCommandResult(success=False, error="bad").to_dict()
    assert r2["success"] is False
    assert r2["error"] == "bad"

    r3 = BotCommandQueryResult(
        success=True, scope_type=7,
        commands=[{"command": "add"}],
    ).to_dict()
    assert r3["success"] is True
    assert r3["scope_type"] == 7
    assert len(r3["commands"]) == 1
