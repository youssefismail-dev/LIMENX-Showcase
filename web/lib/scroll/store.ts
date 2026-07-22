// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { create } from "zustand";

/**
 * Shared scroll state, published by Lenis and consumed by the 3D scene and any
 * scroll-linked UI. `progress` is the spine of the whole experience: it drives
 * the neural network's journey across the sections (hero -> features ->
 * scanner -> contact).
 */
export interface ScrollState {
  /** Document scroll progress in [0, 1]. */
  progress: number;
  /** Smoothed (animated) scroll offset, in px. */
  scrollY: number;
  /** Signed scroll velocity. */
  velocity: number;
  set: (
    partial: Partial<Pick<ScrollState, "progress" | "scrollY" | "velocity">>,
  ) => void;
}

export const useScrollStore = create<ScrollState>((set) => ({
  progress: 0,
  scrollY: 0,
  velocity: 0,
  set: (partial) => set(partial),
}));
