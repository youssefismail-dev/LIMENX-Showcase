// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Nav } from "@/components/nav";

describe("Nav", () => {
  it("shows the LIMENX wordmark linking to the top", () => {
    render(<Nav />);
    const brand = screen.getByRole("link", { name: /limenx/i });
    expect(brand.getAttribute("href")).toBe("#hero");
  });

  it("has minimal in-page links to features and scanner", () => {
    render(<Nav />);
    expect(
      screen.getByRole("link", { name: "How it works" }).getAttribute("href"),
    ).toBe("#features");
    expect(
      screen.getByRole("link", { name: "Scan" }).getAttribute("href"),
    ).toBe("#scanner");
    expect(
      screen.getByRole("link", { name: "Contact" }).getAttribute("href"),
    ).toBe("#contact");
  });
});
