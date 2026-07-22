// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
"use client";

import { useCallback, useState } from "react";

import type { ApiError, PredictResponse } from "@/lib/api/types";

/**
 * Scan state machine, backed by the same-origin BFF (`/api/scan`). A `result`
 * carries the API's own ScoreResult (which is itself scored / invalid / error);
 * `failed` is reserved for BFF/network-level failures (non-2xx or unreachable),
 * so the two are never conflated.
 */
export type ScanState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "result"; result: PredictResponse }
  | { status: "failed"; error: ApiError };

export function useScan() {
  const [state, setState] = useState<ScanState>({ status: "idle" });

  const scan = useCallback(async (url: string) => {
    const trimmed = url.trim();
    if (!trimmed) return;
    setState({ status: "loading" });
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ url: trimmed, include_explanation: true }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        setState({
          status: "failed",
          error: (body?.error as ApiError) ?? {
            code: "error",
            message: "The scan request failed.",
          },
        });
        return;
      }
      setState({ status: "result", result: body as PredictResponse });
    } catch {
      setState({
        status: "failed",
        error: { code: "network", message: "Could not reach the scanner." },
      });
    }
  }, []);

  const reset = useCallback(() => setState({ status: "idle" }), []);

  return { state, scan, reset };
}
