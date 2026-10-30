"""Download long candle history from the OANDA practice feed into a Lab dataset (Phase 8A).

``OandaClient.fetch_candles`` does the paging, rate limiting and retries (never run against the
live API in the build sandbox, which has no route to OANDA). This module only adds what the
Lab needs: the quality check, the same provenance sidecar the file importer writes, and an
honest label. OHLC are the broker's MID prices; bid and ask closes are kept on each candle.
The feed is the broker's practice feed and is NOT independently verified.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

from sx_core.clock import tf_delta
from sx_core.contracts import Candle
from sx_core.contracts._base import Tf
from sx_core.storage import candles_to_frame
from sx_data.importer import ImportRefused, ImportResult, build_provenance
from sx_data.quality import DEFAULT_RULES, GapRules, check_quality

MAX_EDGE_GAP = timedelta(days=5)   # longest honest closure: a weekend plus a holiday
LABEL_OANDA = "OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED"


class CandleSource(Protocol):
    def fetch_candles(self, instrument: str, tf: Tf, start: datetime, end: datetime
                      ) -> list[Candle]: ...


def _check_coverage(candles: list[Candle], tf: Tf, start: datetime, end: datetime,
                    now: datetime) -> None:
    """Refuse a download that silently covers less than was asked for."""
    last_close = candles[-1].time + tf_delta(tf)
    if min(end, now) - last_close > MAX_EDGE_GAP:
        raise ImportRefused(
            f"download stopped early: last bar {candles[-1].time.isoformat()}, "
            f"but data was requested up to {min(end, now).isoformat()}")
    if candles[0].time - start > MAX_EDGE_GAP:
        raise ImportRefused(
            f"history starts late: first bar {candles[0].time.isoformat()}, "
            f"but data was requested from {start.isoformat()} "
            "(the broker may not go back that far)")


def fetch_history(client: CandleSource, instrument: str, tf: Tf, start: datetime, end: datetime,
                  *, rules: GapRules = DEFAULT_RULES, accept_degraded: bool = False,
                  now: datetime | None = None) -> ImportResult:
    candles = client.fetch_candles(instrument, tf, start, end)
    if not candles:
        raise ImportRefused("the broker returned no candles for that range")
    _check_coverage(candles, tf, start, end, now or datetime.now(UTC))
    report = check_quality(candles_to_frame(candles), tf, rules=rules)
    if report.feed_degraded and not accept_degraded:
        raise ImportRefused("quality check failed: " + "; ".join(report.reasons))
    prov = build_provenance(candles, report, source="oanda_practice", label=LABEL_OANDA,
                            instrument=instrument, tf=tf, assumed_complete=False,
                            assume_tz=None)
    prov.update(file="oanda practice API", file_sha256="", files=[],
                price_basis="mid (bid and ask closes kept per candle)",
                range_requested=[start.isoformat(), end.isoformat()])
    return ImportResult(candles, report, prov)
