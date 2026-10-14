"""4.6.4.14 authorizationReq message body (授权请求消息) builders.

Sending side
------------
An authorizationReq body only carries ``authorizationType``; it is sent through
the normal message channels (public account / bot / user), so the SDK ships this
payload builder instead of a bespoke transport::

    from lansenger_sdk.authorization_requests import authorization_req_payload
    from lansenger_sdk.constants import MSG_TYPE_AUTHORIZATION_REQ

    client.send_account_message(MSG_TYPE_AUTHORIZATION_REQ, authorization_req_payload())

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
