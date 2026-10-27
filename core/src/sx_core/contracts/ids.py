"""Deterministic ids: hashes of semantic fields, never of measured price values.

Semantic fields are things like instrument, timeframe, kind, direction and an event
time. Floats are rejected so a price can never leak into an id and make it unstable.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sx_core.contracts._base import format_utc

IdPart = str | int | bool | datetime | None


def _canon(part: IdPart) -> str | int | bool | None:
    if isinstance(part, float):
        raise TypeError("ids must not be built from float values (prices are not semantic)")
    if isinstance(part, datetime):
        if part.tzinfo is None:
            raise ValueError("datetime id parts must be timezone-aware")
        return format_utc(part)
    return part


def make_id(prefix: str, *parts: IdPart) -> str:
    """``prefix:`` plus 16 hex chars of SHA-256 over the canonical JSON of ``parts``."""
    if not prefix or ":" in prefix:
        raise ValueError("prefix must be non-empty and contain no ':'")
    blob = json.dumps([_canon(p) for p in parts], separators=(",", ":"), ensure_ascii=False)
    return f"{prefix}:{hashlib.sha256(blob.encode()).hexdigest()[:16]}"


def setup_id(kind: str, instrument: str, tf: str, direction: str, event_time: datetime,
             discriminator: str = "") -> str:
    """``discriminator`` separates setups that share the fields above (e.g. ``asia_high``)."""
    return make_id("setup", kind, instrument, tf, direction, event_time, discriminator)


def forecast_id(instrument: str, tf: str, issued_at: datetime, target: str,
                model_name: str, params_hash: str) -> str:
    return make_id("fc", instrument, tf, issued_at, target, model_name, params_hash)


def suggestion_id(instrument: str, tf: str, created_at: datetime, side: str,
                  setup_ids: list[str], rules_version: str) -> str:
    return make_id("sug", instrument, tf, created_at, side, ",".join(sorted(setup_ids)),
                   rules_version)


def order_id(suggestion_id: str, backend: str, side: str, rules_version: str) -> str:
    """Idempotent client order id: the same suggestion and rules always give the same id."""
    return make_id("ord", suggestion_id, backend, side, rules_version)
