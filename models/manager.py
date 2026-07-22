# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
models/manager.py

The ModelManager: the architectural boundary between the model layer and
everything that consumes models (Feature Selection today; the training
pipeline and Ensemble next).

Responsibilities implemented now:
- Registration: concrete BaseModel classes register *themselves* via the
  `@register` decorator (plugin pattern) -- the manager never imports a
  concrete model, and neither does any consumer. Only the composition
  root (the training pipeline / app bootstrap) imports concrete modules,
  which triggers their self-registration.
- Registration-time contract enforcement: rejects non-BaseModel classes,
  duplicate registrations, and models whose `supports_feature_importance`
  capability is not an explicitly declared bool -- catching a forgotten
  declaration at import time, before any instance exists.
- Factory semantics: consumers always receive FRESH model instances.
  Feature Selection refits models per CV fold and per RFE round; a shared
  fitted instance would silently leak state across folds.
- Capability queries: `feature_importance_participants()` returns a new
  instance of every registered model that declares the capability --
  Feature Selection's only entry point into the model layer.

Deliberately deferred (lands with the Ensemble phase, where its policies
have a consumer): inference execution and per-model fault isolation
during prediction, and save/load lifecycle orchestration.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Type

from .base import BaseModel

ModelFactory = Callable[[], BaseModel]


class ModelRegistrationError(TypeError):
    """Raised when a class fails the registration-time contract checks."""


class ModelManager:
    """
    Registry and factory for every model family in the system.

    Consumers depend on this class plus the BaseModel contract -- never
    on concrete model implementations.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[BaseModel]] = {}

    # ------------------------------------------------------------------ #
    # Registration (used by concrete model modules)                       #
    # ------------------------------------------------------------------ #

    def register(self, model_cls: Type[BaseModel]) -> Type[BaseModel]:
        """
        Class decorator: `@MODEL_MANAGER.register` above a concrete
        BaseModel subclass adds it to the registry. Returns the class
        unchanged so normal imports keep working.

        Raises
        ------
        ModelRegistrationError
            If the class is not a BaseModel subclass, is registered
            twice, or does not explicitly declare its
            `supports_feature_importance` capability as a bool.
        """
        if not (isinstance(model_cls, type) and issubclass(model_cls, BaseModel)):
            raise ModelRegistrationError(
                f"{model_cls!r} is not a BaseModel subclass; only BaseModel "
                f"implementations can be registered."
            )

        capability = getattr(model_cls, "supports_feature_importance", None)
        if not isinstance(capability, bool):
            raise ModelRegistrationError(
                f"{model_cls.__name__} must explicitly declare "
                f"'supports_feature_importance' as a class-level bool -- the "
                f"capability is required, never defaulted or inherited implicitly."
            )

        key = model_cls.__name__
        if key in self._registry:
            raise ModelRegistrationError(
                f"A model class named '{key}' is already registered."
            )

        self._registry[key] = model_cls
        return model_cls

    # ------------------------------------------------------------------ #
    # Queries (used by Feature Selection / training / ensemble)           #
    # ------------------------------------------------------------------ #

    def registered_names(self) -> List[str]:
        """Class names of every registered model, in registration order."""
        return list(self._registry)

    def create_all(self) -> List[BaseModel]:
        """A fresh, unfitted instance of every registered model."""
        return [cls() for cls in self._registry.values()]

    def feature_importance_participants(self) -> List[BaseModel]:
        """
        Fresh, unfitted instances of every model whose class declares
        `supports_feature_importance = True`.

        This is Feature Selection's sole entry point into the model
        layer: participation is decided by each model's own declaration,
        never by the selection pipeline or its configuration.
        """
        return [
            cls()
            for cls in self._registry.values()
            if cls.supports_feature_importance
        ]


# Default application-wide manager. Concrete model modules register into
# this instance at import time; tests build private ModelManager objects.
MODEL_MANAGER = ModelManager()
