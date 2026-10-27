"""Replay wrapper: makes a retrospective library causal by construction.

Libraries such as smart-money-concepts compute on a whole frame and look ahead (a swing needs
bars to its right, a break carries a future index, edge bars are forced to swings, a
tolerance uses the whole range). We never trust a one-shot call on the full series.
Instead, for each prefix ``candles[:k]`` we call the library on that prefix only, keep only
what the extractor accepts as already confirmed, and **freeze each object the first time it
appears**: ``known_at`` is the close of bar ``k-1`` and its values are those seen then.
Later prefixes cannot change it. The result depends only on data up to ``known_at``, which is
exactly what the Phase 2 prefix-equality harness checks.

Cost: ``n`` extractor calls on up to ``n`` bars (quadratic). The SMC adapter's default engine
uses numpy ports of the slowest library calls (``smc_fast``), about 4 to 5 times faster than
calling the library on every prefix; see ``scripts/bench_smc_replay.py`` for measured times.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from sx_assistant.ta.common import check_series, to_frame
from sx_core.clock import available_at
from sx_core.contracts import Candle


@dataclass(frozen=True)
class Seen:
    """An object frozen at first sight."""

    key: str
    first_k: int              # prefix length (bars 0..k-1) at which it first appeared
    known_at: datetime        # close of bar k-1
    data: Mapping[str, Any]


class PrefixView:
    """The prefix ``df[:k]`` plus a per-prefix cache for expensive shared results."""

    def __init__(self, df: pd.DataFrame, k: int) -> None:
        self.df = df.iloc[:k].reset_index(drop=True)
        self.k = k
        self._cache: dict[str, Any] = {}

    def cached(self, name: str, make: Callable[[], Any]) -> Any:
        if name not in self._cache:
            self._cache[name] = make()
        return self._cache[name]


Extractor = Callable[[PrefixView], Iterable[tuple[str, dict[str, Any]]]]


def replay_first_seen(candles: Sequence[Candle], extract: Extractor, *,
                      min_bars: int = 1) -> list[Seen]:
    """Run ``extract`` on every prefix and freeze each ``(key, data)`` at its first sight."""
    _, tf = check_series(candles)
    df = to_frame(candles)
    seen: dict[str, Seen] = {}
    for k in range(max(1, min_bars), len(candles) + 1):
        for key, data in extract(PrefixView(df, k)):
            if key not in seen:
                seen[key] = Seen(key, k, available_at(candles[k - 1].time, tf), dict(data))
    return list(seen.values())
