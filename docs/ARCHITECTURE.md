# LIMENX — Architecture

How the system is put together, and why. This document covers the layers
published in this showcase; the proprietary detection engine is described only
at the interface level.

> © 2026 Youssef Ismail. All rights reserved. Proprietary — see [`NOTICE`](../NOTICE).

---

## 1. Design goals

LIMENX was built as a **product platform**, not a model in a notebook. Three
goals drove every structural decision:

1. **Replaceability** — any component can be swapped without rewriting the
   layers around it. (This showcase is proof: the entire detection engine was
   replaced and nothing above it changed.)
2. **Explainability by construction** — the system must never be a black box,
   so the output contract carries explanation slots from day one.
3. **Safety** — the engine analyses URL *text*; it never fetches, resolves, or
   renders a URL, so scoring cannot be turned into an SSRF primitive.

## 2. Layers

```
Web app (Next.js)
   │  same-origin fetch
   ▼
BFF proxy (Next route handlers)          ← API key never reaches the browser
   │  HTTPS + Bearer
   ▼
FastAPI service
   ├─ middleware   correlation IDs · timeout · body-size cap · gzip · CORS
   ├─ auth         salted-hash API keys · scopes · rate limit · concurrency
   ├─ routers      /v1/predict · /v1/predict/batch · /v1/version · /v1/info · /health · /metrics
   ▼
Scoring engine (injected behind a stable interface)
   ├─ URL validation + normalization
   ├─ feature extraction   ── proprietary
   ├─ model ensemble       ── proprietary
   └─ explanation engine   ── proprietary
   ▼
ScoreResult  →  risk score · threat level · reasons · per-model votes
```

Each layer depends only on the layer beneath it, through an explicit contract.

## 3. The engine seam (the key decision)

The API never constructs a detector. It receives one that satisfies a small
interface:

```python
scorer.model_version                       # str
scorer.score(url, include_explanation)     # -> ScoreResult
scorer.score_batch(urls, include_explanation)
```

Everything the service needs is expressed in `ScoreResult` — status,
probability, decision, per-member scores, reasons, threat level, and the
explanation status. Because the contract is stable and the engine is injected
at the composition root, the detector is genuinely pluggable.

This is not a theoretical claim. This repository swaps the production ensemble
for `engine/reference_scorer.py` and **every layer above it runs unmodified**.

## 4. Request lifecycle

1. **Middleware** assigns a request ID + correlation ID, enforces the body-size
   cap, and bounds client-perceived latency with a timeout.
2. **Auth** resolves a `Principal` from a Bearer key (or the trusted principal
   when auth is disabled for local development), then checks scopes.
3. **Rate limiting** applies a per-key token bucket; **concurrency limiting**
   bounds simultaneous inferences with a semaphore, shedding load rather than
   thrashing the CPU.
4. **Validation** rejects structurally invalid URLs *before* any model runs.
5. **Scoring** happens in the ASGI threadpool (CPU-bound work off the event
   loop), inside a concurrency slot.
6. **Response** maps `ScoreResult` to the API schema, withholding detailed
   explanation from callers lacking the `explain:full` scope.

## 5. Error philosophy

- **Fail-closed** where correctness matters: an invalid URL or an internal
  invariant break yields a structured non-score (`invalid` / `error`) — never a
  garbage probability, never a raw exception to the caller.
- **Fail-open** where degradation is acceptable: if explanation evidence can't
  be gathered, the verdict still returns with `explanation_status: partial` or
  `unavailable`. **An explanation problem must never break a verdict.**
- Unscoreable URLs return **HTTP 200** with `status: invalid`. 4xx/5xx are
  reserved for genuine API-level failures — a client shouldn't have to parse
  error codes to tell "bad URL" from "server broken".

## 6. Security model

| Control | Implementation |
|---|---|
| Authentication | API keys stored as **salted SHA-256 hashes**, never plaintext |
| Timing safety | Constant-time comparison (`hmac.compare_digest`); every enabled record is checked so timing doesn't reveal which key matched |
| Authorization | Scopes — `predict` and `explain:full` (tiered explanation detail) |
| Abuse control | Per-key token bucket (429 + `Retry-After`) |
| Overload control | Bounded concurrency semaphore (503 load-shed) |
| DoS bounds | Body-size cap (413), URL length cap, batch size cap, request timeout (504) |
| Secret handling | Frontend BFF keeps the API key **server-side**; it is never bundled into browser JavaScript |
| SSRF | Structurally impossible — URLs are analysed as text and never fetched |
| Log hygiene | URLs can carry secrets, so URL redaction in logs is configurable |

## 7. Configuration

All operational knobs are environment-driven (`pydantic-settings`, `PHISH_`
prefix) — including the product name, so re-branding is a config change rather
than a code change. Nothing operational is hard-coded.

## 8. Testing

70 tests ship here, covering the HTTP contract, authentication and scopes,
middleware behaviour, the model interfaces, and validation. Tests inject fakes
through the same seams production uses — which is what makes the API layer
testable without any model present.

## 9. Frontend

A Next.js 16 App Router application. The browser only ever calls same-origin
routes; those route handlers proxy to the API server-side, so the API key and
upstream URL never reach the client. The API types are generated from the
service's OpenAPI schema, so a contract change surfaces at compile time.

One deliberate safety rule: **a scanned URL is always rendered as plain text,
never as a clickable link.**
