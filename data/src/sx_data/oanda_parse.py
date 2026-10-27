"""Turn an OANDA v20 candles payload into ``Candle`` contracts.

Shape relied on (OANDA v20 REST docs, recalled and NOT checked against the live API in this
session; see docs/DEPENDENCIES.md): ``{"instrument", "granularity", "candles": [{"complete",
"volume", "time", "bid": {o,h,l,c}, "ask": {...}, "mid": {...}}]}``, prices as decimal strings,
``time`` as RFC3339 with up to nine fractional digits.

Mapping: OHLC come from ``mid``. ``bid_close`` / ``ask_close`` come from ``bid.c`` / ``ask.c``.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from sx_core.contracts import Candle
from sx_core.contracts._base import Tf
from sx_data.errors import ParseError

_TIME = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?Z$")


def parse_oanda_time(text: str) -> datetime:
    """Parse ``2026-10-19T00:00:00.000000000Z`` (nanoseconds are truncated to microseconds)."""
    m = _TIME.match(text)
    if not m:
        raise ParseError(f"unrecognised OANDA time {text!r}")
    base = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    frac = (m.group(2) or "").ljust(6, "0")[:6]
    return base.replace(microsecond=int(frac))


def _price(block: Any, key: str, what: str) -> float:
    try:
        return float(block[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ParseError(f"missing or bad {what}.{key}") from exc


def parse_candle(raw: dict[str, Any], instrument: str, tf: Tf) -> Candle:
    try:
        mid = raw["mid"]
        bid = raw["bid"]
        ask = raw["ask"]
        complete = raw["complete"]
        volume = float(raw["volume"])
        time = parse_oanda_time(raw["time"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ParseError(f"candle is missing a required field: {exc!r}") from exc
    if not isinstance(complete, bool):
        raise ParseError("candle.complete must be a boolean")
    try:
        return Candle(
            instrument=instrument, tf=tf, time=time,
            open=_price(mid, "o", "mid"), high=_price(mid, "h", "mid"),
            low=_price(mid, "l", "mid"), close=_price(mid, "c", "mid"),
            volume=volume,
            bid_close=_price(bid, "c", "bid"), ask_close=_price(ask, "c", "ask"),
            complete=complete,
        )
    except ValidationError as exc:
        raise ParseError(f"candle at {raw.get('time')!r} failed validation: {exc}") from exc


def parse_candles(payload: dict[str, Any], instrument: str, tf: Tf) -> list[Candle]:
    """Parse every candle in ``payload`` (complete or not; the caller decides what to keep)."""
    rows = payload.get("candles")
    if not isinstance(rows, list):
        raise ParseError("payload has no 'candles' list")
    return [parse_candle(r, instrument, tf) for r in rows]
