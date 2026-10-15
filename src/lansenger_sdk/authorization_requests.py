"""4.6.4.14 authorizationReq message body (授权请求消息) builders.

Sending side
------------
An authorizationReq body only carries ``authorizationType``. The platform
accepts this msgType **only on the bot→staff private-chat channel** (4.6.12,
``POST /v1/bot/messages/create``): sending it through the account channel is
rejected with「非法的msgType｜authorizationReq msgType only support bot-to-staff
private chat」. The client wrapper routes it through ``_send_private``::

    # async client; LansengerSyncClient.send_authorization_request is the same
    result = await client.send_authorization_request("<staff openId>")

    # when talking to the bot channel yourself, build the body with this helper
    from lansenger_sdk.authorization_requests import authorization_req_payload
    from lansenger_sdk.constants import MSG_TYPE_AUTHORIZATION_REQ

Receiving side (where the granted data arrives)
-----------------------------------------------
* Personal bots (个人机器人): after the user grants the request, the location
  report arrives **directly on the long connection** — it surfaces as the
  ``report_location`` callback event (:class:`ReportLocationData`).
* Organization bots (组织机器人): the app must subscribe to the
  「位置上报事件」 in the developer console and configure a callback URL; the
  same report then arrives through the callback interface.
"""

from __future__ import annotations

from typing import Any

from .constants import AUTHORIZATION_TYPE_LOCATION, AUTHORIZATION_TYPES


def authorization_req_payload(
    authorization_type: int = AUTHORIZATION_TYPE_LOCATION,
) -> dict[str, Any]:
    """Build the msgData body of an authorizationReq message (4.6.4.14).

    Args:
        authorization_type: 1 = 位置请求授权 (location permission request) —
            the only value the platform defines today.

    Returns:
        ``{"authorizationType": <int>}``

    Raises:
        ValueError: when the requested type is not defined by the platform.
    """
    if authorization_type not in AUTHORIZATION_TYPES:
        raise ValueError(
            f"invalid authorization_type: {authorization_type!r}; "
            f"known: {sorted(AUTHORIZATION_TYPES)}"
        )
    return {"authorizationType": authorization_type}
