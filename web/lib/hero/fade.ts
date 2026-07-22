// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Pure scroll-fade math for the hero object (the "god particle" video). Kept
 * separate so it is unit-testable. The object stays fully visible through
 * Hero -> Features -> Scanner and fades out only as the Contact section is
 * reached, revealing the normal dark page background.
 */
const FADE_START = 0.85;
const FADE_END = 1.0;

/** Hero-object opacity for a given document scroll progress in [0,1]. */
export function computeVideoOpacity(progress: number): number {
  if (progress <= FADE_START) return 1;
  if (progress >= FADE_END) return 0;
  const t = (progress - FADE_START) / (FADE_END - FADE_START);
  return 1 - t * t * (3 - 2 * t); // smoothstep
}
