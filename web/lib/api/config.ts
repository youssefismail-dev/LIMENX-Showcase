// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Server-side configuration for reaching the LIMENX API. Read from env so the
 * key and upstream URL never appear in the client bundle. Used only by the BFF
 * client (server-only).
 *
 *   LIMENX_API_URL         base URL of the FastAPI service (default localhost:8000)
 *   LIMENX_API_KEY         optional Bearer key (sent only if set)
 *   LIMENX_API_TIMEOUT_MS  upstream timeout (default 30000, matches the API)
 */
export interface ApiConfig {
  baseUrl: string;
  apiKey: string | undefined;
  timeoutMs: number;
}

export function getApiConfig(): ApiConfig {
  return {
    baseUrl: (process.env.LIMENX_API_URL ?? "http://127.0.0.1:8000").replace(
      /\/+$/,
      "",
    ),
    apiKey: process.env.LIMENX_API_KEY || undefined,
    timeoutMs: Number(process.env.LIMENX_API_TIMEOUT_MS ?? 30000),
  };
}
