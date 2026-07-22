// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Minimal fixed top navigation. In-page anchor links smooth-scroll via Lenis
 * (handled globally in the SmoothScrollProvider). Kept intentionally sparse —
 * wordmark + two links — consistent with the premium, minimal LIMENX identity.
 */
export function Nav() {
  return (
    <nav className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-6 py-4 sm:px-8">
      <a
        href="#hero"
        className="font-mono text-lg font-semibold tracking-tight text-neutral-100"
      >
        LIMEN<span className="text-[#FFA63C]">X</span>
      </a>
      <div className="flex items-center gap-6 font-mono text-sm text-neutral-300">
        <a href="#features" className="transition-colors hover:text-neutral-50">
          How it works
        </a>
        <a href="#scanner" className="transition-colors hover:text-neutral-50">
          Scan
        </a>
        <a href="#contact" className="transition-colors hover:text-neutral-50">
          Contact
        </a>
      </div>
    </nav>
  );
}
