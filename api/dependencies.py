# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/dependencies.py

FastAPI dependency providers — the DI seam (docs/API_DESIGN.md §12). Everything
the routers need is resolved here from `app.state` (populated at startup) or
from config, so tests override a single provider (e.g. inject a fake scorer)
instead of patching internals.

Chain for the scoring endpoints:  authenticate -> require predict scope ->
rate-limit  (concurrency is acquired around the compute inside the endpoint).
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request

from engine import PhishingScorer

from .config import Settings
from .errors import APIError, AuthError, ForbiddenError, RateLimitError
from .rate_limit import ConcurrencyLimiter, RateLimiter
from .security import SCOPE_PREDICT, KeyStore, Principal, TRUSTED_PRINCIPAL


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


def get_scorer(request: Request) -> PhishingScorer:
    scorer: Optional[PhishingScorer] = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise APIError(503, "not_ready", "Model is not loaded yet.")
    return scorer


def get_concurrency(request: Request) -> ConcurrencyLimiter:
    return request.app.state.concurrency


def _extract_key(request: Request) -> Optional[str]:
    """Bearer token or X-API-Key header (Bearer preferred)."""
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.headers.get("x-api-key")


def authenticate(request: Request) -> Principal:
    """Resolve the caller. Auth disabled -> the trusted principal (full
    scoring + explanation, never admin)."""
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return TRUSTED_PRINCIPAL
    key = _extract_key(request)
    if not key:
        raise AuthError("Missing API key.")
    keystore: Optional[KeyStore] = getattr(request.app.state, "keystore", None)
    principal = keystore.verify(key) if keystore else None
    if principal is None:
        raise AuthError("Invalid or expired API key.")
    return principal


def require_predict(request: Request) -> Principal:
    """authenticate + predict scope + per-key rate limit. Returns the principal
    for the endpoint (which then reads its scopes for tiered explanation)."""
    principal = authenticate(request)
    if not principal.has_scope(SCOPE_PREDICT):
        raise ForbiddenError("API key lacks the 'predict' scope.")
    limiter: RateLimiter = request.app.state.rate_limiter
    allowed, retry_after = limiter.check(principal.key_id)
    if not allowed:
        raise RateLimitError(retry_after)
    return principal
