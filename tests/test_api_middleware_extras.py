# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
tests/test_api_middleware_extras.py

The cross-cutting middleware added in the hardening pass: correlation id,
request timeout, CORS (for the React frontend), and GZip.

Run with: pytest tests/test_api_middleware_extras.py
"""

import time

from starlette.testclient import TestClient

from api.config import Settings
from api.main import create_app
from tests.test_api_endpoints import FakeScorer


def _client(scorer=None, **overrides):
    settings = Settings(auth_enabled=False, warm_up=False, **overrides)
    return TestClient(create_app(settings=settings, scorer=scorer or FakeScorer()))


# --------------------------------------------------------------------------- #
# Correlation id                                                              #
# --------------------------------------------------------------------------- #

def test_correlation_id_propagated_when_supplied():
    with _client() as c:
        r = c.post("/v1/predict", json={"url": "a.com"},
                   headers={"X-Correlation-ID": "trace-42"})
        assert r.headers["X-Correlation-ID"] == "trace-42"


def test_correlation_id_defaults_to_request_id():
    with _client() as c:
        r = c.get("/health/live")
        # absent inbound correlation id -> falls back to the request id
        assert r.headers["X-Correlation-ID"] == r.headers["X-Request-ID"]


# --------------------------------------------------------------------------- #
# Timeout                                                                     #
# --------------------------------------------------------------------------- #

class _SlowScorer(FakeScorer):
    def score_batch(self, urls, include_explanation=False):
        time.sleep(0.5)                     # exceeds the tiny test timeout
        return super().score_batch(urls, include_explanation)


def test_request_timeout_returns_504():
    with _client(scorer=_SlowScorer(), request_timeout_s=0.1) as c:
        r = c.post("/v1/predict", json={"url": "a.com"})
        assert r.status_code == 504
        assert r.json()["error"]["code"] == "timeout"


def test_fast_request_under_timeout_ok():
    with _client(request_timeout_s=5.0) as c:
        assert c.post("/v1/predict", json={"url": "a.com"}).status_code == 200


# --------------------------------------------------------------------------- #
# CORS                                                                        #
# --------------------------------------------------------------------------- #

def test_cors_allows_configured_origin():
    origin = "http://localhost:5173"
    with _client(cors_allow_origins=[origin]) as c:
        r = c.post("/v1/predict", json={"url": "a.com"},
                   headers={"Origin": origin})
        assert r.headers.get("access-control-allow-origin") == origin


def test_cors_preflight_answered():
    origin = "http://localhost:3000"
    with _client(cors_allow_origins=[origin]) as c:
        r = c.options("/v1/predict", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert r.status_code == 200
        assert r.headers["access-control-allow-origin"] == origin


def test_cors_disallowed_origin_not_reflected():
    with _client(cors_allow_origins=["http://localhost:3000"]) as c:
        r = c.post("/v1/predict", json={"url": "a.com"},
                   headers={"Origin": "http://evil.example"})
        assert r.headers.get("access-control-allow-origin") != "http://evil.example"


# --------------------------------------------------------------------------- #
# GZip                                                                        #
# --------------------------------------------------------------------------- #

def test_large_response_is_gzipped():
    # A big batch response exceeds the gzip threshold; httpx exposes the
    # negotiated encoding and transparently decodes the (valid) JSON.
    with _client(max_batch=100, gzip_min_bytes=100) as c:
        urls = [f"host{i}.com" for i in range(60)]
        r = c.post("/v1/predict/batch", json={"urls": urls},
                   headers={"Accept-Encoding": "gzip"})
        assert r.status_code == 200
        assert len(r.json()["results"]) == 60          # decoded correctly
        assert r.headers.get("content-encoding") == "gzip"
