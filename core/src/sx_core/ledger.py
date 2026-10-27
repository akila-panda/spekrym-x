"""Append-only JSONL ledger with hash chaining (docs/PRINCIPLES.md rule 8).

Each line is a ``LedgerEntry``. ``hash`` = SHA-256 of the previous entry's hash plus the
canonical JSON of this entry without its ``hash``. The first entry chains to ``GENESIS``.
Editing, deleting, inserting or reordering any line breaks every later hash, which
``verify()`` reports with the line number.

There is no update or delete API. Reading never writes and never creates the file.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sx_core.contracts import LedgerEntry, format_utc

try:  # POSIX file locking; the owner runs macOS
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

GENESIS = "0" * 64


class LedgerError(Exception):
    """The ledger file is damaged or an append was refused."""


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def compute_hash(prev_hash: str, entry_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + canonical_json(entry_without_hash)).encode()).hexdigest()


def _body(entry: LedgerEntry) -> dict[str, Any]:
    d = entry.model_dump(mode="json")
    d.pop("hash")
    if d["rules_version"] is None:
        d.pop("rules_version")  # unset optional fields are omitted from the line and the hash
    return d


class Ledger:
    def __init__(self, path: str | Path, *, now: Callable[[], datetime] | None = None):
        self.path = Path(path)
        self._now = now or (lambda: datetime.now(UTC))

    # ---- reads (never mutate) -------------------------------------------------
    def read(self) -> list[LedgerEntry]:
        """All entries in order. An absent file is an empty ledger and is not created."""
        if not self.path.exists():
            return []
        entries: list[LedgerEntry] = []
        with self.path.open("rb") as f:
            for n, raw in enumerate(f, start=1):
                if not raw.endswith(b"\n"):
                    raise LedgerError(f"line {n}: incomplete final line (torn write?)")
                try:
                    entries.append(LedgerEntry.model_validate_json(raw))
                except ValueError as exc:
                    raise LedgerError(f"line {n}: invalid entry: {exc}") from exc
        return entries

    def verify(self) -> int:
        """Check the whole chain; return the entry count or raise ``LedgerError``."""
        prev = GENESIS
        entries = self.read()
        for n, e in enumerate(entries, start=1):
            if compute_hash(prev, _body(e)) != e.hash:
                raise LedgerError(f"line {n}: hash mismatch (entry altered, removed or reordered)")
            prev = e.hash
        return len(entries)

    def head(self) -> str:
        """Hash of the last entry, or ``GENESIS`` for an empty ledger."""
        entries = self.read()
        return entries[-1].hash if entries else GENESIS

    # ---- the only write ---------------------------------------------------------
    def append(self, kind: str, payload: dict[str, Any], data_version: str,
               rules_version: str | None = None, ts: datetime | None = None) -> LedgerEntry:
        """Append one entry and return it.

        Refuses to extend a ledger whose final line is torn or whose last entry does not
        chain correctly. This is a cheap tail check; ``verify()`` checks the whole chain.
        Raises ``TypeError``/``ValueError`` if the payload is not plain JSON (no NaN).
        """
        if not kind:
            raise ValueError("kind must be non-empty")
        when = (ts or self._now()).astimezone(UTC)
        raw: dict[str, Any] = {"ts": format_utc(when), "kind": kind, "payload": payload,
                               "data_version": data_version}
        if rules_version is not None:
            raw["rules_version"] = rules_version
        body = json.loads(canonical_json(raw))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab+") as f:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_EX)
            try:
                prev = self._checked_head(f)
                entry = LedgerEntry(**body, hash=compute_hash(prev, body))
                f.seek(0, os.SEEK_END)
                f.write((canonical_json({**body, "hash": entry.hash}) + "\n").encode())
                f.flush()
                os.fsync(f.fileno())
            finally:
                if fcntl:
                    fcntl.flock(f, fcntl.LOCK_UN)
        return entry

    @staticmethod
    def _checked_head(f: Any) -> str:
        """Hash of the last entry after checking that line chains from the one before it."""
        f.seek(0)
        before: bytes | None = None
        last: bytes | None = None
        for raw in f:
            before, last = last, raw
        if last is None:
            return GENESIS
        if not last.endswith(b"\n"):
            raise LedgerError("incomplete final line (torn write?); refusing to append")
        try:
            e = LedgerEntry.model_validate_json(last)
            prev = LedgerEntry.model_validate_json(before).hash if before else GENESIS
        except ValueError as exc:
            raise LedgerError(f"unreadable tail: {exc}; refusing to append") from exc
        if compute_hash(prev, _body(e)) != e.hash:
            raise LedgerError("last entry does not chain correctly; refusing to append")
        return e.hash
