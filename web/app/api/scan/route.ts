// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { predict } from "@/lib/api/client";
import { badRequest, toResponse } from "@/lib/api/respond";
import type { PredictRequest } from "@/lib/api/types";

// A proxy must never be cached.
export const dynamic = "force-dynamic";

// Explained scans take ~5s (more on a cold backend); Vercel's default function
// timeout is far lower. 60s is the Hobby-plan ceiling. Deployment config only —
// does not change scan behavior.
export const maxDuration = 60;

/**
 * BFF: POST /api/scan -> LIMENX /v1/predict. The browser calls this same-origin
 * route; the API key (if any) is injected server-side by the client. Light
 * shape validation here (defense in depth); the API remains the source of
 * truth for limits.
 */
export async function POST(req: Request): Promise<Response> {
  let body: Partial<PredictRequest>;
  try {
    body = await req.json();
  } catch {
    return badRequest("Invalid JSON body.");
  }
  if (!body || typeof body.url !== "string" || body.url.trim().length === 0) {
    return badRequest("Field 'url' (non-empty string) is required.");
  }
  const result = await predict({
    url: body.url,
    include_explanation: Boolean(body.include_explanation),
  });
  return toResponse(result);
}
