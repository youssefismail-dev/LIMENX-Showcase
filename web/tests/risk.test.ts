// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { describe, expect, it } from "vitest";

import { directionMark, riskStyle } from "@/lib/scan/risk";

describe("riskStyle", () => {
  it("maps each threat level to a distinct label + colour", () => {
    expect(riskStyle("benign").label).toBe("Benign");
    expect(riskStyle("suspicious").label).toBe("Suspicious");
    expect(riskStyle("critical").label).toBe("Critical");
    expect(riskStyle("blocked").label).toBe("Blocked");
    // colours differ across levels
    const colors = ["benign", "low", "suspicious", "high", "critical"].map(
      (l) => riskStyle(l).color,
    );
    expect(new Set(colors).size).toBe(colors.length);
  });

  it("falls back for null/unknown", () => {
    expect(riskStyle(null).label).toBe("Unknown");
    expect(riskStyle("nonsense").label).toBe("Unknown");
  });
});

describe("directionMark", () => {
  it("distinguishes phishing / legitimate / informational", () => {
    expect(directionMark("toward_phishing").symbol).toBe("▲");
    expect(directionMark("toward_legitimate").symbol).toBe("▼");
    expect(directionMark("informational").symbol).toBe("•");
    expect(directionMark("toward_phishing").color).not.toBe(
      directionMark("toward_legitimate").color,
    );
  });
});
