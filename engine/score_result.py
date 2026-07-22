# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
engine/score_result.py

ScoreResult: the output contract of the serving path — what the REST API
serialises and the web app displays. Carries the explainability SLOTS
(`reasons`, `threat_level`) from day one so the Explainability Engine
attaches ADDITIVELY later, never by reshaping this contract
(docs/SERVING_PATH_DESIGN.md §2).

Fail-closed statuses: an invalid URL or an internal failure yields a
structured non-score (INVALID / ERROR with `detail`), never an exception
to the caller and never a garbage probability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class ScoreStatus(str, Enum):
    """Terminal status of one scoring request."""

    SCORED = "scored"     # a trustworthy probability was produced
    INVALID = "invalid"   # the URL failed validation; no model was consulted
    ERROR = "error"       # an internal invariant broke; fail-closed, no score


@dataclass(frozen=True)
class ScoreResult:
    """One URL's scoring outcome (the public inference contract)."""

    status: ScoreStatus
    url_normalized: str
    model_version: str
    probability: Optional[float] = None          # calibrated P(phishing)
    decision: Optional[bool] = None              # probability >= operating_threshold
    operating_threshold: Optional[float] = None
    member_scores: Optional[Dict[str, float]] = None   # raw per-member P(phishing)
    #: Scheme-resolution transparency (serving/scheme_resolver.py). `url_input`
    #: is the raw string the user submitted (before resolution/normalization);
    #: `scheme_assumed` is True when HTTPS was assumed for a scheme-less input
    #: (surface as "HTTPS assumed because no protocol was provided");
    #: `scheme_resolution` is the SchemeResolution enum value for auditing.
    url_input: Optional[str] = None
    scheme_assumed: Optional[bool] = None
    scheme_resolution: Optional[str] = None
    #: Filled by the Explanation Engine (serving/scorer.py, when
    #: include_explanation is on). Empty by default so scoring stays cheap and
    #: the enrichment is purely additive. `threat_level` is the RiskLevel
    #: value; `reasons` are ranked Reason dicts; `member_contributions` is the
    #: exact per-model fusion decomposition; `explanation_status` ∈
    #: {ok,partial,unavailable}; `explanation_version` versions this contract.
    reasons: Optional[List[dict]] = None
    threat_level: Optional[str] = None
    member_contributions: Optional[List[dict]] = None
    explanation_status: Optional[str] = None
    explanation_version: Optional[str] = None
    detail: Optional[str] = None                 # why INVALID / ERROR
    latency_ms: Optional[float] = None

    def as_dict(self) -> dict:
        """JSON-ready form (the REST API's response body)."""
        return {
            "status": self.status.value,
            "url_input": self.url_input,
            "url_normalized": self.url_normalized,
            "model_version": self.model_version,
            "probability": self.probability,
            "decision": self.decision,
            "operating_threshold": self.operating_threshold,
            "member_scores": self.member_scores,
            "scheme_assumed": self.scheme_assumed,
            "scheme_resolution": self.scheme_resolution,
            "reasons": self.reasons,
            "threat_level": self.threat_level,
            "member_contributions": self.member_contributions,
            "explanation_status": self.explanation_status,
            "explanation_version": self.explanation_version,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
        }
