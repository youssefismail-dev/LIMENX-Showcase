# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/rate_limit.py

Two independent guards (docs/API_DESIGN.md §8):

1. ConcurrencyLimiter — the PRIMARY protection for a CPU-bound ML service. A
   bounded semaphore (~CPU cores) so concurrent inferences queue briefly and,
   past a timeout, shed load (503) instead of thrashing the CPU and blowing
   everyone's p99.
2. RateLimiter — a per-key token bucket for fairness/abuse (429 + Retry-After).

Both are thread-safe (sync endpoints run in the ASGI threadpool). Honest
scope: buckets are per-process, so with N workers the effective limit is
per-worker × N (not globally exact); a shared store is deferred (offline).
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from time import monotonic
from typing import Dict, Iterator, Tuple


class OverloadedError(Exception):
    """Raised when a concurrency slot cannot be acquired before the timeout."""


class TokenBucket:
    """Classic token bucket: `capacity` burst, refilled at `refill_per_sec`."""

    def __init__(self, capacity: float, refill_per_sec: float) -> None:
        self._capacity = float(capacity)
        self._refill = float(refill_per_sec)
        self._tokens = float(capacity)
        self._updated = monotonic()
        self._lock = threading.Lock()

    def try_consume(self, n: float = 1.0) -> Tuple[bool, float]:
        """Return (allowed, retry_after_seconds). retry_after is 0 when allowed."""
        with self._lock:
            now = monotonic()
            self._tokens = min(self._capacity,
                               self._tokens + (now - self._updated) * self._refill)
            self._updated = now
            if self._tokens >= n:
                self._tokens -= n
                return True, 0.0
            deficit = n - self._tokens
            retry_after = deficit / self._refill if self._refill > 0 else float("inf")
            return False, retry_after


class RateLimiter:
    """Per-key token buckets built from a per-minute rate and a burst size."""

    def __init__(self, per_minute: int, burst: int) -> None:
        self._refill = per_minute / 60.0
        self._capacity = float(burst)
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> Tuple[bool, float]:
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(self._capacity, self._refill)
                self._buckets[key] = bucket
        return bucket.try_consume(1.0)


class ConcurrencyLimiter:
    """Bounds simultaneous inferences; queues up to a timeout, then sheds load."""

    def __init__(self, max_slots: int, acquire_timeout: float = 10.0) -> None:
        self._sem = threading.BoundedSemaphore(max_slots)
        self._timeout = acquire_timeout
        self._capacity = max_slots
        self._in_use = 0
        self._lock = threading.Lock()

    @contextmanager
    def slot(self) -> Iterator[None]:
        acquired = self._sem.acquire(timeout=self._timeout)
        if not acquired:
            raise OverloadedError(
                "Server at capacity; concurrency slot unavailable.")
        with self._lock:
            self._in_use += 1
        try:
            yield
        finally:
            with self._lock:
                self._in_use -= 1
            self._sem.release()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def in_use(self) -> int:
        with self._lock:
            return self._in_use
