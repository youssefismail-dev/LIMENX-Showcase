// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "@/app/page";

describe("Home hero", () => {
  it("shows the tagline and a 'Scan a URL' CTA linking to the scanner", () => {
    render(<Home />);
    expect(screen.getByText("Know before you click.")).toBeInTheDocument();
    const cta = screen.getByRole("link", { name: "Scan a URL" });
    expect(cta.getAttribute("href")).toBe("#scanner");
  });

  it("gives each section an id for nav / CTA smooth-scroll", () => {
    const { container } = render(<Home />);
    expect(container.querySelector("#hero")).not.toBeNull();
    expect(container.querySelector("#features")).not.toBeNull();
    expect(container.querySelector("#scanner")).not.toBeNull();
    expect(container.querySelector("#contact")).not.toBeNull();
  });
});
