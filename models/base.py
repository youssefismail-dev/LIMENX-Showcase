# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
models/base.py

Common interface every concrete model (RandomForest, CatBoost, CNN,
Transformer) implements, so the Model Manager / ensemble layer can
treat all of them uniformly regardless of underlying framework.

`fit` / `predict_proba` are public template methods that handle the
cross-cutting concerns every model needs (fitted-state tracking,
output validation, threshold defaulting) and delegate the real work
to `_fit` / `_predict_proba` -- that's all a concrete subclass has
to implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
from numpy.typing import NDArray


class BaseModel(ABC):
    """Abstract contract for every model in the ensemble."""

    _is_fitted: bool = False
    _threshold: float = 0.5  # overwritten by the validation-set threshold search during training

    #: Capability declaration: which representation VIEW of the composite
    #: input frame this model's predict_proba consumes (see models/views.py:
    #: "tabular" = engineered feature columns, "url" = the raw URL string,
    #: "composite" = the whole frame). The ensemble selects each member's
    #: declared view -- the decision belongs to the model, never to the
    #: ensemble. Defaults to "tabular" (unlike `supports_feature_importance`,
    #: which has no default): every pre-seam model is tabular, and a
    #: sequence model that forgets to override fails loudly at its first
    #: prediction rather than misbehaving silently.
    required_view: str = "tabular"

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "BaseModel":
        """Trains the model, then marks it fitted. Returns self for chaining."""
        self._fit(X, y)
        self._is_fitted = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        P(phishing) for each row. Shape: (n_samples,).
        Guards against easy-to-hit mistakes: calling this before fit(),
        a concrete implementation returning the wrong number of rows, or
        returning values that aren't actually valid probabilities
        (NaN/Inf, or outside [0, 1] -- e.g. raw un-normalised logits).
        """
        if not self._is_fitted:
            raise RuntimeError(f"{self.name} has not been fitted yet -- call fit() first.")

        proba = np.asarray(self._predict_proba(X), dtype=float)

        if len(proba) != len(X):
            raise ValueError(
                f"{self.name}._predict_proba returned {len(proba)} rows "
                f"for {len(X)} input rows."
            )

        if not np.all(np.isfinite(proba)):
            raise ValueError(f"{self.name}._predict_proba returned NaN or Inf values.")

        if np.any((proba < 0) | (proba > 1)):
            raise ValueError(
                f"{self.name}._predict_proba returned values outside [0, 1] "
                f"(min={proba.min():.4f}, max={proba.max():.4f})."
            )

        return proba

    def predict(self, X: pd.DataFrame, threshold: Optional[float] = None) -> np.ndarray:
        """
        Binary prediction. If `threshold` is omitted, uses the model's
        own tuned threshold (self._threshold, set during training via
        the validation-set recall/precision search) instead of a
        hardcoded constant or an external config file.
        """
        t = self._threshold if threshold is None else threshold
        return (self.predict_proba(X) >= t).astype(int)

    @abstractmethod
    def _fit(self, X: pd.DataFrame, y: np.ndarray) -> None:
        """Concrete training logic."""
        raise NotImplementedError

    @abstractmethod
    def _predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Concrete prediction logic."""
        raise NotImplementedError

    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Persists the trained model (and its tuned threshold) to disk."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(cls, path: Union[str, Path]) -> "BaseModel":
        """Loads a trained model back from disk."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for logs/reports/ensemble output, e.g. 'random_forest'."""
        raise NotImplementedError

    @property
    @abstractmethod
    def supports_feature_importance(self) -> bool:
        """
        Capability declaration: True if this model consumes the engineered
        tabular feature vector, making it a meaningful participant in
        feature-importance scoring (Feature Selection asks the ModelManager
        for every model that declares this).

        Deliberately abstract with NO default: every model author must
        answer this explicitly. Tabular models (RandomForest, CatBoost)
        declare True; sequence models (CNN, Transformer over raw URL
        characters) declare False -- the decision belongs to the model,
        never to the Feature Selection pipeline.

        Concrete classes typically satisfy this with a plain class
        attribute (`supports_feature_importance = True`), which also makes
        the capability readable at class level, before instantiation.
        """
        raise NotImplementedError

    def shap_explainer(self) -> Optional[object]:
        """
        OPTIONAL capability: an efficient SHAP explainer for this model
        (e.g. TreeExplainer for tree ensembles), or None if the model has
        no efficient explainer. The ShapImportanceProvider queries this
        hook -- capability query, never an isinstance check -- and skips
        models that return None rather than falling back to the very
        expensive model-agnostic KernelExplainer.

        Typed as `object` on purpose: the model layer must not import
        shap at module level; implementations import it lazily inside
        the method.
        """
        return None

    def native_feature_importances(self) -> Optional[NDArray[np.float64]]:
        """
        OPTIONAL capability: the model's own built-in importance scores
        (e.g. impurity-based for tree ensembles), aligned with the column
        order of the training DataFrame.

        Default None = "not supported"; the NativeImportanceProvider then
        simply skips this model. Unlike `supports_feature_importance`
        (required, no default), an implicit default is safe here: a
        forgotten override loses an *advisory* score, it cannot cause
        wrong behaviour. Native importances are known-biased (impurity
        measures inflate high-cardinality features), so Feature Selection
        treats them as report-only evidence, never as an elimination gate.
        """
        return None

    # NOTE (deferred -- see TODO.md): `version` and `algorithm` properties
    # were proposed in review. Not added yet -- `algorithm` risks becoming
    # a second, driftable source of truth alongside `name`.