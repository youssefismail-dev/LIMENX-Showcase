# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
core package: cross-cutting primitives shared by the data pipeline and the
serving layer (Project_Context "Core": URLValidator, URLNormalizer, ...).
"""

from .url_normalization import DEFAULT_SCHEME, SCHEME_PREFIXES, normalize_url

__all__ = ["normalize_url", "DEFAULT_SCHEME", "SCHEME_PREFIXES"]
