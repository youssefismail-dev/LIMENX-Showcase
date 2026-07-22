# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
validation/

Shared validation layer (maps to the Core "URLValidator" and the
"Feature Validation" stages in docs/Project_Context.md).

- url_validator:     structural validation of raw URL strings (input gate
                     for the data pipeline and, later, the REST API).
- feature_validator: validation of extracted feature vectors before they
                     reach Feature Selection or any model.
"""

from .url_validator import URLValidator
from .feature_validator import (
    FeatureValidationError,
    FeatureValidator,
    conventional_ranges,
)

__all__ = [
    "URLValidator",
    "FeatureValidator",
    "FeatureValidationError",
    "conventional_ranges",
]
