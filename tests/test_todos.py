"""Tests for Lansenger SDK unified todo (4.33) module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.todos import (
    create_todo_task,
    update_todo_task,
    update_todo_task_status,
    delete_todo_task,
    fetch_todo_task_list,
    fetch_todo_task_by_source_id,
    fetch_todo_task_by_id,
    fetch_todo_task_status_counts,
    update_executor_status,
    add_executors,
    delete_executors,
    fetch_executor_list,
    TODO_TODO_STATUS_PENDING_READ,
    TODO_TODO_STATUS_READ,
    TODO_TODO_STATUS_PENDING_DO,
    TODO_TODO_STATUS_DONE,
    TODO_TYPE_NOTIFICATION,
    TODO_TYPE_APPROVAL,
)
from lansenger_sdk.models import (
    TodoTaskCreateResult,
    TodoTaskInfoResult,
    TodoTaskListResult,
    TodoTaskStatusCountResult,
    TodoTaskExecutorListResult,
)
from lansenger_sdk.client import LansengerClient

from unittest.mock import AsyncMock, patch, MagicMock


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
    mock_response.text = '{"errCode":0,"data":{"todotaskId":"task123"}}'
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    mock.post.return_value = mock_response
    mock.get.return_value = mock_response
    mock.aclose = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_create_todo_task_no_title():
    config = _make_config()
    result = await create_todo_task(config, app_token="tok", title="", link="l", pc_link="p", executor_ids=["e1"], org_id="o1")
    assert result.success is False
    assert "title is required" in result.error


@pytest.mark.asyncio
async def test_create_todo_task_no_link():
    config = _make_config()
    result = await create_todo_task(config, app_token="tok", title="t", link="", pc_link="p", executor_ids=["e1"], org_id="o1")
    assert result.success is False
    assert "link is required" in result.error


@pytest.mark.asyncio
async def test_create_todo_task_no_executor_ids():
    config = _make_config()
    result = await create_todo_task(config, app_token="tok", title="t", link="l", pc_link="p", executor_ids=[], org_id="o1")
    assert result.success is False
    assert "executor_ids is required" in result.error


@pytest.mark.asyncio
async def test_create_todo_task_no_org_id():
    config = _make_config()
    result = await create_todo_task(config, app_token="tok", title="t", link="l", pc_link="p", executor_ids=["e1"], org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_create_todo_task_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"todotaskId": "task123"}})
    result = await create_todo_task(
        config, app_token="tok", title="Test Todo", link="https://app.com/todo",
        pc_link="https://pc.app.com/todo", executor_ids=["staff1"], org_id="org1",
        http_client=mock_client,
    )
    assert result.success is True
    assert result.todotask_id == "task123"


@pytest.mark.asyncio
async def test_create_todo_task_api_error():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 40001, "errMsg": "Invalid token"})
    result = await create_todo_task(
        config, app_token="tok", title="t", link="l", pc_link="p",
        executor_ids=["e1"], org_id="o1", http_client=mock_client,
    )
    assert result.success is False
    assert "errCode=40001" in result.error


@pytest.mark.asyncio
async def test_update_todo_task_no_id():
    config = _make_config()
    result = await update_todo_task(config, app_token="tok", todotask_id="", title="t", link="l", pc_link="p", org_id="o1")
    assert result.success is False
    assert "todotask_id is required" in result.error


@pytest.mark.asyncio
async def test_update_todo_task_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {}})
    result = await update_todo_task(
        config, app_token="tok", todotask_id="task1", title="Updated",
        link="l", pc_link="p", org_id="o1", http_client=mock_client,
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_todo_task_status_invalid_status():
    config = _make_config()
    result = await update_todo_task_status(config, app_token="tok", todotask_id="t1", status="99", org_id="o1")
    assert result.success is False
    assert "status must be one of" in result.error


@pytest.mark.asyncio
async def test_update_todo_task_status_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {}})
    result = await update_todo_task_status(
        config, app_token="tok", todotask_id="t1", status=TODO_TODO_STATUS_DONE,
        org_id="o1", http_client=mock_client,
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_delete_todo_task_no_id():
    config = _make_config()
    result = await delete_todo_task(config, app_token="tok", todotask_id="", org_id="o1")
    assert result.success is False
    assert "todotask_id is required" in result.error


@pytest.mark.asyncio
async def test_delete_todo_task_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {}})
    result = await delete_todo_task(config, app_token="tok", todotask_id="t1", org_id="o1", http_client=mock_client)
    assert result.success is True


@pytest.mark.asyncio
async def test_fetch_todo_task_list_no_org_id():
    config = _make_config()
    result = await fetch_todo_task_list(config, app_token="tok", org_id="")
    assert result.success is False
    assert "org_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_todo_task_list_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"total": 5, "todotaskList": [{"todotaskId": "t1"}]}})
    result = await fetch_todo_task_list(config, app_token="tok", org_id="o1", http_client=mock_client)
    assert result.success is True
    assert result.total == 5
    assert result.todotask_list is not None


@pytest.mark.asyncio
async def test_fetch_todo_task_by_source_id_no_source_id():
    config = _make_config()
    result = await fetch_todo_task_by_source_id(config, app_token="tok", source_id="", org_id="o1")
    assert result.success is False
    assert "source_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_todo_task_by_source_id_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"todotaskId": "t1", "sourceId": "src1", "title": "Test"}})
    result = await fetch_todo_task_by_source_id(config, app_token="tok", source_id="src1", org_id="o1", http_client=mock_client)
    assert result.success is True
    assert result.todotask_id == "t1"
    assert result.source_id == "src1"


@pytest.mark.asyncio
async def test_fetch_todo_task_by_id_no_id():
    config = _make_config()
    result = await fetch_todo_task_by_id(config, app_token="tok", todotask_id="", org_id="o1")
    assert result.success is False
    assert "todotask_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_todo_task_by_id_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"todotaskId": "t1", "title": "Test", "status": "21"}})
    result = await fetch_todo_task_by_id(config, app_token="tok", todotask_id="t1", org_id="o1", http_client=mock_client)
    assert result.success is True
    assert result.todotask_id == "t1"
    assert result.title == "Test"


@pytest.mark.asyncio
async def test_fetch_todo_task_status_counts_no_staff_id():
    config = _make_config()
    result = await fetch_todo_task_status_counts(config, app_token="tok", staff_id="", org_id="o1")
    assert result.success is False
    assert "staff_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_todo_task_status_counts_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": [{"status": "21", "count": 3}]})
    result = await fetch_todo_task_status_counts(config, app_token="tok", staff_id="s1", org_id="o1", http_client=mock_client)
    assert result.success is True
    assert result.status_counts is not None


@pytest.mark.asyncio
async def test_update_executor_status_no_list():
    config = _make_config()
    result = await update_executor_status(config, app_token="tok", executor_status_list=[], org_id="o1")
    assert result.success is False
    assert "executor_status_list is required" in result.error


@pytest.mark.asyncio
async def test_add_executors_no_ids():
    config = _make_config()
    result = await add_executors(config, app_token="tok", executor_ids=[], org_id="o1")
    assert result.success is False
    assert "executor_ids is required" in result.error


@pytest.mark.asyncio
async def test_delete_executors_no_ids():
    config = _make_config()
    result = await delete_executors(config, app_token="tok", executor_ids=[], org_id="o1")
    assert result.success is False
    assert "executor_ids is required" in result.error


@pytest.mark.asyncio
async def test_fetch_executor_list_no_id():
    config = _make_config()
    result = await fetch_executor_list(config, app_token="tok", todotask_id="", org_id="o1")
    assert result.success is False
    assert "todotask_id is required" in result.error


@pytest.mark.asyncio
async def test_fetch_executor_list_success():
    config = _make_config()
    mock_client = _mock_http_client({"errCode": 0, "data": {"total": 2, "executorList": [{"staffId": "s1"}]}})
    result = await fetch_executor_list(config, app_token="tok", todotask_id="t1", org_id="o1", http_client=mock_client)
    assert result.success is True
    assert result.total == 2
    assert result.executor_list is not None


def test_todo_status_constants():
    assert TODO_TODO_STATUS_PENDING_READ == "11"
    assert TODO_TODO_STATUS_READ == "12"
    assert TODO_TODO_STATUS_PENDING_DO == "21"
    assert TODO_TODO_STATUS_DONE == "22"


def test_todo_type_constants():
    assert TODO_TYPE_NOTIFICATION == 1
    assert TODO_TYPE_APPROVAL == 2


@pytest.mark.asyncio
async def test_todo_models_to_dict():
    r = TodoTaskCreateResult(success=True, todotask_id="t1")
    d = r.to_dict()
    assert d["success"] is True
    assert d["todotask_id"] == "t1"

    r2 = TodoTaskInfoResult(success=True, todotask_id="t1", title="Test", status="21")
    d2 = r2.to_dict()
    assert d2["success"] is True
    assert d2["todotask_id"] == "t1"
    assert d2["title"] == "Test"

    r3 = TodoTaskListResult(success=True, total=5, todotask_list=[{"id": "t1"}])
    d3 = r3.to_dict()
    assert d3["success"] is True
    assert d3["total"] == 5

    r4 = TodoTaskStatusCountResult(success=True, status_counts=[{"status": "21", "count": 3}])
    d4 = r4.to_dict()
    assert d4["success"] is True
    assert d4["status_counts"] is not None

    r5 = TodoTaskExecutorListResult(success=True, total=2, executor_list=[{"staffId": "s1"}])
    d5 = r5.to_dict()
    assert d5["success"] is True
    assert d5["total"] == 2


@pytest.mark.asyncio
async def test_client_create_todo_task_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.create_todo_task(title="", link="l", pc_link="p", executor_ids=["e"], org_id="o")
    assert result.success is False
    assert "title is required" in result.error
    await client.close()


@pytest.mark.asyncio
async def test_client_fetch_todo_task_list_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    result = await client.fetch_todo_task_list(org_id="")
    assert result.success is False
    assert "org_id is required" in result.error
    await client.close()
