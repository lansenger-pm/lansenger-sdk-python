"""Tests for Lansenger SDK constants."""

from lansenger_sdk.constants import (
    API_ENDPOINTS,
    MEDIA_TYPE_VIDEO,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_FILE,
    guess_media_type,
)


def test_media_type_constants():
    assert MEDIA_TYPE_VIDEO == 1
    assert MEDIA_TYPE_IMAGE == 2
    assert MEDIA_TYPE_FILE == 3


def test_guess_media_type_image():
    assert guess_media_type("photo.jpg") == MEDIA_TYPE_IMAGE
    assert guess_media_type("photo.png") == MEDIA_TYPE_IMAGE
    assert guess_media_type("photo.gif") == MEDIA_TYPE_IMAGE
    assert guess_media_type("photo.webp") == MEDIA_TYPE_IMAGE


def test_guess_media_type_video():
    assert guess_media_type("video.mp4") == MEDIA_TYPE_VIDEO
    assert guess_media_type("video.mov") == MEDIA_TYPE_VIDEO
    assert guess_media_type("clip.avi") == MEDIA_TYPE_VIDEO


def test_guess_media_type_file():
    assert guess_media_type("report.pdf") == MEDIA_TYPE_FILE
    assert guess_media_type("data.xlsx") == MEDIA_TYPE_FILE
    assert guess_media_type("archive.zip") == MEDIA_TYPE_FILE
    assert guess_media_type("unknown.xyz") == MEDIA_TYPE_FILE


def test_api_endpoints_structure():
    assert "smart_bot" in API_ENDPOINTS
    assert "private_message" in API_ENDPOINTS["smart_bot"]
    assert "group_message" in API_ENDPOINTS["smart_bot"]
    assert "message" in API_ENDPOINTS
    assert "revoke" in API_ENDPOINTS["message"]
    assert "dynamic_update" in API_ENDPOINTS["message"]
    assert "groups" in API_ENDPOINTS
    assert "fetch" in API_ENDPOINTS["groups"]
    assert "staffs" in API_ENDPOINTS
    assert "fetch" in API_ENDPOINTS["staffs"]
    assert "detail_fetch" in API_ENDPOINTS["staffs"]
    assert "department_ancestors" in API_ENDPOINTS["staffs"]
    assert "id_mapping" in API_ENDPOINTS["staffs"]
    assert "search" in API_ENDPOINTS["staffs"]
    assert "org" in API_ENDPOINTS
    assert "extra_field_ids" in API_ENDPOINTS["org"]


def test_staffs_endpoint_paths():
    assert API_ENDPOINTS["staffs"]["fetch"] == "/v1/staffs/{staff_id}/fetch"
    assert API_ENDPOINTS["staffs"]["detail_fetch"] == "/v1/staffs/{staff_id}/infor/fetch"
    assert API_ENDPOINTS["staffs"]["department_ancestors"] == "/v1/staffs/{staff_id}/departmentancestors/fetch"
    assert API_ENDPOINTS["staffs"]["id_mapping"] == "/v2/staffs/id_mapping/fetch"
    assert API_ENDPOINTS["staffs"]["search"] == "/v2/staffs/search"


def test_org_endpoint_paths():
    assert API_ENDPOINTS["org"]["extra_field_ids"] == "/v1/org/{org_id}/extrafieldids/fetch"


def test_groups_v2_endpoint_paths():
    assert "groups_v2" in API_ENDPOINTS
    assert API_ENDPOINTS["groups_v2"]["create"] == "/v2/groups/create"
    assert API_ENDPOINTS["groups_v2"]["info_fetch"] == "/v2/groups/{group_id}/info/fetch"
    assert API_ENDPOINTS["groups_v2"]["members_fetch"] == "/v2/groups/{group_id}/members/fetch"
    assert API_ENDPOINTS["groups_v2"]["groups_fetch"] == "/v2/groups/fetch"
    assert API_ENDPOINTS["groups_v2"]["is_in_group"] == "/v2/groups/{group_id}/members/is_in_group"


def test_departments_endpoint_paths():
    assert "departments" in API_ENDPOINTS
    assert API_ENDPOINTS["departments"]["fetch"] == "/v1/departments/{department_id}/fetch"
    assert API_ENDPOINTS["departments"]["children_fetch"] == "/v1/departments/{department_id}/children/fetch"
    assert API_ENDPOINTS["departments"]["staffs_fetch"] == "/v1/departments/{department_id}/staffs/fetch"


def test_bot_endpoint_paths():
    assert "bot" in API_ENDPOINTS
    assert API_ENDPOINTS["bot"]["message_create"] == "/v1/bot/messages/create"


def test_sse_endpoint_paths():
    assert "sse" in API_ENDPOINTS
    assert API_ENDPOINTS["sse"]["msg_create"] == "/v1/sse/msg/create"
    assert API_ENDPOINTS["sse"]["msg_fetch"] == "/v1/sse/msg/fetch"