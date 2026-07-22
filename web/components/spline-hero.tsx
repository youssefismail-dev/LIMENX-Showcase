// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef } from "react";

import { computeVideoOpacity } from "@/lib/hero/fade";
import { useScrollStore } from "@/lib/scroll/store";

// Spline is client-only (WebGL) — dynamic import with ssr:false so it never
// runs on the server or blocks first paint.
const Spline = dynamic(() => import("@splinetool/react-spline"), { ssr: false });

//: The hosted Spline scene (the "god particle"). Loaded from Spline's CDN at
//: runtime — needs internet (V1 trade-off; exportable to self-host later).
const SCENE = "https://prod.spline.design/7CSO-rSHTR3Eu2sV/scene.splinecode";

/**
 * The V1 hero object: a hosted Spline 3D scene, treated exactly like the
 * reference flow — a FIXED, centred object that stays put while the page
 * content scrolls over it, fading out only near the Contact section.
 * Decorative and non-interactive.
 */
export function SplineHero() {
  const layer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const apply = (progress: number) => {
      if (layer.current) {
        layer.current.style.opacity = String(computeVideoOpacity(progress));
      }
    };
    apply(useScrollStore.getState().progress);
    return useScrollStore.subscribe((state) => apply(state.progress));
  }, []);

  return (
    <div
      ref={layer}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10"
    >
      <Spline scene={SCENE} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}
