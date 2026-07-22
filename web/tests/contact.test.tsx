// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Contact } from "@/components/contact";

describe("Contact", () => {
  it("uses the confident premium headline + a short human line", () => {
    render(<Contact />);
    expect(screen.getByText("Let's talk.")).toBeInTheDocument();
    expect(
      screen.getByText(/open to ideas, feedback, and collaboration/i),
    ).toBeInTheDocument();
  });

  it("holds only the four links, as safe external links", () => {
    render(<Contact />);
    for (const label of ["GitHub", "Email", "X", "Kaggle"]) {
      const link = screen.getByRole("link", { name: new RegExp(`^${label}`) });
      const href = link.getAttribute("href")!;
      expect(href.length).toBeGreaterThan(1);
      expect(href.startsWith("#")).toBe(false); // not caught by the anchor scroller
      if (label !== "Email") {
        expect(link.getAttribute("target")).toBe("_blank");
        expect(link.getAttribute("rel")).toContain("noopener");
      }
    }
    // exactly four links
    expect(screen.getAllByRole("link")).toHaveLength(4);
  });

  it("has the green glow border, 2x faster (unique to Contact), same glass", () => {
    const { container } = render(<Contact />);
    const card = container.querySelector(".glow-card") as HTMLElement;
    expect(card).not.toBeNull();
    expect(card.style.getPropertyValue("--glow-color")).toBe("#4ADE80");
    expect(card.style.getPropertyValue("--glow-speed")).toBe("3.5s"); // 2x of 7s
    expect(card.className).toContain("backdrop-blur-2xl");
    expect(card.className).toContain("rounded-2xl");
  });
});
