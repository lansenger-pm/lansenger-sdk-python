"""Lansenger SDK sync client — blocking wrapper around the async client.

Provides the same API as LansengerClient but with synchronous (blocking)
method calls. Useful for scripts, CLI tools, and non-async frameworks.

Uses asyncio.run() for each call. If an event loop is already running
(e.g. inside an async framework), falls back to a thread-pool executor.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, List, Optional

from .client import LansengerClient
from .config import LansengerConfig
from .models import (
    AccountMessageResult,
    AppCardParams,
    BotMessageResult,
    CalendarPrimaryResult,
    ChatGroupInfo,
    ChatListResult,
    ChatMessageInfo,
    ChatMessagesResult,
    ChatStaffInfo,
    CreateGroupResult,
    DepartmentAncestorsResult,
    DepartmentChildrenResult,
    DepartmentDetailResult,
    DepartmentStaffsResult,
    DownloadMediaResult,
    DynamicCardUpdateParams,
    ExtraFieldIdsResult,
    GroupCreateInfo,
    GroupInfoResult,
    GroupListResult,
    GroupMemberResult,
    IsInGroupResult,
    LinkCardParams,
    OaCardParams,
    OrgInfoResult,
    QueryGroupsResult,
    ScheduleAttendeesResult,
    ScheduleCreateResult,
    ScheduleInfoResult,
    ScheduleListResult,
    SendMessageResult,
    StaffBasicInfoResult,
    StaffDetailResult,
    StaffIdMappingResult,
    StaffSearchResult,
    StreamMessageResult,
    TodoTaskCreateResult,
    TodoTaskExecutorListResult,
    TodoTaskInfoResult,
    TodoTaskListResult,
    TodoTaskStatusCountResult,
    UpdateGroupMembersResult,
    UpdateGroupResult,
    UserMessageResult,
    UserInfoResult,
    UserTokenResult,
)

logger = logging.getLogger("lansenger_sdk.sync_client")


def _run_async(coro):
    """Run an async coroutine from a synchronous context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=30)


class LansengerSyncClient:
    """Synchronous (blocking) wrapper around LansengerClient.

    Usage:
        client = LansengerSyncClient.from_env()
        result = client.send_text(chat_id="user123", content="Hello")
        print(result.success, result.message_id)

    Each method call creates/tears down an ephemeral async client internally.
    For high-frequency usage in async contexts, use LansengerClient directly.
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        api_gateway_url: str = "https://open.e.lanxin.cn/open/apigw",
        passport_url: str = "",
        http_timeout: float = 30.0,
        encoding_key: str = "",
        callback_token: str = "",
    ):
        self._app_id = app_id
        self._app_secret = app_secret
        self._api_gateway_url = api_gateway_url
        self._passport_url = passport_url
        self._http_timeout = http_timeout
        self._encoding_key = encoding_key
        self._callback_token = callback_token

    @classmethod
    def from_env(cls) -> LansengerSyncClient:
        """Create client from environment variables."""
        config = LansengerConfig.from_env()
        return cls(
            app_id=config.app_id,
            app_secret=config.app_secret,
            api_gateway_url=config.api_gateway_url,
            passport_url=config.passport_url,
            http_timeout=config.http_timeout,
            encoding_key=config.encoding_key,
            callback_token=config.callback_token,
        )

    @classmethod
    def from_config(cls, config: LansengerConfig) -> LansengerSyncClient:
        """Create client from a LansengerConfig instance."""
        return cls(
            app_id=config.app_id,
            app_secret=config.app_secret,
            api_gateway_url=config.api_gateway_url,
            passport_url=config.passport_url,
            http_timeout=config.http_timeout,
            encoding_key=config.encoding_key,
            callback_token=config.callback_token,
        )

    @classmethod
    def from_store(cls, profile: str = "default", path: Optional[str] = None) -> LansengerSyncClient:
        """Create client from a CredentialStore profile.

        Args:
            profile: Named profile in the credential store (default: "default").
            path: Optional custom path to the state file.

        Raises LansengerConfigError if the profile has no credentials.
        """
        from .persistence import CredentialStore
        from .exceptions import LansengerConfigError
        store = CredentialStore(path=path, profile=profile)
        creds = store.load_credentials()
        if not creds.get("app_id") or not creds.get("app_secret"):
            raise LansengerConfigError(
                f"No credentials found for profile '{profile}'. "
                "Run lansenger config set or set LANSENGER_APP_ID / LANSENGER_APP_SECRET env vars."
            )
        config = LansengerConfig(
            app_id=creds["app_id"],
            app_secret=creds["app_secret"],
            api_gateway_url=creds.get("api_gateway_url") or "https://open.e.lanxin.cn/open/apigw",
            passport_url=creds.get("passport_url", ""),
        )
        return cls.from_config(config)

    async def _ephemeral_call(self, method_name: str, **kwargs) -> Any:
        """Create an ephemeral async client, call method, then close."""
        client = LansengerClient(
            app_id=self._app_id,
            app_secret=self._app_secret,
            api_gateway_url=self._api_gateway_url,
            http_timeout=self._http_timeout,
            encoding_key=self._encoding_key,
            callback_token=self._callback_token,
        )
        try:
            method = getattr(client, method_name)
            result = await method(**kwargs)
            return result
        finally:
            await client.close()

    async def _ephemeral_call_with_positional(self, method_name: str, args: list, kwargs: dict) -> Any:
        """Create an ephemeral async client, call method with positional args, then close."""
        client = LansengerClient(
            app_id=self._app_id,
            app_secret=self._app_secret,
            api_gateway_url=self._api_gateway_url,
            http_timeout=self._http_timeout,
        )
        try:
            method = getattr(client, method_name)
            result = await method(*args, **kwargs)
            return result
        finally:
            await client.close()

    def send_text(
        self,
        chat_id: str,
        content: str,
        *,
        file_path: str = "",
        media_type: Optional[int] = None,
        reminder_all: bool = False,
        reminder_user_ids: Optional[List[str]] = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send a plain text message (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_text",
            chat_id=chat_id,
            content=content,
            file_path=file_path,
            media_type=media_type,
            reminder_all=reminder_all,
            reminder_user_ids=reminder_user_ids,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_markdown(
        self,
        chat_id: str,
        content: str,
        *,
        reminder_all: bool = False,
        reminder_user_ids: Optional[List[str]] = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send a Markdown message (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_markdown",
            chat_id=chat_id,
            content=content,
            reminder_all=reminder_all,
            reminder_user_ids=reminder_user_ids,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_file(
        self,
        chat_id: str,
        file_path: str,
        *,
        caption: str = "",
        media_type: Optional[int] = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send a file/image/video (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_file",
            chat_id=chat_id,
            file_path=file_path,
            caption=caption,
            media_type=media_type,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_image_url(
        self,
        chat_id: str,
        image_url: str,
        *,
        caption: str = "",
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an image from URL (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_image_url",
            chat_id=chat_id,
            image_url=image_url,
            caption=caption,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_link_card(
        self,
        chat_id: str,
        title: str,
        link: str,
        *,
        description: str = "",
        icon_link: str = "",
        pc_link: str = "",
        pad_link: str = "",
        from_name: str = "",
        from_icon_link: str = "",
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send a linkCard (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_link_card",
            chat_id=chat_id,
            title=title,
            link=link,
            description=description,
            icon_link=icon_link,
            pc_link=pc_link,
            pad_link=pad_link,
            from_name=from_name,
            from_icon_link=from_icon_link,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_link_card_with_params(self, params: LinkCardParams) -> SendMessageResult:
        """Send a linkCard using LinkCardParams (blocking)."""
        return _run_async(self._ephemeral_call_with_positional(
            "send_link_card_with_params",
            args=[params],
            kwargs={},
        ))

    def send_app_articles(
        self,
        chat_id: str,
        articles: List[Dict[str, str]],
        *,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an appArticles card (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_app_articles",
            chat_id=chat_id,
            articles=articles,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_app_card(
        self,
        chat_id: str,
        body_title: str,
        *,
        head_title: str = "",
        body_sub_title: str = "",
        body_content: str = "",
        signature: str = "",
        fields: Optional[List[Dict[str, str]]] = None,
        links: Optional[List[Dict[str, str]]] = None,
        card_link: str = "",
        pc_card_link: str = "",
        pad_card_link: str = "",
        is_dynamic: bool = False,
        head_status_info: Optional[Dict[str, str]] = None,
        staff_id: str = "",
        head_icon_url: str = "",
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an appCard (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_app_card",
            chat_id=chat_id,
            body_title=body_title,
            head_title=head_title,
            body_sub_title=body_sub_title,
            body_content=body_content,
            signature=signature,
            fields=fields,
            links=links,
            card_link=card_link,
            pc_card_link=pc_card_link,
            pad_card_link=pad_card_link,
            is_dynamic=is_dynamic,
            head_status_info=head_status_info,
            staff_id=staff_id,
            head_icon_url=head_icon_url,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_app_card_with_params(self, params: AppCardParams) -> SendMessageResult:
        """Send an appCard using AppCardParams (blocking)."""
        return _run_async(self._ephemeral_call_with_positional(
            "send_app_card_with_params",
            args=[params],
            kwargs={},
        ))

    def send_oacard(
        self,
        chat_id: str,
        title: str,
        *,
        head: str = "",
        sub_title: str = "",
        staff_id: str = "",
        fields: Optional[List[Dict[str, str]]] = None,
        link: str = "",
        pc_link: str = "",
        pad_link: str = "",
        card_action: Optional[Dict[str, Any]] = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an oaCard (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_oacard",
            chat_id=chat_id,
            title=title,
            head=head,
            sub_title=sub_title,
            staff_id=staff_id,
            fields=fields,
            link=link,
            pc_link=pc_link,
            pad_link=pad_link,
            card_action=card_action,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
        ))

    def send_oacard_with_params(self, params: OaCardParams) -> SendMessageResult:
        """Send an oaCard using OaCardParams (blocking)."""
        return _run_async(self._ephemeral_call_with_positional(
            "send_oacard_with_params",
            args=[params],
            kwargs={},
        ))

    def update_dynamic_card(
        self,
        msg_id: str,
        *,
        head_status_info: Optional[Dict[str, str]] = None,
        links: Optional[List[Dict[str, str]]] = None,
        is_last_update: bool = False,
    ) -> SendMessageResult:
        """Update a dynamic appCard status (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_dynamic_card",
            msg_id=msg_id,
            head_status_info=head_status_info,
            links=links,
            is_last_update=is_last_update,
        ))

    def update_dynamic_card_with_params(self, params: DynamicCardUpdateParams) -> SendMessageResult:
        """Update a dynamic card using DynamicCardUpdateParams (blocking)."""
        return _run_async(self._ephemeral_call_with_positional(
            "update_dynamic_card_with_params",
            args=[params],
            kwargs={},
        ))

    def revoke_message(
        self,
        message_ids: List[str],
        *,
        chat_type: str = "bot",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Revoke messages (blocking)."""
        return _run_async(self._ephemeral_call(
            "revoke_message",
            message_ids=message_ids,
            chat_type=chat_type,
            sender_id=sender_id,
        ))

    def query_groups(
        self,
        *,
        page_offset: int = 1,
        page_size: int = 100,
    ) -> QueryGroupsResult:
        """Query bot's groups (blocking)."""
        return _run_async(self._ephemeral_call(
            "query_groups",
            page_offset=page_offset,
            page_size=page_size,
        ))

    def upload_media(
        self,
        file_path: str,
        *,
        media_type: Optional[int] = None,
    ) -> SendMessageResult:
        """Upload a media file (blocking)."""
        return _run_async(self._ephemeral_call(
            "upload_media",
            file_path=file_path,
            media_type=media_type,
        ))

    def download_media(self, media_id: str) -> DownloadMediaResult:
        """Download media bytes (blocking)."""
        return _run_async(self._ephemeral_call(
            "download_media",
            media_id=media_id,
        ))

    def download_media_to_file(
        self,
        media_id: str,
        *,
        target_path: Optional[str] = None,
        media_type: str = "file",
    ) -> str:
        """Download media to a file (blocking)."""
        return _run_async(self._ephemeral_call(
            "download_media_to_file",
            media_id=media_id,
            target_path=target_path,
            media_type=media_type,
        ))

    def health_check(self) -> bool:
        """Verify credentials work (blocking)."""
        return _run_async(self._ephemeral_call("health_check"))

    def get_token(self) -> str:
        """Get current app access token (blocking)."""
        return _run_async(self._ephemeral_call("get_token"))

    # ── OAuth2: User authentication (sync wrappers) ───────────────────

    def build_authorize_url(
        self,
        redirect_uri: str,
        *,
        scope: str | list[str] | None = None,
        state: str | None = None,
    ) -> str:
        """Build the OAuth2 authorize URL for user identity verification (blocking).

        This is a synchronous convenience wrapper. The authorize URL is
        built purely from config parameters — no HTTP call needed.
        """
        from .oauth import build_authorize_url
        config = LansengerConfig(
            app_id=self._app_id,
            app_secret=self._app_secret,
            api_gateway_url=self._api_gateway_url,
            passport_url=self._passport_url,
        )
        return build_authorize_url(config, redirect_uri=redirect_uri, scope=scope, state=state)

    @staticmethod
    def parse_authorize_callback(query_string: str | dict) -> dict:
        """Parse OAuth2 authorize callback parameters."""
        from .oauth import parse_authorize_callback
        return parse_authorize_callback(query_string)

    @staticmethod
    def validate_callback_state(callback_state: str, expected_state: str) -> bool:
        """Validate OAuth2 callback state (CSRF protection)."""
        from .oauth import validate_callback_state
        return validate_callback_state(callback_state, expected_state)

    def exchange_code(
        self,
        code: str,
        *,
        redirect_uri: str = "",
    ) -> UserTokenResult:
        """Exchange an OAuth2 authorization code for userToken (blocking)."""
        return _run_async(self._ephemeral_call(
            "exchange_code",
            code=code,
            redirect_uri=redirect_uri,
        ))

    def refresh_user_token(
        self,
        refresh_token: str,
        *,
        scope: str = "",
    ) -> UserTokenResult:
        """Refresh an expired userToken using refreshToken (blocking)."""
        return _run_async(self._ephemeral_call(
            "refresh_user_token",
            refresh_token=refresh_token,
            scope=scope,
        ))

    def fetch_user_info(
        self,
        user_token: str,
    ) -> UserInfoResult:
        """Fetch a Lansenger user's basic information (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_user_info",
            user_token=user_token,
        ))

    # ── Contacts / Staff (sync wrappers) ────────────────────────────────

    def fetch_staff_basic_info(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> StaffBasicInfoResult:
        """Fetch a staff member's basic information (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_staff_basic_info",
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_staff_detail(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> StaffDetailResult:
        """Fetch a staff member's detailed information (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_staff_detail",
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_department_ancestors(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> DepartmentAncestorsResult:
        """Fetch ancestor department chain for a staff member (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_department_ancestors",
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_staff_id_mapping(
        self,
        org_id: str,
        id_type: str,
        id_value: str,
        *,
        user_token: str = "",
    ) -> StaffIdMappingResult:
        """Map a unique identifier to staffId (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_staff_id_mapping",
            org_id=org_id,
            id_type=id_type,
            id_value=id_value,
            user_token=user_token,
        ))

    def fetch_org_extra_field_ids(
        self,
        org_id: str,
        *,
        user_token: str = "",
        page: int = 1,
        page_size: int = 1000,
    ) -> ExtraFieldIdsResult:
        """Fetch organization extra field ID list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_org_extra_field_ids",
            org_id=org_id,
            user_token=user_token,
            page=page,
            page_size=page_size,
        ))

    def search_staff(
        self,
        keyword: str,
        *,
        user_token: str = "",
        user_id: str = "",
        recursive: bool = True,
        sector_ids=None,
        page=None,
        page_size=None,
    ) -> StaffSearchResult:
        """Search staff by keyword (blocking)."""
        return _run_async(self._ephemeral_call(
            "search_staff",
            keyword=keyword,
            user_token=user_token,
            user_id=user_id,
            recursive=recursive,
            sector_ids=sector_ids,
            page=page,
            page_size=page_size,
        ))

    # ── Bot channel messages (sync wrappers) ──────────────────────────

    def send_bot_message(
        self,
        msg_type: str,
        msg_data: dict,
        chat_ids=None,
        department_ids=None,
        *,
        user_token: str = "",
        entry_id: str = "",
        is_group: bool = False,
    ) -> BotMessageResult:
        return _run_async(self._ephemeral_call(
            "send_bot_message",
            msg_type=msg_type,
            msg_data=msg_data,
            chat_ids=chat_ids,
            department_ids=department_ids,
            user_token=user_token,
            entry_id=entry_id,
            is_group=is_group,
        ))

    # ── Account message (4.6.1 公号通道) (sync wrapper) ──────────────

    def send_account_message(
        self,
        msg_type: str,
        msg_data: dict,
        chat_ids=None,
        department_ids=None,
        *,
        account_id: str = "",
        entry_id: str = "",
        attach: str = "",
        user_token: str = "",
    ) -> AccountMessageResult:
        return _run_async(self._ephemeral_call(
            "send_account_message",
            msg_type=msg_type,
            msg_data=msg_data,
            chat_ids=chat_ids,
            department_ids=department_ids,
            account_id=account_id,
            entry_id=entry_id,
            attach=attach,
            user_token=user_token,
        ))

    # ── User private chat message (4.6.3) (sync wrapper) ──────────

    def send_user_message(
        self,
        receiver_id: str,
        msg_type: str,
        msg_data: dict,
        *,
        user_token: str = "",
        common=None,
        uuid: str = "",
    ) -> UserMessageResult:
        return _run_async(self._ephemeral_call(
            "send_user_message",
            receiver_id=receiver_id,
            msg_type=msg_type,
            msg_data=msg_data,
            user_token=user_token,
            common=common,
            uuid=uuid,
        ))

    # ── Group message (4.6.2 群聊) (sync wrapper) ──────────────────

    def send_group_message(
        self,
        group_id: str,
        msg_type: str,
        msg_data: dict,
        *,
        user_token: str = "",
        sender_id: str = "",
        reminder_all: bool = False,
        reminder_user_ids: Optional[List[str]] = None,
        outlines: str = "",
        uuid: str = "",
        entry_id: str = "",
    ) -> SendMessageResult:
        return _run_async(self._ephemeral_call(
            "send_group_message",
            group_id=group_id,
            msg_type=msg_type,
            msg_data=msg_data,
            user_token=user_token,
            sender_id=sender_id,
            reminder_all=reminder_all,
            reminder_user_ids=reminder_user_ids,
            outlines=outlines,
            uuid=uuid,
            entry_id=entry_id,
        ))

    # ── Streaming messages (sync wrappers) ────────────────────────────

    def create_stream_message(
        self,
        receiver_id: str,
        receiver_type: str,
        stream_id: str,
    ) -> StreamMessageResult:
        return _run_async(self._ephemeral_call(
            "create_stream_message",
            receiver_id=receiver_id,
            receiver_type=receiver_type,
            stream_id=stream_id,
        ))

    def fetch_stream_message(
        self,
        msg_id: str,
    ) -> StreamMessageResult:
        return _run_async(self._ephemeral_call(
            "fetch_stream_message",
            msg_id=msg_id,
        ))

    # ── Groups V2 (sync wrappers) ─────────────────────────────────────

    def create_group(
        self,
        name: str,
        org_id: str,
        *,
        owner_id: str = "",
        description: str = "",
        avatar_id: str = "",
        staff_id_list=None,
        department_id_list=None,
        user_token: str = "",
        apply_request_id: str = "",
        apply_notes: str = "",
        apply_global_unique_id: str = "",
        apply_session_unique_id: str = "",
    ) -> CreateGroupResult:
        return _run_async(self._ephemeral_call(
            "create_group",
            name=name,
            org_id=org_id,
            owner_id=owner_id,
            description=description,
            avatar_id=avatar_id,
            staff_id_list=staff_id_list,
            department_id_list=department_id_list,
            user_token=user_token,
            apply_request_id=apply_request_id,
            apply_notes=apply_notes,
            apply_global_unique_id=apply_global_unique_id,
            apply_session_unique_id=apply_session_unique_id,
        ))

    def fetch_group_info(
        self,
        group_id: str,
        *,
        user_token: str = "",
    ) -> GroupInfoResult:
        return _run_async(self._ephemeral_call(
            "fetch_group_info",
            group_id=group_id,
            user_token=user_token,
        ))

    def fetch_group_members(
        self,
        group_id: str,
        *,
        user_token: str = "",
        page_offset: int = 0,
        page_size: int = 100,
    ) -> GroupMemberResult:
        return _run_async(self._ephemeral_call(
            "fetch_group_members",
            group_id=group_id,
            user_token=user_token,
            page_offset=page_offset,
            page_size=page_size,
        ))

    def fetch_group_list(
        self,
        *,
        user_token: str = "",
        page_offset: int = 0,
        page_size: int = 100,
    ) -> GroupListResult:
        return _run_async(self._ephemeral_call(
            "fetch_group_list",
            user_token=user_token,
            page_offset=page_offset,
            page_size=page_size,
        ))

    def check_is_in_group(
        self,
        group_id: str,
        *,
        user_token: str = "",
        staff_id: str = "",
    ) -> IsInGroupResult:
        return _run_async(self._ephemeral_call(
            "check_is_in_group",
            group_id=group_id,
            user_token=user_token,
            staff_id=staff_id,
        ))

    def update_group_info(
        self,
        group_id: str,
        *,
        name: str = "",
        description: str = "",
        avatar_id: str = "",
        owner_id: str = "",
        assistant=None,
        demote_assistant=None,
        manage_mode=None,
        location_share=None,
        needs_confirm=None,
        is_public=None,
        max_members=None,
        max_history_msg_count=None,
        remind_all=None,
        send_msg_status=None,
        user_token: str = "",
    ) -> UpdateGroupResult:
        return _run_async(self._ephemeral_call(
            "update_group_info",
            group_id=group_id,
            name=name,
            description=description,
            avatar_id=avatar_id,
            owner_id=owner_id,
            assistant=assistant,
            demote_assistant=demote_assistant,
            manage_mode=manage_mode,
            location_share=location_share,
            needs_confirm=needs_confirm,
            is_public=is_public,
            max_members=max_members,
            max_history_msg_count=max_history_msg_count,
            remind_all=remind_all,
            send_msg_status=send_msg_status,
            user_token=user_token,
        ))

    def update_group_members(
        self,
        group_id: str,
        *,
        add_user_list=None,
        del_user_list=None,
        add_department_id_list=None,
        user_token: str = "",
    ) -> UpdateGroupMembersResult:
        return _run_async(self._ephemeral_call(
            "update_group_members",
            group_id=group_id,
            add_user_list=add_user_list,
            del_user_list=del_user_list,
            add_department_id_list=add_department_id_list,
            user_token=user_token,
        ))

    def fetch_org_info(
        self,
        org_id: str,
        *,
        user_token: str = "",
    ) -> OrgInfoResult:
        return _run_async(self._ephemeral_call(
            "fetch_org_info",
            org_id=org_id,
            user_token=user_token,
        ))

    # ── Departments (sync wrappers) ───────────────────────────────────

    def fetch_department_detail(
        self,
        department_id: str,
        *,
        user_token: str = "",
        tag_id: str = "",
    ) -> DepartmentDetailResult:
        return _run_async(self._ephemeral_call(
            "fetch_department_detail",
            department_id=department_id,
            user_token=user_token,
            tag_id=tag_id,
        ))

    def fetch_department_children(
        self,
        department_id: str,
        *,
        user_token: str = "",
    ) -> DepartmentChildrenResult:
        return _run_async(self._ephemeral_call(
            "fetch_department_children",
            department_id=department_id,
            user_token=user_token,
        ))

    def fetch_department_staffs(
        self,
        department_id: str,
        *,
        user_token: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> DepartmentStaffsResult:
        return _run_async(self._ephemeral_call(
            "fetch_department_staffs",
            department_id=department_id,
            user_token=user_token,
            page=page,
            page_size=page_size,
        ))

    # ── Unified Todo (4.33) (sync wrappers) ──────────────────────────

    def create_todo_task(
        self,
        title: str,
        link: str,
        pc_link: str,
        executor_ids: list,
        org_id: str,
        type: int = 1,
        *,
        source_id: str = "",
        desc: str = "",
        sender_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Create a unified todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "create_todo_task",
            title=title,
            link=link,
            pc_link=pc_link,
            executor_ids=executor_ids,
            org_id=org_id,
            type=type,
            source_id=source_id,
            desc=desc,
            sender_id=sender_id,
            user_token=user_token,
        ))

    def update_todo_task(
        self,
        todotask_id: str,
        title: str,
        link: str,
        pc_link: str,
        org_id: str,
        *,
        desc: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Update a todo task's content (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_todo_task",
            todotask_id=todotask_id,
            title=title,
            link=link,
            pc_link=pc_link,
            org_id=org_id,
            desc=desc,
            user_token=user_token,
        ))

    def update_todo_task_status(
        self,
        todotask_id: str,
        status: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Update a todo task's status (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_todo_task_status",
            todotask_id=todotask_id,
            status=status,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
        ))

    def delete_todo_task(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Delete a todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_todo_task",
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_todo_task_list(
        self,
        org_id: str,
        *,
        app_ids=None,
        staff_id: str = "",
        status_list=None,
        user_token: str = "",
    ) -> TodoTaskListResult:
        """Fetch todo task list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_todo_task_list",
            org_id=org_id,
            app_ids=app_ids,
            staff_id=staff_id,
            status_list=status_list,
            user_token=user_token,
        ))

    def fetch_todo_task_by_source_id(
        self,
        source_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskInfoResult:
        """Fetch todo task by sourceId (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_todo_task_by_source_id",
            source_id=source_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_todo_task_by_id(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskInfoResult:
        """Fetch todo task by todotaskId (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_todo_task_by_id",
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
        ))

    def fetch_todo_task_status_counts(
        self,
        staff_id: str,
        org_id: str,
        *,
        app_id: str = "",
        status_list=None,
        user_token: str = "",
    ) -> TodoTaskStatusCountResult:
        """Fetch todo task status counts (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_todo_task_status_counts",
            staff_id=staff_id,
            org_id=org_id,
            app_id=app_id,
            status_list=status_list,
            user_token=user_token,
        ))

    def update_executor_status(
        self,
        executor_status_list: list,
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Update executor status for a todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_executor_status",
            executor_status_list=executor_status_list,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
        ))

    def add_executors(
        self,
        executor_ids: list,
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Add executors to a todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "add_executors",
            executor_ids=executor_ids,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
        ))

    def delete_executors(
        self,
        executor_ids: list,
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Delete executors from a todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_executors",
            executor_ids=executor_ids,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
        ))

    def fetch_executor_list(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        status_list=None,
        user_token: str = "",
    ) -> TodoTaskExecutorListResult:
        """Fetch executor list for a todo task (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_executor_list",
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            status_list=status_list,
            user_token=user_token,
        ))

    # ── Calendar & Schedule (4.23) (sync wrappers) ──────────────────

    def fetch_primary_calendar(
        self,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> CalendarPrimaryResult:
        """Get the primary calendar (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_primary_calendar",
            user_token=user_token,
            user_id=user_id,
        ))

    def create_schedule(
        self,
        calendar_id: str,
        summary: str,
        start_time: dict,
        end_time: dict,
        attendees: list,
        *,
        description: str = "",
        all_day: str = "no",
        repeat_type: str = "no",
        rule: str = "",
        expire_date_type: str = "no",
        reminder_type: str = "yes",
        attendee_permissions: str = "can_see",
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Create a schedule/event (blocking)."""
        return _run_async(self._ephemeral_call(
            "create_schedule",
            calendar_id=calendar_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            description=description,
            all_day=all_day,
            repeat_type=repeat_type,
            rule=rule,
            expire_date_type=expire_date_type,
            reminder_type=reminder_type,
            attendee_permissions=attendee_permissions,
            user_token=user_token,
            user_id=user_id,
        ))

    def fetch_schedule(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleInfoResult:
        """Query a schedule (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_schedule",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            user_token=user_token,
            user_id=user_id,
        ))

    def delete_schedule(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        reminder_type: str = "no",
        operation_type: str = "delete_all",
        current_time: int = 0,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Delete a schedule (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_schedule",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            reminder_type=reminder_type,
            operation_type=operation_type,
            current_time=current_time,
            user_token=user_token,
            user_id=user_id,
        ))

    def fetch_schedule_list(
        self,
        calendar_id: str,
        start_time: int,
        end_time: int,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleListResult:
        """Get schedule list in a time range (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_schedule_list",
            calendar_id=calendar_id,
            start_time=start_time,
            end_time=end_time,
            user_token=user_token,
            user_id=user_id,
        ))

    def fetch_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        page: int = 1,
        page_size: int = 500,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleAttendeesResult:
        """Get schedule attendee list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_schedule_attendees",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            page=page,
            page_size=page_size,
            user_token=user_token,
            user_id=user_id,
        ))

    def add_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        attendees: list,
        *,
        reminder_type: str = "yes",
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Add attendees to a schedule (blocking)."""
        return _run_async(self._ephemeral_call(
            "add_schedule_attendees",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            attendees=attendees,
            reminder_type=reminder_type,
            user_token=user_token,
            user_id=user_id,
        ))

    def delete_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        attendees: list,
        *,
        reminder_type: str = "no",
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Delete attendees from a schedule (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_schedule_attendees",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            attendees=attendees,
            reminder_type=reminder_type,
            user_token=user_token,
            user_id=user_id,
        ))

    # ── Callback event parsing (sync wrappers) ────────────────────────

    @staticmethod
    def parse_callback_payload(
        encrypted_data: str,
        *,
        encoding_key: str = "",
        verify_signature: bool = False,
        timestamp: str = "",
        nonce: str = "",
        signature: str = "",
    ) -> list:
        from .callbacks import parse_callback_payload

        return parse_callback_payload(
            encrypted_data,
            encoding_key=encoding_key,
            verify_signature=verify_signature,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
        )

    @staticmethod
    def verify_callback_signature(
        timestamp: str,
        nonce: str,
        signature: str,
        encoding_key: str,
    ) -> bool:
        from .callbacks import verify_callback_signature

        return verify_callback_signature(timestamp, nonce, signature, encoding_key)

    @staticmethod
    def get_callback_event_types() -> dict:
        from .callbacks import CALLBACK_EVENT_TYPES

        return CALLBACK_EVENT_TYPES

    # ── Chat list & messages (4.24 MCP) (sync wrappers) ────────────────

    def fetch_chat_list(
        self,
        *,
        chat_type: int = 0,
        keyword: str = "",
        start_time: int = 0,
        end_time: int = 0,
        user_token: str = "",
    ) -> ChatListResult:
        """Fetch personal chat list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_chat_list",
            chat_type=chat_type,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            user_token=user_token,
        ))

    def fetch_chat_messages(
        self,
        *,
        staff_id: str = "",
        group_id: str = "",
        page_size: int = 100,
        base_version: str = "0",
        start_time: int = 0,
        end_time: int = 0,
        sender_id: str = "",
        user_token: str = "",
    ) -> ChatMessagesResult:
        """Fetch messages from a conversation (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_chat_messages",
            staff_id=staff_id,
            group_id=group_id,
            page_size=page_size,
            base_version=base_version,
            start_time=start_time,
            end_time=end_time,
            sender_id=sender_id,
            user_token=user_token,
        ))