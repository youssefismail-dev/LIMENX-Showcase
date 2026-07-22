# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
models/views.py

The input-representation seam: which VIEW of the composite input frame
does a model consume?

Tree models (RandomForest, CatBoost) consume the engineered tabular
feature vector; sequence models (CNN, Transformer) consume the raw URL
string. Before this seam existed the ensemble passed the SAME DataFrame
to every member, so a mixed-representation ensemble could not be
expressed at all.

The contract mirrors `supports_feature_importance`: each model declares
its requirement as a class-level capability (`required_view`), and the
consumer (the ensemble) selects that view from a composite frame that
carries the raw `url` column and/or the engineered feature columns.
The decision belongs to the model, never to the ensemble.

Unlike `supports_feature_importance` (abstract, no default -- a wrong
default would silently corrupt Feature Selection), `required_view`
defaults to TABULAR on BaseModel: every model written before this seam
is tabular, and a sequence model that forgets to override the default
fails LOUDLY at its first prediction (a 63-column numeric frame is not
a URL sequence), so the default cannot cause silently wrong behaviour.
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd

# The three representation views a model can require.
TABULAR = "tabular"      # engineered numeric feature columns
URL = "url"              # the raw `url` string column
COMPOSITE = "composite"  # the whole frame, unsliced (an ensemble of
                         # mixed members needs every view its members do)

VALID_VIEWS = (TABULAR, URL, COMPOSITE)

URL_COLUMN = "url"


class ViewError(ValueError):
    """The requested view cannot be produced from the given frame.

    Deliberately NOT treated as a member fault by ensemble fault
    isolation: a missing view is a caller-side input-contract violation
    (every call would fail identically), and silently dropping the
    member would mask a serving misconfiguration.
    """


def select_view(
    X: pd.DataFrame,
    view: str,
    tabular_columns: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """
    Returns the slice of `X` matching `view`.

    - TABULAR: `X[tabular_columns]` when the caller knows the engineered
      feature set; with `tabular_columns=None` the frame passes through
      unchanged -- exactly the pre-seam behaviour, so every existing
      caller (which already passes a purely tabular frame) is unaffected.
    - URL: the raw `url` column as a single-column frame.
    - COMPOSITE: `X` unchanged (the member slices for itself).

    Raises
    ------
    ViewError
        If `view` is unknown, or the frame lacks the columns the view
        requires -- invalid input never passes silently.
    """
    if view == COMPOSITE:
        return X

    if view == URL:
        if URL_COLUMN not in X.columns:
            raise ViewError(
                f"the '{URL}' view requires a '{URL_COLUMN}' column, but the "
                f"input frame does not carry one (columns: "
                f"{list(X.columns)[:8]}{'...' if len(X.columns) > 8 else ''})."
            )
        return X[[URL_COLUMN]]

    if view == TABULAR:
        if tabular_columns is None:
            return X
        missing = [c for c in tabular_columns if c not in X.columns]
        if missing:
            raise ViewError(
                f"the '{TABULAR}' view requires {len(tabular_columns)} feature "
                f"columns but {len(missing)} are missing from the input frame "
                f"(first missing: {missing[:5]})."
            )
        return X[list(tabular_columns)]

    raise ViewError(
        f"unknown representation view '{view}' -- expected one of {VALID_VIEWS}."
    )
