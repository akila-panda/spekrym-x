"""The evidence packet (Phase 9C-1): everything the analyst may talk about, with stable ids.

Built only from a ``PremarketAnalysis`` (closed bars, every item ``known_at <= as_of``).
The model never browses or calculates: it is handed these items and must cite their ids.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from sx_assistant.premarket.builder import PremarketAnalysis
from sx_core.contracts import Setup

MAX_SETUPS = 12


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: str          # "setup" | "context" | "checklist"
    text: str
    known_at: datetime


@dataclass(frozen=True)
class EvidencePacket:
    instrument: str
    as_of: datetime
    source_label: str
    items: tuple[EvidenceItem, ...]
    dropped: int = 0

    @property
    def ids(self) -> frozenset[str]:
        return frozenset(i.id for i in self.items)

    def by_id(self) -> dict[str, EvidenceItem]:
        return {i.id: i for i in self.items}

    def render(self) -> str:
        return "\n".join(f"[{i.id}] ({i.kind}) {i.text}" for i in self.items)

    def hash(self) -> str:
        body = json.dumps([self.instrument, self.as_of.isoformat(), self.source_label,
                           [(i.id, i.kind, i.text) for i in self.items]], sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]


def _setup_text(s: Setup) -> str:
    g = s.geometry
    return (f"{s.tf} {s.kind} ({s.direction}), {s.lifecycle}; price {g.price_low:.5f} to "
            f"{g.price_high:.5f}; {s.plain_text} Invalidation: {s.invalidation}")


def build_packet(a: PremarketAnalysis, max_setups: int = MAX_SETUPS) -> EvidencePacket:
    last = a.candles[-1]
    items: list[EvidenceItem] = [EvidenceItem(
        "ctx:last_close", "context",
        f"Latest closed {last.tf} bar of {a.instrument} (opened {last.time:%Y-%m-%d %H:%M} UTC) "
        f"closed at {last.close:.5f}.", a.as_of)]
    items += [EvidenceItem(c.id, "checklist", f"{c.tf}: {c.text}", c.known_at)
              for c in a.checklist]
    live = [s for s in a.setups if s.lifecycle != "broken"]
    live.sort(key=lambda s: abs((s.geometry.price_low + s.geometry.price_high) / 2 - last.close))
    chosen = live[:max_setups]
    items += [EvidenceItem(s.id, "setup", _setup_text(s), s.known_at) for s in chosen]
    ids = [i.id for i in items]
    if len(set(ids)) != len(ids):
        raise ValueError("evidence ids must be unique")
    late = [i.id for i in items if i.known_at > a.as_of]
    if late:
        raise ValueError(f"evidence known after as_of (look-ahead): {late}")
    return EvidencePacket(a.instrument, a.as_of, a.source.label, tuple(items),
                          len(live) - len(chosen))
