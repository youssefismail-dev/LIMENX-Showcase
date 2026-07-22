# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/logging.py

Structured access/audit logging for the API layer, with URL redaction on by
default (docs/API_DESIGN.md §9). URLs submitted to a phishing scanner can
carry secrets/PII in the query/fragment, so audit logs record host + a URL
hash with query/fragment stripped, unless an operator opts into full URLs.

The scoring layer already emits its own structured logs (serving.scorer);
this adds the HTTP access record and safe URL redaction helpers.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional
from urllib.parse import urlsplit

logger = logging.getLogger("api.access")


def redact_url(raw: str, redact: bool = True) -> str:
    """A log-safe representation of a URL.

    redact=True (default): 'scheme://host/…#<sha8>' — host kept for triage,
    path/query/fragment collapsed, an 8-char content hash for correlation.
    redact=False: the URL unchanged (opt-in for environments that require it).
    """
    if not redact:
        return raw
    digest = hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:8]
    try:
        parts = urlsplit(raw)
        host = parts.hostname or ""
        scheme = parts.scheme or ""
        prefix = f"{scheme}://{host}" if scheme else host
        return f"{prefix}/…#{digest}"
    except ValueError:
        return f"…#{digest}"


def log_access(
    *,
    request_id: Optional[str],
    method: str,
    path: str,
    status_code: int,
    latency_ms: float,
    correlation_id: Optional[str] = None,
) -> None:
    """Emit one structured access record (no raw URLs, no secrets). Called by
    the correlation middleware for every request."""
    logger.info(json.dumps({
        "event": "api_access",
        "request_id": request_id,
        "correlation_id": correlation_id,
        "method": method,
        "path": path,
        "status": status_code,
        "latency_ms": round(latency_ms, 2),
    }))
