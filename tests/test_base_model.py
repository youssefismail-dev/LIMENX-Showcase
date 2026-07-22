# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""tests/test_base_model.py -- sanity checks for the BaseModel contract."""

import numpy as np
import pandas as pd
import pytest

from models.base import BaseModel


class _DummyModel(BaseModel):
    """Minimal concrete model, just to exercise the abstract contract."""

    supports_feature_importance = True

    def _fit(self, X, y):
        pass

    def _predict_proba(self, X):
        return np.where(X["url_length"] > 20, 0.9, 0.1)

    def save(self, path):
        pass

    @classmethod
    def load(cls, path):
        return cls()

    @property
    def name(self):
        return "dummy"


def test_cannot_instantiate_base_model_directly():
    with pytest.raises(TypeError):
        BaseModel()


def test_capability_declaration_is_required():
    """A model that forgets supports_feature_importance must not be
    instantiable -- the capability is an explicit, required declaration,
    never an inherited default."""

    class _ForgotCapability(BaseModel):
        def _fit(self, X, y): pass
        def _predict_proba(self, X): return np.zeros(len(X))
        def save(self, path): pass
        @classmethod
        def load(cls, path): return cls()
        @property
        def name(self): return "forgetful"

    with pytest.raises(TypeError, match="supports_feature_importance"):
        _ForgotCapability()


def test_fit_returns_self_for_chaining():
    model = _DummyModel()
    result = model.fit(pd.DataFrame(), np.array([]))
    assert result is model


def test_predict_derives_from_predict_proba():
    model = _DummyModel().fit(pd.DataFrame(), np.array([]))
    X = pd.DataFrame({"url_length": [10, 30]})
    assert list(model.predict_proba(X)) == [0.1, 0.9]
    assert list(model.predict(X)) == [0, 1]


def test_predict_proba_raises_if_not_fitted():
    model = _DummyModel()
    with pytest.raises(RuntimeError, match="has not been fitted"):
        model.predict_proba(pd.DataFrame({"url_length": [10]}))


def test_predict_proba_validates_output_length():
    class _BrokenModel(_DummyModel):
        def _predict_proba(self, X):
            return np.array([0.5])  # wrong length on purpose

    model = _BrokenModel().fit(pd.DataFrame(), np.array([]))
    with pytest.raises(ValueError, match="returned 1 rows"):
        model.predict_proba(pd.DataFrame({"url_length": [10, 20, 30]}))


@pytest.mark.parametrize("bad_value", [-1.2, 1.8, float("nan"), float("inf")])
def test_predict_proba_rejects_invalid_probability_values(bad_value):
    class _BadProbaModel(_DummyModel):
        def _predict_proba(self, X):
            return np.array([bad_value] * len(X))

    model = _BadProbaModel().fit(pd.DataFrame(), np.array([]))
    with pytest.raises(ValueError):
        model.predict_proba(pd.DataFrame({"url_length": [10]}))


def test_predict_uses_model_own_threshold_by_default():
    class _ThresholdModel(_DummyModel):
        _threshold = 0.95  # this model's own tuned threshold

    model = _ThresholdModel().fit(pd.DataFrame(), np.array([]))
    X = pd.DataFrame({"url_length": [30]})  # predict_proba returns 0.9 here
    assert model.predict(X)[0] == 0                  # 0.9 < 0.95 -> below this model's own bar
    assert model.predict(X, threshold=0.5)[0] == 1   # explicit override still works