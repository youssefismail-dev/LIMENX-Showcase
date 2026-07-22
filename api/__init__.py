# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api package: the V1 REST API (docs/API_DESIGN.md).

A thin FastAPI adapter over the serving.PhishingScorer — URL -> ScoreResult
over HTTP, with auth, rate limiting, request correlation, and Prometheus
metrics. Owns no ML/feature/scheme/explanation logic.
"""

from .config import Settings, get_settings
from .main import create_app

__all__ = ["create_app", "Settings", "get_settings"]
