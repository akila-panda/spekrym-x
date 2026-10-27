from __future__ import annotations

from typing import Any

from sx_core.contracts._base import Contract, UtcDatetime


class LedgerEntry(Contract):
    """One line of the append-only ledger. ``hash`` chains to the previous entry (see ledger.py)."""

    ts: UtcDatetime
    kind: str
    payload: dict[str, Any]
    data_version: str
    rules_version: str | None = None
    hash: str
