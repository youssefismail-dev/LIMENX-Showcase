// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { beforeEach, describe, expect, it } from "vitest";

import { useScrollStore } from "@/lib/scroll/store";

describe("scroll store", () => {
  beforeEach(() => {
    useScrollStore.setState({ progress: 0, scrollY: 0, velocity: 0 });
  });

  it("defaults to zero", () => {
    const s = useScrollStore.getState();
    expect(s.progress).toBe(0);
    expect(s.scrollY).toBe(0);
    expect(s.velocity).toBe(0);
  });

  it("publishes scroll updates via set()", () => {
    useScrollStore.getState().set({ progress: 0.5, scrollY: 820, velocity: -3 });
    const s = useScrollStore.getState();
    expect(s.progress).toBe(0.5);
    expect(s.scrollY).toBe(820);
    expect(s.velocity).toBe(-3);
  });

  it("supports partial updates", () => {
    useScrollStore.getState().set({ progress: 0.25 });
    expect(useScrollStore.getState().progress).toBe(0.25);
    expect(useScrollStore.getState().scrollY).toBe(0);
  });
});
