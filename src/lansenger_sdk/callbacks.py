"""Lansenger callback event parsing and verification.

This module handles parsing and verifying callback payloads sent by the
Lansenger platform to your app's HTTP callback endpoint. It provides event
type categorization, payload decryption (placeholder), and signature
verification (placeholder).

No HTTP calls are made — this is purely data parsing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lansenger_sdk.callbacks")

CALLBACK_EVENT_TYPES: Dict[str, str] = {
    "account_message": "public_account",
    "account_subscribe": "public_account",
    "account_unsubscribe": "public_account",
    "staff_info": "staff",
    "staff_modify": "staff",
    "staff_create": "staff",
    "staff_delete": "staff",
    "dept_modify": "department",
    "dept_create": "department",
    "dept_delete": "department",
    "tag_member": "tag",
    "app_install_org": "app",
    "app_uninstall_org": "app",
    "bot_private_message": "bot",
    "bot_group_message": "bot",
    "group_create_approve": "group",
    "telephone_track": "notification",
    "ua_cert_create": "certificate",
    "ua_cert_modify": "certificate",
    "ua_cert_delete": "certificate",
    "report_location": "location",
    "user_logout": "auth",
    "data_scope": "data_scope",
    "wb_visible_config": "workbench",
    "schedule_modify": "calendar",
    "schedule_delete": "calendar",
}


@dataclass
class CallbackEvent:
    event_id: int
    event_type: str
    category: str
    data: dict
    app_id: str
    org_id: str


def parse_callback_payload(
    encrypted_data: str,
    *,
    encoding_key: str = "",
    verify_signature: bool = False,
    timestamp: str = "",
    nonce: str = "",
    signature: str = "",
) -> list[CallbackEvent]:
    """Parse a callback payload into a list of CallbackEvent objects.

    Args:
        encrypted_data: The callback payload (encrypted if encoding_key is
            provided, otherwise raw JSON).
        encoding_key: Key for decrypting the payload (placeholder — raises
            NotImplementedError if provided).
        verify_signature: Whether to verify the payload signature.
        timestamp: Timestamp for signature verification.
        nonce: Nonce for signature verification.
        signature: Expected signature for verification.
    """
    if encoding_key:
        raise NotImplementedError(
            "Payload decryption is not yet implemented. "
            "Pass the already-decrypted JSON string as encrypted_data."
        )

    if verify_signature and not verify_callback_signature(
        timestamp, nonce, signature, encoding_key
    ):
        raise ValueError("Callback signature verification failed")

    payload = json.loads(encrypted_data)

    events: list[CallbackEvent] = []
    event_list = payload.get("events", [])
    if isinstance(event_list, dict):
        event_list = [event_list]

    for entry in event_list:
        event_type = entry.get("eventType", "")
        category = CALLBACK_EVENT_TYPES.get(event_type, "unknown")
        events.append(
            CallbackEvent(
                event_id=entry.get("eventId", 0),
                event_type=event_type,
                category=category,
                data=entry.get("data", {}),
                app_id=entry.get("appId", ""),
                org_id=entry.get("orgId", ""),
            )
        )

    return events


def verify_callback_signature(
    timestamp: str,
    nonce: str,
    signature: str,
    encoding_key: str,
) -> bool:
    """Verify callback payload signature.

    Placeholder implementation — always returns True. The actual verification
    algorithm requires the encryption spec from section 4.10.1.4 of the
    Lansenger API documentation.
    """
    return True


def get_callback_event_types() -> Dict[str, str]:
    """Return the mapping of callback event types to categories."""
    return CALLBACK_EVENT_TYPES