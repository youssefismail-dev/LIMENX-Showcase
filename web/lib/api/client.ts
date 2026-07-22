// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import "server-only";

import { getApiConfig } from "./config";
import type {
  ApiError,
  BatchPredictRequest,
  BatchResponse,
  InfoResponse,
  PredictRequest,
  PredictResponse,
  VersionResponse,
} from "./types";

/**
 * The server-only LIMENX API client used by the BFF route handlers. `import
 * "server-only"` guarantees the API key + upstream URL can never be bundled
 * into the browser. Adds the Bearer key (if configured), a timeout, and
 * normalizes upstream failures into one envelope — the browser never sees a
 * raw stack trace or an unreachable-socket error.
 */
export interface UpstreamResult<T> {
  ok: boolean;
  status: number;
  data: T | null;
  error: ApiError | null;
}

async function call<T>(
  path: string,
  init: RequestInit,
): Promise<UpstreamResult<T>> {
  const { baseUrl, apiKey, timeoutMs } = getApiConfig();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json");
  if (apiKey) headers.set("authorization", `Bearer ${apiKey}`);

  try {
    const res = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
      cache: "no-store",
    });
    const text = await res.text();
    const body = text ? JSON.parse(text) : null;
    if (!res.ok) {
      return { ok: false, status: res.status, data: null, error: normalize(res.status, body) };
    }
    return { ok: true, status: res.status, data: body as T, error: null };
  } catch (err) {
    const aborted = err instanceof Error && err.name === "AbortError";
    return {
      ok: false,
      status: aborted ? 504 : 502,
      data: null,
      error: {
        code: aborted ? "upstream_timeout" : "upstream_unreachable",
        message: aborted
          ? "The scoring service timed out."
          : "The scoring service is unavailable.",
      },
    };
  } finally {
    clearTimeout(timer);
  }
}

/** Forward the API's own error envelope, a FastAPI validation error, or a generic one. */
function normalize(status: number, body: unknown): ApiError {
  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    if (record.error && typeof record.error === "object") {
      return record.error as ApiError;
    }
    if ("detail" in record) {
      return {
        code: "upstream_validation_error",
        message: "The scoring service rejected the request.",
        detail: record.detail,
      };
    }
  }
  return { code: "upstream_error", message: `Scoring service error (${status}).` };
}

export function predict(body: PredictRequest) {
  return call<PredictResponse>("/v1/predict", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function predictBatch(body: BatchPredictRequest) {
  return call<BatchResponse>("/v1/predict/batch", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function info() {
  return call<InfoResponse>("/v1/info", { method: "GET" });
}

export function version() {
  return call<VersionResponse>("/v1/version", { method: "GET" });
}
