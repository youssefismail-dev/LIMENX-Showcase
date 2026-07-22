// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { predictBatch } from "@/lib/api/client";
import { badRequest, toResponse } from "@/lib/api/respond";
import type { BatchPredictRequest } from "@/lib/api/types";

export const dynamic = "force-dynamic";

// Batch scans can be slower than single; cap at Vercel's Hobby ceiling.
// Deployment config only — does not change scan behavior.
export const maxDuration = 60;

/** BFF: POST /api/scan/batch -> LIMENX /v1/predict/batch. */
export async function POST(req: Request): Promise<Response> {
  let body: Partial<BatchPredictRequest>;
  try {
    body = await req.json();
  } catch {
    return badRequest("Invalid JSON body.");
  }
  if (!body || !Array.isArray(body.urls) || body.urls.length === 0) {
    return badRequest("Field 'urls' (non-empty array) is required.");
  }
  if (!body.urls.every((u) => typeof u === "string")) {
    return badRequest("All 'urls' must be strings.");
  }
  const result = await predictBatch({
    urls: body.urls,
    include_explanation: Boolean(body.include_explanation),
  });
  return toResponse(result);
}
