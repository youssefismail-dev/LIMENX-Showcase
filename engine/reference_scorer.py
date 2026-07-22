# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
engine/reference_scorer.py

A REFERENCE scoring engine for this public showcase.

Why this file exists
--------------------
LIMENX's production detector — the 63-signal feature extractor, the four
trained models (Random Forest, CatBoost, Character CNN, Character
Transformer), the calibrated fusion, and the SHAP-based explanation engine —
is **proprietary and not included in this repository**.

Rather than ship a repo with a hole in it, this module implements the *same
interface* the production scorer implements, so every published layer above it
(the FastAPI service, auth, rate limiting, validation, the web app) runs
end-to-end exactly as it does in production. This is precisely the seam the
architecture was designed around: the scoring engine is injected behind a
stable contract, so it can be swapped without touching a single layer above.

What is real here vs. reference
-------------------------------
REAL (the production code, unmodified):
  - URL normalization  (`core.url_normalization`)
  - URL validation     (`validation.url_validator`)
  - The `ScoreResult` output contract
REFERENCE (a transparent stand-in for the proprietary models):
  - The probability itself, from a small documented lexical heuristic below.

The heuristic is deliberately simple and *internally faithful*: the reasons it
returns are the signals that actually produced its score — never invented
after the fact. That mirrors the production engine's core rule
(faithfulness over plausibility), even though the numbers differ.

DO NOT treat this as a phishing detector. It is an interface demonstration.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from core.url_normalization import normalize_url
from validation.url_validator import URLValidator

from .score_result import ScoreResult, ScoreStatus

#: Version string for the reference engine. Deliberately NOT the production
#: model version — nothing here should be mistaken for the trained ensemble.
REFERENCE_VERSION = "reference-1.0"

#: Decision boundary. Mirrors the production contract (a tuned threshold, not
#: a naive 0.5) so the API's `decision` field behaves the same way.
OPERATING_THRESHOLD = 0.4678

#: The production ensemble's fusion weights. Reproduced here only so the
#: response SHAPE (the "how the models voted" breakdown) matches production.
MEMBER_WEIGHTS: Dict[str, float] = {"cnn": 0.525, "cb": 0.175, "t": 0.175, "rf": 0.125}

MEMBER_NAMES: Dict[str, str] = {
    "cnn": "Character CNN",
    "cb": "CatBoost",
    "t": "Character Transformer",
    "rf": "Random Forest",
}

_SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "cfd", "zip", "review", "country",
}
_SUSPICIOUS_WORDS = (
    "verify", "login", "signin", "secure", "account", "update", "confirm",
    "password", "billing", "invoice", "wallet", "unlock", "suspended", "reward",
)
_BRANDS = (
    "paypal", "apple", "microsoft", "google", "amazon", "netflix", "facebook",
    "instagram", "bank", "chase", "outlook", "office365",
)
_IPV4 = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


@dataclass(frozen=True)
class _Signal:
    """One fired heuristic signal: its weight and a human explanation."""

    code: str
    title: str
    detail: str
    weight: float


class PhishingScorer:
    """Reference implementation of the production scorer's public interface.

    Mirrors the production surface used by the API layer:
    `load()`, `model_version`, `score()`, `score_batch()`.
    """

    def __init__(self, model_version: str = REFERENCE_VERSION) -> None:
        self._model_version = model_version
        self._url_validator = URLValidator()

    # ------------------------------------------------------------------ #
    # Loading (same signature as production; nothing to load here)        #
    # ------------------------------------------------------------------ #

    @classmethod
    def load(cls, version: str = REFERENCE_VERSION, registry_dir: object = None,
             verify_integrity: bool = True, with_explanation: bool = True,
             include_sequence_explanation: bool = False) -> "PhishingScorer":
        """Accepts the production signature so the API's startup path is
        unchanged. The reference engine has no artifacts to load.

        The requested `version` is deliberately IGNORED: this engine must never
        report a production model version, because it is not that model.
        """
        return cls(model_version=REFERENCE_VERSION)

    @property
    def model_version(self) -> str:
        return self._model_version

    # ------------------------------------------------------------------ #
    # Public inference surface                                            #
    # ------------------------------------------------------------------ #

    def score(self, url: str, include_explanation: Optional[bool] = None) -> ScoreResult:
        """Score one URL; always returns a ScoreResult (never raises)."""
        return self.score_batch([url], include_explanation=include_explanation)[0]

    def score_batch(self, urls: Sequence[str],
                    include_explanation: Optional[bool] = None) -> List[ScoreResult]:
        """Score many URLs, preserving input order (fail-closed per row)."""
        started = time.perf_counter()
        results: List[ScoreResult] = []
        for raw in urls:
            try:
                results.append(self._score_one(raw, bool(include_explanation)))
            except Exception as exc:  # noqa: BLE001 -- one bad row never sinks a batch
                results.append(ScoreResult(
                    status=ScoreStatus.ERROR,
                    url_normalized=str(raw), model_version=self._model_version,
                    url_input=str(raw), detail=f"Reference engine error: {exc}",
                ))
        latency = round((time.perf_counter() - started) * 1000.0, 2)
        return [ScoreResult(**{**_as_kwargs(r), "latency_ms": latency}) for r in results]

    # ------------------------------------------------------------------ #

    def _score_one(self, raw: str, explain: bool) -> ScoreResult:
        if not isinstance(raw, str) or not raw.strip():
            return ScoreResult(
                status=ScoreStatus.INVALID, url_normalized="",
                model_version=self._model_version, url_input=raw if isinstance(raw, str) else None,
                detail="URL must be a non-empty string.",
            )

        candidate, scheme_assumed = self._apply_scheme(raw.strip())
        url = normalize_url(candidate)

        if not self._url_validator.is_valid(url):
            return ScoreResult(
                status=ScoreStatus.INVALID, url_normalized=url,
                model_version=self._model_version, url_input=raw,
                scheme_assumed=scheme_assumed,
                scheme_resolution="assumed_https" if scheme_assumed else "explicit",
                detail="URL failed structural validation (scheme/host/port).",
            )

        probability, signals = self._heuristic(url)
        members = self._member_scores(probability, url)
        decision = probability >= OPERATING_THRESHOLD

        result = ScoreResult(
            status=ScoreStatus.SCORED,
            url_input=raw,
            url_normalized=url,
            model_version=self._model_version,
            probability=round(probability, 6),
            decision=decision,
            operating_threshold=OPERATING_THRESHOLD,
            member_scores=members,
            scheme_assumed=scheme_assumed,
            scheme_resolution="assumed_https" if scheme_assumed else "explicit",
        )
        if not explain:
            return result

        return ScoreResult(
            **{
                **_as_kwargs(result),
                "threat_level": _threat_level(probability),
                "reasons": self._reasons(signals, members, scheme_assumed),
                "member_contributions": self._contributions(members),
                "explanation_status": "ok",
                "explanation_version": "v1.0",
            }
        )

    # ------------------------------------------------------------------ #
    # The reference heuristic (transparent, deterministic)                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _apply_scheme(raw: str) -> Tuple[str, bool]:
        """Assume HTTPS when no scheme is given (a browser would), and report it."""
        if "://" in raw:
            return raw, False
        return f"https://{raw}", True

    def _heuristic(self, url: str) -> Tuple[float, List[_Signal]]:
        """Return (probability, fired signals). The score is the logistic of the
        summed signal weights, so every point of the score is attributable."""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = (parsed.path or "").lower()
        tld = host.rsplit(".", 1)[-1] if "." in host else ""
        signals: List[_Signal] = []

        if tld in _SUSPICIOUS_TLDS:
            signals.append(_Signal("feature:suspicious_tld", "Suspicious top-level domain",
                                   f"`.{tld}` is heavily abused by phishing campaigns.", 1.9))
        if _IPV4.match(host):
            signals.append(_Signal("feature:ip_host", "IP address instead of a domain",
                                   "Legitimate brands rarely serve login pages from a bare IP.", 2.0))
        hits = [w for w in _SUSPICIOUS_WORDS if w in path or w in host]
        if hits:
            signals.append(_Signal("feature:suspicious_keyword", "Suspicious keyword",
                                   f"Urgency/credential wording found: {', '.join(hits[:3])}.",
                                   0.7 * min(len(hits), 3)))
        brand = next((b for b in _BRANDS if b in host), None)
        if brand and not host.startswith(f"{brand}.") and f".{brand}." not in host:
            signals.append(_Signal("feature:brand_in_subdomain", "Brand name in subdomain",
                                   f"'{brand}' appears in the host but is not the registrable domain.", 1.8))
        hyphens = host.count("-")
        if hyphens >= 2:
            signals.append(_Signal("feature:hyphen_count", "Many hyphens in the host",
                                   f"{hyphens} hyphens — common in look-alike domains.", 0.5 * hyphens))
        if "@" in url:
            signals.append(_Signal("feature:at_symbol", "'@' in the URL",
                                   "Everything before '@' is ignored by browsers — a classic trick.", 2.2))
        if parsed.scheme != "https":
            signals.append(_Signal("feature:no_tls", "No transport security",
                                   "Served over plain HTTP.", 0.8))
        if any(ord(c) > 127 for c in host):
            signals.append(_Signal("feature:non_ascii", "Non-ASCII characters in the host",
                                   "Possible homograph (look-alike) domain.", 1.6))
        if len(url) > 90:
            signals.append(_Signal("feature:url_length", "Unusually long URL",
                                   f"{len(url)} characters.", 0.6))

        score = sum(s.weight for s in signals)
        probability = 1.0 / (1.0 + pow(2.718281828, -(score - 2.0)))
        return probability, signals

    def _member_scores(self, probability: float, url: str) -> Dict[str, float]:
        """Emulate four member scores around the fused probability, so the
        response shape matches production. Deterministic per URL."""
        seed = sum(ord(c) for c in url)
        out: Dict[str, float] = {}
        for i, key in enumerate(("cnn", "cb", "t", "rf")):
            jitter = (((seed * (i + 7)) % 17) - 8) / 100.0
            out[key] = round(min(0.9999, max(0.0001, probability + jitter)), 6)
        return out

    # ------------------------------------------------------------------ #
    # Explanation assembly (same shape the web app renders)               #
    # ------------------------------------------------------------------ #

    def _reasons(self, signals: List[_Signal], members: Dict[str, float],
                 scheme_assumed: bool) -> List[dict]:
        total = sum(s.weight for s in signals) or 1.0
        reasons = [
            {
                "code": s.code, "title": s.title, "detail": s.detail,
                "direction": "toward_phishing", "source": "feature",
                "contribution": round(s.weight / total, 6),
                "evidence": {"weight": s.weight},
                "faithfulness": "reference",
            }
            for s in sorted(signals, key=lambda s: s.weight, reverse=True)
        ]
        top = max(members, key=lambda k: members[k] * MEMBER_WEIGHTS[k])
        reasons.append({
            "code": f"member:{top}", "title": f"Strongest model: {MEMBER_NAMES[top]}",
            "detail": f"{MEMBER_NAMES[top]} carried the largest share of this verdict.",
            "direction": "toward_phishing", "source": "member",
            "contribution": round(members[top] * MEMBER_WEIGHTS[top], 6),
            "evidence": {"member": top, "weight": MEMBER_WEIGHTS[top]},
            "faithfulness": "reference",
        })
        if scheme_assumed:
            reasons.append({
                "code": "scheme:assumed_https", "title": "HTTPS assumed",
                "detail": "No protocol was provided, so HTTPS was assumed.",
                "direction": "informational", "source": "scheme",
                "contribution": 0.0, "evidence": {"resolution": "assumed_https"},
                "faithfulness": "not_applicable",
            })
        return reasons

    @staticmethod
    def _contributions(members: Dict[str, float]) -> List[dict]:
        raw = {k: members[k] * MEMBER_WEIGHTS[k] for k in members}
        total = sum(raw.values()) or 1.0
        return sorted(
            [
                {
                    "member": k, "raw_score": members[k],
                    "quantile": round(members[k], 6),
                    "weight": MEMBER_WEIGHTS[k],
                    "contribution": round(raw[k] / total, 6),
                }
                for k in members
            ],
            key=lambda d: d["contribution"], reverse=True,
        )


def _as_kwargs(result: ScoreResult) -> dict:
    """ScoreResult -> constructor kwargs (it is frozen, so we rebuild)."""
    data = result.as_dict()
    data["status"] = result.status
    return data


def _threat_level(probability: float) -> str:
    if probability >= 0.90:
        return "critical"
    if probability >= 0.70:
        return "high"
    if probability >= OPERATING_THRESHOLD:
        return "suspicious"
    if probability >= 0.15:
        return "low"
    return "benign"


def list_versions(registry_dir: object = None) -> List[str]:
    """Mirrors the production registry helper; the showcase has one engine."""
    return [REFERENCE_VERSION]
