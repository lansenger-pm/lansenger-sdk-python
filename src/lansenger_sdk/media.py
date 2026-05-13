"""Lansenger SDK media operations — upload and download files."""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional

import httpx

from .auth import TokenManager
from .config import LansengerConfig
from .constants import API_ENDPOINTS, MEDIA_TYPE_FILE, MEDIA_TYPE_IMAGE, MEDIA_TYPE_VIDEO, guess_media_type
from .exceptions import LansengerFileError, LansengerNetworkError
from .models import DownloadMediaResult, UploadMediaResult

logger = logging.getLogger("lansenger_sdk.media")


async def upload_media(
    config: LansengerConfig,
    token_manager: TokenManager,
    http_client: httpx.AsyncClient,
    file_path: str,
    media_type: int = MEDIA_TYPE_FILE,
) -> UploadMediaResult:
    """Upload a media file to Lansenger and return mediaId.

    Args:
        config: SDK config
        token_manager: Token manager for authentication
        http_client: HTTP client
        file_path: Path to the local file
        media_type: 1=video, 2=image, 3=file (default: 3)

    Returns:
        UploadMediaResult with media_id on success
    """
    if not os.path.isfile(file_path):
        return UploadMediaResult(success=False, error=f"File not found: {file_path}")

    try:
        token = await token_manager.get_token()
    except Exception as e:
        return UploadMediaResult(success=False, error=f"Auth failed: {e}")

    url = f"{config.api_gateway_url}/v1/medias/create?type={media_type}&app_token={token}"

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

    media_id = data.get("data", {}).get("mediaId")
    if not media_id:
        return UploadMediaResult(success=False, error="Upload response missing mediaId")

    logger.debug("Media uploaded: %s → %s", filename, media_id)
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

    url = f"{config.api_gateway_url}/v1/medias/{media_id}/fetch"
    params = {"app_token": token}

    try:
        response = await http_client.get(url, params=params)
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