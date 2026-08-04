"""Tests for Lansenger SDK client construction and basic validation."""

import asyncio
import os

import pytest

from lansenger_sdk import LansengerClient, LansengerSyncClient, LansengerConfig
from lansenger_sdk.exceptions import LansengerConfigError


def test_client_from_env_missing_raises():
    os.environ.pop("LANSENGER_APP_ID", None)
    os.environ.pop("LANSENGER_APP_SECRET", None)
    with pytest.raises(LansengerConfigError):
        LansengerClient.from_env()


def test_client_from_env_with_vars():
    os.environ["LANSENGER_APP_ID"] = "test_id"
    os.environ["LANSENGER_APP_SECRET"] = "test_secret"
    try:
        client = LansengerClient.from_env()
        assert client._config.app_id == "test_id"
        assert client._config.app_secret == "test_secret"
    finally:
        os.environ.pop("LANSENGER_APP_ID", None)
        os.environ.pop("LANSENGER_APP_SECRET", None)


def test_client_direct_params():
    client = LansengerClient(app_id="direct_id", app_secret="direct_secret")
    assert client._config.app_id == "direct_id"
    assert client._config.app_secret == "direct_secret"


def test_client_from_config():
    config = LansengerConfig.create(app_id="cfg_id", app_secret="cfg_secret")
    client = LansengerClient.from_config(config)
    assert client._config.app_id == "cfg_id"


def test_sync_client_from_env_missing_raises():
    os.environ.pop("LANSENGER_APP_ID", None)
    os.environ.pop("LANSENGER_APP_SECRET", None)
    with pytest.raises(LansengerConfigError):
        LansengerSyncClient.from_env()


def test_sync_client_direct_params():
    client = LansengerSyncClient(app_id="sync_id", app_secret="sync_secret")
    assert client._app_id == "sync_id"
    assert client._app_secret == "sync_secret"


@pytest.mark.asyncio
async def test_send_text_no_chat_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_text(chat_id="", content="test")
    assert result.success is False
    assert "chat_id is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_send_markdown_no_content():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_markdown(chat_id="user123", content="")
    assert result.success is False
    assert "content is required" in result.error


@pytest.mark.asyncio
async def test_send_text_no_content_or_file():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_text(chat_id="user123", content="")
    assert result.success is False
    assert "content or file_path is required" in result.error


@pytest.mark.asyncio
async def test_revoke_no_message_ids():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.revoke_message(message_ids=[])
    assert result.success is False
    assert "message_ids is required" in result.error


@pytest.mark.asyncio
async def test_revoke_staff_requires_sender_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.revoke_message(message_ids=["msg1"], chat_type="staff")
    assert result.success is False
    assert "sender_id" in result.error


@pytest.mark.asyncio
async def test_link_card_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_link_card(chat_id="", title="T", link="L")
    assert result.success is False
    assert "chat_id is required" in result.error

    result = await client.send_link_card(chat_id="user123", title="", link="L")
    assert result.success is False
    assert "title is required" in result.error

    result = await client.send_link_card(chat_id="user123", title="T", link="")
    assert result.success is False
    assert "link is required" in result.error


@pytest.mark.asyncio
async def test_oacard_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_oacard(chat_id="", title="T")
    assert result.success is False
    assert "chat_id is required" in result.error

    result = await client.send_oacard(chat_id="user123", title="")
    assert result.success is False
    assert "title is required for oaCard" in result.error


@pytest.mark.asyncio
async def test_app_card_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_app_card(chat_id="", body_title="T")
    assert result.success is False
    assert "chat_id is required" in result.error

    result = await client.send_app_card(chat_id="user123", body_title="")
    assert result.success is False
    assert "body_title is required" in result.error


@pytest.mark.asyncio
async def test_update_dynamic_card_no_msg_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.update_dynamic_card(msg_id="")
    assert result.success is False
    assert "msg_id is required" in result.error


@pytest.mark.asyncio
async def test_app_articles_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_app_articles(chat_id="", articles=[{"title": "T"}])
    assert result.success is False
    assert "chat_id is required" in result.error

    result = await client.send_app_articles(chat_id="user123", articles=[])
    assert result.success is False
    assert "articles is required" in result.error


@pytest.mark.asyncio
async def test_image_url_validation():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_image_url(chat_id="", image_url="http://x.com/img.jpg")
    assert result.success is False
    assert "chat_id is required" in result.error

    result = await client.send_image_url(chat_id="user123", image_url="")
    assert result.success is False
    assert "image_url is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_basic_info_no_staff_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_staff_basic_info(staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_detail_no_staff_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_staff_detail(staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_ancestors_no_staff_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_department_ancestors(staff_id="")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_id_mapping_no_org_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_staff_id_mapping(org_id="", id_type="mobile", id_value="123")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_id_mapping_no_id_type():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_staff_id_mapping(org_id="org1", id_type="", id_value="123")
    assert result.success is False
    assert "id_type is required" in result.error


@pytest.mark.asyncio
async def test_fetch_staff_id_mapping_no_id_value():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_staff_id_mapping(org_id="org1", id_type="mobile", id_value="")
    assert result.success is False
    assert "id_value is required" in result.error


@pytest.mark.asyncio
async def test_fetch_org_extra_field_ids_no_org_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_org_extra_field_ids(org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_search_staff_no_keyword():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.search_staff(keyword="")
    assert result.success is False
    assert "keyword is required" in result.error


@pytest.mark.asyncio
async def test_create_group_no_name():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.create_group(name="", org_id="org1")
    assert result.success is False
    assert "name is required" in result.error


@pytest.mark.asyncio
async def test_create_group_no_org_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.create_group(name="MyGroup", org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_group_info_no_group_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_group_info(group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_group_members_no_group_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_group_members(group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_check_is_in_group_no_group_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.check_is_in_group(group_id="")
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_detail_no_department_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_department_detail(department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_children_no_department_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_department_children(department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_department_staffs_no_department_id():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.fetch_department_staffs(department_id="")
    assert result.success is False
    assert "department_id is required" in result.error


@pytest.mark.asyncio
async def test_send_group_message_reminder_text():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="text",
        msg_data={"text": {"content": "hi"}},
        reminder_all=True, reminder_user_ids=["u1"],
    )
    assert result.success is False
    assert "group_id is required" in result.error


@pytest.mark.asyncio
async def test_send_group_message_reminder_non_text_ignored():
    client = LansengerClient(app_id="id", app_secret="secret")
    result = await client.send_group_message(
        group_id="", msg_type="appCard",
        msg_data={"appCard": {"bodyTitle": "hi"}},
        reminder_all=True, reminder_user_ids=["u1"],
    )
    assert result.success is False
    assert "group_id is required" in result.error

def test_client_passthrough_mode_no_app_id_secret():
    """Pass-through mode: app_token only, app_id/app_secret optional (issue #1)."""
    os.environ.pop("LANSENGER_APP_ID", None)
    os.environ.pop("LANSENGER_APP_SECRET", None)
    client = LansengerClient(app_token="at", user_token="ut", api_gateway_url="https://gw")
    assert client._config.app_id == ""
    assert client._config.app_secret == ""
    assert client._config.app_token == "at"
    assert client._config.is_external_mode() is True


def test_sync_client_passthrough_mode_no_app_id_secret():
    """Sync pass-through mode: app_token only (issue #1)."""
    client = LansengerSyncClient(app_token="at", user_token="ut", api_gateway_url="https://gw")
    assert client._app_id == ""
    assert client._app_secret == ""
    assert client._app_token == "at"
