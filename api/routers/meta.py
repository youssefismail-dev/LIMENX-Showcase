# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/routers/meta.py

Metadata endpoints under /v1: `/version` (the three independent version axes)
and `/info` (service identity — the product NAME comes from config, never
hard-coded, so re-branding is a one-line config change).

Public (no auth): they reveal only service name + versions, useful for health
dashboards and clients negotiating compatibility.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from engine import EXPLANATION_VERSION, list_versions

from ..config import Settings
from ..dependencies import get_settings_dep
from ..schemas import InfoResponse, VersionResponse

router = APIRouter(tags=["meta"])


def _model_version(request: Request, settings: Settings) -> str:
    scorer = getattr(request.app.state, "scorer", None)
    return scorer.model_version if scorer is not None else settings.model_version


@router.get("/version", response_model=VersionResponse)
async def version(request: Request,
                  settings: Settings = Depends(get_settings_dep)) -> VersionResponse:
    try:
        registry = settings.registry_dir
        available = list_versions(registry) if registry else list_versions()
    except Exception:  # noqa: BLE001 -- metadata must not fail on a registry hiccup
        available = []
    return VersionResponse(
        api_version=settings.api_version,
        model_version=_model_version(request, settings),
        explanation_version=EXPLANATION_VERSION,
        available_model_versions=available,
    )


@router.get("/info", response_model=InfoResponse)
async def info(request: Request,
               settings: Settings = Depends(get_settings_dep)) -> InfoResponse:
    running = bool(getattr(request.app.state, "ready", False))
    return InfoResponse(
        service=settings.service_name,               # configurable brand
        status="running" if running else "starting",
        model=_model_version(request, settings),
    )
