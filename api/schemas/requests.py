# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/schemas/requests.py

Request bodies. Two layers of bounds:
- ABSOLUTE hard caps here (defense-in-depth against pathological payloads,
  independent of config), and
- the CONFIGURED operational limits (`url_max_length`, `max_batch`) enforced
  at the router using Settings, so operators can tune them without a code
  change and get a clear 422.

`include_explanation` defaults False so the cheap scoring path is the default
and callers opt into explanation cost.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

#: Absolute safety ceilings (NOT the operational limits; see module docstring).
_ABS_URL_MAX = 65_536
_ABS_BATCH_MAX = 10_000


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"url": "paypa1-secure-login.tk/verify/account", "include_explanation": True},
            {"url": "https://www.wikipedia.org/wiki/Phishing", "include_explanation": False},
        ]},
    )

    url: str = Field(min_length=1, max_length=_ABS_URL_MAX,
                     description="The URL to score (raw; scheme optional — a "
                                 "missing scheme is assumed https).")
    include_explanation: bool = Field(
        default=False,
        description="Attach risk/reasons/contributions (requires explain:full "
                    "scope when auth is enabled).")


class BatchPredictRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [
            {"urls": ["google.com", "paypa1-secure-login.tk/verify", "ftp://x.test/a"],
             "include_explanation": False},
        ]},
    )

    urls: List[str] = Field(min_length=1, max_length=_ABS_BATCH_MAX,
                            description="URLs to score (≤ configured max_batch).")
    include_explanation: bool = Field(default=False)
