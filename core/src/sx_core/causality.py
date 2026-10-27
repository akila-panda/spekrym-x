"""Prefix-equality harness (docs/PRINCIPLES.md rule 1).

For a producer ``f(candles) -> objects`` the harness checks, for every prefix
``candles[:k]``, that the objects known by time ``t`` (``known_at <= t``, with ``t`` the
moment bar ``k-1`` became available) are identical whether ``f`` ran on the prefix or on
the full series. Any difference means the producer used data from after ``t``, or
stamped ``known_at`` earlier than it could have known.

Identity of an object is ``obj.id`` (or ``obj["id"]``); equality is ``==`` on the model
or dict. Pass ``identity`` / ``key`` to override.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from sx_core.clock import available_at
from sx_core.contracts import Candle

Producer = Callable[[Sequence[Candle]], Sequence[Any]]
ViolationKind = Literal["missing_in_prefix", "extra_in_prefix", "changed", "known_before_event"]


@dataclass(frozen=True)
class Violation:
    kind: ViolationKind
    prefix_len: int
    t: datetime
    object_id: str
    detail: str

    def __str__(self) -> str:
        return (f"[{self.kind}] prefix={self.prefix_len} t={self.t.isoformat()} "
                f"id={self.object_id}: {self.detail}")


class CausalityViolation(AssertionError):
    def __init__(self, violations: list[Violation], total: int):
        self.violations = violations
        shown = "\n  ".join(str(v) for v in violations[:10])
        more = f"\n  ... and {total - 10} more" if total > 10 else ""
        super().__init__(f"{total} causality violation(s):\n  {shown}{more}")


def _identity(obj: Any) -> str:
    return str(obj["id"] if isinstance(obj, dict) else obj.id)


def _get(obj: Any, name: str) -> Any:
    v = obj[name] if isinstance(obj, dict) else getattr(obj, name)
    if name in ("known_at", "event_time") and isinstance(v, str):
        v = datetime.fromisoformat(v)  # dumped models carry ISO strings
    return v


def _known(objs: Sequence[Any], t: datetime, identity: Callable[[Any], str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for o in objs:
        if _get(o, "known_at") <= t:
            oid = identity(o)
            if oid in out:
                raise ValueError(f"producer returned duplicate id {oid!r}")
            out[oid] = o
    return out


def check_prefix_equality(
    producer: Producer,
    candles: Sequence[Candle],
    *,
    min_prefix: int = 1,
    prefix_lengths: Sequence[int] | None = None,
    identity: Callable[[Any], str] = _identity,
    key: Callable[[Any], Any] = lambda o: o,
    latency: timedelta = timedelta(0),
) -> list[Violation]:
    """Return every violation found; an empty list means the producer looks causal.

    By default every prefix from ``min_prefix`` to ``len(candles)`` is checked. A leak is
    often visible only at a few prefixes (those ending inside a signal's confirmation
    window), so sampling prefixes can miss it; pass ``prefix_lengths`` only deliberately.
    ``latency`` is an optional feed delay added when computing ``t``.
    """
    if min_prefix < 1:
        raise ValueError("min_prefix must be >= 1")
    if not candles:
        raise ValueError("candles must not be empty")
    if any(not c.complete for c in candles):
        raise ValueError("harness inputs must be complete (closed) candles")
    full = list(producer(list(candles)))
    for o in full:
        if _get(o, "known_at") < _get(o, "event_time"):
            raise ValueError(f"object {identity(o)!r} has known_at before event_time")

    n = len(candles)
    ks = sorted({*(prefix_lengths if prefix_lengths is not None else range(min_prefix, n + 1)), n})
    if ks[0] < 1 or ks[-1] > n:
        raise ValueError("prefix lengths must be within 1..len(candles)")
    found: list[Violation] = []
    for k in ks:
        last = candles[k - 1]
        t = available_at(last.time, last.tf, latency)
        part = _known(list(producer(list(candles[:k]))), t, identity)
        whole = _known(full, t, identity)
        for oid in whole.keys() - part.keys():
            found.append(Violation("missing_in_prefix", k, t, oid,
                                   "known on the full series but not computed from the prefix "
                                   "(known_at set earlier than the data allowed)"))
        for oid in part.keys() - whole.keys():
            found.append(Violation("extra_in_prefix", k, t, oid,
                                   "computed from the prefix but absent or later "
                                   "on the full series"))
        for oid in part.keys() & whole.keys():
            if key(part[oid]) != key(whole[oid]):
                found.append(Violation("changed", k, t, oid,
                                       "value differs between prefix and full series "
                                       "(uses data from after t)"))
    return found


def assert_causal(producer: Producer, candles: Sequence[Candle], **kwargs: Any) -> None:
    """Raise ``CausalityViolation`` if the producer fails the prefix-equality check."""
    found = check_prefix_equality(producer, candles, **kwargs)
    if found:
        raise CausalityViolation(found, len(found))
