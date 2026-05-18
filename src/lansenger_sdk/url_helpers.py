"""Shared URL-building helpers for Lansenger API modules."""

from __future__ import annotations

from urllib.parse import quote

from .config import LansengerConfig
from .constants import API_ENDPOINTS


def build_api_url(
    config: LansengerConfig,
    category: str,
    endpoint: str,
    app_token: str,
    *,
    user_token: str = "",
    user_id: str = "",
    **path_vars: str,
) -> str:
    """Build a full API URL from API_ENDPOINTS + config + tokens.

    Args:
        config: LansengerConfig with api_gateway_url.
        category: Top-level key in API_ENDPOINTS (e.g. "calendars").
        endpoint: Second-level key (e.g. "primary").
        app_token: Bot's appToken.
        user_token: Optional userToken query param.
        user_id: Optional userId query param.
        **path_vars: Values to substitute for {calendar_id}, {schedule_id},
            {media_id}, etc. in endpoint path templates.
            Values are URL-quoted automatically.

    Returns:
        Fully formed URL ready for an HTTP request.
    """
    path_template = API_ENDPOINTS[category][endpoint]
    path = path_template
    for var_name, var_value in path_vars.items():
        path = path.replace(f"{{{var_name}}}", quote(var_value, safe=""))

    url = f"{config.api_gateway_url}{path}?app_token={app_token}"
    if user_token:
        url += f"&user_token={user_token}"
    if user_id:
        url += f"&user_id={quote(user_id)}"
    return url