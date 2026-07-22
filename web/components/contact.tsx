// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * Contact section — a short confident headline + one premium frosted-glass card
 * holding only the four links. Same animated glow border as the feature cards,
 * but GREEN and 2x faster (via --glow-speed), unique to this card.
 *
 * Deliberately no brand icons: text labels + a subtle ↗ keep it minimal and
 * consistent — icons would add visual noise without adding premium feel.
 *
 */
const LINKS = [
  { label: "GitHub", href: "https://github.com/youssefismail-dev" },
  { label: "Email", href: "mailto:youssefismail396@gmail.com" },
  { label: "X", href: "https://x.com/YoussefIsmail39" },
  { label: "Kaggle", href: "https://www.kaggle.com/youssefismail396" },
];

export function Contact() {
  return (
    <div className="w-full max-w-md">
      <h2 className="text-center text-3xl font-semibold text-neutral-50">
        Let&apos;s talk.
      </h2>
      <p className="mt-3 text-center text-sm text-neutral-400">
        Always open to ideas, feedback, and collaboration.
      </p>

      <div
        className="glow-card mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-2 backdrop-blur-2xl"
        style={
          { "--glow-color": "#4ADE80", "--glow-speed": "3.5s" } as React.CSSProperties
        }
      >
        <ul>
          {LINKS.map((link) => (
            <li key={link.label}>
              <a
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center justify-between rounded-xl px-5 py-4 text-neutral-200 transition-colors hover:bg-white/[0.04]"
              >
                <span className="font-medium">{link.label}</span>
                <span
                  aria-hidden
                  className="text-neutral-500 transition-all group-hover:translate-x-0.5 group-hover:text-neutral-200"
                >
                  ↗
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
