# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
engine/

The scoring seam of this showcase.

In production, this package is LIMENX's proprietary detection engine: a
63-signal offline feature extractor, four trained models (Random Forest,
CatBoost, Character CNN, Character Transformer), calibrated fusion, and a
SHAP-based explanation engine. That engine is **not part of this public
repository**.

What ships here is a `PhishingScorer` that implements the *same public
interface*, so every layer above it — the FastAPI service, authentication,
rate limiting, validation, and the web app — runs unchanged and end-to-end.
Swapping the engine without touching anything above it is exactly what the
architecture was built for; this package is that seam, made visible.

See `reference_scorer.py` for precisely what is real vs. reference.
"""

from .reference_scorer import (
    MEMBER_NAMES,
    MEMBER_WEIGHTS,
    OPERATING_THRESHOLD,
    REFERENCE_VERSION,
    PhishingScorer,
    list_versions,
)
from .score_result import ScoreResult, ScoreStatus

#: Version of the explanation contract the API advertises.
EXPLANATION_VERSION = "v1.0"

__all__ = [
    "PhishingScorer",
    "ScoreResult",
    "ScoreStatus",
    "list_versions",
    "EXPLANATION_VERSION",
    "REFERENCE_VERSION",
    "OPERATING_THRESHOLD",
    "MEMBER_WEIGHTS",
    "MEMBER_NAMES",
]
