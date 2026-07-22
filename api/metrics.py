# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/metrics.py

Prometheus metrics (pull-based, offline-friendly — docs/API_DESIGN.md §4/§17).
Uses a DEDICATED registry (not the global default) so importing the app twice
or building it in tests never triggers duplicate-collector errors.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

REGISTRY = CollectorRegistry()

REQUESTS = Counter(
    "phish_requests_total", "API requests by endpoint and HTTP status.",
    labelnames=("endpoint", "status"), registry=REGISTRY,
)
PREDICTIONS = Counter(
    "phish_predictions_total", "Scored URLs by verdict status.",
    labelnames=("status",), registry=REGISTRY,   # scored|invalid|error
)
LATENCY = Histogram(
    "phish_request_latency_seconds", "End-to-end request latency.",
    labelnames=("endpoint",), registry=REGISTRY,
)
INFLIGHT = Gauge(
    "phish_inflight_requests", "In-flight scoring requests (concurrency slots).",
    registry=REGISTRY,
)


def render() -> tuple[bytes, str]:
    """(_body, content_type) for the /metrics response."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
