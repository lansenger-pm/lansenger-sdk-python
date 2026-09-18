"""Lansenger questionnaire API — create, publish, and analyze questionnaires (问卷系统).

Endpoints:
- POST /xtra/questionnaire/server/openapi/v1/saveQuestionnaire     — create/update a questionnaire
- POST /xtra/questionnaire/server/openapi/v1/saveQuestionList      — batch-save questions
- POST /xtra/questionnaire/server/openapi/v1/deleteQuestion        — delete a question
- POST /xtra/questionnaire/server/openapi/v1/publish               — publish a questionnaire
- POST /xtra/questionnaire/server/openapi/v1/withdraw              — withdraw to draft
- POST /xtra/questionnaire/server/openapi/v1/finish                — end a questionnaire
- POST /xtra/questionnaire/server/openapi/v1/delete                — delete a questionnaire
- POST /xtra/questionnaire/server/openapi/v1/detail                — full detail (admin, with questions)
- POST /xtra/questionnaire/server/openapi/v1/detailWithoutAuth     — brief detail (no questions)
- POST /xtra/questionnaire/server/openapi/v1/getAnswerUrl          — answer-page URL
- POST /xtra/questionnaire/server/openapi/v1/copy                  — copy as new draft
- POST /xtra/questionnaire/server/openapi/v1/queryList             — batch query by codes
- POST /xtra/questionnaire/server/openapi/v1/userOfficeAccountList — office accounts of a user
- POST /xtra/questionnaire/server/openapi/v1/createList            — paged: created under an office account
- POST /xtra/questionnaire/server/openapi/v1/myCreateList          — paged: my created (personal + official)
- POST /xtra/questionnaire/server/openapi/v1/participationList     — paged: questionnaires I answered
- POST /xtra/questionnaire/server/openapi/v1/answerList            — paged: answer records of a questionnaire
- POST /xtra/questionnaire/server/openapi/v1/answerDetail          — full answer detail
- POST /xtra/questionnaire/server/openapi/v1/lastAnswerDetail      — my last answer detail
- POST /xtra/questionnaire/server/openapi/v1/answerData            — paged: answer data export
- POST /xtra/questionnaire/server/openapi/v1/lastAnswerRecord      — my last answer record (simple)
- POST /xtra/questionnaire/server/openapi/v1/upload                — presigned upload URL (PUT + Content-MD5)

All endpoints use POST with app_token query param. user_token optional: when
provided, body identity fields (createUserId / operateUserId / userId etc.)
may be omitted. Paths carry a ``/server`` segment (production stage; dev/test
environments omit it). Create/publish/answer endpoints require a valid
``accountCode`` (missing → errCode 3104, not a param-missing hint). Multiple
validation failures arrive concatenated without separators in errMsg.
"""

from __future__ import annotations

from typing import Any

import httpx

from .api_utils import do_post, parse_api_response
from .config import LansengerConfig
from .models import (
    QuestionnaireAccountListResult,
    QuestionnaireAnswerDetailResult,
    QuestionnaireAnswerUrlResult,
    QuestionnaireCopyResult,
    QuestionnaireDetailResult,
    QuestionnaireOpResult,
    QuestionnairePageResult,
    QuestionnaireQueryListResult,
    QuestionnaireQuestionDeleteResult,
    QuestionnaireQuestionSaveResult,
    QuestionnaireRecordResult,
    QuestionnaireSaveResult,
    QuestionnaireUploadUrlResult,
)
from .url_helpers import build_api_url

QUESTIONNAIRE_STATUS_DRAFT = 1
QUESTIONNAIRE_STATUS_ONGOING = 2
QUESTIONNAIRE_STATUS_WITHDRAWN = 3
QUESTIONNAIRE_STATUS_FINISHED = 4
QUESTIONNAIRE_STATUS_READY_TO_PUBLISH = 5

QUESTIONNAIRE_SCOPE_INTERNAL = 1
QUESTIONNAIRE_SCOPE_PUBLIC = 2

QUESTIONNAIRE_ANSWER_LIMIT_ONCE = 1
QUESTIONNAIRE_ANSWER_LIMIT_UNLIMITED = -1

# 16 supported question types (questionType strings)
QUESTIONNAIRE_QUESTION_TYPES = (
    "radio", "checkbox", "picturesVote", "fillblank", "name", "phone",
    "email", "sex", "age", "date", "dateTime", "address", "multiScore",
    "remark", "picturesUpload", "filesUpload",
)


def _code_body(questionnaire_code: str, operate_user_id: str) -> dict[str, Any]:
    """Body for the shared ExternalQuestionnaireCodeVO endpoints."""
    body: dict[str, Any] = {"questionnaireCode": questionnaire_code}
    if operate_user_id:
        body["operateUserId"] = operate_user_id
    return body


def _parse_page(data: dict | None) -> dict[str, Any]:
    """Extract the shared PageResult fields."""
    d = data or {}
    return {
        "page_no": d.get("pageNo", 0),
        "page_size": d.get("pageSize", 0),
        "pages": d.get("pages", 0),
        "total": d.get("total", 0),
        "has_more": bool(d.get("hasNextPage", False)),
        "items": d.get("result") or [],
    }


async def save_questionnaire(
    config: LansengerConfig,
    app_token: str,
    title: str,
    account_code: str,
    *,
    code: str = "",
    welcome_speech: str = "",
    bye_speech: str = "",
    cover_resource_id: str = "",
    resource_ids: str = "",
    app_id: str = "",
    user_type: int | None = None,
    create_mobile: str = "",
    create_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireSaveResult:
    """Create a questionnaire, or overwrite an existing one when ``code`` is given (问卷系统 /v1/saveQuestionnaire).

    Args:
        title: Questionnaire title (max 100 chars).
        account_code: Official account CODE — required; missing/unknown → errCode 3104.
        code: Existing questionnaire code to update (empty = create).
        resource_ids: Comma-joined resource id string.
        user_type: 1=phone (createMobile), 2=openid (createUserId); omitted
            when user_token is provided.
    """
    if not title:
        return QuestionnaireSaveResult(success=False, error="title is required")
    if not account_code:
        return QuestionnaireSaveResult(success=False, error="account_code is required")

    url = build_api_url(config, "questionnaires", "save", app_token, user_token=user_token)
    body: dict[str, Any] = {"title": title, "accountCode": account_code}
    if code:
        body["code"] = code
    if welcome_speech:
        body["welcomeSpeech"] = welcome_speech
    if bye_speech:
        body["byeSpeech"] = bye_speech
    if cover_resource_id:
        body["coverResourceId"] = cover_resource_id
    if resource_ids:
        body["resourceIds"] = resource_ids
    if app_id:
        body["appId"] = app_id
    if user_type is not None:
        body["userType"] = user_type
    if create_mobile:
        body["createMobile"] = create_mobile
    if create_user_id:
        body["createUserId"] = create_user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireSaveResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireSaveResult(success=False, error=api_err)
    return QuestionnaireSaveResult(success=True, questionnaire_code=data.get("data"), raw_response=data)


async def save_questionnaire_questions(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    question_list: list[dict[str, Any]],
    *,
    create_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireQuestionSaveResult:
    """Batch-save questions of a questionnaire (new or update) (问卷系统 /v1/saveQuestionList).

    Args:
        questionnaire_code: Questionnaire code.
        question_list: Question dicts in the API's camelCase shape — each item
            requires ``questionName`` / ``questionType`` (16 types, e.g. radio,
            checkbox, fillblank, multiScore) / ``requiredFlag``; options go in
            ``questionOptionList``. Passed through as-is.
    """
    if not questionnaire_code:
        return QuestionnaireQuestionSaveResult(success=False, error="questionnaire_code is required")
    if not question_list:
        return QuestionnaireQuestionSaveResult(success=False, error="question_list is required")

    url = build_api_url(config, "questionnaires", "questions_save", app_token, user_token=user_token)
    body: dict[str, Any] = {"questionnaireCode": questionnaire_code, "questionList": question_list}
    if create_user_id:
        body["createUserId"] = create_user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireQuestionSaveResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireQuestionSaveResult(success=False, error=api_err)
    return QuestionnaireQuestionSaveResult(success=True, saved_count=data.get("data", 0), raw_response=data)


async def delete_questionnaire_question(
    config: LansengerConfig,
    app_token: str,
    question_code: str,
    *,
    create_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireQuestionDeleteResult:
    """Delete a question by its code (问卷系统 /v1/deleteQuestion)."""
    if not question_code:
        return QuestionnaireQuestionDeleteResult(success=False, error="question_code is required")

    url = build_api_url(config, "questionnaires", "question_delete", app_token, user_token=user_token)
    body: dict[str, Any] = {"questionCode": question_code}
    if create_user_id:
        body["createUserId"] = create_user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireQuestionDeleteResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireQuestionDeleteResult(success=False, error=api_err)
    return QuestionnaireQuestionDeleteResult(success=True, deleted=bool(data.get("data")), raw_response=data)


async def publish_questionnaire(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    scope_type: int = QUESTIONNAIRE_SCOPE_INTERNAL,
    staff_ids: list[str] | None = None,
    phones: list[str] | None = None,
    answer_limit: int = QUESTIONNAIRE_ANSWER_LIMIT_ONCE,
    message_flag: int = 0,
    page_flag: int = 0,
    share_flag: int = 0,
    view_stats_flag: int = 1,
    anonym_flag: int = 0,
    publish_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireOpResult:
    """Publish a questionnaire (问卷系统 /v1/publish).

    Args:
        scope_type: 1=internal, 2=public.
        staff_ids/phones: Target staff openIds / mobiles for internal scope.
        answer_limit: 1=answer once, -1=unlimited.
        message_flag/page_flag/share_flag/view_stats_flag/anonym_flag:
            Switches; documented server defaults applied here (0/0/0/1/0).
        publish_user_id: Operator; omit when user_token is provided.
    """
    if not questionnaire_code:
        return QuestionnaireOpResult(success=False, error="questionnaire_code is required")
    if scope_type not in (QUESTIONNAIRE_SCOPE_INTERNAL, QUESTIONNAIRE_SCOPE_PUBLIC):
        return QuestionnaireOpResult(success=False, error="scope_type must be 1 (internal) or 2 (public)")
    if answer_limit not in (QUESTIONNAIRE_ANSWER_LIMIT_ONCE, QUESTIONNAIRE_ANSWER_LIMIT_UNLIMITED):
        return QuestionnaireOpResult(success=False, error="answer_limit must be 1 (once) or -1 (unlimited)")

    url = build_api_url(config, "questionnaires", "publish", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "questionnaireCode": questionnaire_code,
        "scopeType": scope_type,
        "answerLimit": answer_limit,
        "messageFlag": message_flag,
        "pageFlag": page_flag,
        "shareFlag": share_flag,
        "viewStatsFlag": view_stats_flag,
        "anonymFlag": anonym_flag,
    }
    if staff_ids:
        body["staffIdList"] = staff_ids
    if phones:
        body["phoneList"] = phones
    if publish_user_id:
        body["publishUserId"] = publish_user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireOpResult(success=False, error=api_err)
    return QuestionnaireOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def withdraw_questionnaire(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireOpResult:
    """Withdraw a published questionnaire back to draft (问卷系统 /v1/withdraw)."""
    if not questionnaire_code:
        return QuestionnaireOpResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "withdraw", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireOpResult(success=False, error=api_err)
    return QuestionnaireOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def finish_questionnaire(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireOpResult:
    """End an ongoing questionnaire; no more answers accepted (问卷系统 /v1/finish)."""
    if not questionnaire_code:
        return QuestionnaireOpResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "finish", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireOpResult(success=False, error=api_err)
    return QuestionnaireOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def delete_questionnaire(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireOpResult:
    """Delete a questionnaire (问卷系统 /v1/delete)."""
    if not questionnaire_code:
        return QuestionnaireOpResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "delete", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireOpResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireOpResult(success=False, error=api_err)
    return QuestionnaireOpResult(success=True, done=bool(data.get("data")), raw_response=data)


async def fetch_questionnaire_detail(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireDetailResult:
    """Fetch full questionnaire detail incl. question list; requires admin permission (问卷系统 /v1/detail).

    The question list is returned as raw dicts (deep nested DTO).
    """
    if not questionnaire_code:
        return QuestionnaireDetailResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "detail", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return QuestionnaireDetailResult(
        success=True,
        questionnaire_id=d.get("id"),
        code=d.get("code"),
        title=d.get("title"),
        status=d.get("status"),
        account_type=d.get("accountType"),
        account_code=d.get("accountCode"),
        answer_user_count=d.get("answerUserCount"),
        answer_user_times=d.get("answerUserTimes"),
        question_count=d.get("questionCount"),
        questions=d.get("questionList"),
        publish_time=d.get("publishTime"),
        publish_user_name=d.get("publishUserName"),
        create_user_name=d.get("createUserName"),
        create_time=d.get("createTime"),
        raw_response=data,
    )


async def fetch_questionnaire_brief(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireDetailResult:
    """Fetch questionnaire detail without admin check (no question list) (问卷系统 /v1/detailWithoutAuth)."""
    if not questionnaire_code:
        return QuestionnaireDetailResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "detail_no_auth", app_token, user_token=user_token)
    body: dict[str, Any] = {"questionnaireCode": questionnaire_code}
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return QuestionnaireDetailResult(
        success=True,
        questionnaire_id=d.get("id"),
        code=d.get("code"),
        title=d.get("title"),
        status=d.get("status"),
        account_type=d.get("accountType"),
        account_code=d.get("accountCode"),
        answer_user_count=d.get("answerUserCount"),
        answer_user_times=d.get("answerUserTimes"),
        question_count=d.get("questionCount"),
        questions=None,
        create_time=d.get("createTime"),
        create_user_name=d.get("createUserName"),
        raw_response=data,
    )


async def fetch_questionnaire_answer_url(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireAnswerUrlResult:
    """Fetch the answer-page URL of a questionnaire (问卷系统 /v1/getAnswerUrl)."""
    if not questionnaire_code:
        return QuestionnaireAnswerUrlResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "answer_url", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireAnswerUrlResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireAnswerUrlResult(success=False, error=api_err)
    return QuestionnaireAnswerUrlResult(success=True, url=data.get("data"), raw_response=data)


async def copy_questionnaire(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    operate_user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireCopyResult:
    """Copy a questionnaire into a new draft; returns the new code (问卷系统 /v1/copy)."""
    if not questionnaire_code:
        return QuestionnaireCopyResult(success=False, error="questionnaire_code is required")
    url = build_api_url(config, "questionnaires", "copy", app_token, user_token=user_token)
    data, http_err = await do_post(config, url, _code_body(questionnaire_code, operate_user_id), http_client)
    if http_err:
        return QuestionnaireCopyResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireCopyResult(success=False, error=api_err)
    return QuestionnaireCopyResult(success=True, new_code=data.get("data"), raw_response=data)


async def fetch_questionnaires_by_codes(
    config: LansengerConfig,
    app_token: str,
    code_list: list[str],
    *,
    include_deleted: int = 0,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireQueryListResult:
    """Batch-fetch questionnaire basic info by codes (问卷系统 /v1/queryList).

    Args:
        code_list: Questionnaire codes.
        include_deleted: 0=exclude deleted, 1=include.
    """
    if not code_list:
        return QuestionnaireQueryListResult(success=False, error="code_list is required")

    url = build_api_url(config, "questionnaires", "query_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"codeList": code_list, "includeDel": include_deleted}
    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireQueryListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireQueryListResult(success=False, error=api_err)

    items = data.get("data") or []
    return QuestionnaireQueryListResult(success=True, total=len(items), items=items, raw_response=data)


async def fetch_questionnaire_office_accounts(
    config: LansengerConfig,
    app_token: str,
    *,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireAccountListResult:
    """Fetch office accounts the user can manage (问卷系统 /v1/userOfficeAccountList).

    Returns each account's ``code`` — the accountCode required by
    save_questionnaire / publish_questionnaire / answer endpoints.
    """
    url = build_api_url(config, "questionnaires", "user_accounts", app_token, user_token=user_token)
    body: dict[str, Any] = {}
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireAccountListResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireAccountListResult(success=False, error=api_err)

    accounts = data.get("data") or []
    return QuestionnaireAccountListResult(success=True, total=len(accounts), accounts=accounts, raw_response=data)


async def fetch_created_questionnaires(
    config: LansengerConfig,
    app_token: str,
    account_code: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    status: int | None = None,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnairePageResult:
    """Page through questionnaires created under an office account (问卷系统 /v1/createList).

    Args:
        account_code: Official account CODE (required).
        status: 1=draft, 2=ongoing, 3=withdrawn, 4=finished.
    """
    if not account_code:
        return QuestionnairePageResult(success=False, error="account_code is required")

    url = build_api_url(config, "questionnaires", "create_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"pageNo": page_no, "pageSize": page_size, "accountCode": account_code}
    if status is not None:
        body["status"] = status
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnairePageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnairePageResult(success=False, error=api_err)

    d = data.get("data") or {}
    return QuestionnairePageResult(success=True, raw_response=data, **_parse_page(d))


async def fetch_my_created_questionnaires(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    title: str = "",
    status: int | None = None,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnairePageResult:
    """Page through all questionnaires I created (personal + official) (问卷系统 /v1/myCreateList)."""
    if not org_id:
        return QuestionnairePageResult(success=False, error="org_id is required")

    url = build_api_url(config, "questionnaires", "my_create_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"pageNo": page_no, "pageSize": page_size, "orgId": org_id}
    if title:
        body["title"] = title
    if status is not None:
        body["status"] = status
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnairePageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnairePageResult(success=False, error=api_err)

    d = data.get("data") or {}
    return QuestionnairePageResult(success=True, raw_response=data, **_parse_page(d))


async def fetch_participated_questionnaires(
    config: LansengerConfig,
    app_token: str,
    org_id: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    status: int | None = None,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnairePageResult:
    """Page through questionnaires the user has answered (问卷系统 /v1/participationList).

    Args:
        status: Only 2=ongoing and 4=finished are meaningful here.
    """
    if not org_id:
        return QuestionnairePageResult(success=False, error="org_id is required")

    url = build_api_url(config, "questionnaires", "participation_list", app_token, user_token=user_token)
    body: dict[str, Any] = {"pageNo": page_no, "pageSize": page_size, "orgId": org_id}
    if status is not None:
        body["status"] = status
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnairePageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnairePageResult(success=False, error=api_err)

    d = data.get("data") or {}
    return QuestionnairePageResult(success=True, raw_response=data, **_parse_page(d))


async def fetch_answer_records(
    config: LansengerConfig,
    app_token: str,
    account_code: str,
    questionnaire_code: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnairePageResult:
    """Page through answer records of a questionnaire (问卷系统 /v1/answerList)."""
    if not account_code:
        return QuestionnairePageResult(success=False, error="account_code is required")
    if not questionnaire_code:
        return QuestionnairePageResult(success=False, error="questionnaire_code is required")

    url = build_api_url(config, "questionnaires", "answer_list", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "pageNo": page_no, "pageSize": page_size,
        "accountCode": account_code, "questionnaireCode": questionnaire_code,
    }
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnairePageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnairePageResult(success=False, error=api_err)

    d = data.get("data") or {}
    return QuestionnairePageResult(success=True, raw_response=data, **_parse_page(d))


async def fetch_questionnaire_answer_detail(
    config: LansengerConfig,
    app_token: str,
    account_code: str,
    answer_code: str,
    *,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireAnswerDetailResult:
    """Fetch one answer record's full detail: questionnaire + questions + answers (问卷系统 /v1/answerDetail).

    ``answers`` is the raw answerMap ({questionCode: {context}}); ``questionnaire``
    and ``questions`` are raw dicts/lists.
    """
    if not account_code:
        return QuestionnaireAnswerDetailResult(success=False, error="account_code is required")
    if not answer_code:
        return QuestionnaireAnswerDetailResult(success=False, error="answer_code is required")

    url = build_api_url(config, "questionnaires", "answer_detail", app_token, user_token=user_token)
    body: dict[str, Any] = {"accountCode": account_code, "answerCode": answer_code}
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireAnswerDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireAnswerDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return QuestionnaireAnswerDetailResult(
        success=True,
        answer_code=answer_code,
        answer_user_id=d.get("answerUserId"),
        answer_user_name=d.get("answerUserName"),
        answer_status=d.get("answerStatus"),
        answer_type=d.get("answerType"),
        answer_use_time=d.get("answerUseTime"),
        answer_question_count=d.get("answerQuestionCount"),
        answer_commit_time=d.get("answerCommitTime"),
        questionnaire=d.get("questionnaire"),
        questions=d.get("questionList"),
        answers=d.get("answerMap"),
        raw_response=data,
    )


async def fetch_questionnaire_last_answer_detail(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    answer_record_code: str = "",
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireAnswerDetailResult:
    """Fetch the user's last answer detail for a questionnaire (问卷系统 /v1/lastAnswerDetail)."""
    if not questionnaire_code:
        return QuestionnaireAnswerDetailResult(success=False, error="questionnaire_code is required")

    url = build_api_url(config, "questionnaires", "last_answer_detail", app_token, user_token=user_token)
    body: dict[str, Any] = {"questionnaireCode": questionnaire_code}
    if answer_record_code:
        body["answerRecordCode"] = answer_record_code
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireAnswerDetailResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireAnswerDetailResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return QuestionnaireAnswerDetailResult(
        success=True,
        answer_code=d.get("code"),
        answer_user_id=d.get("answerUserId"),
        answer_user_name=d.get("answerUserName"),
        answer_status=d.get("answerStatus"),
        answer_type=d.get("answerType"),
        answer_use_time=d.get("answerUseTime"),
        answer_question_count=d.get("answerQuestionCount"),
        answer_commit_time=d.get("answerCommitTime"),
        questionnaire=d.get("questionnaire"),
        questions=d.get("questionList"),
        answers=d.get("answerMap"),
        raw_response=data,
    )


async def fetch_answer_data(
    config: LansengerConfig,
    app_token: str,
    account_code: str,
    questionnaire_code: str,
    *,
    page_no: int = 1,
    page_size: int = 10,
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnairePageResult:
    """Page through answer data for export; items carry the raw answerMap (问卷系统 /v1/answerData)."""
    if not account_code:
        return QuestionnairePageResult(success=False, error="account_code is required")
    if not questionnaire_code:
        return QuestionnairePageResult(success=False, error="questionnaire_code is required")

    url = build_api_url(config, "questionnaires", "answer_data", app_token, user_token=user_token)
    body: dict[str, Any] = {
        "pageNo": page_no, "pageSize": page_size,
        "accountCode": account_code, "questionnaireCode": questionnaire_code,
    }
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnairePageResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnairePageResult(success=False, error=api_err)

    d = data.get("data") or {}
    return QuestionnairePageResult(success=True, raw_response=data, **_parse_page(d))


async def fetch_questionnaire_last_answer_record(
    config: LansengerConfig,
    app_token: str,
    questionnaire_code: str,
    *,
    answer_record_code: str = "",
    user_id: str = "",
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireRecordResult:
    """Fetch the user's last answer record (main table only) (问卷系统 /v1/lastAnswerRecord)."""
    if not questionnaire_code:
        return QuestionnaireRecordResult(success=False, error="questionnaire_code is required")

    url = build_api_url(config, "questionnaires", "last_answer_record", app_token, user_token=user_token)
    body: dict[str, Any] = {"questionnaireCode": questionnaire_code}
    if answer_record_code:
        body["answerRecordCode"] = answer_record_code
    if user_id:
        body["userId"] = user_id

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireRecordResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireRecordResult(success=False, error=api_err)

    d = data.get("data", {}) or {}
    return QuestionnaireRecordResult(
        success=True,
        record_id=d.get("id"),
        record_code=d.get("code"),
        answer_user_id=d.get("answerUserId"),
        answer_user_name=d.get("answerUserName"),
        answer_status=d.get("answerStatus"),
        answer_type=d.get("answerType"),
        answer_use_time=d.get("answerUseTime"),
        answer_question_count=d.get("answerQuestionCount"),
        answer_commit_time=d.get("answerCommitTime"),
        stats_status=d.get("statsStatus"),
        raw_response=data,
    )


async def fetch_questionnaire_upload_url(
    config: LansengerConfig,
    app_token: str,
    file_name: str,
    md5: str,
    size: int,
    *,
    user_token: str = "",
    http_client: httpx.AsyncClient | None = None,
) -> QuestionnaireUploadUrlResult:
    """Fetch a presigned upload URL; upload via PUT with a ``Content-MD5`` header (问卷系统 /v1/upload).

    Args:
        file_name: File name WITH extension.
        md5: File MD5 hex digest (also the Content-MD5 header value).
        size: File size in bytes.
    """
    if not file_name:
        return QuestionnaireUploadUrlResult(success=False, error="file_name is required")
    if not md5:
        return QuestionnaireUploadUrlResult(success=False, error="md5 is required")
    if not size:
        return QuestionnaireUploadUrlResult(success=False, error="size is required")

    url = build_api_url(config, "questionnaires", "upload_url", app_token, user_token=user_token)
    body: dict[str, Any] = {"fileName": file_name, "md5": md5, "size": size}

    data, http_err = await do_post(config, url, body, http_client)
    if http_err:
        return QuestionnaireUploadUrlResult(success=False, error=http_err)
    ok, api_err = parse_api_response(data)
    if not ok:
        return QuestionnaireUploadUrlResult(success=False, error=api_err)
    return QuestionnaireUploadUrlResult(success=True, url=data.get("data"), raw_response=data)
