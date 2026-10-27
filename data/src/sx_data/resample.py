"""Resample closed candles to a higher timeframe. UTC only, closed bars only, no fake bars.

Buckets are aligned to the Unix epoch, which is 00:00 UTC, so H4 opens at 00/04/08/12/16/20 UTC
and D opens at 00:00 UTC (decision X10). Rules:

* Only ``complete`` source bars are used; an incomplete one is dropped.
* A bucket is emitted only when its end is at or before ``as_of`` (default: the close of the
  last source bar). A bucket still forming is never returned.
* A bucket is built from the bars that exist. Missing source bars (a quiet minute, the weekend)
  are never filled with zero or copied bars; a bucket with no source bars does not exist.
* open = first open, high = max, low = min, close = last close, volume = sum;
  ``bid_close`` / ``ask_close`` = those of the last source bar (None if it had none).
* Known limit: a bucket that starts a few hours before a gap (for example the Sunday D bar) is
  partial. It is a real, complete-as-far-as-the-market-traded bar, not a full session.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import pandas as pd

from sx_core.clock import TF_SECONDS
from sx_core.contracts import Candle
from sx_core.contracts._base import Tf
from sx_core.storage import CANDLE_COLUMNS, candles_to_frame, frame_to_candles
from sx_data.errors import ResampleError


def _check_source(df: pd.DataFrame, to_tf: str) -> str:
    if df.empty:
        raise ResampleError("no source bars")
    if df["instrument"].nunique() != 1 or df["tf"].nunique() != 1:
        raise ResampleError("source must be a single instrument and timeframe")
    src = str(df["tf"].iloc[0])
    if to_tf not in TF_SECONDS or TF_SECONDS[to_tf] <= TF_SECONDS[src] \
            or TF_SECONDS[to_tf] % TF_SECONDS[src]:
        raise ResampleError(f"cannot resample {src} to {to_tf}")
    if df["time"].duplicated().any():
        raise ResampleError("duplicate source bar times")
    if not df["time"].is_monotonic_increasing:
        raise ResampleError("source bars are not in time order")
    return src


def resample_frame(df: pd.DataFrame, to_tf: Tf, as_of: datetime | None = None) -> pd.DataFrame:
    """Frame in, frame out (columns as ``sx_core.storage.CANDLE_COLUMNS``). See module docs."""
    src_tf = _check_source(df, to_tf)
    src = df[df["complete"]]
    if src.empty:
        return df.iloc[0:0].copy()
    src_secs, secs = TF_SECONDS[src_tf], TF_SECONDS[to_tf]
    if as_of is None:
        as_of_ts = src["time"].iloc[-1] + pd.Timedelta(seconds=src_secs)
    else:
        as_of_ts = pd.Timestamp(as_of).tz_convert("UTC")
    bucket = src["time"].dt.floor(f"{secs}s")
    keep = bucket + pd.Timedelta(seconds=secs) <= as_of_ts
    src, bucket = src[keep], bucket[keep]
    if src.empty:
        return df.iloc[0:0].copy()
    g = src.groupby(bucket, sort=True)
    tail = g.tail(1)
    last = tail.set_index(bucket.loc[tail.index])
    out = pd.DataFrame({
        "instrument": str(src["instrument"].iloc[0]),
        "tf": to_tf,
        "open": g["open"].first(),
        "high": g["high"].max(),
        "low": g["low"].min(),
        "close": g["close"].last(),
        "volume": g["volume"].sum(),
        "bid_close": last["bid_close"],
        "ask_close": last["ask_close"],
        "complete": True,
    })
    out.index.name = "time"
    out = out.reset_index()
    out["time"] = out["time"].astype("datetime64[ns, UTC]")
    return out[CANDLE_COLUMNS]


def resample(candles: Sequence[Candle], to_tf: Tf, as_of: datetime | None = None
             ) -> list[Candle]:
    """``Candle`` list in, ``Candle`` list out. Use ``resample_frame`` for long histories."""
    if not candles:
        raise ResampleError("no source bars")
    return frame_to_candles(resample_frame(candles_to_frame(candles), to_tf, as_of))
