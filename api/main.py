# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/main.py

The application factory + ASGI lifespan (docs/API_DESIGN.md §1/§13).

`create_app` wires middleware, error handlers, DI state, and routers over the
existing PhishingScorer. The model is loaded ONCE in the lifespan (fail-fast:
the app never becomes ready on a bad load) and shared read-only across
requests. Tests inject a fake scorer to exercise the HTTP contract without
loading real models.

Run (dev):  uvicorn api.main:app --host 0.0.0.0 --port 8000
Prod:       gunicorn -k uvicorn.workers.UvicornWorker api.main:app -w <N>
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from engine import PhishingScorer

from .config import Settings, get_settings
from .errors import install_error_handlers
from .middleware import (
    BodySizeLimitMiddleware,
    CorrelationMiddleware,
    TimeoutMiddleware,
)
from .rate_limit import ConcurrencyLimiter, RateLimiter
from .routers import health, meta, metrics, predict
from .security import KeyStore

logger = logging.getLogger("api.main")


def _warm_up(scorer: PhishingScorer) -> None:
    """Trigger lazy inits (torch, SHAP explainer build) so the first real
    request isn't a cold-start outlier. Best-effort: never fatal."""
    try:
        scorer.score("http://warm-up.invalid/", include_explanation=True)
    except Exception:  # noqa: BLE001
        logger.exception("warm-up inference failed (non-fatal)")


def create_app(settings: Optional[Settings] = None,
               scorer: Optional[PhishingScorer] = None) -> FastAPI:
    """Build the ASGI app. `scorer` may be injected (tests) to skip loading."""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "scorer", None) is None:
            # Fail-fast: a bad load raises here and the app never serves.
            app.state.scorer = PhishingScorer.load(
                version=settings.model_version,
                registry_dir=settings.registry_dir,
                verify_integrity=settings.verify_integrity,
                with_explanation=True,
                include_sequence_explanation=settings.include_sequence_explanation,
            )
            if settings.warm_up:
                _warm_up(app.state.scorer)
        app.state.ready = True
        logger.info('{"event": "api_ready", "service": "%s", "model": "%s"}',
                    settings.service_name, settings.model_version)
        yield
        app.state.ready = False

    docs_url = "/docs" if settings.docs_enabled else None
    redoc_url = "/redoc" if settings.docs_enabled else None
    app = FastAPI(
        title=settings.service_name,          # configurable brand
        version=settings.api_version,
        description=(
            "Offline, URL-only phishing detection API — a thin HTTP surface over "
            "the frozen ensemble. Never fetches URLs (no SSRF). Unscoreable URLs "
            "return 200 with `status: invalid`; 4xx/5xx are reserved for API-level "
            "errors."
        ),
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    # --- shared state (DI reads these) ---
    app.state.settings = settings
    app.state.ready = False
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute,
                                         settings.rate_limit_burst)
    app.state.concurrency = ConcurrencyLimiter(settings.max_concurrency)
    app.state.keystore = (
        KeyStore.from_file(settings.api_keys_file)
        if settings.auth_enabled and settings.api_keys_file else None
    )
    if scorer is not None:
        app.state.scorer = scorer             # injected fake (tests)

    # --- middleware ---
    # add_middleware stacks LIFO: the LAST added is OUTERMOST. Desired order
    # (outer -> inner): CORS -> Correlation(ids+access log) -> Timeout ->
    # BodySize -> GZip -> app. So add inner-first:
    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_min_bytes)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    app.add_middleware(TimeoutMiddleware, timeout_s=settings.request_timeout_s)
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )

    install_error_handlers(app)

    # --- routers ---
    prefix = settings.route_prefix
    app.include_router(health.router)                 # /health/* (unversioned)
    app.include_router(metrics.router)                # /metrics
    app.include_router(meta.router, prefix=prefix)    # /v1/version, /v1/info
    app.include_router(predict.router, prefix=prefix) # /v1/predict[/batch]
    return app


#: Module-level ASGI app for `uvicorn api.main:app`.
app = create_app()
