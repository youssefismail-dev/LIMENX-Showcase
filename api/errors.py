# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/errors.py

The single error envelope and the exception handlers that produce it. Every
API-level failure returns `ErrorResponse` with a `request_id` for correlation
and NEVER leaks a stack trace, path, or internal detail (security,
docs/API_DESIGN.md §6). Per-URL scoring failures are NOT errors here — they
are 200 responses with a `status` field (fail-closed).
"""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .rate_limit import OverloadedError
from .schemas import ErrorResponse

logger = logging.getLogger("api.errors")


class APIError(Exception):
    """An API-level failure with an HTTP status and a safe, public message."""

    def __init__(self, status_code: int, code: str, message: str,
                 detail: object = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail


class AuthError(APIError):
    def __init__(self, message: str = "Authentication required.",
                 code: str = "unauthorized",
                 status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
        super().__init__(status_code, code, message)


class ForbiddenError(APIError):
    def __init__(self, message: str = "Insufficient scope.") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "forbidden", message)


class RateLimitError(APIError):
    def __init__(self, retry_after: float) -> None:
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited",
                         "Rate limit exceeded.")
        self.retry_after = retry_after


def _envelope(request: Request, code: str, message: str,
              status_code: int, detail: object = None,
              headers: dict | None = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body = ErrorResponse.model_validate(
        {"error": {"code": code, "message": message,
                   "request_id": request_id, "detail": detail}})
    response = JSONResponse(status_code=status_code, content=body.model_dump())
    if request_id:
        response.headers["X-Request-ID"] = request_id
    for key, value in (headers or {}).items():
        response.headers[key] = value
    return response


def install_error_handlers(app) -> None:
    """Register the exception handlers on the FastAPI app."""

    @app.exception_handler(APIError)
    async def _api_error(request: Request, exc: APIError):
        headers = {}
        if isinstance(exc, RateLimitError):
            headers["Retry-After"] = str(max(1, round(exc.retry_after)))
        return _envelope(request, exc.code, exc.message, exc.status_code,
                         exc.detail, headers)

    @app.exception_handler(OverloadedError)
    async def _overloaded(request: Request, exc: OverloadedError):
        return _envelope(request, "overloaded",
                         "Server at capacity; please retry shortly.",
                         status.HTTP_503_SERVICE_UNAVAILABLE,
                         headers={"Retry-After": "1"})

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return _envelope(request, "validation_error",
                         "Request failed validation.",
                         status.HTTP_422_UNPROCESSABLE_ENTITY,
                         detail=exc.errors())

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Log the real cause server-side keyed by request_id; return nothing
        # internal to the client (no stack trace, path, or message leakage).
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled error (request_id=%s)", request_id)
        return _envelope(request, "internal_error",
                         "An internal error occurred.",
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
