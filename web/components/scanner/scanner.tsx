// © 2026 Youssef Ismail. All rights reserved.
// LIMENX is proprietary software. Published for portfolio review only —
// not licensed for reuse, redistribution, or derivative works.
"use client";

import { useState } from "react";

import type { PredictResponse } from "@/lib/api/types";
import { MEMBER_NAMES, directionMark, riskStyle } from "@/lib/scan/risk";
import { useScan } from "@/lib/scan/use-scan";

/**
 * The LIMENX Scanner: a premium, minimal glass panel (lets the Spline hero glow
 * through) over the BFF `/api/scan`. Shows a faithful verdict — risk level,
 * risk score, ranked reasons, and how the four models voted.
 *
 * Safety rule: the scanned URL is ALWAYS rendered as plain text, never a link —
 * a phishing scanner must never make its input clickable.
 */
export function Scanner() {
  const { state, scan } = useScan();
  const [url, setUrl] = useState("");
  const loading = state.status === "loading";

  return (
    <div
      className="glow-card w-full max-w-2xl rounded-2xl border border-white/10 bg-white/[0.04] p-7 shadow-2xl shadow-black/50 backdrop-blur-2xl sm:p-10"
      style={{ "--glow-color": "#5B9BFF" } as React.CSSProperties}
    >
      <p className="text-xs tracking-[0.22em] text-neutral-400 uppercase">
        URL Scanner
      </p>
      <h2 className="mt-2 text-2xl font-semibold text-neutral-50">
        Scan a URL for phishing.
      </h2>

      <form
        className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={(e) => {
          e.preventDefault();
          scan(url);
        }}
      >
        <label className="flex-1">
          <span className="sr-only">URL to scan</span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            placeholder="example.com"
            className="w-full border-b border-white/15 bg-transparent py-2.5 font-mono text-base text-neutral-100 outline-none transition-colors placeholder:text-neutral-600 focus:border-[#FFA63C]"
          />
        </label>
        <button
          type="submit"
          disabled={loading || url.trim().length === 0}
          className="rounded-lg bg-[#FFA63C] px-5 py-2.5 font-medium text-black transition-colors hover:bg-[#ffb75e] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Scanning…" : "Scan"}
        </button>
      </form>

      <div className="mt-7">
        {state.status === "idle" && (
          <p className="font-mono text-sm text-neutral-500">
            Enter a URL — we never open it. Analysis is offline and explained.
          </p>
        )}
        {state.status === "loading" && (
          <p className="animate-pulse font-mono text-sm text-neutral-400">
            Analyzing…
          </p>
        )}
        {state.status === "failed" && (
          <p className="font-mono text-sm text-[#F87171]">
            {state.error.message}
          </p>
        )}
        {state.status === "result" && <Verdict result={state.result} />}
      </div>
    </div>
  );
}

function Verdict({ result }: { result: PredictResponse }) {
  if (result.status !== "scored") {
    // invalid / error / blocked-scheme
    const style = riskStyle(result.threat_level);
    return (
      <div className="space-y-3">
        <RiskBadge label={result.threat_level ? style.label : "Not scored"} color={style.color} />
        <p className="font-mono text-sm text-neutral-400">
          {result.detail ?? "This URL could not be scored."}
        </p>
        <ScannedUrl result={result} />
        {result.reasons && <Reasons reasons={result.reasons} />}
      </div>
    );
  }

  const style = riskStyle(result.threat_level);
  const score =
    result.probability != null ? `${(result.probability * 100).toFixed(1)}%` : "—";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <RiskBadge label={style.label} color={style.color} />
        <span className="font-mono text-sm text-neutral-400">
          risk score <span className="text-neutral-200">{score}</span>
        </span>
      </div>

      <ScannedUrl result={result} />
      {result.reasons && result.reasons.length > 0 && (
        <Reasons reasons={result.reasons} />
      )}
      {result.member_contributions && result.member_contributions.length > 0 && (
        <MemberVotes contributions={result.member_contributions} />
      )}
    </div>
  );
}

function RiskBadge({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium"
      style={{ borderColor: `${color}55`, color, backgroundColor: `${color}14` }}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden
      />
      {label}
    </span>
  );
}

/** The scanned URL — ALWAYS plain text, never a link. */
function ScannedUrl({ result }: { result: PredictResponse }) {
  return (
    <div className="space-y-1">
      <p className="text-xs tracking-wider text-neutral-500 uppercase">Scanned</p>
      <p className="font-mono text-sm break-all text-neutral-300">
        {result.url_normalized}
      </p>
      {result.scheme_assumed && (
        <p className="font-mono text-xs text-neutral-500">
          No protocol provided — HTTPS assumed.
        </p>
      )}
    </div>
  );
}

function Reasons({ reasons }: { reasons: Array<Record<string, unknown>> }) {
  return (
    <ul className="space-y-2 border-t border-white/10 pt-4">
      {reasons.slice(0, 6).map((reason, i) => {
        const mark = directionMark(String(reason.direction ?? ""));
        return (
          <li key={i} className="flex gap-2.5 text-sm">
            <span style={{ color: mark.color }} aria-hidden>
              {mark.symbol}
            </span>
            <span className="text-neutral-300">
              {String(reason.title ?? reason.detail ?? "")}
              {reason.faithfulness === "advisory" && (
                <span className="ml-2 text-xs text-neutral-500">(advisory)</span>
              )}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function MemberVotes({
  contributions,
}: {
  contributions: Array<Record<string, unknown>>;
}) {
  const total =
    contributions.reduce((s, c) => s + Math.abs(Number(c.contribution) || 0), 0) || 1;
  return (
    <div className="space-y-2 border-t border-white/10 pt-4">
      <p className="text-xs tracking-wider text-neutral-500 uppercase">
        How the models voted
      </p>
      {contributions.map((c, i) => {
        const share = (Math.abs(Number(c.contribution) || 0) / total) * 100;
        return (
          <div key={i} className="flex items-center gap-3 text-xs">
            <span className="w-36 shrink-0 text-neutral-400">
              {MEMBER_NAMES[String(c.member)] ?? String(c.member)}
            </span>
            <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
              <span
                className="block h-full rounded-full bg-[#FFA63C]/70"
                style={{ width: `${share}%` }}
              />
            </span>
            <span className="w-9 text-right text-neutral-500">
              {share.toFixed(0)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
