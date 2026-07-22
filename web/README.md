# LIMENX — Web App

The Next.js 16 (App Router) frontend for LIMENX. Part of the
[engineering showcase](../README.md).

> © 2026 Youssef Ismail. All rights reserved. Proprietary — see [`NOTICE`](../NOTICE).

## What it demonstrates

- **BFF (Backend-for-Frontend) proxy.** The browser only ever calls same-origin
  `/api/*` routes. Those route handlers forward the request to the LIMENX API
  **server-side**, so the API key and upstream URL are never bundled into client
  JavaScript. The client module is guarded with `server-only` so it cannot be
  imported into a browser bundle by accident.
- **Typed API seam.** Request/response types are generated from the service's
  OpenAPI schema, so a backend contract change surfaces as a compile error.
- **Normalized failures.** Upstream timeouts and outages are mapped to a single
  error envelope — the browser never sees a stack trace or a raw socket error.
- **A safety rule in the UI.** A scanned URL is always rendered as **plain text,
  never a clickable link** — the product must not become a way to open a
  phishing page.

## Structure

```
app/            routes + BFF proxy handlers (app/api/*)
components/     scanner UI, feature cards, navigation, hero
lib/api/        server-only API client, config, response mapping, generated types
lib/scan/       scan state machine + risk presentation helpers
tests/          component and BFF tests (Vitest + Testing Library)
```

## Run

```bash
npm install
npm run dev        # http://localhost:3000
```

The app expects the LIMENX API on `http://127.0.0.1:8000` by default. In this
showcase that is the reference engine — start it from the repository root:

```bash
uvicorn api.main:app --port 8000
```

Configuration (server-side only):

| Variable | Purpose | Default |
|---|---|---|
| `LIMENX_API_URL` | Base URL of the API | `http://127.0.0.1:8000` |
| `LIMENX_API_KEY` | Bearer key, sent only if set | — |
| `LIMENX_API_TIMEOUT_MS` | Upstream timeout (ms) | `30000` |

## Tests

```bash
npm run lint
npx vitest run
```
