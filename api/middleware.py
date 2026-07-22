# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/middleware.py

Cross-cutting middleware:
- CorrelationMiddleware: assigns/propagates BOTH a per-request id
  (X-Request-ID, generated) and a caller-supplied correlation id
  (X-Correlation-ID, spans multiple requests / services — e.g. one user
  action in the React frontend across several API calls). Both are stored on
  request.state, echoed on the response, and emitted in a structured access
  log line.
- TimeoutMiddleware: bounds client-perceived latency, returning 504 if a
  request exceeds `timeout_s`. Honest caveat: Python cannot preempt the sync
  inference running in the threadpool, so the compute continues to completion
  server-side — this protects the CLIENT's wait, not the CPU. The concurrency
  semaphore + batch cap are what bound server compute; a reverse proxy should
  also set its own timeout in production.
- BodySizeLimitMiddleware: rejects oversized bodies early (413) via
  Content-Length, a cheap DoS bound before parsing.
"""

from __future__ import annotations

import asyncio
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .logging import log_access

_REQUEST_ID_HEADER = "X-Request-ID"
_CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Assign/propagate request + correlation ids; emit an access log line."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        # A caller-supplied correlation id spans requests; default to the
        # request id so there is always a usable trace key.
        correlation_id = request.headers.get(_CORRELATION_ID_HEADER) or request_id
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - started) * 1000.0

        response.headers[_REQUEST_ID_HEADER] = request_id
        response.headers[_CORRELATION_ID_HEADER] = correlation_id
        log_access(
            request_id=request_id, correlation_id=correlation_id,
            method=request.method, path=request.url.path,
            status_code=response.status_code, latency_ms=latency_ms,
        )
        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout_s: float) -> None:
        super().__init__(app)
        self._timeout = timeout_s

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await asyncio.wait_for(call_next(request), timeout=self._timeout)
        except (asyncio.TimeoutError, TimeoutError):
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=504,
                content={"error": {"code": "timeout",
                                   "message": "Request timed out.",
                                   "request_id": request_id, "detail": None}},
                headers={_REQUEST_ID_HEADER: request_id} if request_id else {},
            )


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self._max_bytes:
                    return self._too_large(request)
            except ValueError:
                pass  # malformed header -> let downstream validation handle it
        return await call_next(request)

    def _too_large(self, request: Request) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=413,
            content={"error": {"code": "payload_too_large",
                               "message": "Request body too large.",
                               "request_id": request_id, "detail": None}},
            headers={_REQUEST_ID_HEADER: request_id} if request_id else {},
        )
