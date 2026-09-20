"""Tests for the personal todo (个人待办) SDK domain."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from lansenger_sdk.client import LansengerClient
from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.models import (
    PersonalTodoListResult,
    PersonalTodoResourceResult,
    PersonalTodoSaveResult,
    PersonalTodoUrlResult,
)
from lansenger_sdk.personal_todos import (
    PERSONAL_TODO_PRIORITY_NORMAL,
    PERSONAL_TODO_RESOURCE_MAX_SIZE,
    PERSONAL_TODO_STATUS_FINISHED,
    PERSONAL_TODO_STATUS_UNFINISHED,
    PERSONAL_TODO_TYPE_PERSONAL,
    fetch_personal_todo_list,
    fetch_personal_todo_resource_download_url,
    fetch_personal_todo_resource_upload_url,
    save_personal_todo,
    update_personal_todo,
    upload_personal_todo_resource,
)
from lansenger_sdk.sync_client import LansengerSyncClient


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


@pytest.mark.asyncio
async def test_save_personal_todo_requires_fields():
    r = await save_personal_todo(
        _make_config(), app_token="tok", subject="", start_time=1, due_time=2,
        priority=1, create_user_id="u1", org_id="org1", appid="app1",
    )
    assert r.success is False and "subject is required" in r.error

    r = await save_personal_todo(
        _make_config(), app_token="tok", subject="s", start_time=1, due_time=2,
        priority=9, create_user_id="u1", org_id="org1", appid="app1",
    )
    assert r.success is False and "priority must be" in r.error


@pytest.mark.asyncio
async def test_save_personal_todo_body_and_result():
    mock = _mock_http_client({"errCode": 0, "data": "TASK001"})
    r = await save_personal_todo(
        _make_config(), app_token="tok", subject="完成方案", start_time=100,
        due_time=200, priority=PERSONAL_TODO_PRIORITY_NORMAL, create_user_id="u1",
        org_id="org1", appid="app1", description="desc", finish_time=None,
        executors=[{"staffId": "u1", "opt": 1}],
        resources=[{"fileName": "a.pdf", "resourceId": "r1"}],
        http_client=mock,
    )
    assert r.success is True and r.todo_code == "TASK001"
    body = mock.post.call_args.kwargs["json"]
    assert body["type"] == PERSONAL_TODO_TYPE_PERSONAL
    assert body["finishTime"] is None
    assert body["executors"] == [{"staffId": "u1", "opt": 1}]
    assert body["resources"] == [{"fileName": "a.pdf", "resourceId": "r1"}]


@pytest.mark.asyncio
async def test_update_personal_todo_uses_top_level_org_id():
    mock = _mock_http_client({"errCode": 0, "data": "TASK001"})
    r = await update_personal_todo(
        _make_config(), app_token="tok", todo_code="TASK001", org_id="org1",
        update_fields=["subject", "dueTime"], subject="新主题", due_time=300,
        http_client=mock,
    )
    assert r.success is True and r.todo_code == "TASK001"
    body = mock.post.call_args.kwargs["json"]
    assert body["orgId"] == "org1"
    assert "orgId" not in body["updateContent"]
    assert body["updateContent"]["subject"] == "新主题"
    assert body["updateContent"]["dueTime"] == 300


@pytest.mark.asyncio
async def test_fetch_personal_todo_list_page():
    mock = _mock_http_client({
        "errCode": 0,
        "data": {
            "pageNo": 2, "pageSize": 10, "pages": 3, "total": 21,
            "hasNextPage": True,
            "result": [{"taskCode": "TASK001", "summarySubject": "方案", "status": 0}],
        },
    })
    r = await fetch_personal_todo_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="u1",
        page_no=2, status=PERSONAL_TODO_STATUS_UNFINISHED, http_client=mock,
    )
    assert r.success is True
    assert r.page_no == 2 and r.total == 21 and r.has_more is True
    assert r.items[0]["taskCode"] == "TASK001"
    body = mock.post.call_args.kwargs["json"]
    assert body["status"] == 0 and body["staffId"] == "u1"


@pytest.mark.asyncio
async def test_resource_upload_and_urls():
    upload_mock = _mock_http_client({
        "errCode": 0,
        "data": {
            "fileName": "a.pdf", "mimeType": "application/pdf", "suffix": "pdf",
            "size": 10, "md5": "md5", "resourceId": "res1",
            "downloadUrl": "https://example.com/res1", "imageThumbnailList": {},
        },
    })
    r = await upload_personal_todo_resource(
        _make_config(), app_token="tok", app_id="app1", size=10,
        file_name="a.pdf", content_type="application/pdf", file_data="YWJj",
        org_id="org1", http_client=upload_mock,
    )
    assert r.success is True and r.resource_id == "res1"
    assert upload_mock.post.call_args.kwargs["json"]["fileData"] == "YWJj"

    download_mock = _mock_http_client({"errCode": 0, "data": "https://example.com/download"})
    download = await fetch_personal_todo_resource_download_url(
        _make_config(), app_token="tok", resource_id="res1", org_id="org1",
        http_client=download_mock,
    )
    assert download.success is True and download.url.endswith("/download")

    upload_url_mock = _mock_http_client({"errCode": 0, "data": "https://example.com/upload"})
    upload_url = await fetch_personal_todo_resource_upload_url(
        _make_config(), app_token="tok", file_name="a.pdf", md5="md5",
        size=10, org_id="org1", http_client=upload_url_mock,
    )
    assert upload_url.success is True and upload_url.url.endswith("/upload")


@pytest.mark.asyncio
async def test_personal_todo_legacy_success_code_and_api_error():
    legacy = _mock_http_client({"errCode": 200, "data": "TASK200"})
    r = await save_personal_todo(
        _make_config(), app_token="tok", subject="s", start_time=1, due_time=2,
        priority=1, create_user_id="u1", org_id="org1", appid="app1",
        http_client=legacy,
    )
    assert r.success is True and r.todo_code == "TASK200"

    error = _mock_http_client({"errCode": 3124, "errMsg": "日期格式错误"})
    r = await fetch_personal_todo_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="u1",
        http_client=error,
    )
    assert r.success is False and "errCode=3124" in r.error


@pytest.mark.asyncio
async def test_resource_size_limit_and_http_error():
    r = await upload_personal_todo_resource(
        _make_config(), app_token="tok", app_id="app1",
        size=PERSONAL_TODO_RESOURCE_MAX_SIZE + 1, file_name="a.pdf",
        content_type="application/pdf", file_data="x", org_id="org1",
    )
    assert r.success is False and "byte limit" in r.error

    mock = AsyncMock(spec=httpx.AsyncClient)
    mock.post.side_effect = httpx.HTTPError("boom")
    mock.aclose = AsyncMock()
    r = await fetch_personal_todo_list(
        _make_config(), app_token="tok", org_id="org1", staff_id="u1",
        http_client=mock,
    )
    assert r.success is False and "HTTP error" in r.error


@pytest.mark.asyncio
async def test_client_personal_todo_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    r = await client.save_personal_todo(
        subject="", start_time=1, due_time=2, priority=1,
        create_user_id="u1", org_id="org1", appid="app1",
    )
    assert r.success is False and "subject is required" in r.error
    await client.close()


def test_personal_todo_models_and_constants():
    assert PersonalTodoSaveResult(success=True, todo_code="T1").to_dict()["todo_code"] == "T1"
    page = PersonalTodoListResult(success=True, total=2).to_dict()
    assert page["total"] == 2 and page["has_more"] is False
    resource = PersonalTodoResourceResult(success=True, resource_id="r1").to_dict()
    assert resource["resource_id"] == "r1"
    assert PersonalTodoUrlResult(success=True, url="https://example.com").to_dict()["url"].startswith("https")
    assert PERSONAL_TODO_TYPE_PERSONAL == 1
    assert PERSONAL_TODO_STATUS_UNFINISHED == 0
    assert PERSONAL_TODO_STATUS_FINISHED == 1


def test_sync_personal_todo_methods_exist():
    for name in (
        "save_personal_todo",
        "update_personal_todo",
        "fetch_personal_todo_list",
        "upload_personal_todo_resource",
        "fetch_personal_todo_resource_download_url",
        "fetch_personal_todo_resource_upload_url",
    ):
        assert callable(getattr(LansengerSyncClient, name))
