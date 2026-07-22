# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/config.py

Settings for the REST API — env-driven via pydantic-settings, so every
operational knob (and crucially the PRODUCT NAME) is configuration, never a
hard-coded constant. The final brand is undecided; `service_name` defaults to
a descriptive placeholder and is the ONLY place the name lives. Changing the
brand later is a one-line config / env change (`PHISH_SERVICE_NAME=...`).

Env prefix `PHISH_` is a functional (not brand) namespace: e.g.
`PHISH_SERVICE_NAME`, `PHISH_MODEL_VERSION`, `PHISH_MAX_BATCH`, ...
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable, env-overridable API configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PHISH_",
        env_file=os.environ.get("PHISH_ENV_FILE", ".env"),
        extra="ignore",
        frozen=True,
    )

    # --- Identity (configurable; NO hard-coded brand anywhere else) ---------
    service_name: str = "LIMENX"                 # current brand; override via PHISH_SERVICE_NAME
    api_version: str = "v1"                      # HTTP contract; also route prefix

    # --- Model / registry ---------------------------------------------------
    model_version: str = "reference-1.0"   # showcase engine; NOT the production model
    registry_dir: Optional[str] = None           # None -> default serving registry
    verify_integrity: bool = True                # SHA-verify the bundle on load
    include_sequence_explanation: bool = False   # gated char-saliency layer
    warm_up: bool = True                         # dummy inference at startup

    # --- Request limits (overload / DoS bounds) -----------------------------
    max_batch: int = Field(default=100, ge=1)
    url_max_length: int = Field(default=2048, ge=1)
    max_request_bytes: int = Field(default=1_048_576, ge=1)   # 1 MiB body cap

    # --- Concurrency & rate limiting ----------------------------------------
    max_concurrency: int = Field(default_factory=lambda: os.cpu_count() or 4, ge=1)
    rate_limit_per_minute: int = Field(default=120, ge=1)
    rate_limit_burst: int = Field(default=40, ge=1)

    # --- Auth ---------------------------------------------------------------
    auth_enabled: bool = False                   # trusted network by default
    api_keys_file: Optional[str] = None          # JSON of key records (hashed)

    # --- Logging / audit ----------------------------------------------------
    log_level: str = "INFO"
    redact_urls_in_logs: bool = True             # URLs can carry secrets

    # --- CORS (the React frontend calls this API cross-origin) --------------
    cors_allow_origins: List[str] = [
        "http://localhost:3000", "http://localhost:5173",
        "http://127.0.0.1:3000", "http://127.0.0.1:5173",
    ]
    cors_allow_credentials: bool = True

    # --- Response / timeouts ------------------------------------------------
    gzip_min_bytes: int = Field(default=500, ge=0)   # compress bodies over this
    request_timeout_s: float = Field(default=30.0, gt=0)

    # --- Docs ---------------------------------------------------------------
    docs_enabled: bool = True                    # disable/gate in production

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated env string OR a JSON/list; normalize to a
        list. `PHISH_CORS_ALLOW_ORIGINS=https://app.example,https://admin.example`."""
        if isinstance(value, str) and not value.strip().startswith("["):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value

    @property
    def route_prefix(self) -> str:
        """The versioned route prefix, e.g. '/v1'."""
        return f"/{self.api_version}"


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton (cached). Tests clear the cache or
    override the FastAPI dependency."""
    return Settings()
