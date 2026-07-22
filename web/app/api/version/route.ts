// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { version } from "@/lib/api/client";
import { toResponse } from "@/lib/api/respond";

export const dynamic = "force-dynamic";

/** BFF: GET /api/version -> LIMENX /v1/version (api/model/explanation versions). */
export async function GET(): Promise<Response> {
  return toResponse(await version());
}
