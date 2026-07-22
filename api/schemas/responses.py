# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/schemas/responses.py

Response bodies. `PredictResponse` is a TYPED MIRROR of
`serving.ScoreResult.as_dict()` — that dict remains the single source of
truth; a drift-guard test asserts the field sets match exactly, so the two
can never silently diverge (the same anti-drift discipline used elsewhere).

Detailed explanation fields (`reasons`, `member_contributions`) are withheld
for callers lacking the `explain:full` scope (tiered explainability); the
scalar verdict + `threat_level` are always returned.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PredictResponse(BaseModel):
    """Typed mirror of ScoreResult.as_dict() (fail-closed statuses included)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{
            "status": "scored",
            "url_input": "paypa1-secure-login.tk/verify",
            "url_normalized": "https://paypa1-secure-login.tk/verify",
            "model_version": "v3.4", "probability": 0.9997, "decision": True,
            "operating_threshold": 0.4678,
            "member_scores": {"rf": 0.98, "cb": 0.87, "cnn": 0.99, "t": 0.95},
            "scheme_assumed": True, "scheme_resolution": "assumed_https",
            "threat_level": "critical",
            "reasons": [{"code": "feature:suspicious_tld",
                         "title": "Suspicious top-level domain",
                         "direction": "toward_phishing", "source": "feature",
                         "faithfulness": "exact"}],
            "member_contributions": [{"member": "cnn", "contribution": 0.2}],
            "explanation_status": "ok", "explanation_version": "v1.0",
            "detail": None, "latency_ms": 12.3,
        }]},
    )

    status: str
    url_input: Optional[str] = None
    url_normalized: str
    model_version: str
    probability: Optional[float] = None
    decision: Optional[bool] = None
    operating_threshold: Optional[float] = None
    member_scores: Optional[Dict[str, float]] = None
    scheme_assumed: Optional[bool] = None
    scheme_resolution: Optional[str] = None
    # Explanation (additive; may be withheld by scope)
    reasons: Optional[List[dict]] = None
    threat_level: Optional[str] = None
    member_contributions: Optional[List[dict]] = None
    explanation_status: Optional[str] = None
    explanation_version: Optional[str] = None
    detail: Optional[str] = None
    latency_ms: Optional[float] = None


class BatchSummary(BaseModel):
    n: int
    scored: int
    invalid: int
    error: int


class BatchResponse(BaseModel):
    results: List[PredictResponse]
    summary: BatchSummary


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    detail: Optional[object] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class VersionResponse(BaseModel):
    api_version: str
    model_version: str
    explanation_version: str
    available_model_versions: List[str] = Field(default_factory=list)


class InfoResponse(BaseModel):
    service: str
    status: str
    model: str
