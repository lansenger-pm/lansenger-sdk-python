"""Shared API utilities for Lansenger SDK modules.

This module contains common functions used across multiple API modules
to avoid code duplication and ensure consistent behavior.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import httpx

from .config import LansengerConfig

logger = logging.getLogger("lansenger_sdk.api_utils")


def parse_api_response(data: dict) -> tuple[bool, Optional[str]]:
    """Parse API response and check for errors.

    Args:
        data: Raw response data from the API.

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    err_code = data.get("errCode", -1)
    if err_code != 0:
        msg = data.get("errMsg", "Unknown error")
        return False, f"API error (errCode={err_code}): {msg}"
    return True, None


async def do_get(
    config: LansengerConfig,
    url: str,
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """Execute a GET request to the Lansenger API.

    Args:
        config: LansengerConfig with timeout settings.
        url: Full URL to call.
        http_client: Optional httpx client. If None, creates ephemeral client.

    Returns:
        Tuple of (response_data: Optional[dict], error_message: Optional[str])
    """
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        return None, f"HTTP error: {e}"
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"JSON decode error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None


async def do_post(
    config: LansengerConfig,
    url: str,
    body: Dict[str, Any],
    http_client: Optional[httpx.AsyncClient] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """Execute a POST request to the Lansenger API.

    Args:
        config: LansengerConfig with timeout settings.
        url: Full URL to call.
        body: JSON body to send.
        http_client: Optional httpx client. If None, creates ephemeral client.

    Returns:
        Tuple of (response_data: Optional[dict], error_message: Optional[str])
    """
    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=config.http_timeout)
    try:
        logger.debug("POST %s", url)
        response = await http_client.post(url, json=body)
        response.raise_for_status()
        data = response.json()
        logger.debug("POST %s → 200 OK", url)
    except httpx.HTTPError as e:
        logger.debug("POST %s → HTTP error: %s", url, e)
        return None, f"HTTP error: {e}"
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"JSON decode error: {e}"
    finally:
        if owns_client:
            await http_client.aclose()
    return data, None