// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET as getInfo } from "@/app/api/info/route";
import { GET as getVersion } from "@/app/api/version/route";
import { POST as postBatch } from "@/app/api/scan/batch/route";

function upstream(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
function batchRequest(body: unknown): Request {
  return new Request("http://localhost/api/scan/batch", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
  });
}

describe("BFF batch + meta routes", () => {
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

  it("batch proxies to /v1/predict/batch", async () => {
    const payload = { results: [], summary: { n: 0, scored: 0, invalid: 0, error: 0 } };
    fetchMock.mockResolvedValue(upstream(payload));
    const res = await postBatch(batchRequest({ urls: ["a.com", "b.com"] }));
    expect(res.status).toBe(200);
    expect(fetchMock.mock.calls[0][0]).toBe("http://api.test/v1/predict/batch");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body).urls).toEqual(["a.com", "b.com"]);
  });

  it("batch rejects an empty/invalid urls array with 400", async () => {
    expect((await postBatch(batchRequest({ urls: [] }))).status).toBe(400);
    expect((await postBatch(batchRequest({ urls: "nope" }))).status).toBe(400);
    expect((await postBatch(batchRequest({ urls: [1, 2] }))).status).toBe(400);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("info proxies to /v1/info", async () => {
    fetchMock.mockResolvedValue(
      upstream({ service: "LIMENX", status: "running", model: "v3.4" }),
    );
    const res = await getInfo();
    expect(res.status).toBe(200);
    expect((await res.json()).service).toBe("LIMENX");
    expect(fetchMock.mock.calls[0][0]).toBe("http://api.test/v1/info");
  });

  it("version proxies to /v1/version", async () => {
    fetchMock.mockResolvedValue(
      upstream({
        api_version: "v1",
        model_version: "v3.4",
        explanation_version: "v1.0",
        available_model_versions: ["v3.4"],
      }),
    );
    const res = await getVersion();
    expect(res.status).toBe(200);
    expect((await res.json()).model_version).toBe("v3.4");
    expect(fetchMock.mock.calls[0][0]).toBe("http://api.test/v1/version");
  });

  it("meta routes fail closed to 502 when upstream is down", async () => {
    fetchMock.mockRejectedValue(new Error("down"));
    expect((await getInfo()).status).toBe(502);
    expect((await getVersion()).status).toBe(502);
  });
});
