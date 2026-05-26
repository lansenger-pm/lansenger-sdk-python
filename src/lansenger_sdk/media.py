"""Lansenger SDK media operations — upload and download files.

Two upload endpoints exist:
- 4.5.1 upload_media: Core service upload (/v1/medias/create), numeric type, 1MB limit, optional userToken
- 4.5.4 upload_app_media: App/bot upload (/v1/app/medias/create), string type, 10/20MB limit, no userToken
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

import httpx

from .auth import TokenManager
from .config import LansengerConfig
from .constants import (
    MEDIA_TYPE_FILE,
    MEDIA_TYPE_IMAGE,
    MEDIA_TYPE_VIDEO,
    APP_MEDIA_TYPE_FILE,
    APP_MEDIA_TYPE_VIDEO,
    APP_MEDIA_TYPE_IMAGE,
    APP_MEDIA_TYPE_AUDIO,
    guess_media_type,
    guess_app_media_type,
)
from .exceptions import LansengerFileError, LansengerNetworkError
from .models import DownloadMediaResult, MediaPathResult, UploadMediaResult
from .url_helpers import build_api_url

logger = logging.getLogger("lansenger_sdk.media")


async def upload_media(
    config: LansengerConfig,
    token_manager: TokenManager,
    http_client: httpx.AsyncClient,
    file_path: str,
    media_type: int = MEDIA_TYPE_FILE,
    user_token: str = "",
) -> UploadMediaResult:
    """Upload a media file via core service endpoint (4.5.1).

    Uses /v1/medias/create with numeric type values (1=video, 2=image, 3=file).
    File size limit: 1MB. Optionally accepts userToken.

    Args:
        config: SDK config
        token_manager: Token manager for authentication
        http_client: HTTP client
        file_path: Path to the local file
        media_type: 1=video, 2=image, 3=file (default: 3)
        user_token: Optional userToken (4.5.1 accepts this)

    Returns:
        UploadMediaResult with media_id and created_time on success
    """
    if not os.path.isfile(file_path):
        return UploadMediaResult(success=False, error=f"File not found: {file_path}")

    try:
        token = await token_manager.get_token()
    except Exception as e:
        return UploadMediaResult(success=False, error=f"Auth failed: {e}")

    url = build_api_url(config, "media", "create", token, user_token=user_token) + f"&type={media_type}"

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = {"media": (filename, file_content)}

        response = await http_client.post(url, files=files)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return UploadMediaResult(success=False, error=f"Upload HTTP error: {e}")
    except OSError as e:
        return UploadMediaResult(success=False, error=f"File read error: {e}")

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown upload error")
        return UploadMediaResult(success=False, error=f"Upload API error (errCode={err_code}): {msg}")

    d = data.get("data", {})
    media_id = d.get("mediaId")
    if not media_id:
        return UploadMediaResult(success=False, error="Upload response missing mediaId")

    logger.debug("Media uploaded (4.5.1): %s → %s", filename, media_id)
    return UploadMediaResult(
        success=True,
        media_id=media_id,
        created_time=d.get("createdTime"),
    )


async def upload_app_media(
    config: LansengerConfig,
    token_manager: TokenManager,
    http_client: httpx.AsyncClient,
    file_path: str,
    media_type: str = APP_MEDIA_TYPE_FILE,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    duration: Optional[int] = None,
) -> UploadMediaResult:
    """Upload a media file via app/bot endpoint (4.5.4).

    Uses /v1/app/medias/create with string type values ("file", "video", "image", "audio").
    File size limits: image 10MB, others 20MB. No userToken parameter.
    Supports width/height (for video, image) and duration (for video, audio).
    Only self-built apps (not ISV apps).

    Args:
        config: SDK config
        token_manager: Token manager for authentication
        http_client: HTTP client
        file_path: Path to the local file
        media_type: "file", "video", "image", or "audio" (default: "file")
        width: Optional width (for video/image)
        height: Optional height (for video/image)
        duration: Optional duration in seconds (for video/audio)

    Returns:
        UploadMediaResult with media_id on success
    """
    if not os.path.isfile(file_path):
        return UploadMediaResult(success=False, error=f"File not found: {file_path}")

    try:
        token = await token_manager.get_token()
    except Exception as e:
        return UploadMediaResult(success=False, error=f"Auth failed: {e}")

    url = build_api_url(config, "media", "app_create", token) + f"&type={media_type}"
    if width is not None:
        url += f"&width={width}"
    if height is not None:
        url += f"&height={height}"
    if duration is not None:
        url += f"&duration={duration}"

    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = {"media": (filename, file_content)}

        response = await http_client.post(url, files=files)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return UploadMediaResult(success=False, error=f"Upload HTTP error: {e}")
    except OSError as e:
        return UploadMediaResult(success=False, error=f"File read error: {e}")

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown upload error")
        return UploadMediaResult(success=False, error=f"Upload API error (errCode={err_code}): {msg}")

    d = data.get("data", {})
    media_id = d.get("mediaId")
    if not media_id:
        return UploadMediaResult(success=False, error="Upload response missing mediaId")

    logger.debug("App media uploaded (4.5.4): %s → %s", filename, media_id)
    return UploadMediaResult(success=True, media_id=media_id)


async def download_media(
    config: LansengerConfig,
    token_manager: TokenManager,
    http_client: httpx.AsyncClient,
    media_id: str,
) -> DownloadMediaResult:
    """Download a media file from Lansenger by media ID.

    Args:
        config: SDK config
        token_manager: Token manager for authentication
        http_client: HTTP client
        media_id: Lansenger media ID

    Returns:
        DownloadMediaResult with raw bytes on success
    """
    try:
        token = await token_manager.get_token()
    except Exception as e:
        return DownloadMediaResult(success=False, error=f"Auth failed: {e}")

    url = build_api_url(config, "media", "fetch", token, media_id=media_id)

    try:
        response = await http_client.get(url)
        response.raise_for_status()
        return DownloadMediaResult(success=True, data=response.content)
    except httpx.HTTPError as e:
        return DownloadMediaResult(success=False, error=f"Download HTTP error: {e}")


async def download_media_to_file(
    config: LansengerConfig,
    token_manager: TokenManager,
    http_client: httpx.AsyncClient,
    media_id: str,
    target_path: Optional[str] = None,
    media_type: str = "file",
) -> str:
    """Download a media file and save it to a temp/local file.

    Args:
        config: SDK config
        token_manager: Token manager
        http_client: HTTP client
        media_id: Lansenger media ID
        target_path: Optional target file path. If None, creates a temp file.
        media_type: "image", "video", "file", or "voice" — used for temp file extension.

    Returns:
        Path to the saved file.

    Raises:
        LansengerFileError if download or save fails.
    """
    result = await download_media(config, token_manager, http_client, media_id)
    if not result.success or result.data is None:
        raise LansengerFileError(f"Download failed: {result.error}")

    ext_map = {"image": ".jpg", "video": ".mp4", "file": ".dat", "voice": ".amr"}
    ext = ext_map.get(media_type, ".dat")

    media_bytes = result.data
    if media_type == "image" and len(media_bytes) >= 8:
        if media_bytes[:2] == b'\xff\xd8':
            ext = ".jpg"
        elif media_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            ext = ".png"
        elif media_bytes[:6] in (b'GIF87a', b'GIF89a'):
            ext = ".gif"

    if target_path is None:
        fd, target_path = tempfile.mkstemp(suffix=ext, prefix=f"lansenger_{media_type}_")
        os.close(fd)

    try:
        with open(target_path, "wb") as f:
            f.write(media_bytes)
        logger.debug("Media saved to %s (%d bytes)", target_path, len(media_bytes))
        return target_path
    except OSError as e:
        raise LansengerFileError(f"Save failed: {e}") from e


async def fetch_media_path(
    config: LansengerConfig,
    app_token: str,
    media_id: str,
    *,
    user_token: str = "",
    http_client: Optional[httpx.AsyncClient] = None,
) -> MediaPathResult:
    """Get the download URL path for a media file (4.5.3).

    Args:
        config: LansengerConfig.
        app_token: Bot's appToken.
        media_id: Lansenger media ID.
        user_token: Optional userToken.
        http_client: Optional httpx client.
    """
    if not media_id:
        return MediaPathResult(success=False, error="media_id is required")

    url = build_api_url(config, "media", "path_fetch", app_token, user_token=user_token, media_id=media_id)

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        if owns_client:
            await http_client.aclose()
        return MediaPathResult(success=False, error=f"HTTP error: {e}")
    except Exception as e:
        if owns_client:
            await http_client.aclose()
        return MediaPathResult(success=False, error=f"Request error: {e}")
    finally:
        if owns_client:
            await http_client.aclose()

    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return MediaPathResult(success=False, error=f"API error (errCode={err_code}): {msg}")

    d = data.get("data", {})
    return MediaPathResult(
        success=True,
        media_path=d.get("mediaPath"),
        name=d.get("name"),
        type=d.get("type"),
        size=d.get("size"),
        raw_response=data,
    )