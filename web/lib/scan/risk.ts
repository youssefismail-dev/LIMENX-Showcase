// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Risk-level presentation for the scanner — pure mapping from the API's
 * `threat_level` to a human label + colour. The risk palette is deliberately
 * DISTINCT from the LIMENX brand gold (security clarity: colour carries
 * meaning), and every level also has a text label so it never relies on colour
 * alone.
 */
export interface RiskStyle {
  label: string;
  color: string;
}

const STYLES: Record<string, RiskStyle> = {
  benign: { label: "Benign", color: "#34D399" },
  low: { label: "Low risk", color: "#5CC8A6" },
  suspicious: { label: "Suspicious", color: "#F5B740" },
  high: { label: "High risk", color: "#F97316" },
  critical: { label: "Critical", color: "#F43F5E" },
  blocked: { label: "Blocked", color: "#9AA0AE" },
};

export function riskStyle(level: string | null | undefined): RiskStyle {
  return (level && STYLES[level]) || { label: "Unknown", color: "#9AA0AE" };
}

/** Human phrasing for a reason's direction. */
export function directionMark(direction: string): { symbol: string; color: string } {
  switch (direction) {
    case "toward_phishing":
      return { symbol: "▲", color: "#F87171" };
    case "toward_legitimate":
      return { symbol: "▼", color: "#34D399" };
    default:
      return { symbol: "•", color: "#9AA0AE" }; // informational
  }
}

/** Friendly member names for the "how the models voted" breakdown. */
export const MEMBER_NAMES: Record<string, string> = {
  rf: "Random Forest",
  cb: "CatBoost",
  cnn: "Character CNN",
  t: "Character Transformer",
};
