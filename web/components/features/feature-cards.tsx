// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
/**
 * The three frosted-glass feature cards that scroll over the Spline hero
 * (translucent + backdrop-blur, so the 3D glows through them). Premium and
 * minimal, consistent with the LIMENX identity.
 */

const MODELS = [
  "Random Forest",
  "CatBoost",
  "Character CNN",
  "Character Transformer",
];

const TRUST = [
  "Explainable — every verdict comes with its reasons",
  "Offline — we never open the link",
  "No black box — you see how the models voted",
  "Human-confirmed",
];

function Card({
  index,
  title,
  glow,
  children,
}: {
  index: string;
  title: string;
  glow: string;
  children: React.ReactNode;
}) {
  return (
    <article
      className="glow-card rounded-2xl border border-white/10 bg-white/[0.04] p-7 backdrop-blur-2xl"
      style={{ "--glow-color": glow } as React.CSSProperties}
    >
      <span className="font-mono text-xs tracking-[0.2em] text-[#FFA63C]/80">
        {index}
      </span>
      <h3 className="mt-3 text-xl font-semibold text-neutral-50">{title}</h3>
      <div className="mt-3 text-sm leading-relaxed text-neutral-400">
        {children}
      </div>
    </article>
  );
}

export function FeatureCards() {
  return (
    <div className="mx-auto grid w-full max-w-5xl gap-5 md:grid-cols-3">
      <Card index="01" title="What is LIMENX?" glow="#F87171">
        An AI that reads any URL and tells you whether it&apos;s a phishing trap —
        instantly, offline, and explained.
      </Card>

      <Card index="02" title="How it works" glow="#FFA63C">
        <p>A four-model ensemble votes on every URL:</p>
        <ul className="mt-3 space-y-1.5">
          {MODELS.map((model) => (
            <li key={model} className="flex items-center gap-2 text-neutral-300">
              <span
                className="h-1.5 w-1.5 rounded-full bg-[#FFA63C]/80"
                aria-hidden
              />
              {model}
            </li>
          ))}
        </ul>
      </Card>

      <Card index="03" title="Why you can trust it" glow="#A78BFA">
        <ul className="space-y-1.5">
          {TRUST.map((point) => (
            <li key={point} className="flex gap-2 text-neutral-300">
              <span className="text-[#FFA63C]/80" aria-hidden>
                ✓
              </span>
              {point}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
