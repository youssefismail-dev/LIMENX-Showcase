// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { POST } from "@/app/api/scan/route";

/**
 * BFF /api/scan contract, with the upstream LIMENX API mocked via global fetch.
 * Proves: correct proxying + Bearer injection, key never leaks, light input
 * validation, and clean error normalization (unreachable / timeout / upstream
 * rejection) — the browser never sees a raw socket error or stack trace.
 */
function scanRequest(body: unknown): Request {
  return new Request("http://localhost/api/scan", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
  });
}

function upstream(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const SCORED = {
  status: "scored",
  url_normalized: "https://example.com",
  model_version: "v3.4",
  probability: 0.01,
};

describe("BFF /api/scan", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("LIMENX_API_URL", "http://api.test");
    vi.stubEnv("LIMENX_API_KEY", "");
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("proxies to /v1/predict and returns the scored body", async () => {
    fetchMock.mockResolvedValue(upstream(SCORED));
    const res = await POST(scanRequest({ url: "example.com" }));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual(SCORED);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/v1/predict");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({
      url: "example.com",
      include_explanation: false,
    });
  });

  it("forwards include_explanation", async () => {
    fetchMock.mockResolvedValue(upstream(SCORED));
    await POST(scanRequest({ url: "example.com", include_explanation: true }));
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).include_explanation).toBe(true);
  });

  it("injects the Bearer key server-side when configured", async () => {
    vi.stubEnv("LIMENX_API_KEY", "secret-key");
    fetchMock.mockResolvedValue(upstream(SCORED));
    await POST(scanRequest({ url: "example.com" }));
    const headers = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(headers.get("authorization")).toBe("Bearer secret-key");
  });

  it("omits the Authorization header when no key is set", async () => {
    fetchMock.mockResolvedValue(upstream(SCORED));
    await POST(scanRequest({ url: "example.com" }));
    const headers = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(headers.get("authorization")).toBeNull();
  });

  it("rejects invalid JSON with 400 and never calls upstream", async () => {
    const bad = new Request("http://localhost/api/scan", {
      method: "POST",
      body: "{not json",
      headers: { "content-type": "application/json" },
    });
    const res = await POST(bad);
    expect(res.status).toBe(400);
    expect((await res.json()).error.code).toBe("bad_request");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects a missing url with 400", async () => {
    const res = await POST(scanRequest({ include_explanation: true }));
    expect(res.status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("forwards an upstream validation error (422)", async () => {
    fetchMock.mockResolvedValue(
      upstream({ error: { code: "url_too_long", message: "too long" } }, 422),
    );
    const res = await POST(scanRequest({ url: "x".repeat(5000) }));
    expect(res.status).toBe(422);
    expect((await res.json()).error.code).toBe("url_too_long");
  });

  it("returns 502 when the scoring service is unreachable", async () => {
    fetchMock.mockRejectedValue(new Error("ECONNREFUSED"));
    const res = await POST(scanRequest({ url: "example.com" }));
    expect(res.status).toBe(502);
    expect((await res.json()).error.code).toBe("upstream_unreachable");
  });

  it("returns 504 on an upstream timeout (abort)", async () => {
    const abort = new Error("aborted");
    abort.name = "AbortError";
    fetchMock.mockRejectedValue(abort);
    const res = await POST(scanRequest({ url: "example.com" }));
    expect(res.status).toBe(504);
    expect((await res.json()).error.code).toBe("upstream_timeout");
  });
});
