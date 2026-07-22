// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { describe, expect, it } from "vitest";

import { computeVideoOpacity } from "@/lib/hero/fade";

describe("computeVideoOpacity (visible through sections, fades at Contact)", () => {
  it("is fully visible through hero, features, and scanner", () => {
    expect(computeVideoOpacity(0)).toBe(1);
    expect(computeVideoOpacity(0.5)).toBe(1);
    expect(computeVideoOpacity(0.85)).toBe(1); // fade begins here
  });

  it("fades to zero by the end (Contact)", () => {
    expect(computeVideoOpacity(1)).toBe(0);
  });

  it("decreases monotonically across the fade window", () => {
    const vals = [0.85, 0.9, 0.95, 1].map(computeVideoOpacity);
    for (let i = 1; i < vals.length; i++) {
      expect(vals[i]).toBeLessThanOrEqual(vals[i - 1]);
    }
  });

  it("clamps outside [0,1]", () => {
    expect(computeVideoOpacity(-1)).toBe(1);
    expect(computeVideoOpacity(2)).toBe(0);
  });
});
