// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Scanner } from "@/components/scanner/scanner";

const SCORED = {
  status: "scored",
  url_input: "google.com",
  url_normalized: "https://google.com",
  model_version: "v3.4",
  probability: 0.0123,
  decision: false,
  operating_threshold: 0.4678,
  member_scores: { rf: 0.01, cnn: 0.03 },
  scheme_assumed: true,
  scheme_resolution: "assumed_https",
  threat_level: "benign",
  reasons: [
    {
      code: "feature:is_https",
      title: "Transport security",
      direction: "toward_legitimate",
      source: "feature",
      faithfulness: "exact",
    },
  ],
  member_contributions: [
    { member: "cnn", contribution: -0.02 },
    { member: "rf", contribution: -0.05 },
  ],
  explanation_status: "ok",
  explanation_version: "v1.0",
};

function mockFetch(body: unknown, ok = true) {
  vi.stubGlobal("fetch", vi.fn(async () => ({ ok, json: async () => body })));
}

async function submitUrl(value: string) {
  fireEvent.change(screen.getByPlaceholderText("example.com"), {
    target: { value },
  });
  fireEvent.click(screen.getByRole("button", { name: /scan/i }));
}

describe("Scanner", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders the input and scan button", () => {
    render(<Scanner />);
    expect(screen.getByPlaceholderText("example.com")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /scan/i })).toBeInTheDocument();
  });

  it("has the blue animated glow border with the glass card unchanged", () => {
    const { container } = render(<Scanner />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("glow-card");
    expect(root.style.getPropertyValue("--glow-color")).toBe("#5B9BFF");
    expect(root.className).toContain("backdrop-blur-2xl"); // glass intact
    expect(root.className).toContain("rounded-2xl"); // radius intact
  });

  it("shows a faithful verdict for a scored URL", async () => {
    mockFetch(SCORED);
    render(<Scanner />);
    await submitUrl("google.com");

    expect(await screen.findByText("Benign")).toBeInTheDocument();
    expect(screen.getByText(/risk score/i)).toBeInTheDocument();
    expect(screen.getByText("1.2%")).toBeInTheDocument();
    expect(screen.getByText("Transport security")).toBeInTheDocument();
    expect(screen.getByText("https://google.com")).toBeInTheDocument();
    expect(screen.getByText(/HTTPS assumed/i)).toBeInTheDocument();
    expect(screen.getByText(/how the models voted/i)).toBeInTheDocument();
  });

  it("NEVER renders the scanned URL as a clickable link (safety)", async () => {
    mockFetch(SCORED);
    const { container } = render(<Scanner />);
    await submitUrl("google.com");
    await screen.findByText("https://google.com");
    // No anchors anywhere in the scanner — the phishing URL must not be clickable.
    expect(container.querySelector("a[href]")).toBeNull();
  });

  it("handles an unscoreable (invalid) URL without crashing", async () => {
    mockFetch({
      status: "invalid",
      url_normalized: "javascript:alert(1)",
      model_version: "v3.4",
      threat_level: "blocked",
      detail: "Rejected dangerous scheme 'javascript:'.",
      reasons: [{ title: "Scheme rejected", direction: "informational" }],
    });
    render(<Scanner />);
    await submitUrl("javascript:alert(1)");
    expect(await screen.findByText(/Rejected dangerous scheme/i)).toBeInTheDocument();
    expect(screen.getByText("Blocked")).toBeInTheDocument();
  });

  it("shows a friendly message on a BFF/network failure", async () => {
    mockFetch({ error: { code: "upstream_unreachable", message: "Scanner offline." } }, false);
    render(<Scanner />);
    await submitUrl("google.com");
    expect(await screen.findByText("Scanner offline.")).toBeInTheDocument();
  });
});
