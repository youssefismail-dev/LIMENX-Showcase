# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
tests/test_api_auth.py

Authentication + tiered explainability (api/ with auth_enabled=True). Verifies
the 401/403 gates and the key security control: a caller WITHOUT the
`explain:full` scope still gets the verdict + risk level, but reasons and
member_contributions are withheld (docs/API_DESIGN.md §15).

Run with: pytest tests/test_api_auth.py
"""

from starlette.testclient import TestClient

from api.config import Settings
from api.main import create_app
from api.security import SCOPE_EXPLAIN_FULL, SCOPE_PREDICT, KeyStore, generate_key

from tests.test_api_endpoints import FakeScorer


def _auth_client():
    settings = Settings(auth_enabled=True, warm_up=False)
    app = create_app(settings=settings, scorer=FakeScorer())
    predict_key, predict_rec = generate_key("kp", "predict-only", [SCOPE_PREDICT])
    full_key, full_rec = generate_key("kf", "full", [SCOPE_PREDICT, SCOPE_EXPLAIN_FULL])
    noscope_key, noscope_rec = generate_key("kn", "no-scope", [])
    app.state.keystore = KeyStore([predict_rec, full_rec, noscope_rec])
    client = TestClient(app)
    return client, {"predict": predict_key, "full": full_key, "none": noscope_key}


def _bearer(key):
    return {"Authorization": f"Bearer {key}"}


def test_missing_key_is_401():
    client, _ = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com"})
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "unauthorized"


def test_invalid_key_is_401():
    client, _ = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com"}, headers=_bearer("bad"))
        assert r.status_code == 401


def test_key_without_predict_scope_is_403():
    client, keys = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com"}, headers=_bearer(keys["none"]))
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "forbidden"


def test_predict_scope_can_score():
    client, keys = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com"}, headers=_bearer(keys["predict"]))
        assert r.status_code == 200 and r.json()["status"] == "scored"


def test_explanation_withheld_without_explain_full_scope():
    client, keys = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com", "include_explanation": True},
                   headers=_bearer(keys["predict"]))
        body = r.json()
        assert body["threat_level"] == "high"        # verdict + risk still shown
        assert body["reasons"] is None               # detail withheld
        assert body["member_contributions"] is None


def test_full_scope_receives_reasons():
    client, keys = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com", "include_explanation": True},
                   headers=_bearer(keys["full"]))
        body = r.json()
        assert body["reasons"] and body["reasons"][0]["code"] == "feature:x"
        assert body["member_contributions"]


def test_x_api_key_header_also_accepted():
    client, keys = _auth_client()
    with client as c:
        r = c.post("/v1/predict", json={"url": "a.com"},
                   headers={"X-API-Key": keys["predict"]})
        assert r.status_code == 200
