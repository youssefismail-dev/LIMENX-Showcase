# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/routers/predict.py

The scoring endpoints — a THIN adapter over PhishingScorer.score_batch (the
single scoring entry point). Sync path functions so Starlette runs them in the
ASGI threadpool (CPU-bound work off the event loop); the concurrency semaphore
is acquired around the actual inference.

Tiered explanation (docs/API_DESIGN.md §15): a caller without the
`explain:full` scope still receives the verdict + `threat_level`, but the
detailed `reasons` / `member_contributions` are withheld.
"""

from __future__ import annotations

import time
from typing import List

from fastapi import APIRouter, Depends, Request

from engine import PhishingScorer, ScoreResult

from ..config import Settings
from ..dependencies import get_scorer, get_settings_dep, require_predict
from ..errors import APIError
from ..metrics import INFLIGHT, LATENCY, PREDICTIONS, REQUESTS
from ..schemas import (
    BatchPredictRequest,
    BatchResponse,
    BatchSummary,
    PredictRequest,
    PredictResponse,
)
from ..security import SCOPE_EXPLAIN_FULL, Principal

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    request: Request,
    principal: Principal = Depends(require_predict),
    scorer: PhishingScorer = Depends(get_scorer),
    settings: Settings = Depends(get_settings_dep),
) -> PredictResponse:
    _enforce_url_length([body.url], settings)
    results = _score(request, scorer, [body.url], body.include_explanation, "predict")
    return _to_response(results[0], principal)


@router.post("/predict/batch", response_model=BatchResponse)
def predict_batch(
    body: BatchPredictRequest,
    request: Request,
    principal: Principal = Depends(require_predict),
    scorer: PhishingScorer = Depends(get_scorer),
    settings: Settings = Depends(get_settings_dep),
) -> BatchResponse:
    if len(body.urls) > settings.max_batch:
        raise APIError(422, "batch_too_large",
                       f"Batch exceeds the configured maximum of {settings.max_batch}.")
    _enforce_url_length(body.urls, settings)
    results = _score(request, scorer, body.urls, body.include_explanation,
                     "predict_batch")
    responses = [_to_response(r, principal) for r in results]
    summary = BatchSummary(
        n=len(results),
        scored=sum(1 for r in results if r.status.value == "scored"),
        invalid=sum(1 for r in results if r.status.value == "invalid"),
        error=sum(1 for r in results if r.status.value == "error"),
    )
    return BatchResponse(results=responses, summary=summary)


# --------------------------------------------------------------------------- #

def _enforce_url_length(urls: List[str], settings: Settings) -> None:
    for url in urls:
        if len(url) > settings.url_max_length:
            raise APIError(422, "url_too_long",
                           f"A URL exceeds the configured maximum of "
                           f"{settings.url_max_length} characters.")


def _score(request: Request, scorer: PhishingScorer, urls: List[str],
           include_explanation: bool, endpoint: str) -> List[ScoreResult]:
    """Run scoring under the concurrency slot, with metrics. Overload (slot
    timeout) surfaces as OverloadedError -> 503 via the error handler."""
    started = time.perf_counter()
    concurrency = request.app.state.concurrency
    with concurrency.slot():
        INFLIGHT.set(concurrency.in_use)
        try:
            results = scorer.score_batch(urls, include_explanation=include_explanation)
        finally:
            INFLIGHT.set(max(concurrency.in_use - 1, 0))
    LATENCY.labels(endpoint=endpoint).observe(time.perf_counter() - started)
    REQUESTS.labels(endpoint=endpoint, status="200").inc()
    for r in results:
        PREDICTIONS.labels(status=r.status.value).inc()
    return results


def _to_response(result: ScoreResult, principal: Principal) -> PredictResponse:
    """Map a ScoreResult to the response, withholding detailed explanation for
    callers without the explain:full scope (verdict + risk level still shown)."""
    data = result.as_dict()
    if not principal.has_scope(SCOPE_EXPLAIN_FULL):
        data["reasons"] = None
        data["member_contributions"] = None
    return PredictResponse.model_validate(data)
