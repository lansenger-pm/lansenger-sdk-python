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
    build_personal_todo_resource_entry,
    resource_entry_from_upload,
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
        org_id="org1", appid="app1", description="desc", user_token="ut1",
        executors=[{"staffId": "u1", "opt": 1}],
        resources=[{"fileName": "a.pdf", "resourceId": "r1"}],
        http_client=mock,
    )
    assert r.success is True and r.todo_code == "TASK001"
    body = mock.post.call_args.kwargs["json"]
    assert body["type"] == PERSONAL_TODO_TYPE_PERSONAL
    assert body["finishTime"] == 0
    assert body["executors"] == [{"staffId": "u1", "opt": 1}]
    assert body["resources"] == [{"fileName": "a.pdf", "resourceId": "r1"}]
    url = mock.post.call_args.args[0]
    assert "app_token=tok" in url and "user_token=ut1" in url


@pytest.mark.asyncio
async def test_update_personal_todo_uses_top_level_org_id():
    mock = _mock_http_client({"errCode": 0, "data": "TASK001"})
    r = await update_personal_todo(
        _make_config(), app_token="tok", todo_code="TASK001", org_id="org1",
        update_fields=["subject"], subject="新主题",
        create_user_id="u1", appid="app1",
        http_client=mock,
    )
    assert r.success is True and r.todo_code == "TASK001"
    body = mock.post.call_args.kwargs["json"]
    assert body["orgId"] == "org1"
    assert "orgId" not in body["updateContent"]
    assert body["updateContent"]["subject"] == "新主题"
    assert body["updateContent"]["createUserId"] == "u1"
    assert body["updateContent"]["appid"] == "app1"


@pytest.mark.asyncio
async def test_update_personal_todo_requires_identity_fields():
    r = await update_personal_todo(
        _make_config(), app_token="tok", todo_code="TASK001", org_id="org1",
        update_fields=["subject"], subject="新主题",
    )
    assert r.success is False and "create_user_id is required" in r.error
    r = await update_personal_todo(
        _make_config(), app_token="tok", todo_code="TASK001", org_id="org1",
        update_fields=["subject"], subject="新主题", create_user_id="u1",
    )
    assert r.success is False and "appid is required" in r.error


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


# ---------------------------------------------------------------------------
# 附件条目构造（resources）
# ---------------------------------------------------------------------------

_UPLOAD_RAW = {
    "errCode": 0,
    "data": {
        "fileName": "a.pdf",
        "mimeType": "application/pdf",
        "size": 10,
        "resourceId": "res1",
    },
}

_EXPECTED_ENTRY = {
    "fileName": "a.pdf",
    "resourceId": "res1",
    "fileType": "application/pdf",  # 上传响应用 mimeType，挂附件必须叫 fileType
    "fileSize": 10,                 # 上传响应用 size，挂附件必须叫 fileSize
    "opt": 1,
}


def test_resource_entry_from_upload_accepts_raw_response():
    """传 /resource/update 的原始响应（外层带 errCode）。"""
    assert resource_entry_from_upload(_UPLOAD_RAW) == _EXPECTED_ENTRY


def test_resource_entry_from_upload_accepts_inner_data():
    """传已经剥掉外层的 data。"""
    assert resource_entry_from_upload(_UPLOAD_RAW["data"]) == _EXPECTED_ENTRY


def test_resource_entry_from_upload_accepts_result_object():
    """传上传结果对象：参数名就叫 upload_result，但早期实现只认 dict，会 AttributeError。"""
    result = PersonalTodoResourceResult(
        success=True, file_name="a.pdf", mime_type="application/pdf",
        size=10, resource_id="res1",
    )
    assert resource_entry_from_upload(result) == _EXPECTED_ENTRY


@pytest.mark.asyncio
async def test_resource_entry_from_upload_object_matches_raw_response():
    """端到端：真实上传一次，两条入口必须产出同一个条目。"""
    mock = _mock_http_client(_UPLOAD_RAW)
    result = await upload_personal_todo_resource(
        _make_config(), app_token="tok", app_id="app1", size=10,
        file_name="a.pdf", content_type="application/pdf", file_data="YWJj",
        org_id="org1", http_client=mock,
    )
    assert result.to_resource_entry() == _EXPECTED_ENTRY
    assert resource_entry_from_upload(result) == _EXPECTED_ENTRY
    assert resource_entry_from_upload(result.raw_response) == _EXPECTED_ENTRY


def test_to_resource_entry_delegates_to_build_entry():
    """结果类方法与显式构造函数必须同构（否则条目结构会在两处漂移）。"""
    result = PersonalTodoResourceResult(
        success=True, file_name="a.pdf", mime_type="application/pdf",
        size=10, resource_id="res1",
    )
    assert result.to_resource_entry() == build_personal_todo_resource_entry(
        resource_id="res1", file_name="a.pdf",
        file_type="application/pdf", file_size=10,
    )


def test_resource_entry_opt_and_missing_fields():
    """opt=0 表示移除；字段缺失时回落为空串/0 而不是抛错。"""
    empty = PersonalTodoResourceResult(success=True)
    assert empty.to_resource_entry(opt=0) == {
        "fileName": "", "resourceId": "", "fileType": "", "fileSize": 0, "opt": 0,
    }
    assert resource_entry_from_upload(empty, opt=0)["opt"] == 0


def test_resource_entry_from_upload_rejects_unusable_input():
    """既不是 dict、也没有可用字段/raw_response 的入参要显式报错，不能静默产出残缺条目。"""
    with pytest.raises(TypeError):
        resource_entry_from_upload(object())
