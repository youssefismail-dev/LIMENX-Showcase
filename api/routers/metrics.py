# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/routers/metrics.py

Prometheus scrape endpoint. Unauthenticated by convention (scrapers rarely
carry API keys); restrict via network policy / reverse proxy in production.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from ..metrics import render

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics() -> Response:
    body, content_type = render()
    return Response(content=body, media_type=content_type)
