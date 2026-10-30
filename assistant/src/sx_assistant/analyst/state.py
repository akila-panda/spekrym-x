"""Persisted provider state (Phase 9C-2): cooldowns, local usage estimates, health.

One row per (provider, model). Counters are LOCAL ESTIMATES (they count every request sent,
including ones that timed out, because a timeout may still have used quota); the provider's own
429 remains the real limit. Times are wall-clock epoch seconds so they survive a restart. The
day for the counters is the UTC date: the providers' real reset times are not known here.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class ProviderState:
    provider: str
    model: str
    key_fp: str | None = None          # short hash of the key; a new key clears a stale disable
    disabled_reason: str | None = None
    cooldown_until: float = 0.0
    day: str = ""
    requests_today: int = 0
    tokens_today: int = 0
    last_error: str | None = None      # None after a success
    last_success_at: float | None = None

    def health(self, now: float) -> str:
        if self.disabled_reason:
            return "disabled"
        if self.cooldown_until > now:
            return "cooling_down"
        if self.last_error:
            return "degraded"
        return "healthy" if self.last_success_at else "unknown"

    def roll_day(self, today: str) -> None:
        if self.day != today:
            self.day, self.requests_today, self.tokens_today = today, 0, 0


class StateStore(Protocol):
    def load(self, provider: str, model: str) -> ProviderState: ...
    def save(self, state: ProviderState) -> None: ...
    def all(self) -> list[ProviderState]: ...
    def reset(self, provider: str) -> int:
        """Forget a provider's state (cooldown, disable, counters). Returns rows removed."""


class MemoryState:
    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], ProviderState] = {}

    def load(self, provider: str, model: str) -> ProviderState:
        row = self._rows.get((provider, model))
        return ProviderState(**asdict(row)) if row else ProviderState(provider, model)

    def save(self, state: ProviderState) -> None:
        self._rows[(state.provider, state.model)] = ProviderState(**asdict(state))

    def all(self) -> list[ProviderState]:
        return [ProviderState(**asdict(r)) for r in self._rows.values()]

    def reset(self, provider: str) -> int:
        keys = [k for k in self._rows if k[0] == provider]
        for k in keys:
            del self._rows[k]
        return len(keys)


class SqliteState:
    """Small dedicated SQLite file (stdlib). One connection per call: safe across threads."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS provider_state "
                      "(provider TEXT, model TEXT, data TEXT, PRIMARY KEY (provider, model))")

    def _conn(self):
        return closing(sqlite3.connect(self.path, timeout=10))

    def load(self, provider: str, model: str) -> ProviderState:
        with self._conn() as c:
            row = c.execute("SELECT data FROM provider_state WHERE provider=? AND model=?",
                            (provider, model)).fetchone()
        return ProviderState(**json.loads(row[0])) if row else ProviderState(provider, model)

    def save(self, state: ProviderState) -> None:
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO provider_state VALUES (?, ?, ?)",
                      (state.provider, state.model, json.dumps(asdict(state))))
            c.commit()

    def all(self) -> list[ProviderState]:
        with self._conn() as c:
            rows = c.execute("SELECT data FROM provider_state ORDER BY provider, model").fetchall()
        return [ProviderState(**json.loads(r[0])) for r in rows]

    def reset(self, provider: str) -> int:
        with self._conn() as c:
            n = c.execute("DELETE FROM provider_state WHERE provider=?", (provider,)).rowcount
            c.commit()
        return n
