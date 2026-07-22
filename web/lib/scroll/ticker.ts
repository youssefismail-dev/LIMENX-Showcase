// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
export type FrameCallback = (time: number, deltaMs: number) => void;

/**
 * A single requestAnimationFrame loop shared by every animated subscriber
 * (Lenis smooth-scroll, the R3F scene, scroll-progress updates).
 *
 * Why one loop and not one per feature: two competing rAF loops let the WebGL
 * scene drift a sub-frame against the DOM, which reads as the hero "swimming"
 * against the type. Everything that needs a frame subscribes here, so the
 * canvas, Lenis, and scroll all update on the exact same tick.
 *
 * Lifecycle: the loop starts on the first subscriber and stops on the last —
 * no wasted frames when nothing is animating (and nothing runs during SSR,
 * since `requestAnimationFrame` is only ever called from `add`).
 */
export class Ticker {
  private callbacks = new Set<FrameCallback>();
  private frame: number | null = null;
  private last: number | null = null;

  /** Subscribe to the frame loop. Returns an unsubscribe function. */
  add(cb: FrameCallback): () => void {
    this.callbacks.add(cb);
    this.ensureRunning();
    return () => this.remove(cb);
  }

  /** Unsubscribe; stops the loop when the last subscriber leaves. */
  remove(cb: FrameCallback): void {
    this.callbacks.delete(cb);
    if (this.callbacks.size === 0) this.stop();
  }

  get size(): number {
    return this.callbacks.size;
  }

  get running(): boolean {
    return this.frame !== null;
  }

  private ensureRunning(): void {
    if (this.frame !== null) return;
    this.last = null; // first tick reports delta 0, never a huge cross-clock jump
    this.frame = requestAnimationFrame(this.tick);
  }

  private stop(): void {
    if (this.frame === null) return;
    cancelAnimationFrame(this.frame);
    this.frame = null;
    this.last = null;
  }

  private tick = (time: number): void => {
    const delta = this.last === null ? 0 : time - this.last;
    this.last = time;
    // Snapshot so a callback may unsubscribe (or subscribe) mid-tick safely.
    for (const cb of Array.from(this.callbacks)) cb(time, delta);
    // Reschedule exactly ONE frame while subscribers remain (never one per cb).
    this.frame = this.callbacks.size > 0 ? requestAnimationFrame(this.tick) : null;
  };
}

/** Process-wide shared ticker for the app. */
export const ticker = new Ticker();
