# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
tests/test_model_manager.py

Tests for the ModelManager boundary: self-registration, registration-time
contract enforcement (BaseModel subclass, explicit capability, no
duplicates), factory freshness, and capability-based participant queries.

Run with: pytest tests/test_model_manager.py
"""

import numpy as np
import pytest

from models.base import BaseModel
from models.manager import ModelManager, ModelRegistrationError


def _stub_model(class_name: str, capability):
    """Builds a minimal concrete BaseModel class for registry tests."""
    namespace = {
        "_fit": lambda self, X, y: None,
        "_predict_proba": lambda self, X: np.zeros(len(X)),
        "save": lambda self, path: None,
        "load": classmethod(lambda cls, path: cls()),
        "name": property(lambda self: class_name.lower()),
    }
    if capability is not None:
        namespace["supports_feature_importance"] = capability
    return type(class_name, (BaseModel,), namespace)


# ---------------------------------------------------------------------- #
# Registration contract                                                   #
# ---------------------------------------------------------------------- #

def test_register_returns_class_unchanged():
    manager = ModelManager()
    cls = _stub_model("TabularA", True)
    assert manager.register(cls) is cls           # decorator contract
    assert manager.registered_names() == ["TabularA"]


def test_register_rejects_non_basemodel_class():
    manager = ModelManager()
    with pytest.raises(ModelRegistrationError, match="not a BaseModel subclass"):
        manager.register(dict)


def test_register_rejects_missing_capability_declaration():
    manager = ModelManager()
    with pytest.raises(ModelRegistrationError, match="supports_feature_importance"):
        manager.register(_stub_model("Forgetful", None))


def test_register_rejects_non_bool_capability():
    # A truthy non-bool (e.g. 1 or "yes") is still an undeclared contract.
    manager = ModelManager()
    with pytest.raises(ModelRegistrationError, match="class-level bool"):
        manager.register(_stub_model("Sloppy", "yes"))


def test_register_rejects_duplicates():
    manager = ModelManager()
    manager.register(_stub_model("TabularA", True))
    with pytest.raises(ModelRegistrationError, match="already registered"):
        manager.register(_stub_model("TabularA", True))


# ---------------------------------------------------------------------- #
# Factory semantics                                                       #
# ---------------------------------------------------------------------- #

def test_create_all_returns_fresh_instances_every_call():
    manager = ModelManager()
    manager.register(_stub_model("TabularA", True))

    first, second = manager.create_all(), manager.create_all()
    assert first[0] is not second[0]               # never a shared singleton

    first[0].fit(__import__("pandas").DataFrame(), np.array([]))
    assert first[0]._is_fitted and not second[0]._is_fitted   # no state leak


# ---------------------------------------------------------------------- #
# Capability-based participation                                          #
# ---------------------------------------------------------------------- #

def test_feature_importance_participants_filters_by_declaration():
    manager = ModelManager()
    manager.register(_stub_model("TabularA", True))
    manager.register(_stub_model("SequenceB", False))   # e.g. CNN: opts out
    manager.register(_stub_model("TabularC", True))

    participants = manager.feature_importance_participants()

    assert sorted(type(p).__name__ for p in participants) == ["TabularA", "TabularC"]
    assert all(isinstance(p, BaseModel) for p in participants)
    assert all(not p._is_fitted for p in participants)  # fresh and unfitted


def test_no_participants_is_an_empty_list_not_an_error():
    # Zero participants is a policy decision for the *selection pipeline*
    # (which must raise); the manager just reports the truth.
    manager = ModelManager()
    manager.register(_stub_model("SequenceB", False))
    assert manager.feature_importance_participants() == []
