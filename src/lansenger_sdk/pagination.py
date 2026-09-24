"""Shared V2 pagination parser for qingjia / jiaban (and any future V2 app).

qingjia / jiaban page shape:
    { pageNo, pageSize, pages, total, result, hasNextPage, extAttributes, lastKey }

boardrooms uses {count, data} — do NOT reuse the boardrooms page parsing here.
"""

from __future__ import annotations

from typing import Any


def parse_v2_page_info(data: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize a V2 page payload into the SDK's page-info dict."""
    d = data or {}
    return {
        "page_no": d.get("pageNo", 0),
        "page_size": d.get("pageSize", 0),
        "pages": d.get("pages", 0),
        "total": d.get("total", 0),
        "items": d.get("result") or [],
        "has_next_page": bool(d.get("hasNextPage", False)),
    }
