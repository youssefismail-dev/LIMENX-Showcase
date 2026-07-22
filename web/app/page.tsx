// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
import { Contact } from "@/components/contact";
import { FeatureCards } from "@/components/features/feature-cards";
import { Scanner } from "@/components/scanner/scanner";

/**
 * V1 page. The fixed Spline hero (in the layout) floats behind and the content
 * scrolls over it: Hero (title + tagline + CTA) -> Features -> Scanner ->
 * Contact. Section ids power the nav + CTA smooth-scroll (via Lenis).
 */
export default function Home() {
  return (
    <main className="flex flex-col">
      <section
        id="hero"
        className="flex min-h-screen flex-col items-center gap-5 px-6 pt-[13vh] text-center"
      >
        <h1 className="font-mono text-6xl font-semibold tracking-tighter text-neutral-100 sm:text-7xl">
          LIMEN<span className="text-[#FFA63C]">X</span>
        </h1>
        <p className="text-lg text-neutral-300 sm:text-xl">
          Know before you click.
        </p>
        <p className="max-w-md text-sm leading-relaxed text-neutral-200">
          AI phishing detection that reads any URL — instant, offline, and
          explained.
        </p>
        <a
          href="#scanner"
          className="mt-2 rounded-lg bg-[#FFA63C] px-6 py-3 font-medium text-black transition-colors hover:bg-[#ffb75e]"
        >
          Scan a URL
        </a>
      </section>

      <section
        id="features"
        className="flex min-h-screen items-center justify-center px-6"
      >
        <FeatureCards />
      </section>

      <section
        id="scanner"
        className="flex min-h-screen items-center justify-center px-6"
      >
        <Scanner />
      </section>

      <section
        id="contact"
        className="flex min-h-screen items-center justify-center px-6"
      >
        <Contact />
      </section>
    </main>
  );
}
