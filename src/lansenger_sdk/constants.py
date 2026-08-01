"""Lansenger API constants — endpoints, defaults, media type definitions."""

from __future__ import annotations

API_ENDPOINTS = {
    "auth": {
        "tenant_access_token": "/auth/v3/tenant_access_token/internal",
    },
    "app_token": {
        "create": "/v1/apptoken/create",
    },
    "oauth2": {
        "authorize": "/oauth2/authorize",
        "user_token_create": "/v2/user_token/create",
        "refresh_token_create": "/v1/refresh_token/create",
    },
    "users": {
        "fetch": "/v1/users/fetch",
    },
    "staffs": {
        "fetch": "/v1/staffs/{staff_id}/fetch",
        "detail_fetch": "/v1/staffs/{staff_id}/infor/fetch",
        "department_ancestors": "/v1/staffs/{staff_id}/departmentancestors/fetch",
        "id_mapping": "/v2/staffs/id_mapping/fetch",
        "search": "/v2/staffs/search",
    },
    "departments": {
        "fetch": "/v1/departments/{department_id}/fetch",
        "children_fetch": "/v1/departments/{department_id}/children/fetch",
        "staffs_fetch": "/v1/departments/{department_id}/staffs/fetch",
    },
    "org": {
        "fetch": "/v1/org/{org_id}/fetch",
        "extra_field_ids": "/v1/org/{org_id}/extrafieldids/fetch",
    },
    "websocket": {
        "endpoint": "/v1/ws/endpoint/create",
    },
    "smart_bot": {
        "private_message": "/v1/bot/messages/create",
        "group_message": "/v1/messages/group/create",
    },
    "account_message": {
        "create": "/v1/messages/create",
    },
    "user_message": {
        "create": "/v1/messages/chat/create",
    },
    "bot": {
        "message_create": "/v1/bot/messages/create",
    },
    "sse": {
        "msg_create": "/v1/sse/msg/create",
        "msg_fetch": "/v1/sse/msg/fetch",
    },
    "media": {
        "create": "/v1/medias/create",
        "app_create": "/v1/app/medias/create",
        "app_create_v2": "/v2/app/medias/create",
        "fetch": "/v1/medias/{media_id}/fetch",
        "path_fetch": "/v1/medias/{media_id}/path/fetch",
        "share_fetch": "/v1/media/share/{share_id}/fetch",
    },
    "message": {
        "revoke": "/v1/messages/revoke",
        "dynamic_update": "/v1/messages/dynamic/update",
        "reminder_create": "/v1/messages/reminder/create",
    },
    "groups": {
        "create": "/v2/groups/create",
        "info_fetch": "/v2/groups/{group_id}/info/fetch",
        "info_update": "/v2/groups/{group_id}/info/update",
        "members_fetch": "/v2/groups/{group_id}/members/fetch",
        "members_update": "/v2/groups/{group_id}/members/update",
        "groups_fetch": "/v2/groups/fetch",
        "is_in_group": "/v2/groups/{group_id}/members/is_in_group",
        "delete": "/v2/groups/{group_id}/delete",
    },
    "chats": {
        "fetch": "/v1/chats/fetch",
        "messages_fetch": "/v1/messages/fetch",
    },
    "calendars": {
        "primary": "/v1/calendars/primary",
        "schedule_create": "/v1/calendars/{calendar_id}/schedules/create",
        "schedule_fetch": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/fetch",
        "schedule_update": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/update",
        "schedule_delete": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/delete",
        "schedule_list": "/v1/calendars/{calendar_id}/schedules/fetch",
        "attendees_fetch": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/members/fetch",
        "attendees_create": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/members/create",
        "attendees_delete": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/members/delete",
        "attendees_update": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/members/update",
        "attendees_meta_update": "/v1/calendars/{calendar_id}/schedules/{schedule_id}/members/meta/update",
    },
    "bot_commands": {
        "create": "/v1/bot/commands/create",
        "fetch": "/v1/bot/commands/fetch",
        "delete": "/v1/bot/commands/delete",
    },
    "personal_apps": {
        "create": "/v1/personal/apps/create",
        "update": "/v1/personal/apps/{app_id}/update",
        "fetch": "/v1/personal/apps/{app_id}/fetch",
        "delete": "/v1/personal/apps/{app_id}/delete",
        "list_fetch": "/v1/personal/apps/list/fetch",
    },
    "todo": {
        "create": "/xtra/task/unified/v1/todotask/create",
        "info_update": "/xtra/task/unified/v1/todotask/info/update",
        "status_update": "/xtra/task/unified/v1/todotask/status/update",
        "sender_delete": "/xtra/task/unified/v1/sender/todotask/delete",
        "list_fetch": "/xtra/task/unified/v1/todotask/list/fetch",
        "info_fetch_by_source_id": "/xtra/task/unified/v1/todotask/info/fetchbysourceid",
        "info_fetch": "/xtra/task/unified/v1/todotask/info/fetch",
        "status_count_list_fetch": "/xtra/task/unified/v1/todotask/status/countList/fetch",
        "executor_status_update": "/xtra/task/unified/v1/todotask/executor/status/update",
        "executor_create": "/xtra/task/unified/v1/todotask/executor/create",
        "executor_delete": "/xtra/task/unified/v1/todotask/executor/delete",
        "executor_list_fetch": "/xtra/task/unified/v1/todotask/executor/list/fetch",
        "staff_application_fetch": "/xtra/task/unified/v1/staff/application/fetch",  # not yet implemented
    },
}

OAUTH2_SCOPE_BASIC_USER_INFO = "basic_userinfor"

OAUTH2_SCOPES = {
    "basic_user_info": OAUTH2_SCOPE_BASIC_USER_INFO,
}

MEDIA_TYPE_VIDEO = 1
MEDIA_TYPE_IMAGE = 2
MEDIA_TYPE_AUDIO = 3
MEDIA_TYPE_FILE = 3  # generic file upload

APP_MEDIA_TYPE_FILE = "file"
APP_MEDIA_TYPE_VIDEO = "video"
APP_MEDIA_TYPE_IMAGE = "image"
APP_MEDIA_TYPE_AUDIO = "audio"

# Map app media type string (4.5.4) → message body mediaType int (1=video, 2=image, 3=file)
APP_TO_MSG_MEDIA_TYPE = {
    APP_MEDIA_TYPE_VIDEO: MEDIA_TYPE_VIDEO,   # "video" → 1
    APP_MEDIA_TYPE_IMAGE: MEDIA_TYPE_IMAGE,   # "image" → 2
    APP_MEDIA_TYPE_FILE: MEDIA_TYPE_FILE,     # "file"  → 3
    APP_MEDIA_TYPE_AUDIO: MEDIA_TYPE_FILE,    # "audio" → 3 (msg body has no audio)
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".amr", ".m4a", ".ogg", ".flac", ".aac"}


def guess_media_type(file_path: str) -> Optional[int]:
    """Guess media_type for core upload (4.5.1): 1=video, 2=image, 3=audio/file.

    Returns None for unknown types so callers can fall back to their own default.
    """
    import os

    ext = os.path.splitext(file_path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return MEDIA_TYPE_IMAGE
    if ext in VIDEO_EXTENSIONS:
        return MEDIA_TYPE_VIDEO
    if ext in AUDIO_EXTENSIONS:
        return MEDIA_TYPE_AUDIO
    return None


def guess_app_media_type(file_path: str) -> str:
    """Guess app media type string ('file', 'video', 'image', 'audio') from file extension — for 4.5.4."""
    import os

    ext = os.path.splitext(file_path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return APP_MEDIA_TYPE_IMAGE
    if ext in VIDEO_EXTENSIONS:
        return APP_MEDIA_TYPE_VIDEO
    if ext in AUDIO_EXTENSIONS:
        return APP_MEDIA_TYPE_AUDIO
    return APP_MEDIA_TYPE_FILE
