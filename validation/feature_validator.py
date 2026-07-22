# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
validation/feature_validator.py

The Feature Validation stage of the pipeline (docs/Project_Context.md):
every extracted feature matrix must pass through here before it reaches
Feature Selection or any model. Invalid feature vectors must never reach
the models -- violations raise an explicit FeatureValidationError rather
than silently passing.

Checks implemented: exact schema (names + order + count), numeric dtypes,
no NaN, no Inf, and optional per-feature value ranges.

Deliberately NOT owned here:
- The schema itself. The validator is *configured* with the expected
  column list (e.g. URLExtractor.feature_names()); it does not import the
  extractor. This keeps the layer generic and loosely coupled -- when the
  feature registry lands (post-Feature-Selection refactor), the registry
  becomes the schema/range provider with no changes to this module.
- Schema *version* compatibility. Meaningful only once trained artifacts
  are persisted alongside a schema version (models/ + training/ phases);
  adding it before any artifact exists would be speculative API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd


class FeatureValidationError(ValueError):
    """Raised when a feature matrix violates the expected schema.

    The message enumerates *every* violation found, not just the first,
    so one failed run yields a complete diagnosis.
    """


def conventional_ranges(columns: Sequence[str]) -> Dict[str, Tuple[float, float]]:
    """
    Derives (min, max) bounds from the catalog's naming conventions:
    `has_*` / `is_*` features are binary -> [0, 1]; `*_ratio` / `ratio_*`
    features are proportions -> [0, 1]. Columns matching neither
    convention receive no bound.

    Interim helper until the feature registry provides authoritative
    per-feature metadata (see docs/FEATURE_CATALOG.md); bounds are
    intervals, so it cannot distinguish a binary 1 from a 0.7 -- the
    registry's dtype metadata will tighten that later.
    """
    ranges: Dict[str, Tuple[float, float]] = {}
    for name in columns:
        if name.startswith(("has_", "is_")) or name.endswith("_ratio") or name.startswith("ratio_"):
            ranges[name] = (0.0, 1.0)
    return ranges


@dataclass(frozen=True)
class FeatureValidator:
    """
    Validates a feature matrix against an expected schema.

    Parameters
    ----------
    expected_columns : Sequence[str]
        The exact, ordered column names the matrix must have
        (e.g. URLExtractor.feature_names(), with or without the
        trailing sentinel depending on the pipeline stage).
    ranges : Mapping[str, Tuple[float, float]], optional
        Per-column inclusive (min, max) bounds. Columns absent from the
        mapping are not range-checked. See `conventional_ranges`.
    """

    expected_columns: Tuple[str, ...]
    ranges: Mapping[str, Tuple[float, float]] = field(default_factory=dict)

    def __init__(
        self,
        expected_columns: Sequence[str],
        ranges: Mapping[str, Tuple[float, float]] | None = None,
    ) -> None:
        object.__setattr__(self, "expected_columns", tuple(expected_columns))
        object.__setattr__(self, "ranges", dict(ranges) if ranges else {})
        if not self.expected_columns:
            raise ValueError("expected_columns must not be empty.")

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def validate(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Checks `X` against the configured schema and returns it unchanged
        on success (enabling `validator.validate(extract(url))` chaining).

        Raises
        ------
        FeatureValidationError
            Listing every violation found: wrong type, empty input,
            schema mismatch (missing/unexpected/misordered columns),
            non-numeric dtypes, NaN, Inf, or out-of-range values.
        """
        if not isinstance(X, pd.DataFrame):
            raise FeatureValidationError(
                f"Expected a pandas DataFrame, got {type(X).__name__}."
            )

        violations: List[str] = []

        if len(X) == 0:
            violations.append("Feature matrix is empty (0 rows).")

        violations += self._check_schema(X)

        # Value-level checks only make sense for columns that exist and
        # are numeric; schema errors above already cover the rest.
        checkable = [c for c in self.expected_columns if c in X.columns]
        violations += self._check_dtypes(X, checkable)
        numeric = [c for c in checkable if pd.api.types.is_numeric_dtype(X[c])]
        violations += self._check_finiteness(X, numeric)
        violations += self._check_ranges(X, numeric)

        if violations:
            raise FeatureValidationError(
                f"Feature validation failed with {len(violations)} violation(s):\n- "
                + "\n- ".join(violations)
            )
        return X

    # ------------------------------------------------------------------ #
    # Individual checks                                                   #
    # ------------------------------------------------------------------ #

    def _check_schema(self, X: pd.DataFrame) -> List[str]:
        """Exact column names, count, and order."""
        actual = list(X.columns)
        expected = list(self.expected_columns)
        if actual == expected:
            return []

        violations: List[str] = []
        missing = [c for c in expected if c not in actual]
        unexpected = [c for c in actual if c not in expected]
        if missing:
            violations.append(f"Missing column(s): {missing}.")
        if unexpected:
            violations.append(f"Unexpected column(s): {unexpected}.")
        if len(actual) != len(expected):
            violations.append(
                f"Expected {len(expected)} columns, got {len(actual)}."
            )
        if not missing and not unexpected:
            violations.append(
                "Columns are correct but out of order; feature order is part "
                "of the schema contract."
            )
        return violations

    @staticmethod
    def _check_dtypes(X: pd.DataFrame, columns: Sequence[str]) -> List[str]:
        """Every feature column must be numeric."""
        bad = [
            f"{c} (dtype={X[c].dtype})"
            for c in columns
            if not pd.api.types.is_numeric_dtype(X[c])
        ]
        return [f"Non-numeric column(s): {bad}."] if bad else []

    @staticmethod
    def _check_finiteness(X: pd.DataFrame, columns: Sequence[str]) -> List[str]:
        """No NaN and no +/-Inf anywhere in the matrix."""
        violations: List[str] = []
        nan_cols = [c for c in columns if X[c].isna().any()]
        if nan_cols:
            violations.append(f"NaN values in column(s): {nan_cols}.")
        inf_cols = [c for c in columns if np.isinf(X[c].to_numpy(dtype=float, na_value=0.0)).any()]
        if inf_cols:
            violations.append(f"Inf values in column(s): {inf_cols}.")
        return violations

    def _check_ranges(self, X: pd.DataFrame, columns: Sequence[str]) -> List[str]:
        """Optional inclusive (min, max) bounds per column."""
        violations: List[str] = []
        for c in columns:
            if c not in self.ranges:
                continue
            lo, hi = self.ranges[c]
            values = X[c].dropna()
            if len(values) == 0:
                continue
            v_min, v_max = float(values.min()), float(values.max())
            if v_min < lo or v_max > hi:
                violations.append(
                    f"Column '{c}' outside [{lo}, {hi}] "
                    f"(observed min={v_min}, max={v_max})."
                )
        return violations
