// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FeatureCards } from "@/components/features/feature-cards";

describe("FeatureCards", () => {
  it("renders the three cards", () => {
    render(<FeatureCards />);
    expect(screen.getByText("What is LIMENX?")).toBeInTheDocument();
    expect(screen.getByText("How it works")).toBeInTheDocument();
    expect(screen.getByText("Why you can trust it")).toBeInTheDocument();
  });

  it("names the four-model ensemble and all four models", () => {
    render(<FeatureCards />);
    expect(screen.getByText(/four-model ensemble/i)).toBeInTheDocument();
    expect(screen.getByText("Random Forest")).toBeInTheDocument();
    expect(screen.getByText("CatBoost")).toBeInTheDocument();
    expect(screen.getByText("Character CNN")).toBeInTheDocument();
    expect(screen.getByText("Character Transformer")).toBeInTheDocument();
  });

  it("states the trust pillars", () => {
    render(<FeatureCards />);
    expect(screen.getByText(/Explainable/)).toBeInTheDocument();
    expect(screen.getByText(/we never open the link/)).toBeInTheDocument();
    expect(screen.getByText(/No black box/)).toBeInTheDocument();
    expect(screen.getByText("Human-confirmed")).toBeInTheDocument();
  });

  it("uses frosted-glass panels (translucent + blur) so the hero shows through", () => {
    const { container } = render(<FeatureCards />);
    const cards = container.querySelectorAll("article");
    expect(cards.length).toBe(3);
    cards.forEach((card) => {
      expect(card.className).toContain("backdrop-blur");
      expect(card.className).toMatch(/bg-white\//);
    });
  });

  it("adds a per-card animated glow border WITHOUT changing the glass/radius", () => {
    const { container } = render(<FeatureCards />);
    const cards = [...container.querySelectorAll("article")] as HTMLElement[];
    cards.forEach((c) => {
      expect(c.className).toContain("glow-card");
      // the existing card is untouched
      expect(c.className).toContain("backdrop-blur-2xl");
      expect(c.className).toContain("rounded-2xl");
      expect(c.className).toContain("border-white/10");
    });
    // red, gold, purple — distinct per card
    expect(cards.map((c) => c.style.getPropertyValue("--glow-color"))).toEqual([
      "#F87171",
      "#FFA63C",
      "#A78BFA",
    ]);
    // feature cards keep the DEFAULT glow speed (only Contact overrides it)
    cards.forEach((c) => expect(c.style.getPropertyValue("--glow-speed")).toBe(""));
  });
});
