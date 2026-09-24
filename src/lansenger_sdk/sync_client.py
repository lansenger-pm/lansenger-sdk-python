"""Lansenger SDK sync client — blocking wrapper around the async client.

Provides the same API as LansengerClient but with synchronous (blocking)
method calls. Useful for scripts, CLI tools, and non-async frameworks.

Uses asyncio.run() for each call. If an event loop is already running
(e.g. inside an async framework), falls back to a thread-pool executor.
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
from typing import Any

from .client import LansengerClient
from .config import LansengerConfig
from .exceptions import LansengerAuthError
from .models import (
    AccountMessageResult,
    AppCardParams,
    ApproveCardParams,
    BotCommandQueryResult,
    BotCommandResult,
    BotMessageResult,
    CalendarPrimaryResult,
    ChatListResult,
    ChatMessagesResult,
    CreateGroupResult,
    DepartmentAncestorsResult,
    DepartmentChildrenResult,
    DepartmentDetailResult,
    DepartmentStaffsResult,
    DownloadMediaResult,
    DynamicCardUpdateParams,
    ExtraFieldIdsResult,
    GroupInfoResult,
    GroupListResult,
    GroupMemberResult,
    IsInGroupResult,
    LinkCardParams,
    MediaPathResult,
    NoticeAccountListResult,
    NoticeSendResult,
    OaCardParams,
    QuestionnaireAccountListResult,
    QuestionnaireAnswerDetailResult,
    QuestionnaireAnswerUrlResult,
    QuestionnaireCopyResult,
    QuestionnaireDetailResult,
    QuestionnaireOpResult,
    QuestionnairePageResult,
    QuestionnaireQuestionDeleteResult,
    QuestionnaireQuestionSaveResult,
    QuestionnaireRecordResult,
    QuestionnaireSaveResult,
    QuestionnaireUploadUrlResult,
    BoardroomAreaListResult,
    BoardroomDetailResult,
    BoardroomGradingListResult,
    BoardroomListResult,
    BoardroomOpResult,
    BoardroomReserveDetailResult,
    BoardroomReserveResult,
    BoardroomScheduleResult,
    OrgInfoResult,
    PersonalAppCreateResult,
    PersonalAppInfoResult,
    PersonalAppListResult,
    PersonalTodoListResult,
    VideoconferenceConfResult,
    VideoconferenceDetailResult,
    VideoconferenceListResult,
    VideoconferenceOpResult,
    VideoconferenceParamResult,
    VideoconferenceStatusListResult,
    VideoconferenceVodListResult,
    VideoconferenceVodUrlResult,
    PersonalTodoResourceResult,
    PersonalTodoSaveResult,
    PersonalTodoUrlResult,
    QueryGroupsResult,
    ScheduleAttendeeMetaResult,
    ScheduleAttendeesResult,
    ScheduleAttendeesUpdateResult,
    ScheduleCreateResult,
    ScheduleInfoResult,
    ScheduleListResult,
    ScheduleUpdateResult,
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
    UserInfoResult,
    UserMessageResult,
    UserTokenResult,
)

logger = logging.getLogger("lansenger_sdk.sync_client")


def _run_async(coro):
    """Run an async coroutine from a synchronous context."""
    import asyncio
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
        app_id: str = "",
        app_secret: str = "",
        api_gateway_url: str = "",
        passport_url: str = "",
        http_timeout: float = 30.0,
        encoding_key: str = "",
        callback_token: str = "",
        app_token: str = "",
        user_token: str = "",
    ):
        """Initialize the sync client.

        Two mutually exclusive modes:
        - **Standard mode**: pass ``app_id`` + ``app_secret`` (or use
          ``from_env()`` / ``from_store()``). The SDK auto-fetches and
          refreshes the appToken.
        - **External / pass-through mode**: pass ``app_token`` directly
          (optionally ``user_token``). ``app_id``/``app_secret`` are
          optional and default to empty strings; the SDK does not refresh
          tokens — the caller manages their lifecycle.

        Raises LansengerConfigError only when neither app_id/app_secret nor
        app_token is provided.
        """
        self._app_id = app_id
        self._app_secret = app_secret
        self._api_gateway_url = api_gateway_url
        self._passport_url = passport_url
        self._http_timeout = http_timeout
        self._encoding_key = encoding_key
        self._callback_token = callback_token
        self._app_token = app_token
        self._user_token = user_token
        self._async_client_for_tokens: LansengerClient | None = None

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
            app_token=config.app_token,
            user_token=config.user_token,
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
            app_token=config.app_token,
            user_token=config.user_token,
        )

    @classmethod
    def from_store(cls, profile: str = "default", path: str | None = None) -> LansengerSyncClient:
        """Create client from a CredentialStore profile.

        Args:
            profile: Named profile in the credential store (default: "default").
            path: Optional custom path to the state file.

        Raises LansengerConfigError if the profile has no credentials.
        """
        from .exceptions import LansengerConfigError
        from .persistence import CredentialStore
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
            api_gateway_url=creds.get("api_gateway_url") or "",
            passport_url=creds.get("passport_url", ""),
            redirect_uri=creds.get("redirect_uri", ""),
            encoding_key=creds.get("encoding_key", ""),
            callback_token=creds.get("callback_token", ""),
        )
        client = cls.from_config(config)

        # Auto-load user token if available in store
        user_token_data = store.load_user_token()
        if user_token_data.get("user_token"):
            # Create a temporary async client to register tokens
            async_client = LansengerClient(
                app_id=config.app_id,
                app_secret=config.app_secret,
                api_gateway_url=config.api_gateway_url,
                http_timeout=config.http_timeout,
                encoding_key=config.encoding_key,
                callback_token=config.callback_token,
                app_token=config.app_token,
            )
            try:
                raw_ut_expiry = user_token_data.get("user_token_expiry", 0)
                if raw_ut_expiry:
                    remaining_ut = max(0, int(raw_ut_expiry - time.time()))
                    expires_in = remaining_ut if remaining_ut > 0 else 7200
                else:
                    expires_in = 7200
                raw_rt_expiry = user_token_data.get("refresh_token_expiry", 0)
                refresh_expires_in = max(0, int(raw_rt_expiry - time.time())) if raw_rt_expiry else 0
                async_client.set_user_tokens(
                    user_token=user_token_data["user_token"],
                    refresh_token=user_token_data.get("refresh_token", ""),
                    expires_in=expires_in,
                    staff_id=user_token_data.get("staff_id", ""),
                    refresh_expires_in=refresh_expires_in,
                )
                # Store the async client instance for token management
                client._async_client_for_tokens = async_client
            except Exception as e:
                logger.warning("Failed to load user token from store: %s", e)

        return client

    async def _ephemeral_call(self, method_name: str, **kwargs) -> Any:
        """Create an ephemeral async client, call method, then close."""
        client = LansengerClient(
            app_id=self._app_id,
            app_secret=self._app_secret,
            api_gateway_url=self._api_gateway_url,
            http_timeout=self._http_timeout,
            encoding_key=self._encoding_key,
            callback_token=self._callback_token,
            app_token=self._app_token,
            user_token=self._user_token,
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
            encoding_key=self._encoding_key,
            callback_token=self._callback_token,
            app_token=self._app_token,
            user_token=self._user_token,
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
        media_type: str | None = None,
        cover_image_path: str = "",
        reminder_all: bool = False,
        reminder_user_ids: list[str] | None = None,
        reminder_bot_ids: list[str] | None = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
        ref_msg_id: str = "",
    ) -> SendMessageResult:
        """Send a plain text message (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_text",
            chat_id=chat_id,
            content=content,
            file_path=file_path,
            media_type=media_type,
            cover_image_path=cover_image_path,
            reminder_all=reminder_all,
            reminder_user_ids=reminder_user_ids,
            reminder_bot_ids=reminder_bot_ids,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
            ref_msg_id=ref_msg_id,
        ))

    def send_markdown(
        self,
        chat_id: str,
        content: str,
        *,
        reminder_all: bool = False,
        reminder_user_ids: list[str] | None = None,
        reminder_bot_ids: list[str] | None = None,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
        ref_msg_id: str = "",
    ) -> SendMessageResult:
        """Send a Markdown message (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_markdown",
            chat_id=chat_id,
            content=content,
            reminder_all=reminder_all,
            reminder_user_ids=reminder_user_ids,
            reminder_bot_ids=reminder_bot_ids,
            is_group=is_group,
            user_token=user_token,
            sender_id=sender_id,
            ref_msg_id=ref_msg_id,
        ))

    def send_file(
        self,
        chat_id: str,
        file_path: str,
        *,
        caption: str = "",
        media_type: str | None = None,
        cover_image_path: str = "",
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
            cover_image_path=cover_image_path,
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
        articles: list[dict[str, str]],
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
        fields: list[dict[str, str]] | None = None,
        links: list[dict[str, str]] | None = None,
        card_link: str = "",
        pc_card_link: str = "",
        pad_card_link: str = "",
        is_dynamic: bool = False,
        head_status_info: dict[str, str] | None = None,
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
        fields: list[dict[str, str]] | None = None,
        link: str = "",
        pc_link: str = "",
        pad_link: str = "",
        card_action: dict[str, Any] | None = None,
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

    # ── ApproveCard (blocking) ────────────────────────────────────────

    def send_approve_card(
        self,
        body_title: str,
        body_content: str,
        *,
        chat_id: str = "",
        head_title: str = "",
        head_icon_link: str = "",
        head_icon_id: str = "",
        head_status_describe: str = "",
        head_status_icon: int = 0,
        head_status_icon_link: str = "",
        head_status_colour: str = "",
        body_format_type: int = 1,
        fields: list[dict[str, str]] | None = None,
        reminder_all: bool = False,
        reminder_user_ids: list[str] | None = None,
        reminder_bot_ids: list[str] | None = None,
        card_link: str = "",
        card_link_for_pc: str = "",
        card_link_for_pad: str = "",
        buttons: list[dict[str, Any]] | None = None,
        expire_time: int = 0,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an approveCard message (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_approve_card",
            body_title=body_title, body_content=body_content,
            chat_id=chat_id, head_title=head_title,
            head_icon_link=head_icon_link, head_icon_id=head_icon_id,
            head_status_describe=head_status_describe,
            head_status_icon=head_status_icon,
            head_status_icon_link=head_status_icon_link,
            head_status_colour=head_status_colour,
            body_format_type=body_format_type, fields=fields,
            reminder_all=reminder_all, reminder_user_ids=reminder_user_ids,
            reminder_bot_ids=reminder_bot_ids,
            card_link=card_link, card_link_for_pc=card_link_for_pc,
            card_link_for_pad=card_link_for_pad,
            buttons=buttons, expire_time=expire_time,
            is_group=is_group, user_token=user_token, sender_id=sender_id,
        ))

    def send_approve_card_with_params(self, params: ApproveCardParams) -> SendMessageResult:
        """Send an approveCard using ApproveCardParams (blocking)."""
        return _run_async(self._ephemeral_call_with_positional(
            "send_approve_card_with_params",
            args=[params],
            kwargs={},
        ))

    def update_approve_card(
        self,
        msg_id: str,
        *,
        head_status_describe: str = "",
        head_status_icon: int = 0,
        head_status_icon_link: str = "",
        head_status_colour: str = "",
        buttons: list[dict[str, Any]] | None = None,
    ) -> SendMessageResult:
        """Update an approveCard status (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_approve_card",
            msg_id=msg_id,
            head_status_describe=head_status_describe,
            head_status_icon=head_status_icon,
            head_status_icon_link=head_status_icon_link,
            head_status_colour=head_status_colour,
            buttons=buttons,
        ))

    def update_dynamic_card(
        self,
        msg_id: str,
        *,
        head_status_info: dict[str, str] | None = None,
        links: list[dict[str, str]] | None = None,
        is_last_update: bool = False,
        user_token: str = "",
        user_id: str = "",
    ) -> SendMessageResult:
        """Update a dynamic appCard status (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_dynamic_card",
            msg_id=msg_id,
            head_status_info=head_status_info,
            links=links,
            is_last_update=is_last_update,
            user_token=user_token,
            user_id=user_id,
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
        message_ids: list[str],
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
        page_offset: int = 0,
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
        media_type: int | None = None,
        user_token: str = "",
    ) -> SendMessageResult:
        """Upload a media file via core service endpoint (blocking, 4.5.1)."""
        return _run_async(self._ephemeral_call(
            "upload_media",
            file_path=file_path,
            media_type=media_type,
            user_token=user_token,
        ))

    def fetch_media_path(
        self,
        media_id: str,
        *,
        user_token: str = "",
    ) -> MediaPathResult:
        """Get the download URL path for a media file (blocking, 4.5.3)."""
        return _run_async(self._ephemeral_call(
            "fetch_media_path",
            media_id=media_id,
            user_token=user_token,
        ))

    def upload_app_media(
        self,
        file_path: str,
        *,
        media_type: str | None = None,
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
    ) -> SendMessageResult:
        """Upload a media file via app/bot endpoint (blocking, 4.5.4)."""
        return _run_async(self._ephemeral_call(
            "upload_app_media",
            file_path=file_path,
            media_type=media_type,
            width=width,
            height=height,
            duration=duration,
        ))

    def upload_app_media_v2(
        self,
        file_path: str,
        *,
        media_type: str | None = None,
        user_token: str = "",
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
    ) -> SendMessageResult:
        """Upload a media file via app/bot endpoint V2 (blocking, 4.5.5)."""
        return _run_async(self._ephemeral_call(
            "upload_app_media_v2",
            file_path=file_path,
            media_type=media_type,
            user_token=user_token,
            width=width,
            height=height,
            duration=duration,
        ))

    def download_media_by_share_id(
        self,
        share_id: str,
        *,
        user_token: str = "",
    ) -> DownloadMediaResult:
        """Download a file by its share ID (blocking, 4.5.6)."""
        return _run_async(self._ephemeral_call(
            "download_media_by_share_id",
            share_id=share_id,
            user_token=user_token,
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
        target_path: str | None = None,
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

    def get_user_token(self, staff_id: str = "") -> str:
        """Get a valid userToken with auto-refresh (blocking).

        When staff_id is provided, loads the token from the CredentialStore
        for that specific user.

        Requires tokens registered via exchange_code or set_user_tokens first.

        Args:
            staff_id: Optional staff_id to get the token for a specific user.
        """
        if self._async_client_for_tokens:
            return _run_async(self._async_client_for_tokens.get_user_token(staff_id=staff_id))
        elif staff_id:
            raise LansengerAuthError(
                "CredentialStore is required for multi-user token management. "
                "Use LansengerSyncClient.from_store() to enable credential persistence."
            )
        else:
            raise LansengerAuthError(
                "No userToken available. Call exchange_code() or set_user_tokens() first."
            )

    def set_user_tokens(
        self,
        user_token: str,
        refresh_token: str,
        expires_in: int = 7200,
        staff_id: str = "",
        refresh_expires_in: int = 0,
    ) -> None:
        """Register userToken + refreshToken for auto-refresh.

        When staff_id is provided, saves the token to the CredentialStore
        for that specific user (multi-user mode).

        Args:
            user_token: The user's userToken.
            refresh_token: The user's refreshToken.
            expires_in: Token expiry in seconds (default: 7200).
            staff_id: Optional staff_id to associate with this token.
            refresh_expires_in: Refresh token expiry in seconds.
        """
        if self._async_client_for_tokens is None:
            self._async_client_for_tokens = LansengerClient(
                app_id=self._app_id,
                app_secret=self._app_secret,
                api_gateway_url=self._api_gateway_url,
                http_timeout=self._http_timeout,
                encoding_key=self._encoding_key,
                callback_token=self._callback_token,
                app_token=self._app_token,
            )
        self._async_client_for_tokens.set_user_tokens(
            user_token=user_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            staff_id=staff_id,
            refresh_expires_in=refresh_expires_in,
        )

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
        ref_msg_id: str = "",
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
            ref_msg_id=ref_msg_id,
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
        reminder_user_ids: list[str] | None = None,
        reminder_bot_ids: list[str] | None = None,
        outlines: str = "",
        uuid: str = "",
        entry_id: str = "",
        ref_msg_id: str = "",
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
            reminder_bot_ids=reminder_bot_ids,
            outlines=outlines,
            uuid=uuid,
            entry_id=entry_id,
            ref_msg_id=ref_msg_id,
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
        start_time: int | None = None,
        end_time: int | None = None,
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
        callback_token: str = "",
        known_app_id: str = "",
    ) -> list:
        from .callbacks import parse_callback_payload

        return parse_callback_payload(
            encrypted_data,
            encoding_key=encoding_key,
            verify_signature=verify_signature,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
            callback_token=callback_token,
            known_app_id=known_app_id,
        )

    def parse_callback(
        self,
        encrypted_data: str,
        *,
        verify_signature: bool = False,
        timestamp: str = "",
        nonce: str = "",
        signature: str = "",
        known_app_id: str = "",
    ) -> list:
        """Parse callback payload using encoding_key/callback_token from this client.

        Values are read from the client's encoding_key/callback_token fields,
        falling back to the CredentialStore if from_store() was used.
        """
        from .callbacks import parse_callback_payload

        encoding_key = self._encoding_key
        callback_token = self._callback_token

        return parse_callback_payload(
            encrypted_data,
            encoding_key=encoding_key,
            verify_signature=verify_signature,
            timestamp=timestamp,
            nonce=nonce,
            signature=signature,
            callback_token=callback_token,
            known_app_id=known_app_id,
        )

    @staticmethod
    def verify_callback_signature(
        timestamp: str,
        nonce: str,
        signature: str,
        encoding_key: str,
        *,
        data_encrypt: str = "",
        callback_token: str = "",
    ) -> bool:
        from .callbacks import verify_callback_signature

        return verify_callback_signature(
            timestamp, nonce, signature, encoding_key,
            data_encrypt=data_encrypt,
            callback_token=callback_token,
        )

    def verify_callback(
        self,
        timestamp: str,
        nonce: str,
        signature: str,
        *,
        data_encrypt: str = "",
    ) -> bool:
        """Verify callback signature using encoding_key/callback_token from this client.

        Values are read from the client's encoding_key/callback_token fields,
        falling back to the CredentialStore if from_store() was used.
        """
        from .callbacks import verify_callback_signature

        encoding_key = self._encoding_key
        callback_token = self._callback_token

        return verify_callback_signature(
            timestamp, nonce, signature, encoding_key,
            data_encrypt=data_encrypt,
            callback_token=callback_token,
        )

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

    def dismiss_group(
        self,
        group_id: str,
        *,
        user_token: str = "",
    ) -> UpdateGroupResult:
        """Dismiss/delete a group (blocking, 4.28.6)."""
        return _run_async(self._ephemeral_call(
            "dismiss_group",
            group_id=group_id,
            user_token=user_token,
        ))

    def send_reminder(
        self,
        msg_id: str,
        reminder_types: list[int],
        user_id_list: list[str],
    ) -> SendMessageResult:
        """Send an urgent reminder for a message (blocking, 4.6.14)."""
        return _run_async(self._ephemeral_call(
            "send_reminder",
            msg_id=msg_id,
            reminder_types=reminder_types,
            user_id_list=user_id_list,
        ))

    def update_schedule(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        operation_type: str = "modify_all",
        current_time: int | None = None,
        reminder_type: str | None = None,
        repeat_type: str | None = None,
        rule: str | None = None,
        expire_date_type: str | None = None,
        all_day: str | None = None,
        attendee_permissions: str | None = None,
        start_time: dict[str, Any] | None = None,
        end_time: dict[str, Any] | None = None,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleUpdateResult:
        """Update a schedule (blocking, 4.23.12)."""
        return _run_async(self._ephemeral_call(
            "update_schedule",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            summary=summary,
            description=description,
            operation_type=operation_type,
            current_time=current_time,
            reminder_type=reminder_type,
            repeat_type=repeat_type,
            rule=rule,
            expire_date_type=expire_date_type,
            all_day=all_day,
            attendee_permissions=attendee_permissions,
            start_time=start_time,
            end_time=end_time,
            user_token=user_token,
            user_id=user_id,
        ))

    def update_schedule_attendee_meta(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        rsvp_status: str | None = None,
        color: str | None = None,
        permissions: str | None = None,
        busy_free_state: str | None = None,
        remind_times: list[int] | None = None,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleAttendeeMetaResult:
        """Update schedule attendee metadata (blocking, 4.23.17)."""
        return _run_async(self._ephemeral_call(
            "update_schedule_attendee_meta",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            rsvp_status=rsvp_status,
            color=color,
            permissions=permissions,
            busy_free_state=busy_free_state,
            remind_times=remind_times,
            user_token=user_token,
            user_id=user_id,
        ))

    def update_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        add_attendees: list | None = None,
        delete_attendees: list | None = None,
        reminder_type: str | None = None,
        operation_type: str | None = None,
        current_time: int | None = None,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleAttendeesUpdateResult:
        """Batch add and/or delete schedule attendees (blocking, 4.23.19)."""
        return _run_async(self._ephemeral_call(
            "update_schedule_attendees",
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            add_attendees=add_attendees,
            delete_attendees=delete_attendees,
            reminder_type=reminder_type,
            operation_type=operation_type,
            current_time=current_time,
            user_token=user_token,
            user_id=user_id,
        ))

    # ── Bot Commands (4.37, blocking wrappers) ─────────────────────────

    def create_bot_commands(
        self,
        scope_type: int,
        commands: list,
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandResult:
        """Create bot slash commands (blocking, 4.37.1)."""
        return _run_async(self._ephemeral_call(
            "create_bot_commands",
            scope_type=scope_type,
            commands=commands,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
        ))

    def fetch_bot_commands(
        self,
        scope_type: int,
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandQueryResult:
        """Query bot slash commands (blocking, 4.37.2)."""
        return _run_async(self._ephemeral_call(
            "fetch_bot_commands",
            scope_type=scope_type,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
        ))

    def delete_bot_commands(
        self,
        scope_type: int,
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandResult:
        """Delete bot slash commands (blocking, 4.37.3)."""
        return _run_async(self._ephemeral_call(
            "delete_bot_commands",
            scope_type=scope_type,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
        ))

    # ── Personal Apps (4.38, blocking wrappers) ────────────────────────

    def create_personal_app(
        self,
        *,
        user_token: str,
        name: str = "",
        avatar_id: str = "",
        description: str = "",
    ) -> PersonalAppCreateResult:
        """Create a personal app/bot (blocking, 4.38.1)."""
        return _run_async(self._ephemeral_call(
            "create_personal_app",
            user_token=user_token,
            name=name,
            avatar_id=avatar_id,
            description=description,
        ))

    def update_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
        name: str,
        avatar_id: str = "",
        description: str = "",
    ) -> PersonalAppInfoResult:
        """Update a personal app/bot (blocking, 4.38.2)."""
        return _run_async(self._ephemeral_call(
            "update_personal_app",
            app_id=app_id,
            user_token=user_token,
            name=name,
            avatar_id=avatar_id,
            description=description,
        ))

    def fetch_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
    ) -> PersonalAppInfoResult:
        """Fetch personal app info (blocking, 4.38.3)."""
        return _run_async(self._ephemeral_call(
            "fetch_personal_app",
            app_id=app_id,
            user_token=user_token,
        ))

    def delete_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
    ) -> PersonalAppInfoResult:
        """Delete a personal app/bot (blocking, 4.38.4)."""
        return _run_async(self._ephemeral_call(
            "delete_personal_app",
            app_id=app_id,
            user_token=user_token,
        ))

    def fetch_personal_app_list(
        self,
        *,
        user_token: str,
    ) -> PersonalAppListResult:
        """Fetch personal app list (blocking, 4.38.5)."""
        return _run_async(self._ephemeral_call(
            "fetch_personal_app_list",
            user_token=user_token,
        ))

    # ── Notice (通知系统) (sync wrappers) ──────────────────────────────

    def send_notice(
        self,
        title: str,
        content_type: int,
        account_code: str,
        user_type: int,
        *,
        content: str = "",
        notice_link: str = "",
        notice_location: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        release_phones: list | None = None,
        cc_phones: list | None = None,
        release_range: list | None = None,
        cc_staff_ids: list | None = None,
        create_mobile: str = "",
        create_user_id: str = "",
        resource_list: list | None = None,
        extend_id: str = "",
        confirm_flag: int | None = None,
        forward_flag: int | None = None,
        reply_flag: int | None = None,
        anonymous_flag: int | None = None,
        remind_status: int | None = None,
        remind_msg_type: str = "",
        at_once_flag: int | None = None,
        remind_after_type: str = "",
        remind_max_count: int | None = None,
        remind_interval_time: int | None = None,
        remind_interval_time_duration: str = "",
        remind_range_type: str = "",
        remind_range_staff_ids: list | None = None,
        user_token: str = "",
    ) -> NoticeSendResult:
        """Send a notice via an official account (blocking)."""
        return _run_async(self._ephemeral_call(
            "send_notice",
            title=title,
            content_type=content_type,
            account_code=account_code,
            user_type=user_type,
            content=content,
            notice_link=notice_link,
            notice_location=notice_location,
            latitude=latitude,
            longitude=longitude,
            release_phones=release_phones,
            cc_phones=cc_phones,
            release_range=release_range,
            cc_staff_ids=cc_staff_ids,
            create_mobile=create_mobile,
            create_user_id=create_user_id,
            resource_list=resource_list,
            extend_id=extend_id,
            confirm_flag=confirm_flag,
            forward_flag=forward_flag,
            reply_flag=reply_flag,
            anonymous_flag=anonymous_flag,
            remind_status=remind_status,
            remind_msg_type=remind_msg_type,
            at_once_flag=at_once_flag,
            remind_after_type=remind_after_type,
            remind_max_count=remind_max_count,
            remind_interval_time=remind_interval_time,
            remind_interval_time_duration=remind_interval_time_duration,
            remind_range_type=remind_range_type,
            remind_range_staff_ids=remind_range_staff_ids,
            user_token=user_token,
        ))

    def fetch_notice_accounts(
        self,
        *,
        org_id: str = "",
        user_token: str = "",
    ) -> NoticeAccountListResult:
        """List official accounts of an organization (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_notice_accounts",
            org_id=org_id,
            user_token=user_token,
        ))

    # ── Questionnaire (问卷系统) (sync wrappers) ───────────────────────

    def save_questionnaire(
        self,
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
    ) -> QuestionnaireSaveResult:
        """Create/update a questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "save_questionnaire",
            title=title, account_code=account_code, code=code,
            welcome_speech=welcome_speech, bye_speech=bye_speech,
            cover_resource_id=cover_resource_id, resource_ids=resource_ids,
            app_id=app_id, user_type=user_type, create_mobile=create_mobile,
            create_user_id=create_user_id, user_token=user_token,
        ))

    def save_questionnaire_questions(
        self,
        questionnaire_code: str,
        question_list: list,
        *,
        create_user_id: str = "",
        user_token: str = "",
    ) -> QuestionnaireQuestionSaveResult:
        """Batch-save questions of a questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "save_questionnaire_questions",
            questionnaire_code=questionnaire_code, question_list=question_list,
            create_user_id=create_user_id, user_token=user_token,
        ))

    def delete_questionnaire_question(
        self,
        question_code: str,
        *,
        create_user_id: str = "",
        user_token: str = "",
    ) -> QuestionnaireQuestionDeleteResult:
        """Delete a question by code (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_questionnaire_question",
            question_code=question_code, create_user_id=create_user_id,
            user_token=user_token,
        ))

    def publish_questionnaire(
        self,
        questionnaire_code: str,
        *,
        scope_type: int = 1,
        staff_ids: list | None = None,
        phones: list | None = None,
        answer_limit: int = 1,
        message_flag: int = 0,
        page_flag: int = 0,
        share_flag: int = 0,
        view_stats_flag: int = 1,
        anonym_flag: int = 0,
        publish_user_id: str = "",
        user_token: str = "",
    ) -> QuestionnaireOpResult:
        """Publish a questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "publish_questionnaire",
            questionnaire_code=questionnaire_code, scope_type=scope_type,
            staff_ids=staff_ids, phones=phones, answer_limit=answer_limit,
            message_flag=message_flag, page_flag=page_flag, share_flag=share_flag,
            view_stats_flag=view_stats_flag, anonym_flag=anonym_flag,
            publish_user_id=publish_user_id, user_token=user_token,
        ))

    def withdraw_questionnaire(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireOpResult:
        """Withdraw a published questionnaire to draft (blocking)."""
        return _run_async(self._ephemeral_call(
            "withdraw_questionnaire",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def finish_questionnaire(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireOpResult:
        """End an ongoing questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "finish_questionnaire",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def delete_questionnaire(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireOpResult:
        """Delete a questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "delete_questionnaire",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def fetch_questionnaire_detail(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireDetailResult:
        """Fetch full questionnaire detail incl. questions (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_detail",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def fetch_questionnaire_brief(
        self, questionnaire_code: str, *, user_token: str = "",
    ) -> QuestionnaireDetailResult:
        """Fetch questionnaire detail without admin check (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_brief",
            questionnaire_code=questionnaire_code, user_token=user_token,
        ))

    def fetch_questionnaire_answer_url(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireAnswerUrlResult:
        """Fetch the answer-page URL (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_answer_url",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def copy_questionnaire(
        self, questionnaire_code: str, *, operate_user_id: str = "", user_token: str = "",
    ) -> QuestionnaireCopyResult:
        """Copy a questionnaire into a new draft (blocking)."""
        return _run_async(self._ephemeral_call(
            "copy_questionnaire",
            questionnaire_code=questionnaire_code, operate_user_id=operate_user_id,
            user_token=user_token,
        ))

    def fetch_questionnaires_by_codes(
        self, code_list: list, *, include_deleted: int = 0, user_token: str = "",
    ) -> QuestionnaireQueryListResult:
        """Batch-fetch questionnaire basic info by codes (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaires_by_codes",
            code_list=code_list, include_deleted=include_deleted, user_token=user_token,
        ))

    def fetch_questionnaire_office_accounts(
        self, *, user_id: str = "", user_token: str = "",
    ) -> QuestionnaireAccountListResult:
        """Fetch office accounts the user can manage (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_office_accounts",
            user_id=user_id, user_token=user_token,
        ))

    def fetch_created_questionnaires(
        self, account_code: str, *, page_no: int = 1, page_size: int = 10,
        status: int | None = None, user_id: str = "", user_token: str = "",
    ) -> QuestionnairePageResult:
        """Page questionnaires created under an office account (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_created_questionnaires",
            account_code=account_code, page_no=page_no, page_size=page_size,
            status=status, user_id=user_id, user_token=user_token,
        ))

    def fetch_my_created_questionnaires(
        self, org_id: str, *, page_no: int = 1, page_size: int = 10,
        title: str = "", status: int | None = None, user_id: str = "", user_token: str = "",
    ) -> QuestionnairePageResult:
        """Page all questionnaires I created (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_my_created_questionnaires",
            org_id=org_id, page_no=page_no, page_size=page_size, title=title,
            status=status, user_id=user_id, user_token=user_token,
        ))

    def fetch_participated_questionnaires(
        self, org_id: str, *, page_no: int = 1, page_size: int = 10,
        status: int | None = None, user_id: str = "", user_token: str = "",
    ) -> QuestionnairePageResult:
        """Page questionnaires the user answered (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_participated_questionnaires",
            org_id=org_id, page_no=page_no, page_size=page_size, status=status,
            user_id=user_id, user_token=user_token,
        ))

    def fetch_answer_records(
        self, account_code: str, questionnaire_code: str, *, page_no: int = 1, page_size: int = 10,
        user_id: str = "", user_token: str = "",
    ) -> QuestionnairePageResult:
        """Page answer records of a questionnaire (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_answer_records",
            account_code=account_code, questionnaire_code=questionnaire_code,
            page_no=page_no, page_size=page_size, user_id=user_id, user_token=user_token,
        ))

    def fetch_questionnaire_answer_detail(
        self, account_code: str, answer_code: str, *, user_id: str = "", user_token: str = "",
    ) -> QuestionnaireAnswerDetailResult:
        """Fetch one answer record's full detail (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_answer_detail",
            account_code=account_code, answer_code=answer_code,
            user_id=user_id, user_token=user_token,
        ))

    def fetch_questionnaire_last_answer_detail(
        self, questionnaire_code: str, *, answer_record_code: str = "", user_id: str = "", user_token: str = "",
    ) -> QuestionnaireAnswerDetailResult:
        """Fetch the user's last answer detail (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_last_answer_detail",
            questionnaire_code=questionnaire_code, answer_record_code=answer_record_code,
            user_id=user_id, user_token=user_token,
        ))

    def fetch_answer_data(
        self, account_code: str, questionnaire_code: str, *, page_no: int = 1, page_size: int = 10,
        user_id: str = "", user_token: str = "",
    ) -> QuestionnairePageResult:
        """Page answer data for export (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_answer_data",
            account_code=account_code, questionnaire_code=questionnaire_code,
            page_no=page_no, page_size=page_size, user_id=user_id, user_token=user_token,
        ))

    def fetch_questionnaire_last_answer_record(
        self, questionnaire_code: str, *, answer_record_code: str = "", user_id: str = "", user_token: str = "",
    ) -> QuestionnaireRecordResult:
        """Fetch the user's last answer record (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_last_answer_record",
            questionnaire_code=questionnaire_code, answer_record_code=answer_record_code,
            user_id=user_id, user_token=user_token,
        ))

    def fetch_questionnaire_upload_url(
        self, file_name: str, md5: str, size: int, *, user_token: str = "",
    ) -> QuestionnaireUploadUrlResult:
        """Fetch a presigned upload URL (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_questionnaire_upload_url",
            file_name=file_name, md5=md5, size=size, user_token=user_token,
        ))

    # ── Boardroom (会议室预定 V2) (sync wrappers) ──────────────────────

    def fetch_boardroom_list(
        self, *, grading_id: str = "", area_office_id: str = "",
        floor_ids: list | None = None, equipment: list | None = None,
        reserve_time_start: str = "", reserve_time_end: str = "",
        query_date: str = "", page: int = 1, limit: int = 10,
        lx_user_id: str = "", org_id: str = "", user_token: str = "",
    ) -> BoardroomListResult:
        """Filter meeting rooms (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_list",
            grading_id=grading_id, area_office_id=area_office_id, floor_ids=floor_ids,
            equipment=equipment, reserve_time_start=reserve_time_start,
            reserve_time_end=reserve_time_end, query_date=query_date,
            page=page, limit=limit, lx_user_id=lx_user_id, org_id=org_id,
            user_token=user_token,
        ))

    def fetch_boardroom_detail(
        self, room_id: str, *, org_id: str = "", user_token: str = "",
    ) -> BoardroomDetailResult:
        """Fetch meeting-room detail (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_detail", room_id=room_id, org_id=org_id, user_token=user_token,
        ))

    def fetch_boardroom_schedule(
        self, room_id: str, query_date: str, grading_id: str, *,
        reserve_user_id: str = "", org_id: str = "", user_token: str = "",
    ) -> BoardroomScheduleResult:
        """Fetch a room's bookings for a date (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_schedule", room_id=room_id, query_date=query_date,
            grading_id=grading_id, reserve_user_id=reserve_user_id, org_id=org_id,
            user_token=user_token,
        ))

    def fetch_boardroom_reserve_detail(
        self, reserve_room_id: str, *, grading_id: str = "", org_id: str = "", user_token: str = "",
    ) -> BoardroomReserveDetailResult:
        """Fetch reservation detail (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_reserve_detail", reserve_room_id=reserve_room_id,
            grading_id=grading_id, org_id=org_id, user_token=user_token,
        ))

    def reserve_boardroom(
        self, boardroom_id: str, name: str, grading_id: str,
        reserve_time_start: str, reserve_time_end: str, notice_time: str, *,
        reserve_user: str = "", org_id: str = "", toastmaster: str = "",
        leader: str = "", leader_attend: str = "", people_number: str = "",
        other_demand: str = "", is_video: str = "", video_name: str = "",
        user_list: list | None = None, invitation_user_list: list | None = None,
        table_cards: str = "", reserve_type: str = "0", repeat_type: str = "",
        repeat_days: list | None = None, skip: str = "", repeat_end_date: str = "",
        user_token: str = "",
    ) -> BoardroomReserveResult:
        """Reserve a meeting room (blocking)."""
        return _run_async(self._ephemeral_call(
            "reserve_boardroom", boardroom_id=boardroom_id, name=name,
            grading_id=grading_id, reserve_time_start=reserve_time_start,
            reserve_time_end=reserve_time_end, notice_time=notice_time,
            reserve_user=reserve_user, org_id=org_id, toastmaster=toastmaster,
            leader=leader, leader_attend=leader_attend, people_number=people_number,
            other_demand=other_demand, is_video=is_video, video_name=video_name,
            user_list=user_list, invitation_user_list=invitation_user_list,
            table_cards=table_cards, reserve_type=reserve_type, repeat_type=repeat_type,
            repeat_days=repeat_days, skip=skip, repeat_end_date=repeat_end_date,
            user_token=user_token,
        ))

    def edit_boardroom_reserve(
        self, reserve_id: str, boardroom_id: str, name: str, grading_id: str,
        reserve_time_start: str, reserve_time_end: str, notice_time: str, *,
        edit_type: str = "1", reserve_user: str = "", org_id: str = "",
        toastmaster: str = "", leader: str = "", leader_attend: str = "",
        people_number: str = "", other_demand: str = "", is_video: str = "",
        video_name: str = "", user_list: list | None = None,
        invitation_user_list: list | None = None, table_cards: str = "",
        reserve_type: str = "0", repeat_type: str = "", repeat_days: list | None = None,
        skip: str = "", repeat_end_date: str = "", user_token: str = "",
    ) -> BoardroomReserveResult:
        """Edit a reservation (blocking)."""
        return _run_async(self._ephemeral_call(
            "edit_boardroom_reserve", reserve_id=reserve_id, boardroom_id=boardroom_id,
            name=name, grading_id=grading_id, reserve_time_start=reserve_time_start,
            reserve_time_end=reserve_time_end, notice_time=notice_time,
            edit_type=edit_type, reserve_user=reserve_user, org_id=org_id,
            toastmaster=toastmaster, leader=leader, leader_attend=leader_attend,
            people_number=people_number, other_demand=other_demand, is_video=is_video,
            video_name=video_name, user_list=user_list,
            invitation_user_list=invitation_user_list, table_cards=table_cards,
            reserve_type=reserve_type, repeat_type=repeat_type, repeat_days=repeat_days,
            skip=skip, repeat_end_date=repeat_end_date, user_token=user_token,
        ))

    def cancel_boardroom_reserve(
        self, reserve_id: str, *, cancel_user_id: str = "", org_id: str = "",
        cancel_reason: str = "", is_send: bool | None = None,
        notify_user_list: list | None = None, cancel_video: str = "",
        cancel_type: str = "", user_token: str = "",
    ) -> BoardroomOpResult:
        """Cancel a reservation (blocking)."""
        return _run_async(self._ephemeral_call(
            "cancel_boardroom_reserve", reserve_id=reserve_id,
            cancel_user_id=cancel_user_id, org_id=org_id, cancel_reason=cancel_reason,
            is_send=is_send, notify_user_list=notify_user_list, cancel_video=cancel_video,
            cancel_type=cancel_type, user_token=user_token,
        ))

    def confirm_boardroom_sign(
        self, reserve_id: str, *, org_id: str = "", user_token: str = "",
    ) -> BoardroomOpResult:
        """Scan-code confirmation (blocking)."""
        return _run_async(self._ephemeral_call(
            "confirm_boardroom_sign", reserve_id=reserve_id, org_id=org_id,
            user_token=user_token,
        ))

    def fetch_my_boardroom_reserves(
        self, grading_id: str, *, keys: str = "", start_time: str = "",
        end_time: str = "", boardroom_id: str = "", floor_ids: list | None = None,
        page: int = 1, limit: int = 10, lx_user_id: str = "", org_id: str = "",
        user_token: str = "",
    ) -> BoardroomListResult:
        """Page my reservations (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_my_boardroom_reserves", grading_id=grading_id, keys=keys,
            start_time=start_time, end_time=end_time, boardroom_id=boardroom_id,
            floor_ids=floor_ids, page=page, limit=limit, lx_user_id=lx_user_id,
            org_id=org_id, user_token=user_token,
        ))

    def fetch_boardroom_gradings(
        self, *, lx_user_id: str = "", org_id: str = "", user_token: str = "",
    ) -> BoardroomGradingListResult:
        """Fetch visible gradings (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_gradings", lx_user_id=lx_user_id, org_id=org_id,
            user_token=user_token,
        ))

    def fetch_boardroom_area_offices(
        self, grading_id: str, *, user_token: str = "",
    ) -> BoardroomAreaListResult:
        """Fetch office areas under a grading (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_boardroom_area_offices", grading_id=grading_id, user_token=user_token,
        ))

    def save_personal_todo(
        self,
        subject: str,
        start_time: int,
        due_time: int,
        priority: int,
        create_user_id: str,
        org_id: str,
        appid: str,
        *,
        description: str = "",
        parent_code: str = "",
        group_id: str = "",
        group_category_code: str = "",
        finish_time: int | None = 0,
        status_tag_no: str = "",
        status_tag_yes: str = "",
        app_info_id: int | None = None,
        app_category_id: int | None = None,
        platform: int | None = None,
        subscribe_status: int | None = None,
        user_code: str = "",
        executors: list | None = None,
        copys: list | None = None,
        resources: list | None = None,
        reminds: list | None = None,
        user_token: str = "",
    ) -> PersonalTodoSaveResult:
        """Create a personal todo (blocking)."""
        return _run_async(self._ephemeral_call(
            "save_personal_todo", subject=subject, start_time=start_time,
            due_time=due_time, priority=priority, create_user_id=create_user_id,
            org_id=org_id, appid=appid, description=description,
            parent_code=parent_code, group_id=group_id,
            group_category_code=group_category_code, finish_time=finish_time,
            status_tag_no=status_tag_no, status_tag_yes=status_tag_yes,
            app_info_id=app_info_id, app_category_id=app_category_id,
            platform=platform, subscribe_status=subscribe_status, user_code=user_code,
            executors=executors, copys=copys, resources=resources, reminds=reminds,
            user_token=user_token,
        ))

    def update_personal_todo(
        self,
        todo_code: str,
        org_id: str,
        update_fields: list,
        *,
        subject: str = "",
        description: str = "",
        start_time: int | None = None,
        due_time: int | None = None,
        finish_time: int | None = None,
        priority: int | None = None,
        status_tag_no: str = "",
        status_tag_yes: str = "",
        subscribe_status: int | None = None,
        create_user_id: str = "",
        group_id: str = "",
        group_category_code: str = "",
        appid: str = "",
        executors: list | None = None,
        copys: list | None = None,
        resources: list | None = None,
        reminds: list | None = None,
        user_token: str = "",
    ) -> PersonalTodoSaveResult:
        """Edit a personal todo (blocking)."""
        return _run_async(self._ephemeral_call(
            "update_personal_todo", todo_code=todo_code, org_id=org_id,
            update_fields=update_fields, subject=subject, description=description,
            start_time=start_time, due_time=due_time, finish_time=finish_time,
            priority=priority, status_tag_no=status_tag_no, status_tag_yes=status_tag_yes,
            subscribe_status=subscribe_status, create_user_id=create_user_id,
            group_id=group_id, group_category_code=group_category_code, appid=appid,
            executors=executors, copys=copys, resources=resources, reminds=reminds,
            user_token=user_token,
        ))

    def fetch_personal_todo_list(
        self,
        org_id: str,
        staff_id: str,
        *,
        page_no: int = 1,
        page_size: int = 10,
        status: int | None = None,
        app_id: str = "",
        app_category_name: str = "",
        user_token: str = "",
    ) -> PersonalTodoListResult:
        """Page a user's personal todos (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_personal_todo_list", org_id=org_id, staff_id=staff_id,
            page_no=page_no, page_size=page_size, status=status, app_id=app_id,
            app_category_name=app_category_name, user_token=user_token,
        ))

    def upload_personal_todo_resource(
        self,
        app_id: str,
        size: int,
        file_name: str,
        content_type: str,
        file_data: str,
        org_id: str,
        *,
        extension_info: str = "",
        thumb: bool = False,
        user_token: str = "",
    ) -> PersonalTodoResourceResult:
        """Upload a personal-todo resource (blocking)."""
        return _run_async(self._ephemeral_call(
            "upload_personal_todo_resource", app_id=app_id, size=size,
            file_name=file_name, content_type=content_type, file_data=file_data,
            org_id=org_id, extension_info=extension_info, thumb=thumb,
            user_token=user_token,
        ))

    def fetch_personal_todo_resource_download_url(
        self,
        resource_id: str,
        org_id: str,
        *,
        file_name: str = "",
        user_token: str = "",
    ) -> PersonalTodoUrlResult:
        """Fetch a personal-todo resource download URL (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_personal_todo_resource_download_url",
            resource_id=resource_id, org_id=org_id, file_name=file_name,
            user_token=user_token,
        ))

    def fetch_personal_todo_resource_upload_url(
        self,
        file_name: str,
        md5: str,
        size: int,
        org_id: str,
        *,
        user_token: str = "",
    ) -> PersonalTodoUrlResult:
        """Fetch a presigned personal-todo resource upload URL (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_personal_todo_resource_upload_url", file_name=file_name,
            md5=md5, size=size, org_id=org_id, user_token=user_token,
        ))

    # ── Public API: Videoconference (视频会议开放能力) ────────────────────

    def create_meeting(self, *, subject, start_time, members, org_id,
                       auto_record=0, type=1, group_new=0,
                       conf_password="", control_password="", mask_type=0,
                       ext_attr="", join_mute=None, open_mute=None,
                       enable_pre_join=None, user_stop_time=None,
                       invite_admin=None, user_token="") -> VideoconferenceDetailResult:
        """Create a meeting (blocking)."""
        return _run_async(self._ephemeral_call(
            "create_meeting", subject=subject, start_time=start_time,
            members=members, org_id=org_id, auto_record=auto_record, type=type,
            group_new=group_new, conf_password=conf_password,
            control_password=control_password, mask_type=mask_type,
            ext_attr=ext_attr, join_mute=join_mute, open_mute=open_mute,
            enable_pre_join=enable_pre_join, user_stop_time=user_stop_time,
            invite_admin=invite_admin, user_token=user_token,
        ))

    def modify_meeting(self, *, mid, subject, start_time, members, org_id,
                       operator, auto_record=0, type=1, group_new=0,
                       conf_password="", control_password="",
                       user_stop_time=None, user_token="") -> VideoconferenceOpResult:
        """Modify a meeting that has not started (blocking)."""
        return _run_async(self._ephemeral_call(
            "modify_meeting", mid=mid, subject=subject, start_time=start_time,
            members=members, org_id=org_id, operator=operator,
            auto_record=auto_record, type=type, group_new=group_new,
            conf_password=conf_password, control_password=control_password,
            user_stop_time=user_stop_time, user_token=user_token,
        ))

    def cancel_meeting(self, *, mid, org_id, operator, user_token="") -> VideoconferenceOpResult:
        """Cancel a meeting that has not started (blocking)."""
        return _run_async(self._ephemeral_call(
            "cancel_meeting", mid=mid, org_id=org_id, operator=operator, user_token=user_token))

    def stop_meeting(self, *, mid, org_id, operator, user_token="") -> VideoconferenceOpResult:
        """End a running meeting (blocking)."""
        return _run_async(self._ephemeral_call(
            "stop_meeting", mid=mid, org_id=org_id, operator=operator, user_token=user_token))

    def fetch_meeting_detail(self, *, mid, org_id, operator, user_token="") -> VideoconferenceDetailResult:
        """Meeting detail by mid (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_meeting_detail", mid=mid, org_id=org_id, operator=operator, user_token=user_token))

    def fetch_meeting_list(self, *, org_id, start_time, end_time, fetch_range="all",
                           staff_id="", limit=10, offset=0, user_token="") -> VideoconferenceListResult:
        """Meeting list by time range (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_meeting_list", org_id=org_id, start_time=start_time,
            end_time=end_time, fetch_range=fetch_range, staff_id=staff_id,
            limit=limit, offset=offset, user_token=user_token))

    def fetch_meeting_record_list(self, *, org_id, start_time, end_time, admin="",
                                  create_source=0, limit=10, offset=0,
                                  user_token="") -> VideoconferenceListResult:
        """Meeting operation record list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_meeting_record_list", org_id=org_id, start_time=start_time,
            end_time=end_time, admin=admin, create_source=create_source,
            limit=limit, offset=offset, user_token=user_token))

    def fetch_member_simplerecord(self, *, mid, org_id, operator, limit=10,
                                  offset=0, user_token="") -> VideoconferenceListResult:
        """Member join/leave records (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_member_simplerecord", mid=mid, org_id=org_id,
            operator=operator, limit=limit, offset=offset, user_token=user_token))

    def fetch_fixroom_list(self, *, org_id, operator, limit=10, offset=0,
                           user_token="") -> VideoconferenceListResult:
        """Fixed (cloud) meeting-room list (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_fixroom_list", org_id=org_id, operator=operator,
            limit=limit, offset=offset, user_token=user_token))

    def fetch_meeting_status(self, *, mids, org_id, user_token="") -> VideoconferenceStatusListResult:
        """Batch meeting status (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_meeting_status", mids=mids, org_id=org_id, user_token=user_token))

    def subscribe_meeting_events(self, *, mid, org_id, events, call_back_info="",
                                 user_token="") -> VideoconferenceOpResult:
        """Subscribe meeting status-change events (blocking)."""
        return _run_async(self._ephemeral_call(
            "subscribe_meeting_events", mid=mid, org_id=org_id, events=events,
            call_back_info=call_back_info, user_token=user_token))

    def fetch_meeting_params(self, *, meeting_number, org_id, operator, user_token="") -> VideoconferenceParamResult:
        """Meeting params by meetingNumber (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_meeting_params", meeting_number=meeting_number, org_id=org_id,
            operator=operator, user_token=user_token))

    def fetch_history_meetings(self, *, org_id, operator, limit=10, offset=0,
                               user_token="") -> VideoconferenceListResult:
        """A person's past meetings (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_history_meetings", org_id=org_id, operator=operator,
            limit=limit, offset=offset, user_token=user_token))

    def fetch_active_meetings(self, *, org_id, operator, limit=10, offset=0,
                              user_token="") -> VideoconferenceListResult:
        """A person's running + reserved meetings (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_active_meetings", org_id=org_id, operator=operator,
            limit=limit, offset=offset, user_token=user_token))

    def control_member(self, *, mid, staff_id, op_code, operator, org_id,
                       user_token="") -> VideoconferenceOpResult:
        """Host controls a member (blocking)."""
        return _run_async(self._ephemeral_call(
            "control_member", mid=mid, staff_id=staff_id, op_code=op_code,
            operator=operator, org_id=org_id, user_token=user_token))

    def invite_members(self, *, meeting_number, members, org_id, operator,
                       user_token="") -> VideoconferenceOpResult:
        """Invite members to a running meeting (blocking)."""
        return _run_async(self._ephemeral_call(
            "invite_members", meeting_number=meeting_number, members=members,
            org_id=org_id, operator=operator, user_token=user_token))

    def fetch_member_list(self, *, mid, org_id, operator, limit=10, offset=0,
                          user_token="") -> VideoconferenceListResult:
        """Paged member list of a meeting (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_member_list", mid=mid, org_id=org_id, operator=operator,
            limit=limit, offset=offset, user_token=user_token))

    def fetch_vod_list(self, *, mid, org_id, operator, user_token="") -> VideoconferenceVodListResult:
        """Recording list of a meeting (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_vod_list", mid=mid, org_id=org_id, operator=operator, user_token=user_token))

    def fetch_vod_download_urls(self, *, vods, org_id, operator, user_token="") -> VideoconferenceVodUrlResult:
        """Recording download URLs, max 3 vods (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_vod_download_urls", vods=vods, org_id=org_id,
            operator=operator, user_token=user_token))

    def fetch_org_videoconference_conf(self, *, org_id, meeting_number="",
                                       operator="", user_token="") -> VideoconferenceConfResult:
        """Org videoconference config (blocking)."""
        return _run_async(self._ephemeral_call(
            "fetch_org_videoconference_conf", org_id=org_id,
            meeting_number=meeting_number, operator=operator, user_token=user_token))
