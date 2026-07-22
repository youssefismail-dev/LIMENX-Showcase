# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
api/security.py

API-key authentication primitives (design per docs/API_DESIGN.md §7): keys
are stored as SALTED HASHES — never plaintext — and verified in constant time.
This module owns hashing, the key store, and the resolved `Principal` with its
scopes; header extraction and the auth gate live in dependencies.py (SRP).

On-prem/offline posture: a static hashed key set, no external identity
provider. The `Principal` seam is where mTLS/JWT slots in later.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import FrozenSet, List, Mapping, Optional, Tuple

#: Scopes.
SCOPE_PREDICT = "predict"          # call the scoring endpoints
SCOPE_EXPLAIN_FULL = "explain:full"  # receive reasons + member_contributions
SCOPE_ADMIN = "admin"              # reserved; unused in V1 (no admin endpoints)

_HASH_NAME = "sha256"


def hash_key(presented_key: str, salt_hex: str) -> str:
    """Salted SHA-256 of an API key. Keys are high-entropy random tokens, so a
    single salted hash (not a slow KDF) is appropriate and fast."""
    salt = bytes.fromhex(salt_hex)
    return hashlib.new(_HASH_NAME, salt + presented_key.encode("utf-8")).hexdigest()


def generate_key(
    key_id: str,
    name: str,
    scopes: List[str],
    expires_at: Optional[str] = None,
) -> Tuple[str, dict]:
    """Mint a new (plaintext_key, hashed_record) pair — for ops/tests. The
    plaintext is shown ONCE; only the record (with the hash) is persisted."""
    plaintext = secrets.token_urlsafe(32)
    salt_hex = secrets.token_hex(16)
    record = {
        "key_id": key_id,
        "name": name,
        "salt": salt_hex,
        "hash": hash_key(plaintext, salt_hex),
        "scopes": list(scopes),
        "enabled": True,
        "expires_at": expires_at,
    }
    return plaintext, record


@dataclass(frozen=True)
class Principal:
    """The authenticated caller and its scopes."""

    key_id: str
    name: str
    scopes: FrozenSet[str]

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or SCOPE_ADMIN in self.scopes


#: Principal used when auth is DISABLED (trusted network) — full scoring +
#: full explanation, but never admin.
TRUSTED_PRINCIPAL = Principal(
    key_id="anonymous", name="anonymous",
    scopes=frozenset({SCOPE_PREDICT, SCOPE_EXPLAIN_FULL}),
)


class KeyStore:
    """Verifies presented API keys against salted-hash records."""

    def __init__(self, records: List[Mapping[str, object]]) -> None:
        self._records = [dict(r) for r in records]

    @classmethod
    def from_file(cls, path: str) -> "KeyStore":
        data = json.loads(Path(path).read_text("utf-8"))
        if not isinstance(data, list):
            raise ValueError("API keys file must be a JSON list of key records.")
        return cls(data)

    def verify(self, presented_key: str, now: Optional[datetime] = None) -> Optional[Principal]:
        """Return the Principal for a valid, enabled, unexpired key, else None.

        Constant-time hash comparison (hmac.compare_digest) avoids a timing
        oracle. Every enabled record is checked so timing does not reveal
        WHICH key matched.
        """
        if not presented_key:
            return None
        now = now or datetime.now(timezone.utc)
        match: Optional[Principal] = None
        for record in self._records:
            if not record.get("enabled", False):
                continue
            expected = str(record.get("hash", ""))
            candidate = hash_key(presented_key, str(record.get("salt", "")))
            if hmac.compare_digest(candidate, expected):
                if self._expired(record, now):
                    continue
                match = Principal(
                    key_id=str(record["key_id"]),
                    name=str(record.get("name", record["key_id"])),
                    scopes=frozenset(record.get("scopes", [])),
                )
        return match

    @staticmethod
    def _expired(record: Mapping[str, object], now: datetime) -> bool:
        raw = record.get("expires_at")
        if not raw:
            return False
        expires = datetime.fromisoformat(str(raw))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires
