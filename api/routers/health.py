# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/routers/health.py

Liveness vs readiness (docs/API_DESIGN.md §4/§13). Mounted at the root (NOT
under /v1) — orchestrators probe these regardless of API version.

- /health/live  : the process is up. Never depends on the model, so a slow
  model load cannot trip a liveness restart loop.
- /health/ready : the model is loaded AND warmed up (app.state.ready). Gates
  traffic; returns 503 until ready so the first real request isn't a
  cold-start outlier.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live() -> dict:
    return {"status": "alive"}


@router.get("/health/ready")
async def ready(request: Request, response: Response) -> dict:
    is_ready = bool(getattr(request.app.state, "ready", False))
    if not is_ready:
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}
