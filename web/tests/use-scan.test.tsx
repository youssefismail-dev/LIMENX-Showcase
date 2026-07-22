// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useScan } from "@/lib/scan/use-scan";

function mockFetch(impl: () => unknown) {
  const fn = vi.fn(async () => impl());
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("useScan", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("starts idle", () => {
    const { result } = renderHook(() => useScan());
    expect(result.current.state.status).toBe("idle");
  });

  it("posts to /api/scan (with explanation) and stores the result", async () => {
    const scored = { status: "scored", url_normalized: "https://a.test", model_version: "v" };
    const fetchFn = mockFetch(() => ({ ok: true, json: async () => scored }));
    const { result } = renderHook(() => useScan());

    await act(async () => {
      await result.current.scan("a.test");
    });

    expect(result.current.state).toEqual({ status: "result", result: scored });
    const [url, init] = fetchFn.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/scan");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      url: "a.test",
      include_explanation: true,
    });
  });

  it("surfaces a BFF error envelope as failed", async () => {
    mockFetch(() => ({
      ok: false,
      json: async () => ({ error: { code: "rate_limited", message: "Slow down." } }),
    }));
    const { result } = renderHook(() => useScan());
    await act(async () => {
      await result.current.scan("a.test");
    });
    expect(result.current.state).toMatchObject({
      status: "failed",
      error: { code: "rate_limited", message: "Slow down." },
    });
  });

  it("fails gracefully when the scanner is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("network down");
      }),
    );
    const { result } = renderHook(() => useScan());
    await act(async () => {
      await result.current.scan("a.test");
    });
    expect(result.current.state.status).toBe("failed");
  });

  it("ignores empty input", async () => {
    const fetchFn = mockFetch(() => ({ ok: true, json: async () => ({}) }));
    const { result } = renderHook(() => useScan());
    await act(async () => {
      await result.current.scan("   ");
    });
    expect(result.current.state.status).toBe("idle");
    expect(fetchFn).not.toHaveBeenCalled();
  });
});
