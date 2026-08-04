"""Lansenger SDK async client — framework-independent API client.

This is the core SDK client. It provides all Lansenger Smart Bot API
operations as async methods, with zero dependency on any agent framework.

Lansenger (蓝信) has multiple message types with different capabilities.
Developer-accessible msgType: text, formatText, oacard, appCard, linkCard,
appArticles, verifyCard, i18nAppCard, i18nSystemAction, i18nSystem.

This constraint shapes the API:
- send_text:       msgType=text   → plain text + optional file/image/video
- send_markdown:   msgType=formatText → Markdown text, NO attachments
- send_file:       msgType=text   → file/image/video only, optional caption
- send_image_url:  msgType=text   → image from URL, optional caption
- send_link_card:  msgType=linkCard → link preview card
- send_app_articles: msgType=appArticles → multi-article card
- send_app_card:    msgType=appCard → rich card with dynamic update support
- update_dynamic_card: POST → update appCard status in-place
- revoke_message:    POST → retract previously sent messages
- query_groups:      GET → list bot's group IDs
"""

from __future__ import annotations

import contextlib
import logging
import os
import tempfile
import time
from typing import Any
from urllib.parse import quote

import httpx

from .auth import _USER_TOKEN_REFRESH_MARGIN, TokenManager, UserTokenManager
from .config import LansengerConfig
from .constants import (
    APP_MEDIA_TYPE_FILE,
    APP_MEDIA_TYPE_IMAGE,
    APP_MEDIA_TYPE_VIDEO,
    APP_TO_MSG_MEDIA_TYPE,
    MEDIA_TYPE_FILE,
    guess_app_media_type,
    guess_media_type,
)
from .exceptions import LansengerAuthError, LansengerNetworkError
from .media import download_media, upload_app_media, upload_media
from .models import (
    AccountMessageResult,
    AppCardParams,
    ApproveCardParams,
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
    OaCardParams,
    OrgInfoResult,
    PersonalAppCreateResult,
    PersonalAppInfoResult,
    PersonalAppListResult,
    QueryGroupsResult,
    ScheduleAttendeeMetaResult,
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
from .oauth import exchange_code_for_user_token, refresh_user_token
from .persistence import CredentialStore
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.client")


def _parse_send_response(data: dict, msg_type: str = "", operation: str = "") -> SendMessageResult:
    """Parse a Lansenger API response into a SendMessageResult."""
    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return SendMessageResult(
            success=False,
            error=f"API error (errCode={err_code}): {msg}",
            msg_type=msg_type,
            operation=operation,
            retryable=True,
        )

    msg_id = data.get("data", {}).get("msgId")
    return SendMessageResult(
        success=True,
        message_id=msg_id,
        msg_type=msg_type,
        operation=operation,
        raw_response=data,
    )


class LansengerClient:
    """Framework-independent async client for Lansenger Smart Bot API.

    Usage:
        # From env vars
        client = LansengerClient.from_env()

        # Direct params
        client = LansengerClient(app_id="...", app_secret="...")

        # Send messages
        result = await client.send_text(chat_id="user123", content="Hello")
        result = await client.send_markdown(chat_id="user123", content="**Bold**")
    """

    def __init__(
        self,
        app_id: str = "",
        app_secret: str = "",
        api_gateway_url: str = "",
        passport_url: str = "",
        http_timeout: float = 30.0,
        store_path: str | None = None,
        encoding_key: str = "",
        callback_token: str = "",
        app_token: str = "",
        user_token: str = "",
    ):
        """Initialize the async client.

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
        self._config = LansengerConfig(
            app_id=app_id,
            app_secret=app_secret,
            api_gateway_url=api_gateway_url,
            passport_url=passport_url,
            http_timeout=http_timeout,
            encoding_key=encoding_key,
            callback_token=callback_token,
            app_token=app_token,
            user_token=user_token,
        )
        self._http_client: httpx.AsyncClient | None = None
        self._token_manager: TokenManager | None = None
        self._user_token_manager: UserTokenManager | None = None
        self._owns_http_client = True
        self._store: CredentialStore | None = CredentialStore(store_path) if store_path else None

    @classmethod
    def from_env(cls, store_path: str | None = None) -> LansengerClient:
        """Create client from environment variables.

        If store_path is provided, credentials and tokens are persisted
        to that file. Without store_path, everything stays in memory only.
        """
        config = LansengerConfig.from_env()
        return cls(
            app_id=config.app_id,
            app_secret=config.app_secret,
            api_gateway_url=config.api_gateway_url,
            passport_url=config.passport_url,
            http_timeout=config.http_timeout,
            store_path=store_path,
            encoding_key=config.encoding_key,
            callback_token=config.callback_token,
            app_token=config.app_token,
            user_token=config.user_token,
        )

    @classmethod
    def from_config(cls, config: LansengerConfig, store_path: str | None = None) -> LansengerClient:
        """Create client from a LansengerConfig instance."""
        return cls(
            app_id=config.app_id,
            app_secret=config.app_secret,
            api_gateway_url=config.api_gateway_url,
            passport_url=config.passport_url,
            http_timeout=config.http_timeout,
            store_path=store_path,
            encoding_key=config.encoding_key,
            callback_token=config.callback_token,
            app_token=config.app_token,
            user_token=config.user_token,
        )

    @classmethod
    def from_store(cls, profile: str = "default", path: str | None = None) -> LansengerClient:
        """Create client from a CredentialStore profile.

        Args:
            profile: Named profile in the credential store (default: "default").
            path: Optional custom path to the state file.

        Raises LansengerConfigError if the profile has no credentials.
        """
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
            api_gateway_url=creds.get("api_gateway_url") or "",
            passport_url=creds.get("passport_url", ""),
            redirect_uri=creds.get("redirect_uri", ""),
            encoding_key=creds.get("encoding_key", ""),
            callback_token=creds.get("callback_token", ""),
        )
        return cls.from_config(config, store_path=path)

    def _ensure_clients(self) -> None:
        """Lazily initialize HTTP client and token managers."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self._config.http_timeout)
            self._token_manager = TokenManager(self._config, self._http_client, store=self._store)
            self._user_token_manager = UserTokenManager(
                self._config, self._http_client, self._token_manager, store=self._store
            )
            self._owns_http_client = True

    def attach_http_client(self, http_client: httpx.AsyncClient) -> None:
        """Attach an external httpx.AsyncClient (e.g. shared from an agent framework).

        When attached, close() will NOT close the external client.
        """
        self._http_client = http_client
        self._token_manager = TokenManager(self._config, http_client, store=self._store)
        self._owns_http_client = False

    async def close(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_http_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            self._token_manager = None

    async def __aenter__(self) -> LansengerClient:
        self._ensure_clients()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    # ── Internal helpers ────────────────────────────────────────────────

    async def _get_token(self) -> str:
        self._ensure_clients()
        return await self._token_manager.get_token()

    async def get_user_token(self, staff_id: str = "") -> str:
        """Get a valid userToken, auto-refreshing if expired.

        When staff_id is provided, loads the token from the CredentialStore
        for that specific user. When staff_id is empty, uses the token
        registered with set_user_tokens() (single-user mode).

        Requires that tokens were registered via exchange_code() or
        set_user_tokens() first. Raises LansengerAuthError if
        refreshToken has expired (must re-authorize).

        Args:
            staff_id: Optional staff_id to get the token for a specific user.
                When provided, reads from the per-user credential store.
        """
        self._ensure_clients()

        if not staff_id:
            return await self._user_token_manager.get_token()

        if not self._store:
            raise LansengerAuthError(
                "CredentialStore is required for multi-user token management. "
                "Provide store_path when creating the client."
            )

        cached = self._store.load_user_token(staff_id=staff_id)
        user_token = cached.get("user_token", "")
        refresh_token = cached.get("refresh_token", "")
        expiry = cached.get("user_token_expiry", 0)

        if user_token and expiry > time.time():
            return user_token

        if not refresh_token:
            raise LansengerAuthError(
                f"No userToken available for staff_id={staff_id} and no refreshToken for auto-refresh. "
                "Run OAuth2 authorize flow: build_authorize_url → exchange_code."
            )

        app_token = await self._get_token()
        url = build_api_url(self._config, "oauth2", "refresh_token_create", app_token)
        url += f"&grant_type=refresh_token&refresh_token={quote(refresh_token)}"

        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise LansengerNetworkError(f"userToken refresh failed: {e}") from e

        err_code = data.get("errCode", -1)
        if err_code != 0:
            msg = data.get("errMsg", "Unknown refresh error")
            raise LansengerAuthError(
                f"userToken refresh error (errCode={err_code}): {msg}",
                err_code=err_code,
            )

        token_data = data.get("data", {})
        new_user_token = token_data.get("userToken")
        expires_in = token_data.get("expiresIn", 7200)
        new_refresh_token = token_data.get("refreshToken")
        refresh_expires_in = token_data.get("refreshExpiresIn", 0)
        new_staff_id = token_data.get("staffId") or staff_id

        if not new_user_token:
            raise LansengerAuthError("Refresh response missing userToken field")

        self._store.save_user_token(
            user_token=new_user_token,
            refresh_token=new_refresh_token or "",
            expires_in=expires_in,
            margin=_USER_TOKEN_REFRESH_MARGIN,
            refresh_expires_in=refresh_expires_in,
            staff_id=new_staff_id,
        )

        return new_user_token

    def set_user_tokens(
        self,
        user_token: str,
        refresh_token: str,
        expires_in: int = 7200,
        staff_id: str = "",
        refresh_expires_in: int = 0,
    ) -> None:
        """Register userToken + refreshToken for auto-refresh.

        Call after exchange_code() or any manual OAuth2 authorization
        to enable proactive refresh before expiry.

        When staff_id is provided, saves the token to the CredentialStore
        for that specific user (multi-user mode). When staff_id is empty,
        uses single-user mode.

        Args:
            user_token: The user's userToken.
            refresh_token: The user's refreshToken.
            expires_in: Token expiry in seconds (default: 7200).
            staff_id: Optional staff_id to associate with this token.
                When provided, saves to the per-user credential store.
            refresh_expires_in: Refresh token expiry in seconds.
        """
        self._ensure_clients()

        if self._store:
            self._store.save_user_token(
                user_token=user_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                margin=_USER_TOKEN_REFRESH_MARGIN,
                refresh_expires_in=refresh_expires_in,
                staff_id=staff_id,
            )

        self._user_token_manager.set_tokens(
            user_token=user_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            staff_id=staff_id,
            refresh_expires_in=refresh_expires_in,
        )

    def _private_msg_url(self, token: str) -> str:
        return build_api_url(self._config, "smart_bot", "private_message", token)

    def _group_msg_url(self, token: str) -> str:
        return build_api_url(self._config, "smart_bot", "group_message", token)

    async def _send_private(self, chat_id: str, msg_type: str, msg_data: dict, *, ref_msg_id: str = "") -> SendMessageResult:
        token = await self._get_token()
        url = self._private_msg_url(token)
        logger.debug("Sending %s to %s", msg_type, chat_id)
        payload = {
            "userIdList": [chat_id],
            "msgType": msg_type,
            "msgData": msg_data,
        }
        if ref_msg_id:
            payload["refMsgId"] = ref_msg_id
        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)

        if not response.text or not response.text.strip():
            return SendMessageResult(
                success=False, error="Empty API response — likely a payload format issue", retryable=True
            )

        return _parse_send_response(data, msg_type=msg_type)

    async def _send_group(self, group_id: str, msg_type: str, msg_data: dict, *, user_token: str = "", sender_id: str = "", ref_msg_id: str = "") -> SendMessageResult:
        token = await self._get_token()
        url = self._group_msg_url(token)
        logger.debug("Sending %s to group %s", msg_type, group_id)
        if user_token:
            url += f"&user_token={quote(user_token, safe='')}"
        payload: dict[str, Any] = {
            "groupId": group_id,
            "msgType": msg_type,
            "msgData": msg_data,
        }
        if sender_id:
            payload["senderId"] = sender_id
        if ref_msg_id:
            payload["refMsgId"] = ref_msg_id
        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)

        return _parse_send_response(data, msg_type=msg_type)

    # ── Public API: Message sending ─────────────────────────────────────

    async def send_text(
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
        """Send a plain text message (msgType=text).

        For private chat (is_group=False): uses 4.6.12 bot channel.
        For group chat (is_group=True): uses 4.6.2 group channel.
          - With user_token: sender appears as human user
          - Without user_token: sender appears as bot

        msgType=text supports: plain text, @mentions (group only),
        and optional file/image/video attachments.

        Args:
            chat_id: Recipient user ID or group chat ID.
            content: Plain text content (no Markdown).
            file_path: Optional local file/image/video to attach.
            media_type: "file"/"video"/"image"/"audio". Auto-detected if omitted.
            cover_image_path: Optional cover image for video attachments.
                When sending a video, the API requires mediaIds to be
                [videoMediaId, coverImageMediaId]. If omitted for video,
                mediaIds will only contain the video mediaId.
            reminder_all: @mention all members in group chat.
            reminder_user_ids: @mention specific user IDs in group chat.
            reminder_bot_ids: @mention specific bot IDs in group chat (prs5.7.0).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId (if no user_token).
            ref_msg_id: Reference message openId for reply (prs5.9.0).
        """
        self._ensure_clients()

        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not content and not file_path:
            return SendMessageResult(success=False, error="content or file_path is required")

        reminder: dict[str, Any] | None = None
        if reminder_all or (reminder_user_ids and len(reminder_user_ids) > 0) or (reminder_bot_ids and len(reminder_bot_ids) > 0):
            reminder = {"all": reminder_all, "userIds": reminder_user_ids or [], "botIds": reminder_bot_ids or []}

        text_data: dict[str, Any] = {"content": content}
        if reminder:
            text_data["reminder"] = reminder

        if file_path and os.path.isfile(file_path):
            mt = media_type or guess_app_media_type(file_path) or APP_MEDIA_TYPE_FILE
            upload_result = await upload_app_media(
                self._config, self._token_manager, self._http_client, file_path, mt
            )
            if upload_result.success and upload_result.media_id:
                text_data["mediaType"] = APP_TO_MSG_MEDIA_TYPE.get(mt, MEDIA_TYPE_FILE)
                media_ids = [upload_result.media_id]
                if cover_image_path and mt == APP_MEDIA_TYPE_VIDEO:
                    cover_upload = await upload_app_media(
                        self._config, self._token_manager, self._http_client,
                        cover_image_path, APP_MEDIA_TYPE_IMAGE,
                    )
                    if cover_upload.success and cover_upload.media_id:
                        media_ids.append(cover_upload.media_id)
                    else:
                        logger.warning("Cover image upload failed: %s", cover_upload.error)
                text_data["mediaIds"] = media_ids
            else:
                logger.warning("Media upload failed, sending plain text only: %s", upload_result.error)

        msg_data = {"text": text_data}

        if is_group:
            return await self._send_group(chat_id, "text", msg_data, user_token=user_token, sender_id=sender_id, ref_msg_id=ref_msg_id)
        return await self._send_private(chat_id, "text", msg_data, ref_msg_id=ref_msg_id)

    async def send_markdown(
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
        """Send a Markdown-formatted message (msgType=formatText).

        msgType=formatText supports: Markdown formatting (headings, bold,
        italic, code blocks, lists, links, tables).

        If reminder fails, automatically retries without reminder.

        Args:
            chat_id: Recipient user ID or group chat ID.
            content: Markdown-formatted content.
            reminder_all: @mention all members in group chat.
            reminder_user_ids: @mention specific user IDs in group chat.
            reminder_bot_ids: @mention specific bot IDs in group chat (prs5.7.0).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
            ref_msg_id: Reference message openId for reply (prs5.9.0).
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not content:
            return SendMessageResult(success=False, error="content is required")

        reminder: dict[str, Any] | None = None
        if reminder_all or (reminder_user_ids and len(reminder_user_ids) > 0) or (reminder_bot_ids and len(reminder_bot_ids) > 0):
            reminder = {"all": reminder_all, "userIds": reminder_user_ids or [], "botIds": reminder_bot_ids or []}

        fmt_data: dict[str, Any] = {"formatType": 1, "text": content}
        if reminder:
            fmt_data["reminder"] = reminder

        msg_data = {"formatText": fmt_data}

        if is_group:
            result = await self._send_group(chat_id, "formatText", msg_data, user_token=user_token, sender_id=sender_id, ref_msg_id=ref_msg_id)
        else:
            result = await self._send_private(chat_id, "formatText", msg_data, ref_msg_id=ref_msg_id)

        if not result.success and reminder:
            logger.info("send_markdown with reminder failed, retrying without reminder")
            fmt_data_no_reminder = {"formatType": 1, "text": content}
            msg_data_no_reminder = {"formatText": fmt_data_no_reminder}
            if is_group:
                return await self._send_group(chat_id, "formatText", msg_data_no_reminder, user_token=user_token, sender_id=sender_id)
            return await self._send_private(chat_id, "formatText", msg_data_no_reminder)

        return result

    async def send_file(
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
        """Send a local file/image/video (msgType=text, attachment only).

        Caption is plain text (no Markdown). If you need Markdown text
        alongside a file, use send_markdown() first, then send_file().

        Files do NOT support @mention/reminder (even though msgType=text).

        Args:
            chat_id: Recipient user ID or group chat ID.
            file_path: Path to the local file. Must exist on disk.
            caption: Optional plain-text caption.
            media_type: "file"/"video"/"image"/"audio". Auto-detected if omitted.
            cover_image_path: Optional cover image for video attachments.
                When sending a video, the API requires mediaIds to be
                [videoMediaId, coverImageMediaId].
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        self._ensure_clients()

        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not file_path:
            return SendMessageResult(success=False, error="file_path is required")

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        if not os.path.isfile(file_path):
            return SendMessageResult(success=False, error=f"File not found: {file_path}")

        mt = media_type or guess_app_media_type(file_path) or APP_MEDIA_TYPE_FILE

        upload_result = await upload_app_media(
            self._config, self._token_manager, self._http_client, file_path, mt
        )
        if not upload_result.success or not upload_result.media_id:
            return SendMessageResult(
                success=False,
                error=f"Failed to upload file: {upload_result.error}",
            )

        media_ids = [upload_result.media_id]
        if cover_image_path and mt == APP_MEDIA_TYPE_VIDEO:
            cover_upload = await upload_app_media(
                self._config, self._token_manager, self._http_client,
                cover_image_path, APP_MEDIA_TYPE_IMAGE,
            )
            if cover_upload.success and cover_upload.media_id:
                media_ids.append(cover_upload.media_id)

        text_data: dict[str, Any] = {
            "content": caption,
            "mediaType": APP_TO_MSG_MEDIA_TYPE.get(mt, MEDIA_TYPE_FILE),
            "mediaIds": media_ids,
        }
        msg_data = {"text": text_data}

        if is_group:
            return await self._send_group(chat_id, "text", msg_data, user_token=user_token, sender_id=sender_id)
        return await self._send_private(chat_id, "text", msg_data)

    async def send_image_url(
        self,
        chat_id: str,
        image_url: str,
        *,
        caption: str = "",
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an image from a URL (download first, then upload to Lansenger).

        Args:
            chat_id: Recipient user ID or group chat ID.
            image_url: URL of the image to download and send.
            caption: Optional plain-text caption (no Markdown).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        self._ensure_clients()

        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not image_url:
            return SendMessageResult(success=False, error="image_url is required")

        try:
            resp = await self._http_client.get(image_url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            image_bytes = resp.content
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"Failed to download image: {e}")

        ct = resp.headers.get("content-type", "")
        if "png" in ct:
            suffix = ".png"
        elif "gif" in ct:
            suffix = ".gif"
        elif "webp" in ct:
            suffix = ".webp"
        else:
            suffix = ".jpg"

        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="lansenger_url_image_")
        os.write(fd, image_bytes)
        os.close(fd)

        try:
            result = await self.send_file(chat_id, temp_path, caption=caption, media_type=APP_MEDIA_TYPE_IMAGE, is_group=is_group, user_token=user_token, sender_id=sender_id)
            with contextlib.suppress(OSError):
                os.remove(temp_path)
            return result
        except Exception as e:
            with contextlib.suppress(OSError):
                os.remove(temp_path)
            return SendMessageResult(success=False, error=str(e))

    async def send_link_card(
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
        """Send a linkCard message (rich link preview card).

        linkCard does NOT support @mention/reminder.

        Args:
            chat_id: Recipient user ID or group chat ID.
            title: Card title (required).
            link: Card click-through link (required).
            description: Card description text.
            icon_link: Card icon image link.
            pc_link: PC client redirect link.
            pad_link: Pad client redirect link.
            from_name: Card source name.
            from_icon_link: Source icon image link.
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not title:
            return SendMessageResult(success=False, error="title is required")
        if not link:
            return SendMessageResult(success=False, error="link is required")

        msg_data = {
            "linkCard": {
                "title": title,
                "link": link,
                "description": description,
                "iconLink": icon_link,
                "pcLink": pc_link,
                "padLink": pad_link,
                "fromName": from_name,
                "fromIconLink": from_icon_link,
            }
        }

        if is_group:
            return await self._send_group(chat_id, "linkCard", msg_data, user_token=user_token, sender_id=sender_id)
        return await self._send_private(chat_id, "linkCard", msg_data)

    async def send_link_card_with_params(
        self,
        params: LinkCardParams,
    ) -> SendMessageResult:
        """Send a linkCard using a LinkCardParams object."""
        return await self.send_link_card(
            chat_id=params.chat_id,
            title=params.title,
            link=params.link,
            description=params.description,
            icon_link=params.icon_link,
            pc_link=params.pc_link,
            pad_link=params.pad_link,
            from_name=params.from_name,
            from_icon_link=params.from_icon_link,
            is_group=params.is_group,
            user_token=params.user_token,
            sender_id=params.sender_id,
        )

    async def send_app_articles(
        self,
        chat_id: str,
        articles: list[dict[str, str]],
        *,
        is_group: bool = False,
        user_token: str = "",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Send an appArticles (图文卡片) multi-article card.

        appArticles does NOT support @mention/reminder.

        Each article dict must contain:
            - imgUrl (required): Image URL
            - title (required): Article title
            - url (required): Content link URL
            - pcUrl (required): PC content link URL
            Optional: summary

        Args:
            chat_id: Recipient user ID or group chat ID.
            articles: List of article dicts (1+ entries).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not articles:
            return SendMessageResult(success=False, error="articles is required")

        msg_data = {"appArticles": articles}

        if is_group:
            return await self._send_group(chat_id, "appArticles", msg_data, user_token=user_token, sender_id=sender_id)
        return await self._send_private(chat_id, "appArticles", msg_data)

    async def send_app_card(
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
        """Send an appCard (应用卡片) rich formatted card.

        appCard supports div-style HTML formatting (color, font-size,
        text-align, text-indent) in body_title, body_sub_title,
        body_content, and signature fields.

        appCard does NOT support @mention/reminder.

        NOTE: appCard vs i18nAppCard:
        - appCard: supports isDynamic + headStatusInfo for in-place status
          updates, but uses a SINGLE language.
        - i18nAppCard: supports 5 languages but NO dynamic updates or
          headStatusInfo.

        Args:
            chat_id: Recipient user ID or group chat ID.
            body_title: Card body title (required, max 600 bytes).
            head_title: Card header title.
            body_sub_title: Card body subtitle (max 1200 bytes).
            body_content: Card body content (max 3000 bytes).
            signature: Card signature line.
            fields: Key-value pairs (max 10).
            links: Link entries (max 3).
            card_link: Card click-through link.
            pc_card_link: PC client click-through link.
            pad_card_link: Pad client click-through link.
            is_dynamic: Enable dynamic card status updates.
            head_status_info: Dynamic card status dict (iconLink/description/colour).
            staff_id: Staff ID for sender avatar.
            head_icon_url: Header icon URL.
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not body_title:
            return SendMessageResult(success=False, error="body_title is required for appCard")

        app_card_data: dict[str, Any] = {
            "bodyTitle": body_title,
        }
        if head_title:
            app_card_data["headTitle"] = head_title
        if head_icon_url:
            app_card_data["headIconUrl"] = head_icon_url
        app_card_data["isDynamic"] = is_dynamic
        if card_link:
            app_card_data["cardLink"] = card_link
        if pc_card_link:
            app_card_data["pcCardLink"] = pc_card_link

        if is_dynamic and not head_status_info:
            head_status_info = {
                "description": '<div style="color:rgba(0,0,0,.47)">Active</div>',
                "colour": "rgba(0,0,0,.47)",
            }
        if is_dynamic and head_status_info:
            app_card_data["headStatusInfo"] = head_status_info

        if body_sub_title:
            app_card_data["bodySubTitle"] = body_sub_title
        if body_content:
            app_card_data["bodyContent"] = body_content
        if signature:
            app_card_data["signature"] = signature
        if staff_id:
            app_card_data["staffId"] = staff_id
        if fields:
            app_card_data["fields"] = fields
        if pad_card_link:
            app_card_data["padCardLink"] = pad_card_link
        if links:
            app_card_data["links"] = links

        msg_data = {"appCard": app_card_data}

        if is_group:
            return await self._send_group(chat_id, "appCard", msg_data, user_token=user_token, sender_id=sender_id)

        return await self._send_private(chat_id, "appCard", msg_data)

    async def send_app_card_with_params(
        self,
        params: AppCardParams,
    ) -> SendMessageResult:
        """Send an appCard using an AppCardParams object."""
        return await self.send_app_card(
            chat_id=params.chat_id,
            body_title=params.body_title,
            head_title=params.head_title,
            body_sub_title=params.body_sub_title,
            body_content=params.body_content,
            signature=params.signature,
            fields=params.fields,
            links=params.links,
            card_link=params.card_link,
            pc_card_link=params.pc_card_link,
            pad_card_link=params.pad_card_link,
            is_dynamic=params.is_dynamic,
            head_status_info=params.head_status_info,
            staff_id=params.staff_id,
            head_icon_url=params.head_icon_url,
            is_group=params.is_group,
            user_token=params.user_token,
            sender_id=params.sender_id,
        )

    async def send_oacard(
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
        """Send an oaCard (OA审批卡片) message.

        oaCard does NOT support @mention/reminder.

        Args:
            chat_id: Recipient user ID or group chat ID.
            title: Card title (required).
            head: Card header text.
            sub_title: Card subtitle.
            staff_id: Staff ID for sender avatar.
            fields: Key-value pairs (max 10).
            link: Card click-through link.
            pc_link: PC client click-through link.
            pad_link: Pad client click-through link.
            card_action: Card action dict (prs5.3.0).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not title:
            return SendMessageResult(success=False, error="title is required for oaCard")

        oa_card_data: dict[str, Any] = {
            "title": title,
        }
        if head:
            oa_card_data["head"] = head
        if sub_title:
            oa_card_data["subTitle"] = sub_title
        if staff_id:
            oa_card_data["staffId"] = staff_id
        if fields:
            oa_card_data["fields"] = fields
        if link:
            oa_card_data["link"] = link
        if pc_link:
            oa_card_data["pcLink"] = pc_link
        if pad_link:
            oa_card_data["padLink"] = pad_link
        if card_action:
            oa_card_data["cardAction"] = card_action

        msg_data = {"oacard": oa_card_data}

        if is_group:
            return await self._send_group(chat_id, "oacard", msg_data, user_token=user_token, sender_id=sender_id)

        return await self._send_private(chat_id, "oacard", msg_data)

    async def send_oacard_with_params(
        self,
        params: OaCardParams,
    ) -> SendMessageResult:
        """Send an oaCard using an OaCardParams object."""
        return await self.send_oacard(
            chat_id=params.chat_id,
            title=params.title,
            head=params.head,
            sub_title=params.sub_title,
            staff_id=params.staff_id,
            fields=params.fields,
            link=params.link,
            pc_link=params.pc_link,
            pad_link=params.pad_link,
            card_action=params.card_action,
            is_group=params.is_group,
            user_token=params.user_token,
            sender_id=params.sender_id,
        )

    # ── Public API: ApproveCard (审批卡片) ───────────────────────────────

    def _build_approve_card_data(self, params: ApproveCardParams) -> dict[str, Any]:
        """Build approveCard msgData from params."""
        card: dict[str, Any] = {}

        # head
        head: dict[str, Any] = {}
        if params.head_title:
            head["title"] = params.head_title
        if params.head_icon_link:
            head["iconLink"] = params.head_icon_link
        if params.head_icon_id:
            head["iconId"] = params.head_icon_id
        if any([params.head_status_describe, params.head_status_icon,
                params.head_status_icon_link, params.head_status_colour]):
            head_status: dict[str, Any] = {}
            if params.head_status_describe:
                head_status["describe"] = params.head_status_describe
            if params.head_status_icon:
                head_status["statusIcon"] = params.head_status_icon
            if params.head_status_icon_link:
                head_status["iconLink"] = params.head_status_icon_link
            if params.head_status_colour:
                head_status["colour"] = params.head_status_colour
            head["headStatus"] = head_status
        if head:
            card["head"] = head

        # body
        body: dict[str, Any] = {}
        if params.body_title:
            body["title"] = params.body_title
        if params.body_content:
            body["content"] = {
                "formatType": params.body_format_type,
                "text": params.body_content,
            }
        if params.fields:
            body["fields"] = params.fields
        if body:
            card["body"] = body

        # reminder
        reminder: dict[str, Any] = {}
        if params.reminder_all:
            reminder["all"] = True
        if params.reminder_user_ids:
            reminder["userIds"] = params.reminder_user_ids
        if params.reminder_bot_ids:
            reminder["botIds"] = params.reminder_bot_ids
        if reminder:
            card["reminder"] = reminder

        # cardLink
        if params.card_link:
            card_link: dict[str, str] = {"cardLink": params.card_link}
            if params.card_link_for_pc:
                card_link["cardLinkForPc"] = params.card_link_for_pc
            if params.card_link_for_pad:
                card_link["cardLinkForPad"] = params.card_link_for_pad
            card["cardLink"] = card_link

        # buttons
        if params.buttons:
            card["buttons"] = params.buttons

        # expireTime
        if params.expire_time:
            card["expireTime"] = params.expire_time

        return {"approveCard": card}

    async def send_approve_card(
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
        is_bot_channel: bool = False,
    ) -> SendMessageResult:
        """Send an approveCard (审批卡片) message — 4.6.4.13.

        Supports @mention/reminder, buttons with callbackInfo,
        per-button permission scopes, and card expiry.

        Args:
            chat_id: Recipient user ID (private) or group ID (is_group=True).
            body_title: Card body title (required).
            body_content: Card body markdown content (required).
            head_title: Card header title.
            head_icon_link: Header icon URL.
            head_icon_id: Header icon ID.
            head_status_describe: Status description text.
            head_status_icon: Status icon type (1=实心圆).
            head_status_icon_link: Status icon URL.
            head_status_colour: Status text/icon colour.
            body_format_type: 0=INVALID, 1=MARK_DOWN (default 1).
            fields: Form key-value pairs.
            reminder_all: @mention all members (group only).
            reminder_user_ids: @mention specific users (group only).
            reminder_bot_ids: @mention specific bots (group only).
            card_link: Overall card click link.
            card_link_for_pc: PC click link.
            card_link_for_pad: Pad click link.
            buttons: Button list. Each dict: text, buttonTheme, state,
                link, pcLink, padLink, callbackInfo,
                permissionScope (permittedStaffs/prohibitedStaffs),
                prohibitedState.
            expire_time: Card expiry in seconds (max 30 days, 0=default 7d).
            is_group: True if chat_id is a group ID.
            user_token: For group messages — makes sender appear as human.
            sender_id: For group messages — explicit sender openId.
            is_bot_channel: True to use bot channel, False for smart_bot.
        """
        if not chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not body_title:
            return SendMessageResult(success=False, error="body_title is required for approveCard")
        if not body_content:
            return SendMessageResult(success=False, error="body_content is required for approveCard")

        params = ApproveCardParams(
            chat_id=chat_id, body_title=body_title, body_content=body_content,
            head_title=head_title, head_icon_link=head_icon_link,
            head_icon_id=head_icon_id, head_status_describe=head_status_describe,
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
            is_bot_channel=is_bot_channel,
        )
        return await self.send_approve_card_with_params(params)

    async def send_approve_card_with_params(
        self,
        params: ApproveCardParams,
    ) -> SendMessageResult:
        """Send an approveCard using an ApproveCardParams object."""
        if not params.chat_id:
            return SendMessageResult(success=False, error="chat_id is required")
        if not params.body_title:
            return SendMessageResult(success=False, error="body_title is required for approveCard")
        if not params.body_content:
            return SendMessageResult(success=False, error="body_content is required for approveCard")

        msg_data = self._build_approve_card_data(params)

        if params.is_group:
            return await self._send_group(params.chat_id, "approveCard", msg_data,
                                         user_token=params.user_token, sender_id=params.sender_id)

        # Smart bot channel (also used for bot channel — same endpoint)
        return await self._send_private(params.chat_id, "approveCard", msg_data)

    async def update_approve_card(
        self,
        msg_id: str,
        *,
        head_status_describe: str = "",
        head_status_icon: int = 0,
        head_status_icon_link: str = "",
        head_status_colour: str = "",
        buttons: list[dict[str, Any]] | None = None,
    ) -> SendMessageResult:
        """Update an approveCard's status in-place — 4.6.4.12.

        Uses POST /v1/messages/dynamic/update with msgType=approveCard.
        The card body is wrapped in approveCardUpdateMsg.

        Args:
            msg_id: The message ID from the original send_approve_card response.
            head_status_describe: Updated status description.
            head_status_icon: Updated status icon (1=实心圆).
            head_status_icon_link: Updated status icon URL.
            head_status_colour: Updated status colour.
            buttons: Updated button list (same structure as create).
        """
        self._ensure_clients()

        if not msg_id:
            return SendMessageResult(success=False, error="msg_id is required")

        token = await self._get_token()
        url = build_api_url(self._config, "message", "dynamic_update", token)

        update_data: dict[str, Any] = {}
        if any([head_status_describe, head_status_icon,
                head_status_icon_link, head_status_colour]):
            head_status: dict[str, Any] = {}
            if head_status_describe:
                head_status["describe"] = head_status_describe
            if head_status_icon:
                head_status["statusIcon"] = head_status_icon
            if head_status_icon_link:
                head_status["iconLink"] = head_status_icon_link
            if head_status_colour:
                head_status["colour"] = head_status_colour
            update_data["headStatus"] = head_status

        if buttons:
            update_data["buttons"] = buttons

        payload = {
            "msgId": msg_id,
            "msgType": "approveCard",
            "msgData": {"approveCardUpdateMsg": update_data},
        }

        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)

        return _parse_send_response(data, operation="approve_card_update")

    # ── Public API: Dynamic card update ─────────────────────────────────

    async def update_dynamic_card(
        self,
        msg_id: str,
        *,
        head_status_info: dict[str, str] | None = None,
        links: list[dict[str, str]] | None = None,
        is_last_update: bool = False,
    ) -> SendMessageResult:
        """Update a dynamic appCard's status in-place.

        The card must have been sent with is_dynamic=True.
        Uses POST /v1/messages/dynamic/update.

        Args:
            msg_id: The message ID from the original send_app_card response.
            head_status_info: Updated status dict (description/colour/iconLink).
            links: Updated link entries (max 3).
            is_last_update: True = final state, card becomes static after this.
        """
        self._ensure_clients()

        if not msg_id:
            return SendMessageResult(success=False, error="msg_id is required")

        token = await self._get_token()
        url = build_api_url(self._config, "message", "dynamic_update", token)

        app_card_update: dict[str, Any] = {"isLastUpdate": is_last_update}
        if head_status_info:
            app_card_update["headStatusInfo"] = head_status_info
        if links:
            app_card_update["links"] = links

        payload = {
            "msgId": msg_id,
            "msgType": "appCard",
            "msgData": {"appCardUpdateMsg": app_card_update},
        }

        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)

        return _parse_send_response(data, operation="dynamic_card_update")

    async def update_dynamic_card_with_params(
        self,
        params: DynamicCardUpdateParams,
    ) -> SendMessageResult:
        """Update a dynamic card using a DynamicCardUpdateParams object."""
        return await self.update_dynamic_card(
            msg_id=params.msg_id,
            head_status_info=params.head_status_info,
            links=params.links,
            is_last_update=params.is_last_update,
        )

    # ── Public API: Message management ──────────────────────────────────

    async def revoke_message(
        self,
        message_ids: list[str],
        *,
        chat_type: str = "bot",
        sender_id: str = "",
    ) -> SendMessageResult:
        """Revoke previously sent messages.

        Args:
            message_ids: List of message IDs to revoke.
            chat_type: Message type: staff, group, notification, account, bot.
            sender_id: Sender ID (required for staff/group chat types).
        """
        self._ensure_clients()

        if not message_ids:
            return SendMessageResult(success=False, error="message_ids is required")
        if chat_type in ("staff", "group") and not sender_id:
            return SendMessageResult(
                success=False, error=f"chat_type='{chat_type}' requires sender_id"
            )

        token = await self._get_token()
        url = build_api_url(self._config, "message", "revoke", token)

        payload: dict[str, Any] = {
            "chatType": chat_type,
            "messageIds": message_ids,
        }
        if sender_id:
            payload["senderId"] = sender_id

        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return SendMessageResult(success=False, error=f"HTTP error: {e}", retryable=True)

        return _parse_send_response(data, operation="revoke")

    async def query_groups(
        self,
        *,
        page_offset: int = 0,
        page_size: int = 100,
    ) -> QueryGroupsResult:
        """Query the bot's group ID list via GET /v2/groups/fetch.

        .. deprecated::
            Use :func:`lansenger_sdk.groups.fetch_group_list` instead.

        Args:
            page_offset: Page offset, starting from 0 (default: 0).
            page_size: Per-page count (max 100, default: 100).

        Returns:
            QueryGroupsResult with total_group_ids and group_ids.
        """
        from .groups import fetch_group_list

        token = await self._get_token()
        result = await fetch_group_list(
            self._config, token,
            page_offset=page_offset, page_size=page_size,
        )
        return QueryGroupsResult(
            success=result.success,
            total_group_ids=result.total_group_ids,
            group_ids=result.group_ids or [],
            error=result.error,
            raw_response=result.raw_response,
        )

    # ── Public API: Media operations ────────────────────────────────────

    async def upload_media(
        self,
        file_path: str,
        *,
        media_type: int | None = None,
        user_token: str = "",
    ) -> SendMessageResult:
        """Upload a media file via core service endpoint (4.5.1).

        Args:
            file_path: Path to the local file.
            media_type: 1=video, 2=image, 3=file. Auto-detected if omitted.
            user_token: Optional userToken (4.5.1 accepts this).
        """
        self._ensure_clients()
        mt = media_type or guess_media_type(file_path) or MEDIA_TYPE_FILE
        result = await upload_media(
            self._config, self._token_manager, self._http_client,
            file_path, mt, user_token=user_token,
        )
        if result.success:
            return SendMessageResult(
                success=True, message_id=result.media_id, operation="upload_media",
                raw_response=result.raw_response if hasattr(result, "raw_response") else None,
            )
        return SendMessageResult(success=False, error=result.error, operation="upload_media")

    async def upload_app_media(
        self,
        file_path: str,
        *,
        media_type: str | None = None,
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
    ) -> SendMessageResult:
        """Upload a media file via app/bot endpoint (4.5.4).

        Uses /v1/app/medias/create with string type values ("file", "video", "image", "audio").
        Higher size limits: 10MB for image, 20MB for others.
        Only for self-built apps (not ISV apps). No userToken parameter.

        Args:
            file_path: Path to the local file.
            media_type: "file", "video", "image", or "audio". Auto-detected if omitted.
            width: Optional width (for video/image).
            height: Optional height (for video/image).
            duration: Optional duration in seconds (for video/audio).
        """
        self._ensure_clients()
        from .constants import APP_MEDIA_TYPE_FILE, guess_app_media_type
        from .media import upload_app_media

        mt = media_type or guess_app_media_type(file_path) or APP_MEDIA_TYPE_FILE
        result = await upload_app_media(
            self._config, self._token_manager, self._http_client,
            file_path, mt, width=width, height=height, duration=duration,
        )
        if result.success:
            return SendMessageResult(
                success=True, message_id=result.media_id, operation="upload_app_media",
            )
        return SendMessageResult(success=False, error=result.error, operation="upload_app_media")

    async def upload_app_media_v2(
        self,
        file_path: str,
        *,
        media_type: str | None = None,
        user_token: str = "",
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
    ) -> SendMessageResult:
        """Upload a media file via app/bot endpoint V2 (4.5.5).

        Uses /v2/app/medias/create. Same parameters as 4.5.4 (V1) plus the
        required user_token.

        Args:
            file_path: Path to the local file.
            media_type: "file", "video", "image", or "audio". Auto-detected if omitted.
            user_token: User token (required by V2).
            width: Optional width (for video/image).
            height: Optional height (for video/image).
            duration: Optional duration in seconds (for video/audio).
        """
        self._ensure_clients()
        from .media import upload_app_media_v2

        mt = media_type or guess_app_media_type(file_path) or APP_MEDIA_TYPE_FILE
        result = await upload_app_media_v2(
            self._config, self._token_manager, self._http_client,
            file_path, mt, user_token=user_token,
            width=width, height=height, duration=duration,
        )
        if result.success:
            return SendMessageResult(
                success=True, message_id=result.media_id, operation="upload_app_media_v2",
            )
        return SendMessageResult(success=False, error=result.error, operation="upload_app_media_v2")

    async def download_media_by_share_id(
        self,
        share_id: str,
        *,
        user_token: str = "",
    ) -> DownloadMediaResult:
        """Download a file by its share ID (4.5.6).

        Uses GET /v1/media/share/{shareid}/fetch. Success returns the file
        binary stream.

        Args:
            share_id: File share ID.
            user_token: Optional user token.

        Returns:
            DownloadMediaResult with data bytes on success.
        """
        self._ensure_clients()
        from .media import download_media_by_share_id

        return await download_media_by_share_id(
            self._config, self._token_manager, self._http_client,
            share_id, user_token=user_token,
        )

    async def download_media(
        self,
        media_id: str,
    ) -> DownloadMediaResult:
        """Download media bytes from Lansenger by media ID.

        Args:
            media_id: Lansenger media ID.

        Returns:
            DownloadMediaResult with data bytes on success.
        """
        self._ensure_clients()
        return await download_media(
            self._config, self._token_manager, self._http_client, media_id
        )

    async def download_media_to_file(
        self,
        media_id: str,
        *,
        target_path: str | None = None,
        media_type: str = "file",
    ) -> str:
        """Download media and save to a file.

        Args:
            media_id: Lansenger media ID.
            target_path: Target path. None = auto temp file.
            media_type: "image"/"video"/"file"/"voice" for extension hint.

        Returns:
            Path to the saved file.
        """
        self._ensure_clients()
        from .media import download_media_to_file

        return await download_media_to_file(
            self._config,
            self._token_manager,
            self._http_client,
            media_id,
            target_path=target_path,
            media_type=media_type,
        )

    # ── Utility: Token management ───────────────────────────────────────

    async def get_token(self) -> str:
        """Get the current app access token (public accessor)."""
        return await self._get_token()

    def invalidate_token(self) -> None:
        """Force token refresh on next API call."""
        if self._token_manager:
            self._token_manager.invalidate()

    # ── Utility: Health check ───────────────────────────────────────────

    async def health_check(self) -> bool:
        """Verify credentials work by attempting to get a token.

        Returns True if token was obtained successfully, False otherwise.
        """
        try:
            await self._get_token()
            return True
        except Exception:
            return False

    # ── OAuth2: User authentication ─────────────────────────────────────

    def build_authorize_url(
        self,
        redirect_uri: str,
        *,
        scope: str | list[str] | None = None,
        state: str | None = None,
    ) -> str:
        """Build the OAuth2 authorize URL for user identity verification.

        Lansenger uses OAuth2 when an org bot/app needs to identify a
        specific user. The flow:
        1. Build this URL and redirect the user to it
        2. User logs in on the Lansenger passport page
        3. Lansenger redirects back to redirect_uri with code + state
        4. Exchange the code for a user access token (future API)

        This is different from appToken auth:
        - appToken: authenticates the bot itself (for sending messages)
        - OAuth2 code: authenticates a specific Lansenger user (for user-level ops)

        Args:
            redirect_uri: URL Lansenger redirects to after authorization.
                Domain must be in the app's trusted domain list.
            scope: OAuth2 scope(s). Default: "basic_userinfor".
                Pass a list for multiple scopes: ["basic_userinfor", ...]
            state: CSRF protection string. Auto-generated UUID if None.

        Returns:
            Full authorize URL string.

        Raises:
            LansengerConfigError: if passport_url is not configured.
        """
        from .oauth import build_authorize_url

        return build_authorize_url(
            self._config,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
        )

    @staticmethod
    def parse_authorize_callback(query_string: str | dict) -> dict:
        """Parse the OAuth2 authorize callback redirect parameters.

        After the user authorizes, Lansenger redirects to redirect_uri
        with code and state. Use this to parse them.

        Args:
            query_string: Dict or raw query string "code=XXX&state=YYY".

        Returns:
            Dict with: code, state, (optional) error, error_description.
        """
        from .oauth import parse_authorize_callback

        return parse_authorize_callback(query_string)

    @staticmethod
    def validate_callback_state(callback_state: str, expected_state: str) -> bool:
        """Validate OAuth2 callback state matches expected (CSRF protection).

        Args:
            callback_state: State received in the callback.
            expected_state: State that was sent in the authorize request.

        Returns:
            True if match, False otherwise.
        """
        from .oauth import validate_callback_state

        return validate_callback_state(callback_state, expected_state)

    # ── OAuth2: Code exchange ───────────────────────────────────────────

    async def exchange_code(
        self,
        code: str,
        *,
        redirect_uri: str = "",
    ) -> UserTokenResult:
        """Exchange an OAuth2 authorization code for userToken + refreshToken.

        This is step 2 of the OAuth2 flow. Uses GET /v2/user_token/create
        with the bot's appToken + the authorization code obtained from the
        authorize callback.

        Authentication hierarchy:
        - appToken: bot's credential → used by this method to prove bot identity
        - code: user's authorization → proves user consented
        - userToken: returned here → authenticates the specific user for future calls
        - refreshToken: returned here → long-lived (30 days), used to refresh userToken

        Args:
            code: The authorization code from the OAuth2 callback.
                Valid for 5 minutes, one-time use only.
            redirect_uri: Optional, same redirect_uri used in authorize URL.

        Returns:
            UserTokenResult with userToken, refreshToken, staffId, scope, state.
        """
        self._ensure_clients()

        app_token = await self._get_token()
        result = await exchange_code_for_user_token(
            self._config,
            app_token=app_token,
            code=code,
            http_client=self._http_client,
            redirect_uri=redirect_uri,
        )

        if result.success:
            if self._store:
                self._store.save_user_token(
                    user_token=result.user_token,
                    refresh_token=result.refresh_token,
                    expires_in=result.expires_in,
                    refresh_expires_in=result.refresh_expires_in or 0,
                    staff_id=result.staff_id or "",
                )
            self._user_token_manager.set_tokens(
                user_token=result.user_token,
                refresh_token=result.refresh_token,
                expires_in=result.expires_in,
                refresh_expires_in=result.refresh_expires_in or 0,
                staff_id=result.staff_id or "",
            )

        return result

    async def refresh_user_token(
        self,
        refresh_token: str,
        *,
        scope: str = "",
    ) -> UserTokenResult:
        """Refresh an expired userToken using a refreshToken.

        Uses GET /v1/refresh_token/create. The returned refreshToken
        replaces the old one (old becomes invalid). Total validity
        does NOT extend — only the remaining time from the original
        30-day grant.

        If refreshToken has expired, must re-initiate the full OAuth2
        authorize flow (build_authorize_url → exchange_code).

        Args:
            refresh_token: The refreshToken from a previous exchange_code
                or refresh_user_token call.
            scope: Optional scope (can only narrow from original grant).

        Returns:
            UserTokenResult with new userToken, new refreshToken, staffId.
            IMPORTANT: Always use the returned refreshToken for subsequent
            refreshes — the old one is invalidated.
        """
        self._ensure_clients()

        app_token = await self._get_token()
        return await refresh_user_token(
            self._config,
            app_token=app_token,
            refresh_token=refresh_token,
            http_client=self._http_client,
            scope=scope,
        )

    # ── User information ──────────────────────────────────────────────

    async def fetch_user_info(
        self,
        user_token: str,
    ) -> UserInfoResult:
        """Fetch a Lansenger user's basic information.

        Uses GET /v1/users/fetch with appToken + userToken. Returns the
        user's name, org, department, phone, email, avatar, etc.

        Requires both tokens:
        - appToken: bot's credential (obtained automatically by this method)
        - userToken: user's OAuth2 credential (obtained via exchange_code)

        Args:
            user_token: The user's userToken from a previous exchange_code
                or refresh_user_token call.

        Returns:
            UserInfoResult with staffId, name, org, department, email, phone, etc.
        """
        self._ensure_clients()
        from .users import fetch_user_info

        app_token = await self._get_token()
        return await fetch_user_info(
            self._config,
            app_token=app_token,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Public API: Contacts / Staff ────────────────────────────────────────

    async def fetch_staff_basic_info(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> StaffBasicInfoResult:
        """Fetch a staff member's basic information.

        Uses GET /v1/staffs/:staffid/fetch with appToken (and optional
        userToken).

        Args:
            staff_id: Staff openId.
            user_token: Optional userToken for user-scoped access.

        Returns:
            StaffBasicInfoResult with orgId, name, gender, avatar, departments, etc.
        """
        if not staff_id:
            return StaffBasicInfoResult(success=False, error="staff_id is required")
        self._ensure_clients()
        from .contacts import fetch_staff_basic_info

        app_token = await self._get_token()
        return await fetch_staff_basic_info(
            self._config,
            app_token=app_token,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_staff_detail(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> StaffDetailResult:
        """Fetch a staff member's detailed information.

        Uses GET /v1/staffs/:staffid/infor/fetch. Requires org or personal
        auth — providing userToken is recommended.

        Args:
            staff_id: Staff openId.
            user_token: Optional userToken (recommended for personal auth).

        Returns:
            StaffDetailResult with full profile: email, phone, education, career, etc.
        """
        if not staff_id:
            return StaffDetailResult(success=False, error="staff_id is required")
        self._ensure_clients()
        from .contacts import fetch_staff_detail

        app_token = await self._get_token()
        return await fetch_staff_detail(
            self._config,
            app_token=app_token,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_department_ancestors(
        self,
        staff_id: str,
        *,
        user_token: str = "",
    ) -> DepartmentAncestorsResult:
        """Fetch ancestor department chain for a staff member.

        Uses GET /v1/staffs/:staffid/departmentancestors/fetch.

        Args:
            staff_id: Staff openId.
            user_token: Optional userToken.

        Returns:
            DepartmentAncestorsResult with ancestor_groups (list of ancestor chains).
        """
        if not staff_id:
            return DepartmentAncestorsResult(success=False, error="staff_id is required")
        self._ensure_clients()
        from .contacts import fetch_department_ancestors

        app_token = await self._get_token()
        return await fetch_department_ancestors(
            self._config,
            app_token=app_token,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_staff_id_mapping(
        self,
        org_id: str,
        id_type: str,
        id_value: str,
        *,
        user_token: str = "",
    ) -> StaffIdMappingResult:
        """Map a unique identifier (phone/email/etc) to staffId.

        Uses GET /v2/staffs/id_mapping/fetch.

        Args:
            org_id: Organization ID.
            id_type: One of: "employ_id", "mobile", "mail", "login", "external_id".
            id_value: The identifier value to look up.
            user_token: Optional userToken.

        Returns:
            StaffIdMappingResult with staff_id.
        """
        if not org_id:
            return StaffIdMappingResult(success=False, error="org_id is required")
        if not id_type:
            return StaffIdMappingResult(success=False, error="id_type is required")
        if not id_value:
            return StaffIdMappingResult(success=False, error="id_value is required")
        self._ensure_clients()
        from .contacts import fetch_staff_id_mapping

        app_token = await self._get_token()
        return await fetch_staff_id_mapping(
            self._config,
            app_token=app_token,
            org_id=org_id,
            id_type=id_type,
            id_value=id_value,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_org_extra_field_ids(
        self,
        org_id: str,
        *,
        user_token: str = "",
        page: int = 1,
        page_size: int = 1000,
    ) -> ExtraFieldIdsResult:
        """Fetch organization extra field ID list.

        Uses GET /v1/org/:orgid/extrafieldids/fetch.

        Args:
            org_id: Organization ID.
            user_token: Optional userToken.
            page: Page offset (default 1).
            page_size: Per-page count (default 1000, max 100000).

        Returns:
            ExtraFieldIdsResult with has_more, total, extra_field_ids.
        """
        if not org_id:
            return ExtraFieldIdsResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .contacts import fetch_org_extra_field_ids

        app_token = await self._get_token()
        return await fetch_org_extra_field_ids(
            self._config,
            app_token=app_token,
            org_id=org_id,
            user_token=user_token,
            page=page,
            page_size=page_size,
            http_client=self._http_client,
        )

    async def fetch_org_info(
        self,
        org_id: str,
        *,
        user_token: str = "",
    ) -> OrgInfoResult:
        """Fetch organization basic information.

        Uses GET /v1/org/:orgid/fetch.

        Args:
            org_id: Organization ID.
            user_token: Optional userToken.

        Returns:
            OrgInfoResult with org_id, org_name, icon_url, org_order_type, etc.
        """
        if not org_id:
            return OrgInfoResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .contacts import fetch_org_info

        app_token = await self._get_token()
        return await fetch_org_info(
            self._config,
            app_token=app_token,
            org_id=org_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def search_staff(
        self,
        keyword: str,
        *,
        user_token: str = "",
        user_id: str = "",
        recursive: bool = True,
        sector_ids: list[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> StaffSearchResult:
        """Search staff by keyword with optional department scope.

        Uses POST /v2/staffs/search. Requires user_token or user_id for auth.

        Args:
            keyword: Search keyword.
            user_token: Optional userToken (one of user_token/user_id required).
            user_id: Optional staff openId (one of user_token/user_id required).
            recursive: Whether to search sub-departments (default True).
            sector_ids: Optional department openId list to limit scope.
            page: Optional page number.
            page_size: Optional page size (max 100).

        Returns:
            StaffSearchResult with has_more, total, staff_info.
        """
        if not keyword:
            return StaffSearchResult(success=False, error="keyword is required")
        self._ensure_clients()
        from .contacts import search_staff

        app_token = await self._get_token()
        return await search_staff(
            self._config,
            app_token=app_token,
            keyword=keyword,
            user_token=user_token,
            user_id=user_id,
            recursive=recursive,
            sector_ids=sector_ids,
            page=page,
            page_size=page_size,
            http_client=self._http_client,
        )

    # ── Public API: Bot channel messages ──────────────────────────────

    async def send_bot_message(
        self,
        msg_type: str,
        msg_data: dict,
        chat_ids: list[str] | None = None,
        department_ids: list[str] | None = None,
        *,
        user_token: str = "",
        entry_id: str = "",
        is_group: bool = False,
        ref_msg_id: str = "",
    ) -> BotMessageResult:
        """Send a message via the bot channel (4.6.12).

        Bot channel does NOT support @mention/reminder.

        When is_group=True, chat_ids are treated as group IDs and sent
        via the group message endpoint instead of the bot endpoint.

        Args:
            msg_type: Message type (all developer-accessible types).
            msg_data: Message body dict.
            chat_ids: Recipient user openId list (or group IDs if is_group=True).
            department_ids: Recipient department openId list (bot channel only).
            user_token: Optional userToken.
            entry_id: Optional app entry selector.
            is_group: True to send to groups via group message endpoint.
            ref_msg_id: Optional reference message openId for reply (prs5.9.0).
        """
        self._ensure_clients()
        if is_group:
            if not chat_ids:
                return BotMessageResult(success=False, error="chat_ids (group IDs) is required when is_group=True")
            if not msg_type:
                return BotMessageResult(success=False, error="msg_type is required")
            if not msg_data:
                return BotMessageResult(success=False, error="msg_data is required")
            results = []
            app_token = await self._get_token()
            from .group_messages import send_group_message
            for gid in chat_ids:
                r = await send_group_message(
                    self._config,
                    app_token=app_token,
                    group_id=gid,
                    msg_type=msg_type,
                    msg_data=msg_data,
                    user_token=user_token,
                    entry_id=entry_id,
                    ref_msg_id=ref_msg_id,
                    http_client=self._http_client,
                )
                results.append(r)
            if not results:
                return BotMessageResult(success=False, error="no group IDs provided")
            first = results[0]
            all_success = all(r.success for r in results)
            return BotMessageResult(
                success=all_success,
                message_id=first.message_id if all_success else "",
                error=first.error if not all_success else "",
                raw_response=first.raw_response if all_success else results,
            )

        if not chat_ids and not department_ids:
            return BotMessageResult(success=False, error="at least one of chat_ids or department_ids is required")
        if not msg_type:
            return BotMessageResult(success=False, error="msg_type is required")
        if not msg_data:
            return BotMessageResult(success=False, error="msg_data is required")
        token = await self._get_token()
        url = build_api_url(self._config, "bot", "message_create", token, user_token=user_token)
        payload: dict[str, Any] = {
            "msgType": msg_type,
            "msgData": msg_data,
        }
        if chat_ids:
            payload["userIdList"] = chat_ids
        if department_ids:
            payload["departmentIdList"] = department_ids
        if entry_id:
            payload["entryId"] = entry_id
        if ref_msg_id:
            payload["refMsgId"] = ref_msg_id
        try:
            response = await self._http_client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return BotMessageResult(success=False, error=f"HTTP error: {e}")
        err_code = data.get("errCode", -1)
        if err_code != 0:
            msg = data.get("errMsg", "Unknown error")
            return BotMessageResult(success=False, error=f"API error (errCode={err_code}): {msg}")
        result_data = data.get("data", {})
        return BotMessageResult(
            success=True,
            message_id=result_data.get("msgId"),
            invalid_staff=result_data.get("invalidStaff"),
            invalid_department=result_data.get("invalidDepartment"),
            raw_response=data,
        )

    # ── Public API: Account message (4.6.1 公号通道) ────────────────

    async def send_account_message(
        self,
        msg_type: str,
        msg_data: dict,
        chat_ids: list[str] | None = None,
        department_ids: list[str] | None = None,
        *,
        account_id: str = "",
        entry_id: str = "",
        attach: str = "",
        user_token: str = "",
    ) -> AccountMessageResult:
        """Send a message via the public account channel (4.6.1).

        Messages appear as if from the application's Public Account (公号).
        The sender identity is determined by accountId or entryId.

        Args:
            msg_type: Message type (all developer-accessible types supported).
            msg_data: Message body dict (msgData field).
            chat_ids: Recipient user openId list.
            department_ids: Recipient department openId list.
            account_id: Public account ID to send as.
            entry_id: App entry ID (selects associated public account).
            attach: Extra data string for blueprint app context.
            user_token: Optional userToken.
        """
        if not chat_ids and not department_ids:
            return AccountMessageResult(success=False, error="at least one of chat_ids or department_ids is required")
        if not msg_type:
            return AccountMessageResult(success=False, error="msg_type is required")
        if not msg_data:
            return AccountMessageResult(success=False, error="msg_data is required")
        self._ensure_clients()
        from .account_messages import send_account_message

        app_token = await self._get_token()
        return await send_account_message(
            self._config,
            app_token=app_token,
            msg_type=msg_type,
            msg_data=msg_data,
            chat_ids=chat_ids,
            department_ids=department_ids,
            account_id=account_id,
            entry_id=entry_id,
            attach=attach,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Public API: User private chat message (4.6.3) ────────────────

    async def send_user_message(
        self,
        receiver_id: str,
        msg_type: str,
        msg_data: dict,
        *,
        user_token: str = "",
        common: dict[str, Any] | None = None,
        uuid: str = "",
    ) -> UserMessageResult:
        """Send a private chat message impersonating a user (4.6.3).

        Messages appear as if from the actual human user whose userToken
        is provided. Creates a 1:1 private chat conversation. userToken
        is REQUIRED — must be obtained via OAuth2 flow.

        Args:
            receiver_id: Single recipient's openId.
            msg_type: Message type (text, formatText, appCard, etc.).
            msg_data: Message body dict.
            user_token: REQUIRED userToken from OAuth2 flow.
            common: Optional "common" sub-object in msgData.
            uuid: Optional deduplication UUID.
        """
        if not user_token:
            return UserMessageResult(success=False, error="user_token is required for user private chat messages")
        if not receiver_id:
            return UserMessageResult(success=False, error="receiver_id is required")
        if not msg_type:
            return UserMessageResult(success=False, error="msg_type is required")
        if not msg_data:
            return UserMessageResult(success=False, error="msg_data is required")
        self._ensure_clients()
        from .user_messages import send_user_message

        app_token = await self._get_token()
        return await send_user_message(
            self._config,
            app_token=app_token,
            user_token=user_token,
            receiver_id=receiver_id,
            msg_type=msg_type,
            msg_data=msg_data,
            common=common,
            uuid=uuid,
            http_client=self._http_client,
        )

    # ── Public API: Group message (4.6.2) ────────────────────────────────

    async def send_group_message(
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
        """Send a message in a group chat (4.6.2).

        Sender identity determined by auth:
        - With user_token: appears from the human user
        - Without user_token, with sender_id: appears from specified person
        - Without both: appears from the bot

        Group chat supports all developer-accessible msgType.
        Only text and formatText support @mentions (reminder). Other msgTypes
        silently ignore reminder parameters.

        If reminder fails for text/formatText, automatically retries without reminder.

        Args:
            group_id: Group openId.
            msg_type: Message type (text, oacard, linkCard, appCard, formatText, appArticles, verifyCard, etc.).
            msg_data: Message body dict.
            user_token: Optional — makes sender appear as human.
            sender_id: Optional — explicit sender openId (used if no user_token).
            reminder_all: @mention all members (only text/formatText).
            reminder_user_ids: @mention specific users (only text/formatText).
            reminder_bot_ids: @mention specific bots (only text/formatText, prs5.7.0).
            outlines: Optional group notification digest text.
            uuid: Optional deduplication key.
            entry_id: Optional app entry selector.
            ref_msg_id: Optional reference message openId for reply (prs5.9.0).
        """
        if not msg_type:
            return SendMessageResult(success=False, error="msg_type is required")
        if not group_id:
            return SendMessageResult(success=False, error="group_id is required")
        if not msg_data:
            return SendMessageResult(success=False, error="msg_data is required")

        reminder: dict[str, Any] | None = None
        if reminder_all or (reminder_user_ids and len(reminder_user_ids) > 0) or (reminder_bot_ids and len(reminder_bot_ids) > 0):
            if msg_type in ("text", "formatText"):
                reminder = {"all": reminder_all, "userIds": reminder_user_ids or [], "botIds": reminder_bot_ids or []}
                if msg_type == "text":
                    text_data = msg_data.get("text", {})
                    text_data["reminder"] = reminder
                    msg_data = {"text": text_data}
                elif msg_type == "formatText":
                    fmt_data = msg_data.get("formatText", {})
                    fmt_data["reminder"] = reminder
                    msg_data = {"formatText": fmt_data}

        self._ensure_clients()
        from .group_messages import send_group_message

        app_token = await self._get_token()
        result = await send_group_message(
            self._config,
            app_token=app_token,
            group_id=group_id,
            msg_type=msg_type,
            msg_data=msg_data,
            user_token=user_token,
            sender_id=sender_id,
            outlines=outlines,
            uuid=uuid,
            entry_id=entry_id,
            ref_msg_id=ref_msg_id,
            http_client=self._http_client,
        )

        if not result.success and reminder and msg_type in ("text", "formatText"):
            logger.info("send_group_message with reminder failed, retrying without reminder")
            if msg_type == "text":
                clean_text = msg_data.get("text", {}).get("content", "")
                clean_msg_data = {"text": {"content": clean_text}}
            else:
                clean_text = msg_data.get("formatText", {}).get("text", "")
                clean_fmt = msg_data.get("formatText", {}).get("formatType", 1)
                clean_msg_data = {"formatText": {"formatType": clean_fmt, "text": clean_text}}
            return await send_group_message(
                self._config,
                app_token=app_token,
                group_id=group_id,
                msg_type=msg_type,
                msg_data=clean_msg_data,
                user_token=user_token,
                sender_id=sender_id,
                outlines=outlines,
                uuid=uuid,
                entry_id=entry_id,
                ref_msg_id=ref_msg_id,
                http_client=self._http_client,
            )

        return result

    # ── Public API: Streaming messages ────────────────────────────────

    async def create_stream_message(
        self,
        receiver_id: str,
        receiver_type: str,
        stream_id: str,
    ) -> StreamMessageResult:
        if not receiver_id:
            return StreamMessageResult(success=False, error="receiver_id is required")
        if receiver_type not in ("staff", "group"):
            return StreamMessageResult(success=False, error="receiver_type must be 'staff' or 'group'")
        if not stream_id:
            return StreamMessageResult(success=False, error="stream_id is required")
        self._ensure_clients()
        from .streaming import create_stream_message

        app_token = await self._get_token()
        return await create_stream_message(
            self._config,
            app_token=app_token,
            receiver_id=receiver_id,
            receiver_type=receiver_type,
            stream_id=stream_id,
            http_client=self._http_client,
        )

    async def fetch_stream_message(
        self,
        msg_id: str,
    ) -> StreamMessageResult:
        if not msg_id:
            return StreamMessageResult(success=False, error="msg_id is required")
        self._ensure_clients()
        from .streaming import fetch_stream_message

        app_token = await self._get_token()
        return await fetch_stream_message(
            self._config,
            app_token=app_token,
            msg_id=msg_id,
            http_client=self._http_client,
        )

    # ── Public API: Groups V2 ─────────────────────────────────────────

    async def create_group(
        self,
        name: str,
        org_id: str,
        *,
        owner_id: str = "",
        description: str = "",
        avatar_id: str = "",
        staff_id_list: list[str] | None = None,
        department_id_list: list[str] | None = None,
        user_token: str = "",
        apply_request_id: str = "",
        apply_notes: str = "",
        apply_global_unique_id: str = "",
        apply_session_unique_id: str = "",
    ) -> CreateGroupResult:
        if not name:
            return CreateGroupResult(success=False, error="name is required")
        if not org_id:
            return CreateGroupResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .groups import create_group

        app_token = await self._get_token()
        return await create_group(
            self._config,
            app_token=app_token,
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
            http_client=self._http_client,
        )

    async def fetch_group_info(
        self,
        group_id: str,
        *,
        user_token: str = "",
    ) -> GroupInfoResult:
        if not group_id:
            return GroupInfoResult(success=False, error="group_id is required")
        self._ensure_clients()
        from .groups import fetch_group_info

        app_token = await self._get_token()
        return await fetch_group_info(
            self._config,
            app_token=app_token,
            group_id=group_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_group_members(
        self,
        group_id: str,
        *,
        user_token: str = "",
        page_offset: int = 0,
        page_size: int = 100,
    ) -> GroupMemberResult:
        if not group_id:
            return GroupMemberResult(success=False, error="group_id is required")
        self._ensure_clients()
        from .groups import fetch_group_members

        app_token = await self._get_token()
        return await fetch_group_members(
            self._config,
            app_token=app_token,
            group_id=group_id,
            user_token=user_token,
            page_offset=page_offset,
            page_size=page_size,
            http_client=self._http_client,
        )

    async def fetch_group_list(
        self,
        *,
        user_token: str = "",
        page_offset: int = 0,
        page_size: int = 100,
    ) -> GroupListResult:
        self._ensure_clients()
        from .groups import fetch_group_list

        app_token = await self._get_token()
        return await fetch_group_list(
            self._config,
            app_token=app_token,
            user_token=user_token,
            page_offset=page_offset,
            page_size=page_size,
            http_client=self._http_client,
        )

    async def check_is_in_group(
        self,
        group_id: str,
        *,
        user_token: str = "",
        staff_id: str = "",
    ) -> IsInGroupResult:
        if not group_id:
            return IsInGroupResult(success=False, error="group_id is required")
        self._ensure_clients()
        from .groups import check_is_in_group

        app_token = await self._get_token()
        return await check_is_in_group(
            self._config,
            app_token=app_token,
            group_id=group_id,
            user_token=user_token,
            staff_id=staff_id,
            http_client=self._http_client,
        )

    async def update_group_info(
        self,
        group_id: str,
        *,
        name: str = "",
        description: str = "",
        avatar_id: str = "",
        owner_id: str = "",
        assistant: list[str] | None = None,
        demote_assistant: list[str] | None = None,
        manage_mode: int | None = None,
        location_share: bool | None = None,
        needs_confirm: bool | None = None,
        is_public: bool | None = None,
        max_members: int | None = None,
        max_history_msg_count: int | None = None,
        remind_all: bool | None = None,
        send_msg_status: bool | None = None,
        user_token: str = "",
    ) -> UpdateGroupResult:
        """Update a group's basic information (4.28.2).

        Only sends keys you provide. App must have robot capability.

        Args:
            group_id: Group openId.
            name: New group name.
            description: New description.
            owner_id: New owner (must be group member).
            manage_mode: 0=all manage, 1=owner only.
            remind_all: @mention enabled/disabled.
            send_msg_status: Group mute enabled/disabled.
            user_token: Optional userToken.
        """
        if not group_id:
            return UpdateGroupResult(success=False, error="group_id is required")
        self._ensure_clients()
        from .groups import update_group_info

        app_token = await self._get_token()
        return await update_group_info(
            self._config,
            app_token=app_token,
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
            http_client=self._http_client,
        )

    async def update_group_members(
        self,
        group_id: str,
        *,
        add_user_list: list[str] | None = None,
        del_user_list: list[str] | None = None,
        add_department_id_list: list[str] | None = None,
        user_token: str = "",
    ) -> UpdateGroupMembersResult:
        """Update group members — add/remove (4.28.5).

        Robot identity cannot add department members.

        Args:
            group_id: Group openId.
            add_user_list: Staff IDs to add.
            del_user_list: Staff IDs to remove.
            add_department_id_list: Dept IDs to add (not with robot identity).
            user_token: Optional userToken.
        """
        if not group_id:
            return UpdateGroupMembersResult(success=False, error="group_id is required")
        if not add_user_list and not del_user_list and not add_department_id_list:
            return UpdateGroupMembersResult(
                success=False, error="at least one of add_user_list, del_user_list, or add_department_id_list is required"
            )
        self._ensure_clients()
        from .groups import update_group_members

        app_token = await self._get_token()
        return await update_group_members(
            self._config,
            app_token=app_token,
            group_id=group_id,
            add_user_list=add_user_list,
            del_user_list=del_user_list,
            add_department_id_list=add_department_id_list,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def dismiss_group(
        self,
        group_id: str,
        *,
        user_token: str = "",
    ) -> UpdateGroupResult:
        """Dismiss/delete a group (4.28.6). Only the group owner can dismiss."""
        if not group_id:
            return UpdateGroupResult(success=False, error="group_id is required")
        self._ensure_clients()
        from .groups import dismiss_group

        app_token = await self._get_token()
        return await dismiss_group(
            self._config,
            app_token=app_token,
            group_id=group_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Public API: Departments ───────────────────────────────────────

    async def fetch_department_detail(
        self,
        department_id: str,
        *,
        user_token: str = "",
        tag_id: str = "",
    ) -> DepartmentDetailResult:
        if not department_id:
            return DepartmentDetailResult(success=False, error="department_id is required")
        self._ensure_clients()
        from .departments import fetch_department_detail

        app_token = await self._get_token()
        return await fetch_department_detail(
            self._config,
            app_token=app_token,
            department_id=department_id,
            user_token=user_token,
            tag_id=tag_id,
            http_client=self._http_client,
        )

    async def fetch_department_children(
        self,
        department_id: str,
        *,
        user_token: str = "",
    ) -> DepartmentChildrenResult:
        if not department_id:
            return DepartmentChildrenResult(success=False, error="department_id is required")
        self._ensure_clients()
        from .departments import fetch_department_children

        app_token = await self._get_token()
        return await fetch_department_children(
            self._config,
            app_token=app_token,
            department_id=department_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_department_staffs(
        self,
        department_id: str,
        *,
        user_token: str = "",
        page: int = 1,
        page_size: int = 100,
    ) -> DepartmentStaffsResult:
        if not department_id:
            return DepartmentStaffsResult(success=False, error="department_id is required")
        self._ensure_clients()
        from .departments import fetch_department_staffs

        app_token = await self._get_token()
        return await fetch_department_staffs(
            self._config,
            app_token=app_token,
            department_id=department_id,
            user_token=user_token,
            page=page,
            page_size=page_size,
            http_client=self._http_client,
        )

    # ── Public API: Unified Todo (4.33) ──────────────────────────────────

    async def create_todo_task(
        self,
        title: str,
        link: str,
        pc_link: str,
        executor_ids: list[str],
        org_id: str,
        type: int = 1,
        *,
        source_id: str = "",
        desc: str = "",
        sender_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Create a unified todo task (4.33.1)."""
        if not title:
            return TodoTaskCreateResult(success=False, error="title is required")
        if not link:
            return TodoTaskCreateResult(success=False, error="link is required")
        if not pc_link:
            return TodoTaskCreateResult(success=False, error="pc_link is required")
        if not executor_ids:
            return TodoTaskCreateResult(success=False, error="executor_ids is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import create_todo_task

        app_token = await self._get_token()
        return await create_todo_task(
            self._config,
            app_token=app_token,
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
            http_client=self._http_client,
        )

    async def update_todo_task(
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
        """Update a todo task's content (4.33.2)."""
        if not todotask_id:
            return TodoTaskCreateResult(success=False, error="todotask_id is required")
        if not title:
            return TodoTaskCreateResult(success=False, error="title is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import update_todo_task

        app_token = await self._get_token()
        return await update_todo_task(
            self._config,
            app_token=app_token,
            todotask_id=todotask_id,
            title=title,
            link=link,
            pc_link=pc_link,
            org_id=org_id,
            desc=desc,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def update_todo_task_status(
        self,
        todotask_id: str,
        status: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Update a todo task's status (4.33.3)."""
        if not todotask_id:
            return TodoTaskCreateResult(success=False, error="todotask_id is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import update_todo_task_status

        app_token = await self._get_token()
        return await update_todo_task_status(
            self._config,
            app_token=app_token,
            todotask_id=todotask_id,
            status=status,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def delete_todo_task(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Delete a todo task (4.33.4 — sender only)."""
        if not todotask_id:
            return TodoTaskCreateResult(success=False, error="todotask_id is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import delete_todo_task

        app_token = await self._get_token()
        return await delete_todo_task(
            self._config,
            app_token=app_token,
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_todo_task_list(
        self,
        org_id: str,
        *,
        app_ids: list[str] | None = None,
        staff_id: str = "",
        status_list: list[str] | None = None,
        user_token: str = "",
    ) -> TodoTaskListResult:
        """Fetch todo task list (4.33.5)."""
        if not org_id:
            return TodoTaskListResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import fetch_todo_task_list

        app_token = await self._get_token()
        return await fetch_todo_task_list(
            self._config,
            app_token=app_token,
            org_id=org_id,
            app_ids=app_ids,
            staff_id=staff_id,
            status_list=status_list,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_todo_task_by_source_id(
        self,
        source_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskInfoResult:
        """Fetch todo task by sourceId (4.33.6)."""
        if not source_id:
            return TodoTaskInfoResult(success=False, error="source_id is required")
        if not org_id:
            return TodoTaskInfoResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import fetch_todo_task_by_source_id

        app_token = await self._get_token()
        return await fetch_todo_task_by_source_id(
            self._config,
            app_token=app_token,
            source_id=source_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_todo_task_by_id(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        user_token: str = "",
    ) -> TodoTaskInfoResult:
        """Fetch todo task by todotaskId (4.33.7)."""
        if not todotask_id:
            return TodoTaskInfoResult(success=False, error="todotask_id is required")
        if not org_id:
            return TodoTaskInfoResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import fetch_todo_task_by_id

        app_token = await self._get_token()
        return await fetch_todo_task_by_id(
            self._config,
            app_token=app_token,
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_todo_task_status_counts(
        self,
        staff_id: str,
        org_id: str,
        *,
        app_id: str = "",
        status_list: list[str] | None = None,
        user_token: str = "",
    ) -> TodoTaskStatusCountResult:
        """Fetch todo task status counts (4.33.9)."""
        if not staff_id:
            return TodoTaskStatusCountResult(success=False, error="staff_id is required")
        if not org_id:
            return TodoTaskStatusCountResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import fetch_todo_task_status_counts

        app_token = await self._get_token()
        return await fetch_todo_task_status_counts(
            self._config,
            app_token=app_token,
            staff_id=staff_id,
            org_id=org_id,
            app_id=app_id,
            status_list=status_list,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def update_executor_status(
        self,
        executor_status_list: list[dict[str, str]],
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Update executor status for a todo task (4.33.10)."""
        if not executor_status_list:
            return TodoTaskCreateResult(success=False, error="executor_status_list is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import update_executor_status

        app_token = await self._get_token()
        return await update_executor_status(
            self._config,
            app_token=app_token,
            executor_status_list=executor_status_list,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def add_executors(
        self,
        executor_ids: list[str],
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Add executors to a todo task (4.33.11)."""
        if not executor_ids:
            return TodoTaskCreateResult(success=False, error="executor_ids is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import add_executors

        app_token = await self._get_token()
        return await add_executors(
            self._config,
            app_token=app_token,
            executor_ids=executor_ids,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def delete_executors(
        self,
        executor_ids: list[str],
        org_id: str,
        *,
        todotask_id: str = "",
        user_token: str = "",
    ) -> TodoTaskCreateResult:
        """Delete executors from a todo task (4.33.12)."""
        if not executor_ids:
            return TodoTaskCreateResult(success=False, error="executor_ids is required")
        if not org_id:
            return TodoTaskCreateResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import delete_executors

        app_token = await self._get_token()
        return await delete_executors(
            self._config,
            app_token=app_token,
            executor_ids=executor_ids,
            org_id=org_id,
            todotask_id=todotask_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_executor_list(
        self,
        todotask_id: str,
        org_id: str,
        *,
        staff_id: str = "",
        status_list: list[str] | None = None,
        user_token: str = "",
    ) -> TodoTaskExecutorListResult:
        """Fetch executor list for a todo task (4.33.13)."""
        if not todotask_id:
            return TodoTaskExecutorListResult(success=False, error="todotask_id is required")
        if not org_id:
            return TodoTaskExecutorListResult(success=False, error="org_id is required")
        self._ensure_clients()
        from .todos import fetch_executor_list

        app_token = await self._get_token()
        return await fetch_executor_list(
            self._config,
            app_token=app_token,
            todotask_id=todotask_id,
            org_id=org_id,
            staff_id=staff_id,
            status_list=status_list,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Public API: Calendar & Schedule (4.23) ──────────────────────────

    async def fetch_primary_calendar(
        self,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> CalendarPrimaryResult:
        """Get the primary calendar (4.23.9)."""
        self._ensure_clients()
        from .calendars import fetch_primary_calendar

        app_token = await self._get_token()
        return await fetch_primary_calendar(
            self._config,
            app_token=app_token,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def create_schedule(
        self,
        calendar_id: str,
        summary: str,
        start_time: dict,
        end_time: dict,
        attendees: list[dict[str, str]],
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
        """Create a schedule/event (4.23.10)."""
        if not calendar_id:
            return ScheduleCreateResult(success=False, error="calendar_id is required")
        if not summary:
            return ScheduleCreateResult(success=False, error="summary is required")
        self._ensure_clients()
        from .calendars import create_schedule

        app_token = await self._get_token()
        return await create_schedule(
            self._config,
            app_token=app_token,
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
            http_client=self._http_client,
        )

    async def fetch_schedule(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleInfoResult:
        """Query a schedule (4.23.11)."""
        if not calendar_id:
            return ScheduleInfoResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleInfoResult(success=False, error="schedule_id is required")
        self._ensure_clients()
        from .calendars import fetch_schedule

        app_token = await self._get_token()
        return await fetch_schedule(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def delete_schedule(
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
        """Delete a schedule (4.23.13)."""
        if not calendar_id:
            return ScheduleCreateResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleCreateResult(success=False, error="schedule_id is required")
        self._ensure_clients()
        from .calendars import delete_schedule

        app_token = await self._get_token()
        return await delete_schedule(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            reminder_type=reminder_type,
            operation_type=operation_type,
            current_time=current_time,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def fetch_schedule_list(
        self,
        calendar_id: str,
        start_time: int | None = None,
        end_time: int | None = None,
        *,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleListResult:
        """Get schedule list in a time range (4.23.14)."""
        if not calendar_id:
            return ScheduleListResult(success=False, error="calendar_id is required")
        if start_time is None or end_time is None:
            return ScheduleListResult(success=False, error="start_time and end_time are required")
        self._ensure_clients()
        from .calendars import fetch_schedule_list

        app_token = await self._get_token()
        return await fetch_schedule_list(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            start_time=start_time,
            end_time=end_time,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def fetch_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        page: int = 1,
        page_size: int = 500,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleAttendeesResult:
        """Get schedule attendee list (4.23.15)."""
        if not calendar_id:
            return ScheduleAttendeesResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleAttendeesResult(success=False, error="schedule_id is required")
        self._ensure_clients()
        from .calendars import fetch_schedule_attendees

        app_token = await self._get_token()
        return await fetch_schedule_attendees(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            page=page,
            page_size=page_size,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def add_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        attendees: list[str],
        *,
        reminder_type: str = "yes",
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Add attendees to a schedule (4.23.16)."""
        if not calendar_id:
            return ScheduleCreateResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleCreateResult(success=False, error="schedule_id is required")
        if not attendees:
            return ScheduleCreateResult(success=False, error="attendees is required")
        self._ensure_clients()
        from .calendars import add_schedule_attendees

        app_token = await self._get_token()
        return await add_schedule_attendees(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            attendees=attendees,
            reminder_type=reminder_type,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def delete_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        attendees: list[str],
        *,
        reminder_type: str = "no",
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleCreateResult:
        """Delete attendees from a schedule (4.23.18)."""
        if not calendar_id:
            return ScheduleCreateResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleCreateResult(success=False, error="schedule_id is required")
        if not attendees:
            return ScheduleCreateResult(success=False, error="attendees is required")
        self._ensure_clients()
        from .calendars import delete_schedule_attendees

        app_token = await self._get_token()
        return await delete_schedule_attendees(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            attendees=attendees,
            reminder_type=reminder_type,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def update_schedule(
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
        """Update a schedule (4.23.12)."""
        if not calendar_id:
            return ScheduleUpdateResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleUpdateResult(success=False, error="schedule_id is required")
        self._ensure_clients()
        from .calendars import update_schedule

        app_token = await self._get_token()
        return await update_schedule(
            self._config,
            app_token=app_token,
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
            http_client=self._http_client,
        )

    async def update_schedule_attendee_meta(
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
        """Update schedule attendee metadata (4.23.17)."""
        if not calendar_id:
            return ScheduleAttendeeMetaResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleAttendeeMetaResult(success=False, error="schedule_id is required")
        self._ensure_clients()
        from .calendars import update_schedule_attendee_meta

        app_token = await self._get_token()
        return await update_schedule_attendee_meta(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            rsvp_status=rsvp_status,
            color=color,
            permissions=permissions,
            busy_free_state=busy_free_state,
            remind_times=remind_times,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def update_schedule_attendees(
        self,
        calendar_id: str,
        schedule_id: str,
        *,
        add_attendees: list[str] | None = None,
        delete_attendees: list[str] | None = None,
        reminder_type: str | None = None,
        operation_type: str | None = None,
        current_time: int | None = None,
        user_token: str = "",
        user_id: str = "",
    ) -> ScheduleAttendeesUpdateResult:
        """Batch add and/or delete schedule attendees (4.23.19)."""
        if not calendar_id:
            return ScheduleAttendeesUpdateResult(success=False, error="calendar_id is required")
        if not schedule_id:
            return ScheduleAttendeesUpdateResult(success=False, error="schedule_id is required")
        if not add_attendees and not delete_attendees:
            return ScheduleAttendeesUpdateResult(success=False, error="at least one of add_attendees or delete_attendees is required")
        self._ensure_clients()
        from .calendars import update_schedule_attendees

        app_token = await self._get_token()
        return await update_schedule_attendees(
            self._config,
            app_token=app_token,
            calendar_id=calendar_id,
            schedule_id=schedule_id,
            add_attendees=add_attendees,
            delete_attendees=delete_attendees,
            reminder_type=reminder_type,
            operation_type=operation_type,
            current_time=current_time,
            user_token=user_token,
            user_id=user_id,
            http_client=self._http_client,
        )

    async def send_reminder(
        self,
        msg_id: str,
        reminder_types: list[int],
        user_id_list: list[str],
    ) -> SendMessageResult:
        """Send an urgent reminder for a previously sent message (4.6.14).

        Args:
            msg_id: The message ID to remind about.
            reminder_types: List of reminder type ints (1=popup, 2=SMS, 3=phone).
            user_id_list: List of staff openIds to remind (max 100).
        """
        if not msg_id:
            return SendMessageResult(success=False, error="msg_id is required")
        if not reminder_types:
            return SendMessageResult(success=False, error="reminder_types is required")
        if not user_id_list:
            return SendMessageResult(success=False, error="user_id_list is required")
        self._ensure_clients()
        from .reminders import send_reminder

        app_token = await self._get_token()
        return await send_reminder(
            self._config,
            app_token=app_token,
            msg_id=msg_id,
            reminder_types=reminder_types,
            user_id_list=user_id_list,
            http_client=self._http_client,
        )

    async def fetch_media_path(
        self,
        media_id: str,
        *,
        user_token: str = "",
    ) -> MediaPathResult:
        """Get the download URL path for a media file (4.5.3).

        Args:
            media_id: Lansenger media ID.
            user_token: Optional userToken.
        """
        if not media_id:
            return MediaPathResult(success=False, error="media_id is required")
        self._ensure_clients()
        from .media import fetch_media_path

        app_token = await self._get_token()
        return await fetch_media_path(
            self._config,
            app_token=app_token,
            media_id=media_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Bot Commands (4.37) ────────────────────────────────────────────

    async def create_bot_commands(
        self,
        scope_type: int,
        commands: list[dict[str, Any]],
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandResult:
        """Create bot slash commands (4.37.1)."""
        self._ensure_clients()
        from .bot_commands import create_bot_commands

        app_token = await self._get_token()
        return await create_bot_commands(
            self._config,
            app_token=app_token,
            scope_type=scope_type,
            commands=commands,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
            http_client=self._http_client,
        )

    async def fetch_bot_commands(
        self,
        scope_type: int,
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandQueryResult:
        """Query bot slash commands (4.37.2)."""
        self._ensure_clients()
        from .bot_commands import fetch_bot_commands

        app_token = await self._get_token()
        return await fetch_bot_commands(
            self._config,
            app_token=app_token,
            scope_type=scope_type,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
            http_client=self._http_client,
        )

    async def delete_bot_commands(
        self,
        scope_type: int,
        *,
        chat_id: str = "",
        chat_type: str = "",
        staff_id: str = "",
    ) -> BotCommandResult:
        """Delete bot slash commands (4.37.3)."""
        self._ensure_clients()
        from .bot_commands import delete_bot_commands

        app_token = await self._get_token()
        return await delete_bot_commands(
            self._config,
            app_token=app_token,
            scope_type=scope_type,
            chat_id=chat_id,
            chat_type=chat_type,
            staff_id=staff_id,
            http_client=self._http_client,
        )

    # ── Personal Apps (4.38) ───────────────────────────────────────────

    async def create_personal_app(
        self,
        *,
        user_token: str,
        name: str = "",
        avatar_id: str = "",
        description: str = "",
    ) -> PersonalAppCreateResult:
        """Create a personal app/bot (4.38.1)."""
        self._ensure_clients()
        from .personal_apps import create_personal_app

        app_token = await self._get_token()
        return await create_personal_app(
            self._config,
            app_token=app_token,
            user_token=user_token,
            name=name,
            avatar_id=avatar_id,
            description=description,
            http_client=self._http_client,
        )

    async def update_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
        name: str,
        avatar_id: str = "",
        description: str = "",
    ) -> PersonalAppInfoResult:
        """Update a personal app/bot (4.38.2)."""
        self._ensure_clients()
        from .personal_apps import update_personal_app

        app_token = await self._get_token()
        return await update_personal_app(
            self._config,
            app_token=app_token,
            app_id=app_id,
            user_token=user_token,
            name=name,
            avatar_id=avatar_id,
            description=description,
            http_client=self._http_client,
        )

    async def fetch_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
    ) -> PersonalAppInfoResult:
        """Fetch personal app info (4.38.3)."""
        self._ensure_clients()
        from .personal_apps import fetch_personal_app

        app_token = await self._get_token()
        return await fetch_personal_app(
            self._config,
            app_token=app_token,
            app_id=app_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def delete_personal_app(
        self,
        app_id: str,
        *,
        user_token: str,
    ) -> PersonalAppInfoResult:
        """Delete a personal app/bot (4.38.4)."""
        self._ensure_clients()
        from .personal_apps import delete_personal_app

        app_token = await self._get_token()
        return await delete_personal_app(
            self._config,
            app_token=app_token,
            app_id=app_id,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_personal_app_list(
        self,
        *,
        user_token: str,
    ) -> PersonalAppListResult:
        """Fetch personal app list (4.38.5)."""
        self._ensure_clients()
        from .personal_apps import fetch_personal_app_list

        app_token = await self._get_token()
        return await fetch_personal_app_list(
            self._config,
            app_token=app_token,
            user_token=user_token,
            http_client=self._http_client,
        )

    # ── Utility: Callback event parsing ───────────────────────────────

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
        """Parse callback payload using encoding_key/callback_token from this client's config.

        If a CredentialStore is attached and the config fields are empty,
        values are read from the store file automatically.
        """
        from .callbacks import parse_callback_payload

        encoding_key = self._config.encoding_key
        callback_token = self._config.callback_token
        if self._store and not encoding_key:
            creds = self._store.load_credentials()
            encoding_key = creds.get("encoding_key", "")
            if not callback_token:
                callback_token = creds.get("callback_token", "")

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
        """Verify callback signature using encoding_key/callback_token from this client's config.

        If a CredentialStore is attached and the config fields are empty,
        values are read from the store file automatically.
        """
        from .callbacks import verify_callback_signature

        encoding_key = self._config.encoding_key
        callback_token = self._config.callback_token
        if self._store and not encoding_key:
            creds = self._store.load_credentials()
            encoding_key = creds.get("encoding_key", "")
            if not callback_token:
                callback_token = creds.get("callback_token", "")

        return verify_callback_signature(
            timestamp, nonce, signature, encoding_key,
            data_encrypt=data_encrypt,
            callback_token=callback_token,
        )

    @staticmethod
    def get_callback_event_types() -> dict:
        from .callbacks import CALLBACK_EVENT_TYPES

        return CALLBACK_EVENT_TYPES

    # ── Public API: Chat list & messages (4.24 MCP) ──────────────────

    async def fetch_chat_list(
        self,
        *,
        chat_type: int = 0,
        keyword: str = "",
        start_time: int = 0,
        end_time: int = 0,
        user_token: str = "",
    ) -> ChatListResult:
        """Fetch personal chat list (private + group conversations).

        Args:
            chat_type: 0=all, 1=private, 2=group (default 0).
            keyword: Search keyword (only works when chat_type is 1 or 2).
            start_time: Filter start time in microseconds.
            end_time: Filter end time in microseconds.
            user_token: Optional userToken for human identity.

        Returns:
            ChatListResult with staff_infos and group_infos.
        """
        self._ensure_clients()
        from .chats import fetch_chat_list

        app_token = await self._get_token()
        return await fetch_chat_list(
            self._config,
            app_token=app_token,
            chat_type=chat_type,
            keyword=keyword,
            start_time=start_time,
            end_time=end_time,
            user_token=user_token,
            http_client=self._http_client,
        )

    async def fetch_chat_messages(
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
        """Fetch messages from a specific conversation.

        staff_id and group_id are mutually exclusive (pick one).

        Args:
            staff_id: Private chat partner's staffId.
            group_id: Group openId.
            page_size: Per-page count (max 100, default 100).
            base_version: Deep pagination cursor. First call: "0".
            start_time: Filter start time in microseconds.
            end_time: Filter end time in microseconds.
            sender_id: Filter by sender staffId.
            user_token: Optional userToken for human identity.

        Returns:
            ChatMessagesResult with messages list.
        """
        if not staff_id and not group_id:
            return ChatMessagesResult(
                success=False, error="staff_id or group_id is required"
            )
        self._ensure_clients()
        from .chats import fetch_chat_messages

        app_token = await self._get_token()
        return await fetch_chat_messages(
            self._config,
            app_token=app_token,
            staff_id=staff_id,
            group_id=group_id,
            page_size=page_size,
            base_version=base_version,
            start_time=start_time,
            end_time=end_time,
            sender_id=sender_id,
            user_token=user_token,
            http_client=self._http_client,
        )
