// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import type { UpstreamResult } from "./client";

/**
 * BFF response helpers. Turns the server-only client's result into the JSON
 * the browser receives — success data as-is, or the normalized error envelope.
 * Uses the Response constructor (not Response.json) for portability across
 * runtimes/test envs.
 */
function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function toResponse<T>(result: UpstreamResult<T>): Response {
  return result.ok
    ? json(result.data, 200)
    : json({ error: result.error }, result.status);
}

export function badRequest(message: string): Response {
  return json({ error: { code: "bad_request", message } }, 400);
}
