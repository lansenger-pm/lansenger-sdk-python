"""Tests for Lansenger SDK questionnaire (问卷系统) module functions."""

import httpx
import pytest

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.questionnaires import (
    save_questionnaire,
    save_questionnaire_questions,
    delete_questionnaire_question,
    publish_questionnaire,
    withdraw_questionnaire,
    finish_questionnaire,
    delete_questionnaire,
    fetch_questionnaire_detail,
    fetch_questionnaire_brief,
    fetch_questionnaire_answer_url,
    copy_questionnaire,
    fetch_questionnaires_by_codes,
    fetch_questionnaire_office_accounts,
    fetch_created_questionnaires,
    fetch_my_created_questionnaires,
    fetch_participated_questionnaires,
    fetch_answer_records,
    fetch_questionnaire_answer_detail,
    fetch_questionnaire_last_answer_detail,
    fetch_answer_data,
    fetch_questionnaire_last_answer_record,
    fetch_questionnaire_upload_url,
    QUESTIONNAIRE_STATUS_DRAFT,
    QUESTIONNAIRE_STATUS_ONGOING,
    QUESTIONNAIRE_STATUS_FINISHED,
    QUESTIONNAIRE_SCOPE_INTERNAL,
    QUESTIONNAIRE_SCOPE_PUBLIC,
    QUESTIONNAIRE_ANSWER_LIMIT_ONCE,
    QUESTIONNAIRE_ANSWER_LIMIT_UNLIMITED,
    QUESTIONNAIRE_QUESTION_TYPES,
)
from lansenger_sdk.models import (
    QuestionnaireSaveResult,
    QuestionnaireOpResult,
    QuestionnaireDetailResult,
    QuestionnairePageResult,
    QuestionnaireAnswerDetailResult,
)
from lansenger_sdk.client import LansengerClient

from unittest.mock import AsyncMock, MagicMock


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


_QN_OK = {"errCode": 0, "errMsg": "操作成功", "data": "QN001"}
_PAGE_OK = {
    "errCode": 0,
    "data": {"pageNo": 2, "pageSize": 10, "pages": 3, "total": 25,
             "result": [{"code": "QN001", "title": "t"}], "hasNextPage": True},
}


# ---------- validation guards ----------

@pytest.mark.asyncio
async def test_save_questionnaire_no_title():
    r = await save_questionnaire(_make_config(), app_token="tok", title="", account_code="ACC")
    assert r.success is False and "title is required" in r.error


@pytest.mark.asyncio
async def test_save_questionnaire_no_account_code():
    r = await save_questionnaire(_make_config(), app_token="tok", title="t", account_code="")
    assert r.success is False and "account_code is required" in r.error


@pytest.mark.asyncio
async def test_save_questions_no_list():
    r = await save_questionnaire_questions(_make_config(), app_token="tok", questionnaire_code="QN", question_list=[])
    assert r.success is False and "question_list is required" in r.error


@pytest.mark.asyncio
async def test_delete_question_no_code():
    r = await delete_questionnaire_question(_make_config(), app_token="tok", question_code="")
    assert r.success is False and "question_code is required" in r.error


@pytest.mark.asyncio
async def test_publish_invalid_scope():
    r = await publish_questionnaire(_make_config(), app_token="tok", questionnaire_code="QN", scope_type=9)
    assert r.success is False and "scope_type must be 1" in r.error


@pytest.mark.asyncio
async def test_publish_invalid_answer_limit():
    r = await publish_questionnaire(_make_config(), app_token="tok", questionnaire_code="QN", answer_limit=5)
    assert r.success is False and "answer_limit must be 1" in r.error


@pytest.mark.asyncio
async def test_withdraw_no_code():
    r = await withdraw_questionnaire(_make_config(), app_token="tok", questionnaire_code="")
    assert r.success is False and "questionnaire_code is required" in r.error


@pytest.mark.asyncio
async def test_fetch_detail_no_code():
    r = await fetch_questionnaire_detail(_make_config(), app_token="tok", questionnaire_code="")
    assert r.success is False and "questionnaire_code is required" in r.error


@pytest.mark.asyncio
async def test_fetch_by_codes_no_list():
    r = await fetch_questionnaires_by_codes(_make_config(), app_token="tok", code_list=[])
    assert r.success is False and "code_list is required" in r.error


@pytest.mark.asyncio
async def test_fetch_by_codes_include_del_param_name():
    """实测锁定：服务端参数名为 includeDel（非 includeDeleted），拼错会被静默忽略。"""
    mock = _mock_http_client(_QN_OK)
    await fetch_questionnaires_by_codes(_make_config(), app_token="tok", code_list=["QN1"], include_deleted=1, http_client=mock)
    body = mock.post.call_args.kwargs["json"]
    assert body["includeDel"] == 1 and "includeDeleted" not in body


@pytest.mark.asyncio
async def test_fetch_created_no_account():
    r = await fetch_created_questionnaires(_make_config(), app_token="tok", account_code="")
    assert r.success is False and "account_code is required" in r.error


@pytest.mark.asyncio
async def test_fetch_my_created_no_org():
    r = await fetch_my_created_questionnaires(_make_config(), app_token="tok", org_id="")
    assert r.success is False and "org_id is required" in r.error


@pytest.mark.asyncio
async def test_fetch_answer_records_no_account():
    r = await fetch_answer_records(_make_config(), app_token="tok", account_code="", questionnaire_code="QN")
    assert r.success is False and "account_code is required" in r.error


@pytest.mark.asyncio
async def test_fetch_answer_detail_no_answer_code():
    r = await fetch_questionnaire_answer_detail(_make_config(), app_token="tok", account_code="ACC", answer_code="")
    assert r.success is False and "answer_code is required" in r.error


@pytest.mark.asyncio
async def test_upload_url_no_md5():
    r = await fetch_questionnaire_upload_url(_make_config(), app_token="tok", file_name="a.png", md5="", size=10)
    assert r.success is False and "md5 is required" in r.error


@pytest.mark.asyncio
async def test_upload_url_no_size():
    r = await fetch_questionnaire_upload_url(_make_config(), app_token="tok", file_name="a.png", md5="m", size=0)
    assert r.success is False and "size is required" in r.error


# ---------- success paths ----------

@pytest.mark.asyncio
async def test_save_questionnaire_success():
    mock = _mock_http_client(_QN_OK)
    r = await save_questionnaire(
        _make_config(), app_token="tok", title="满意度调查", account_code="ACC001",
        welcome_speech="欢迎", code="QN000", create_user_id="U1", http_client=mock,
    )
    assert r.success is True and r.questionnaire_code == "QN001"
    body = mock.post.call_args.kwargs["json"]
    assert body["title"] == "满意度调查" and body["accountCode"] == "ACC001"
    assert body["code"] == "QN000" and body["welcomeSpeech"] == "欢迎"
    assert "createUserId" in body  # create_user_id 传入且无 user_token → 显式下发


@pytest.mark.asyncio
async def test_publish_success_body_shape():
    mock = _mock_http_client({"errCode": 0, "data": True})
    r = await publish_questionnaire(
        _make_config(), app_token="tok", questionnaire_code="QN001",
        scope_type=QUESTIONNAIRE_SCOPE_PUBLIC, staff_ids=["U1", "U2"],
        message_flag=1, publish_user_id="U9", http_client=mock,
    )
    assert r.success is True and r.done is True
    body = mock.post.call_args.kwargs["json"]
    assert body["scopeType"] == 2 and body["staffIdList"] == ["U1", "U2"]
    assert body["answerLimit"] == 1 and body["viewStatsFlag"] == 1 and body["anonymFlag"] == 0
    assert body["publishUserId"] == "U9"


@pytest.mark.asyncio
async def test_withdraw_finish_delete_share_code_body():
    for fn in (withdraw_questionnaire, finish_questionnaire, delete_questionnaire):
        mock = _mock_http_client({"errCode": 0, "data": True})
        r = await fn(_make_config(), app_token="tok", questionnaire_code="QN1", operate_user_id="U1", http_client=mock)
        assert r.success is True and r.done is True
        body = mock.post.call_args.kwargs["json"]
        assert body == {"questionnaireCode": "QN1", "operateUserId": "U1"}


@pytest.mark.asyncio
async def test_fetch_detail_extracts_fields():
    mock = _mock_http_client({"errCode": 0, "data": {
        "id": 1001, "code": "QN001", "title": "满意度", "status": 2,
        "accountCode": "ACC001", "answerUserCount": 120, "questionCount": 5,
        "questionList": [{"code": "Q1", "questionType": "radio"}],
        "createTime": 1780000000000,
    }})
    r = await fetch_questionnaire_detail(_make_config(), app_token="tok", questionnaire_code="QN001", http_client=mock)
    assert r.success is True
    assert r.questionnaire_id == 1001 and r.status == 2 and r.question_count == 5
    assert r.questions[0]["code"] == "Q1"
    body = mock.post.call_args.kwargs["json"]
    assert body == {"questionnaireCode": "QN001"}


@pytest.mark.asyncio
async def test_fetch_brief_has_no_questions():
    mock = _mock_http_client({"errCode": 0, "data": {"code": "QN001", "title": "t", "status": 2, "questionCount": 3}})
    r = await fetch_questionnaire_brief(_make_config(), app_token="tok", questionnaire_code="QN001", http_client=mock)
    assert r.success is True and r.questions is None and r.question_count == 3


@pytest.mark.asyncio
async def test_fetch_answer_url_and_copy():
    mock = _mock_http_client({"errCode": 0, "data": "https://qn.example.com/answer/QN1"})
    r = await fetch_questionnaire_answer_url(_make_config(), app_token="tok", questionnaire_code="QN1", http_client=mock)
    assert r.success is True and r.url.endswith("/QN1")

    mock2 = _mock_http_client({"errCode": 0, "data": "QN-NEW"})
    r2 = await copy_questionnaire(_make_config(), app_token="tok", questionnaire_code="QN1", http_client=mock2)
    assert r2.success is True and r2.new_code == "QN-NEW"


@pytest.mark.asyncio
async def test_page_result_parsing():
    for fn, kwargs in (
        (fetch_created_questionnaires, {"account_code": "ACC"}),
        (fetch_my_created_questionnaires, {"org_id": "o1"}),
        (fetch_participated_questionnaires, {"org_id": "o1"}),
        (fetch_answer_records, {"account_code": "ACC", "questionnaire_code": "QN"}),
        (fetch_answer_data, {"account_code": "ACC", "questionnaire_code": "QN"}),
    ):
        mock = _mock_http_client(_PAGE_OK)
        r = await fn(_make_config(), app_token="tok", page_no=2, page_size=10, http_client=mock, **kwargs)
        assert r.success is True, fn.__name__
        assert r.total == 25 and r.pages == 3 and r.page_no == 2 and r.has_more is True
        assert r.items[0]["code"] == "QN001"


@pytest.mark.asyncio
async def test_answer_detail_maps():
    mock = _mock_http_client({"errCode": 0, "data": {
        "answerUserId": "U1", "answerUserName": "张三", "answerStatus": 1,
        "questionnaire": {"code": "QN1", "title": "t"},
        "questionList": [{"code": "Q1"}],
        "answerMap": {"Q1": {"context": "非常满意"}},
    }})
    r = await fetch_questionnaire_answer_detail(
        _make_config(), app_token="tok", account_code="ACC", answer_code="AR1", http_client=mock,
    )
    assert r.success is True
    assert r.answer_user_name == "张三"
    assert r.questionnaire["code"] == "QN1"
    assert r.answers["Q1"]["context"] == "非常满意"


@pytest.mark.asyncio
async def test_last_answer_record_extracts():
    mock = _mock_http_client({"errCode": 0, "data": {
        "id": 9001, "code": "AR1", "answerUserName": "张三", "statsStatus": 1,
    }})
    r = await fetch_questionnaire_last_answer_record(_make_config(), app_token="tok", questionnaire_code="QN1", http_client=mock)
    assert r.success is True and r.record_id == 9001 and r.record_code == "AR1" and r.stats_status == 1


@pytest.mark.asyncio
async def test_upload_url_success():
    mock = _mock_http_client({"errCode": 0, "data": "https://oss.example.com/u?sign=x"})
    r = await fetch_questionnaire_upload_url(_make_config(), app_token="tok", file_name="a.png", md5="m", size=10, http_client=mock)
    assert r.success is True and r.url.startswith("https://oss.example.com")


# ---------- error paths ----------

@pytest.mark.asyncio
async def test_save_questionnaire_api_error():
    mock = _mock_http_client({"errCode": 3104, "errMsg": "官方账号不存在！"})
    r = await save_questionnaire(_make_config(), app_token="tok", title="t", account_code="BAD", http_client=mock)
    assert r.success is False and "errCode=3104" in r.error


@pytest.mark.asyncio
async def test_fetch_detail_http_error():
    mock = _mock_http_client({"errCode": 0})
    mock.post.side_effect = httpx.ConnectError("boom")
    r = await fetch_questionnaire_detail(_make_config(), app_token="tok", questionnaire_code="QN", http_client=mock)
    assert r.success is False and "HTTP error" in r.error


@pytest.mark.asyncio
async def test_client_save_questionnaire_validation():
    client = LansengerClient(app_id="test", app_secret="test")
    r = await client.save_questionnaire(title="", account_code="ACC")
    assert r.success is False and "title is required" in r.error
    await client.close()


# ---------- models & constants ----------

def test_questionnaire_models_to_dict():
    d = QuestionnaireSaveResult(success=True, questionnaire_code="QN1").to_dict()
    assert d["questionnaire_code"] == "QN1" and "raw_response" not in d

    d2 = QuestionnaireOpResult(success=True, done=True).to_dict()
    assert d2["done"] is True

    d3 = QuestionnaireDetailResult(success=True, code="QN1").to_dict()
    assert "questions" not in d3 and d3["code"] == "QN1"

    d4 = QuestionnairePageResult(success=True, total=3, items=[]).to_dict()
    assert d4["total"] == 3 and d4["has_more"] is False

    d5 = QuestionnaireAnswerDetailResult(success=True, answers={"Q1": {"context": "x"}}).to_dict()
    assert d5["answers"]["Q1"]["context"] == "x"

    failed = QuestionnaireSaveResult(success=False, error="boom")
    assert failed.to_dict()["error"] == "boom"


def test_questionnaire_constants():
    assert QUESTIONNAIRE_STATUS_DRAFT == 1
    assert QUESTIONNAIRE_STATUS_ONGOING == 2
    assert QUESTIONNAIRE_STATUS_FINISHED == 4
    assert QUESTIONNAIRE_SCOPE_INTERNAL == 1
    assert QUESTIONNAIRE_SCOPE_PUBLIC == 2
    assert QUESTIONNAIRE_ANSWER_LIMIT_ONCE == 1
    assert QUESTIONNAIRE_ANSWER_LIMIT_UNLIMITED == -1
    assert len(QUESTIONNAIRE_QUESTION_TYPES) == 16
    assert "radio" in QUESTIONNAIRE_QUESTION_TYPES and "filesUpload" in QUESTIONNAIRE_QUESTION_TYPES
