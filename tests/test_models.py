"""Tests for Lansenger SDK models."""

from lansenger_sdk.models import (
    SendMessageResult,
    QueryGroupsResult,
    UploadMediaResult,
    DownloadMediaResult,
    AppCardParams,
    LinkCardParams,
    DynamicCardUpdateParams,
    StaffBasicInfoResult,
    StaffDetailResult,
    DepartmentAncestorsResult,
    StaffIdMappingResult,
    ExtraFieldIdsResult,
    StaffSearchResult,
    UserTokenResult,
    UserInfoResult,
    ScheduleAttendeesUpdateResult,
    BotCommandResult,
    BotCommandQueryResult,
    PersonalAppCreateResult,
    PersonalAppInfoResult,
    PersonalAppListResult,
)


def test_send_message_result_success():
    result = SendMessageResult(success=True, message_id="msg123", msg_type="text")
    d = result.to_dict()
    assert d["success"] is True
    assert d["message_id"] == "msg123"


def test_send_message_result_failure():
    result = SendMessageResult(success=False, error="something failed", retryable=True)
    d = result.to_dict()
    assert d["success"] is False
    assert d["error"] == "something failed"


def test_query_groups_result():
    result = QueryGroupsResult(success=True, total_group_ids=5, group_ids=["g1", "g2", "g3"])
    d = result.to_dict()
    assert d["success"] is True
    assert d["total_group_ids"] == 5
    assert d["group_ids"] == ["g1", "g2", "g3"]
    assert d["operation"] == "query_groups"


def test_upload_media_result():
    result = UploadMediaResult(success=True, media_id="media_abc")
    d = result.to_dict()
    assert d["success"] is True
    assert d["media_id"] == "media_abc"


def test_download_media_result():
    result = DownloadMediaResult(success=True, data=b"hello world")
    d = result.to_dict()
    assert d["success"] is True
    assert d["size"] == 11


def test_app_card_params():
    params = AppCardParams(
        chat_id="user123",
        body_title="Card Title",
        is_dynamic=True,
        head_status_info={"description": "Pending", "colour": "#FFB116"},
    )
    assert params.body_title == "Card Title"
    assert params.is_dynamic is True
    assert params.head_status_info["colour"] == "#FFB116"


def test_link_card_params():
    params = LinkCardParams(
        chat_id="user123",
        title="My Link",
        link="https://example.com",
    )
    assert params.title == "My Link"
    assert params.link == "https://example.com"


def test_dynamic_card_update_params():
    params = DynamicCardUpdateParams(
        msg_id="msg123",
        is_last_update=True,
        head_status_info={"description": "Approved", "colour": "#198754"},
    )
    assert params.msg_id == "msg123"
    assert params.is_last_update is True


def test_staff_basic_info_result_success():
    result = StaffBasicInfoResult(
        success=True, org_id="org1", name="Alice", gender=1,
        departments=[{"departmentId": "d1"}],
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["org_id"] == "org1"
    assert d["name"] == "Alice"
    assert d["gender"] == 1
    assert d["departments"] == [{"departmentId": "d1"}]


def test_staff_basic_info_result_failure():
    result = StaffBasicInfoResult(success=False, error="staff_id is required")
    d = result.to_dict()
    assert d["success"] is False
    assert d["error"] == "staff_id is required"


def test_staff_detail_result_success():
    result = StaffDetailResult(
        success=True, name="Bob", email="bob@org.com",
        employee_number="E001", org_name="MyOrg",
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["name"] == "Bob"
    assert d["email"] == "bob@org.com"
    assert d["employee_number"] == "E001"


def test_department_ancestors_result_success():
    ancestors = [{"departmentId": "d1", "departmentName": "Root"}]
    result = DepartmentAncestorsResult(success=True, ancestor_groups=[ancestors])
    d = result.to_dict()
    assert d["success"] is True
    assert d["ancestor_groups"] == [ancestors]


def test_staff_id_mapping_result_success():
    result = StaffIdMappingResult(success=True, staff_id="staff123")
    d = result.to_dict()
    assert d["success"] is True
    assert d["staff_id"] == "staff123"


def test_extra_field_ids_result_success():
    fields = [{"extraFieldId": "ef1"}]
    result = ExtraFieldIdsResult(success=True, has_more=False, total=1, extra_field_ids=fields)
    d = result.to_dict()
    assert d["success"] is True
    assert d["has_more"] is False
    assert d["total"] == 1
    assert d["extra_field_ids"] == fields


def test_staff_search_result_success():
    staff_info = [{"staffId": "s1", "name": "Alice"}]
    result = StaffSearchResult(success=True, has_more=False, total=1, staff_info=staff_info)
    d = result.to_dict()
    assert d["success"] is True
    assert d["has_more"] is False
    assert d["total"] == 1
    assert d["staff_info"] == staff_info


def test_user_token_result_success():
    result = UserTokenResult(
        success=True, user_token="ut123", expires_in=7200,
        refresh_token="rt456", staff_id="staff1",
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["user_token"] == "ut123"
    assert d["expires_in"] == 7200
    assert d["refresh_token"] == "rt456"
    assert d["staff_id"] == "staff1"


def test_user_info_result_success():
    result = UserInfoResult(
        success=True, staff_id="s1", name="Alice", org_name="MyOrg",
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["staff_id"] == "s1"
    assert d["name"] == "Alice"
    assert d["org_name"] == "MyOrg"


def test_schedule_attendees_update_result():
    result = ScheduleAttendeesUpdateResult(
        success=True, schedule_ids=["s1", "s2"], failed_attendees=["f1"],
    )
    d = result.to_dict()
    assert d["success"] is True
    assert d["schedule_ids"] == ["s1", "s2"]
    assert d["failed_attendees"] == ["f1"]


def test_bot_command_result():
    result = BotCommandResult(success=True)
    d = result.to_dict()
    assert d["success"] is True

    result2 = BotCommandResult(success=False, error="bad")
    d2 = result2.to_dict()
    assert d2["error"] == "bad"


def test_bot_command_query_result():
    result = BotCommandQueryResult(success=True, scope_type=7, chat_id="c1")
    d = result.to_dict()
    assert d["success"] is True
    assert d["scope_type"] == 7
    assert d["chat_id"] == "c1"


def test_personal_app_create_result():
    result = PersonalAppCreateResult(success=True, app_id="a1", secret="s1")
    d = result.to_dict()
    assert d["success"] is True
    assert d["app_id"] == "a1"
    assert d["secret"] == "s1"


def test_personal_app_info_result():
    result = PersonalAppInfoResult(success=True, name="MyApp", apigw_addr="https://gw")
    d = result.to_dict()
    assert d["success"] is True
    assert d["name"] == "MyApp"


def test_personal_app_list_result():
    result = PersonalAppListResult(success=True, app_list=[])
    d = result.to_dict()
    assert d["success"] is True
    assert d["app_list"] == []
