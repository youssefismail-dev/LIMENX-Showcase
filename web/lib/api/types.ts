// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Friendly aliases over the auto-generated OpenAPI types (`schema.ts`). The
 * generated file is the single source of truth (regenerate with
 * `npm run gen:api-types` after the API contract changes); this module just
 * gives the app readable names. Never edit `schema.ts` by hand.
 */
import type { components } from "./schema";

export type PredictRequest = components["schemas"]["PredictRequest"];
export type PredictResponse = components["schemas"]["PredictResponse"];
export type BatchPredictRequest = components["schemas"]["BatchPredictRequest"];
export type BatchResponse = components["schemas"]["BatchResponse"];
export type InfoResponse = components["schemas"]["InfoResponse"];
export type VersionResponse = components["schemas"]["VersionResponse"];

/** The error envelope the BFF returns to the browser (mirrors the API's shape). */
export interface ApiError {
  code: string;
  message: string;
  detail?: unknown;
}
