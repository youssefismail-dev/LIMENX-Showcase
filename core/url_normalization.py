# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
core/url_normalization.py

THE URL normalization applied before validation, feature extraction, and
sequence encoding — the single source of truth shared by the TRAINING
pipeline (data_pipeline/sanitizer.py) and the SERVING path
(serving/scorer.py).

Why one function matters (docs/SERVING_PATH_DESIGN.md §2): the frozen
models were trained on URLs that received EXACTLY this transformation.
If serving normalized differently — more, less, or subtly otherwise —
the frozen models would see inputs from a distribution they never
trained on and degrade SILENTLY (train/serve skew). Sharing the literal
code path makes skew impossible by construction, not by discipline.

Why so minimal (deliberate, twice over):
1. Consistency: this is precisely what DataSanitizer did to the training
   corpus — strip surrounding whitespace, then default a missing scheme.
   Nothing more. (Inspected, not assumed: no lowercasing, no percent-
   decoding, no punycode, no path canonicalization ever ran in training.)
2. Security: obfuscation is SIGNAL for a phishing detector. Percent-
   encoding tricks, mixed case, dword IPs, weird paths — features exist
   to detect exactly these. Aggressive canonicalization would erase the
   evidence (see validation/url_validator.py's dword-IP rationale).
"""

from __future__ import annotations

#: Scheme prefixes the training sanitizer accepted as "already has a
#: scheme" (checked case-insensitively, exactly as in training).
SCHEME_PREFIXES = ("http://", "https://", "ftp://", "//")

#: Scheme prepended when none is present ('google.com' -> 'http://google.com'),
#: matching DataSanitizer's default.
DEFAULT_SCHEME = "http"


def normalize_url(raw: str, default_scheme: str = DEFAULT_SCHEME) -> str:
    """
    Normalizes a raw URL string exactly as the training pipeline did:
    strip surrounding whitespace; prepend `default_scheme://` iff the
    string does not already start (case-insensitively) with a known
    scheme prefix. Deterministic and idempotent.

    Returns the normalized string. An empty/whitespace-only input
    normalizes to the empty string — rejection is the URLValidator's
    job, not this function's (single responsibility).

    Raises
    ------
    TypeError
        If `raw` is not a string (never coerce silently).
    """
    if not isinstance(raw, str):
        raise TypeError(f"normalize_url expects str, got {type(raw).__name__}.")
    url = raw.strip()
    if not url:
        return ""
    if not url.lower().startswith(SCHEME_PREFIXES):
        url = f"{default_scheme}://{url}"
    return url
