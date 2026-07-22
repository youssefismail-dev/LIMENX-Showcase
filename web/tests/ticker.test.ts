// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Ticker } from "@/lib/scroll/ticker";

/**
 * The Ticker is the guarantee that the whole app animates on ONE rAF loop.
 * These tests pin that contract: one loop regardless of subscriber count,
 * correct start/stop lifecycle, and framerate-independent deltas.
 *
 * requestAnimationFrame is mocked with an id-tracked queue so cancellation is
 * faithful (a cancelled frame is actually removed, as in a real browser).
 */
describe("Ticker (shared rAF loop)", () => {
  let pending: Array<{ id: number; cb: FrameRequestCallback }>;
  let nextId: number;

  beforeEach(() => {
    pending = [];
    nextId = 1;
    vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
      const id = nextId++;
      pending.push({ id, cb });
      return id;
    });
    vi.stubGlobal("cancelAnimationFrame", (id: number) => {
      pending = pending.filter((p) => p.id !== id);
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  /** Fire every currently-scheduled frame at `time`; callbacks may reschedule. */
  function flush(time: number) {
    const due = pending;
    pending = [];
    for (const { cb } of due) cb(time);
  }

  it("runs no loop with no subscribers", () => {
    const t = new Ticker();
    expect(t.running).toBe(false);
    expect(pending).toHaveLength(0);
  });

  it("starts exactly one frame on the first subscriber", () => {
    const t = new Ticker();
    t.add(() => {});
    expect(t.running).toBe(true);
    expect(pending).toHaveLength(1);
  });

  it("reports a timestamp and a framerate-independent delta", () => {
    const t = new Ticker();
    const calls: Array<[number, number]> = [];
    t.add((time, delta) => calls.push([time, delta]));
    flush(1000); // first frame -> delta 0 (no cross-clock jump)
    flush(1016); // ~60fps
    flush(1049); // ~30fps
    expect(calls[0]).toEqual([1000, 0]);
    expect(calls[1]).toEqual([1016, 16]);
    expect(calls[2]).toEqual([1049, 33]);
  });

  it("drives many subscribers from a SINGLE loop", () => {
    const t = new Ticker();
    const a = vi.fn();
    const b = vi.fn();
    const c = vi.fn();
    t.add(a);
    t.add(b);
    t.add(c);
    expect(pending).toHaveLength(1); // three adds, still ONE scheduled frame
    flush(1000);
    expect(a).toHaveBeenCalledOnce();
    expect(b).toHaveBeenCalledOnce();
    expect(c).toHaveBeenCalledOnce();
    expect(pending).toHaveLength(1); // rescheduled ONE frame, not one per cb
  });

  it("unsubscribe removes only that callback", () => {
    const t = new Ticker();
    const a = vi.fn();
    const b = vi.fn();
    const offA = t.add(a);
    t.add(b);
    offA();
    flush(1000);
    expect(a).not.toHaveBeenCalled();
    expect(b).toHaveBeenCalledOnce();
  });

  it("stops the loop when the last subscriber leaves", () => {
    const t = new Ticker();
    const off = t.add(() => {});
    off();
    expect(t.running).toBe(false);
    flush(1000);
    expect(pending).toHaveLength(0); // nothing reschedules
  });

  it("keeps running while any subscriber remains", () => {
    const t = new Ticker();
    const off1 = t.add(() => {});
    t.add(() => {});
    off1();
    expect(t.running).toBe(true);
    flush(1000);
    expect(pending).toHaveLength(1);
  });

  it("lets a callback unsubscribe itself mid-tick without breaking iteration", () => {
    const t = new Ticker();
    const b = vi.fn();
    let off: () => void = () => {};
    const a = vi.fn(() => off());
    off = t.add(a);
    t.add(b);
    flush(1000);
    expect(a).toHaveBeenCalledOnce();
    expect(b).toHaveBeenCalledOnce(); // b still ran despite a removing itself
    flush(1016);
    expect(a).toHaveBeenCalledOnce(); // a gone
    expect(b).toHaveBeenCalledTimes(2);
  });
});
