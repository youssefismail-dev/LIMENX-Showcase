// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
"use client";

import Lenis from "lenis";
import { useEffect } from "react";

import { ticker } from "./ticker";
import { useScrollStore } from "./store";

/**
 * Enables Lenis smooth scrolling, driven by the SHARED ticker (`autoRaf:false`)
 * so Lenis does not spin up its own rAF loop — the whole app animates on one
 * frame callback. Publishes scroll progress/offset/velocity into the zustand
 * store for the 3D scene and scroll-linked UI.
 *
 * Respects `prefers-reduced-motion`: no smoothing, no rAF loop; native scroll
 * is used and the store simply stays at its defaults (the scene falls back to a
 * static render). The app is fully functional without this provider.
 */
export function SmoothScrollProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const lenis = new Lenis({ autoRaf: false });
    const publish = useScrollStore.getState().set;

    lenis.on("scroll", (instance: Lenis) => {
      publish({
        progress: instance.progress ?? 0,
        scrollY: instance.animatedScroll ?? 0,
        velocity: instance.velocity ?? 0,
      });
    });

    // In-page anchor links (nav / CTA) glide via Lenis instead of jumping.
    const onAnchorClick = (event: MouseEvent) => {
      const anchor = (event.target as HTMLElement | null)?.closest?.(
        'a[href^="#"]',
      );
      const href = anchor?.getAttribute("href");
      if (href && href.length > 1) {
        event.preventDefault();
        lenis.scrollTo(href);
      }
    };
    document.addEventListener("click", onAnchorClick);

    const unsubscribe = ticker.add((time) => lenis.raf(time));

    return () => {
      document.removeEventListener("click", onAnchorClick);
      unsubscribe();
      lenis.destroy();
    };
  }, []);

  return <>{children}</>;
}
