"""Parquet read/write for candles and content-based ``data_version`` hashing.

``data_version`` hashes the *content* (column names, types, values), not the file bytes,
so re-writing the same data gives the same version regardless of Parquet encoding.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from sx_core.contracts import Candle

CANDLE_COLUMNS = ["instrument", "tf", "time", "open", "high", "low", "close", "volume",
                  "bid_close", "ask_close", "complete"]
_FLOATS = ["open", "high", "low", "close", "volume", "bid_close", "ask_close"]
_STRINGS = ["instrument", "tf"]


def candles_to_frame(candles: Sequence[Candle]) -> pd.DataFrame:
    """Candles to a frame with ``time`` as UTC ``datetime64[ns, UTC]``; missing bid/ask is NaN."""
    rows = [{**c.model_dump(), "time": c.time} for c in candles]
    df = pd.DataFrame(rows, columns=CANDLE_COLUMNS)
    df["time"] = pd.to_datetime(df["time"], utc=True).astype("datetime64[ns, UTC]")
    for col in _FLOATS:
        df[col] = df[col].astype("float64")
    df["complete"] = df["complete"].astype(bool)
    return df


def frame_to_candles(df: pd.DataFrame) -> list[Candle]:
    out: list[Candle] = []
    for row in df.to_dict("records"):
        for col in ("bid_close", "ask_close"):
            if pd.isna(row[col]):
                row[col] = None
        row["time"] = pd.Timestamp(row["time"]).to_pydatetime()
        out.append(Candle(**{k: row[k] for k in CANDLE_COLUMNS}))
    return out


def data_version(df: pd.DataFrame) -> str:
    """SHA-256 (first 16 hex chars, prefixed ``dv:``) of the frame's canonical content.

    Order of rows and columns matters. The index is ignored. NaN hashes as NaN.
    """
    h = hashlib.sha256()
    for col in df.columns:
        s = df[col]
        h.update(f"|{col}|{len(s)}|".encode())
        if isinstance(s.dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_any_dtype(s):
            ts = pd.to_datetime(s, utc=True).astype("datetime64[ns, UTC]")
            h.update(b"ts")
            h.update(ts.astype("int64").to_numpy().astype("<i8").tobytes())
        elif pd.api.types.is_bool_dtype(s):
            h.update(b"bool" + s.to_numpy(dtype=bool).tobytes())
        elif pd.api.types.is_float_dtype(s):
            arr = s.to_numpy(dtype="float64", na_value=np.nan).astype("<f8")
            arr = np.where(np.isnan(arr), np.float64("nan"), arr)  # one canonical NaN
            h.update(b"f8" + arr.tobytes())
        elif pd.api.types.is_integer_dtype(s):
            h.update(b"i8" + s.to_numpy(dtype="int64").astype("<i8").tobytes())
        else:
            h.update(b"str")
            for v in s.tolist():
                h.update(b"\x00" + (b"\x01" if v is None else str(v).encode()))
    return "dv:" + h.hexdigest()[:16]


def write_parquet(df: pd.DataFrame, path: str | Path) -> str:
    """Write ``df`` to ``path`` (parent dirs created) and return its ``data_version``."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), p)
    return data_version(df)


def read_parquet(path: str | Path) -> pd.DataFrame:
    return pq.read_table(Path(path)).to_pandas()
