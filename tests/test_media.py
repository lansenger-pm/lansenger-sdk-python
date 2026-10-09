"""Tests for Lansenger SDK media APIs — V2 upload (4.5.5) and share download (4.5.6)."""

import os

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from lansenger_sdk.config import LansengerConfig
from lansenger_sdk.exceptions import LansengerFileError
from lansenger_sdk.media import (
    download_media_to_file,
    download_media_to_file_result,
    upload_app_media_v2,
    download_media_by_share_id,
)


def _make_config():
    return LansengerConfig(
        app_id="test_app",
        app_secret="test_secret",
        api_gateway_url="https://test-gateway.example.com",
    )


def _make_token_manager():
    tm = MagicMock()
    tm.get_token = AsyncMock(return_value="test_app_token")
    return tm


def _make_upload_client(payload):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=payload)
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


def _make_download_client(
    *,
    status_code=200,
    content=b"file-bytes",
    content_type="application/octet-stream",
    json_data=None,
):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"content-type": content_type}
    mock_response.content = content
    if json_data is not None:
        mock_response.json = MagicMock(return_value=json_data)
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client


# ---------- upload_app_media_v2 (4.5.5) ----------


@pytest.mark.asyncio
async def test_upload_app_media_v2_success(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_bytes(b"hello world")
    config = _make_config()
    tm = _make_token_manager()
    client = _make_upload_client({"errCode": 0, "data": {"mediaId": "mid123"}})

    result = await upload_app_media_v2(config, tm, client, str(f), user_token="ut_1")

    assert result.success is True
    assert result.media_id == "mid123"


@pytest.mark.asyncio
async def test_upload_app_media_v2_file_not_found():
    config = _make_config()
    tm = _make_token_manager()
    client = AsyncMock()

    result = await upload_app_media_v2(
        config, tm, client, "/nonexistent/path/missing.bin", user_token="ut_1",
    )

    assert result.success is False
    assert "File not found" in result.error
    tm.get_token.assert_not_called()
    client.post.assert_not_called()


@pytest.mark.asyncio
async def test_upload_app_media_v2_api_error(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"data")
    config = _make_config()
    tm = _make_token_manager()
    client = _make_upload_client({"errCode": 40010, "errMsg": "invalid media type"})

    result = await upload_app_media_v2(config, tm, client, str(f), user_token="ut_1")

    assert result.success is False
    assert "errCode=40010" in result.error
    assert "invalid media type" in result.error


@pytest.mark.asyncio
async def test_upload_app_media_v2_user_token_in_url(tmp_path):
    f = tmp_path / "img.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")
    config = _make_config()
    tm = _make_token_manager()
    client = _make_upload_client({"errCode": 0, "data": {"mediaId": "mid9"}})

    result = await upload_app_media_v2(
        config, tm, client, str(f), media_type="image", user_token="ut_abc",
    )

    assert result.success is True
    url = client.post.call_args.args[0]
    assert "/v2/app/medias/create" in url
    assert "app_token=test_app_token" in url
    assert "user_token=ut_abc" in url
    assert "type=image" in url


@pytest.mark.asyncio
async def test_upload_app_media_v2_build_api_url_args(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4")
    config = _make_config()
    tm = _make_token_manager()
    client = _make_upload_client({"errCode": 0, "data": {"mediaId": "mid7"}})

    with patch("lansenger_sdk.media.build_api_url", return_value="https://gw/mock") as mock_build:
        result = await upload_app_media_v2(config, tm, client, str(f), user_token="ut_xyz")

    assert result.success is True
    mock_build.assert_called_once_with(
        config, "media", "app_create_v2", "test_app_token", user_token="ut_xyz",
    )


# ---------- download_media_by_share_id (4.5.6) ----------


@pytest.mark.asyncio
async def test_download_media_by_share_id_success():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(content=b"\x00\x01binary-data")

    result = await download_media_by_share_id(config, tm, client, "share_1")

    assert result.success is True
    assert result.data == b"\x00\x01binary-data"


@pytest.mark.asyncio
async def test_download_media_by_share_id_json_error():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(
        content_type="application/json",
        json_data={"errCode": 64001, "errMsg": "share not found"},
    )

    result = await download_media_by_share_id(config, tm, client, "share_bad")

    assert result.success is False
    assert "errCode=64001" in result.error
    assert "share not found" in result.error


@pytest.mark.asyncio
async def test_download_media_by_share_id_non_200():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(
        status_code=404, content_type="text/html", content=b"<html>not found</html>",
    )

    result = await download_media_by_share_id(config, tm, client, "share_404")

    assert result.success is False
    assert "404" in result.error


@pytest.mark.asyncio
async def test_download_media_by_share_id_user_token_in_url():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client()

    result = await download_media_by_share_id(config, tm, client, "shareX123", user_token="ut_dl")

    assert result.success is True
    url = client.get.call_args.args[0]
    assert "/v1/media/share/shareX123/fetch" in url
    assert "app_token=test_app_token" in url
    assert "user_token=ut_dl" in url


@pytest.mark.asyncio
async def test_download_media_by_share_id_build_api_url_args():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client()

    with patch("lansenger_sdk.media.build_api_url", return_value="https://gw/mock") as mock_build:
        result = await download_media_by_share_id(config, tm, client, "sid1", user_token="ut_z")

    assert result.success is True
    mock_build.assert_called_once_with(
        config, "media", "share_fetch", "test_app_token", user_token="ut_z", share_id="sid1",
    )


# ---------- download_media_to_file / download_media_to_file_result (4.5.2) ----------


@pytest.mark.asyncio
async def test_download_media_to_file_result_success(tmp_path):
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(content=b"hello-bytes")
    target = tmp_path / "out.dat"

    result = await download_media_to_file_result(
        config, tm, client, "media_1", str(target)
    )

    assert result.success is True
    assert result.path == str(target)
    assert result.size == len(b"hello-bytes")
    assert target.read_bytes() == b"hello-bytes"
    assert result.error is None
    assert result.to_dict() == {"success": True, "path": str(target), "size": 11}


@pytest.mark.asyncio
async def test_download_media_to_file_result_api_error_is_not_raised():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(
        content_type="application/json",
        content=b'{"errCode": 50000, "errMsg": "OPEN ID invalid"}',
    )

    result = await download_media_to_file_result(config, tm, client, "media_bad")

    assert result.success is False
    assert result.path is None
    assert "errCode=50000" in result.error
    assert "OPEN ID invalid" in result.error


@pytest.mark.asyncio
async def test_download_media_to_file_result_save_failure_reports_error():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(content=b"payload")

    result = await download_media_to_file_result(
        config, tm, client, "media_1", "/nonexistent-dir-xyz/out.dat"
    )

    assert result.success is False
    assert "Save failed" in result.error
    assert result.size == 0


@pytest.mark.asyncio
async def test_download_media_to_file_result_temp_path_uses_media_type():
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(content=b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)

    result = await download_media_to_file_result(
        config, tm, client, "media_img", media_type="image"
    )

    try:
        assert result.success is True
        assert result.path.endswith(".png")
        assert os.path.getsize(result.path) == 16
    finally:
        if result.path:
            os.unlink(result.path)


@pytest.mark.asyncio
async def test_download_media_to_file_keeps_raising_contract(tmp_path):
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(
        content_type="application/json",
        content=b'{"errCode": 50000, "errMsg": "OPEN ID invalid"}',
    )

    with pytest.raises(LansengerFileError) as exc:
        await download_media_to_file(
            config, tm, client, "media_bad", str(tmp_path / "never.dat")
        )

    assert "Download failed" in str(exc.value)
    assert not (tmp_path / "never.dat").exists()


@pytest.mark.asyncio
async def test_download_media_to_file_success_still_returns_path(tmp_path):
    config = _make_config()
    tm = _make_token_manager()
    client = _make_download_client(content=b"abc")
    target = tmp_path / "ok.dat"

    path = await download_media_to_file(config, tm, client, "media_1", str(target))

    assert path == str(target)
    assert target.read_bytes() == b"abc"
