# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
tests/test_api_endpoints.py

The REST API HTTP contract (api/), tested through Starlette's TestClient over
a FAKE scorer injected via the app factory — so the contract is exercised
without loading real models (the DI payoff). Covers health, meta/info,
predict happy-path + validation + fail-closed, batch caps, request-id, body
size, metrics, and the error envelope.

Run with: pytest tests/test_api_endpoints.py
"""


from starlette.testclient import TestClient

from api.config import Settings
from api.main import create_app
from engine.score_result import ScoreResult, ScoreStatus


class FakeScorer:
    model_version = "fake-v9"

    def __init__(self):
        self.calls = []

    def score_batch(self, urls, include_explanation=False):
        self.calls.append((list(urls), include_explanation))
        results = []
        for u in urls:
            if "invalid" in u:
                results.append(ScoreResult(
                    status=ScoreStatus.INVALID, url_input=u, url_normalized=u,
                    model_version=self.model_version, detail="failed validation"))
            else:
                results.append(ScoreResult(
                    status=ScoreStatus.SCORED, url_input=u,
                    url_normalized="https://" + u, model_version=self.model_version,
                    probability=0.9, decision=True, operating_threshold=0.5,
                    member_scores={"m": 0.9},
                    threat_level="high" if include_explanation else None,
                    reasons=[{"code": "feature:x", "title": "X"}] if include_explanation else None,
                    member_contributions=[{"member": "m", "contribution": 0.4}] if include_explanation else None,
                    explanation_status="ok" if include_explanation else None,
                    explanation_version="v1.0" if include_explanation else None))
        return results

    def score(self, url, include_explanation=False):
        return self.score_batch([url], include_explanation)[0]


def _client(**overrides):
    settings = Settings(auth_enabled=False, warm_up=False,
                        service_name="test-brand", max_batch=5,
                        url_max_length=100, **overrides)
    app = create_app(settings=settings, scorer=FakeScorer())
    return TestClient(app)


# --------------------------------------------------------------------------- #
# Health                                                                       #
# --------------------------------------------------------------------------- #

def test_live_is_always_ok():
    with _client() as c:
        assert c.get("/health/live").json() == {"status": "alive"}


def test_ready_reflects_lifespan():
    with _client() as c:                    # lifespan ran -> ready
        r = c.get("/health/ready")
        assert r.status_code == 200 and r.json()["status"] == "ready"


# --------------------------------------------------------------------------- #
# Meta                                                                         #
# --------------------------------------------------------------------------- #

def test_info_uses_configurable_service_name():
    with _client() as c:
        body = c.get("/v1/info").json()
        assert body["service"] == "test-brand"     # NOT hardcoded
        assert body["model"] == "fake-v9"
        assert body["status"] == "running"


def test_version_exposes_three_axes():
    with _client() as c:
        body = c.get("/v1/version").json()
        assert body["api_version"] == "v1"
        assert body["model_version"] == "fake-v9"
        assert body["explanation_version"] == "v1.0"


# --------------------------------------------------------------------------- #
# Predict                                                                      #
# --------------------------------------------------------------------------- #

def test_predict_scored():
    with _client() as c:
        r = c.post("/v1/predict", json={"url": "example.com"})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "scored"
        assert body["url_normalized"] == "https://example.com"
        assert body["probability"] == 0.9


def test_predict_explanation_when_requested():
    with _client() as c:
        r = c.post("/v1/predict",
                   json={"url": "example.com", "include_explanation": True})
        body = r.json()
        assert body["threat_level"] == "high"
        assert body["reasons"] and body["reasons"][0]["code"] == "feature:x"
        assert body["explanation_version"] == "v1.0"


def test_predict_default_has_no_explanation():
    with _client() as c:
        body = c.post("/v1/predict", json={"url": "example.com"}).json()
        assert body["threat_level"] is None and body["reasons"] is None


def test_invalid_url_is_200_with_invalid_status_not_http_error():
    # Fail-closed: an unscoreable URL is a SUCCESSFUL call with status=invalid.
    with _client() as c:
        r = c.post("/v1/predict", json={"url": "invalid-thing"})
        assert r.status_code == 200
        assert r.json()["status"] == "invalid"


def test_predict_batch_and_summary():
    with _client() as c:
        r = c.post("/v1/predict/batch",
                   json={"urls": ["a.com", "invalid-x", "b.com"]})
        body = r.json()
        assert [x["status"] for x in body["results"]] == ["scored", "invalid", "scored"]
        assert body["summary"] == {"n": 3, "scored": 2, "invalid": 1, "error": 0}


def test_batch_over_cap_is_422():
    with _client() as c:                    # max_batch=5
        r = c.post("/v1/predict/batch", json={"urls": [f"u{i}.com" for i in range(6)]})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "batch_too_large"


def test_url_too_long_is_422():
    with _client() as c:                    # url_max_length=100
        r = c.post("/v1/predict", json={"url": "x" * 101})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "url_too_long"


def test_missing_body_is_422_validation():
    with _client() as c:
        r = c.post("/v1/predict", json={})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "validation_error"


def test_unknown_field_rejected():
    with _client() as c:
        r = c.post("/v1/predict", json={"url": "a.com", "bogus": 1})
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# Cross-cutting                                                                #
# --------------------------------------------------------------------------- #

def test_request_id_echoed():
    with _client() as c:
        r = c.get("/health/live", headers={"X-Request-ID": "abc123"})
        assert r.headers["X-Request-ID"] == "abc123"


def test_request_id_generated_when_absent():
    with _client() as c:
        r = c.post("/v1/predict", json={"url": "a.com"})
        assert r.headers.get("X-Request-ID")


def test_body_too_large_is_413():
    with _client(max_request_bytes=50) as c:
        big = {"url": "x" * 200}
        r = c.post("/v1/predict", json=big)
        assert r.status_code == 413
        assert r.json()["error"]["code"] == "payload_too_large"


def test_metrics_endpoint_exposes_prometheus():
    with _client() as c:
        c.post("/v1/predict", json={"url": "a.com"})
        r = c.get("/metrics")
        assert r.status_code == 200
        assert "phish_predictions_total" in r.text
