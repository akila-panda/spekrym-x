"""Column and time-format handling for owner-supplied candle files (Phase 8A import helper).

Nothing here guesses silently:
  * Column names are matched case-insensitively against a short alias list. A file whose
    columns cannot be matched is refused and the columns seen are printed.
  * A time column is parsed with an explicit ``time_format``, or with the ONE candidate format
    that parses every row. If none parses, or more than one parses (day/month ambiguity), the
    file is refused; a month of hourly bars always contains a day above 12, so a genuine
    day-first or month-first file resolves.
The alias list and candidate formats are NOT verified against any provider's real export. They
are common layouts; the first real file decides what is added.
"""

from __future__ import annotations

import pandas as pd

ALIASES: dict[str, tuple[str, ...]] = {
    "time": ("time", "gmt time", "utc time", "datetime", "timestamp", "date"),
    "open": ("open",), "high": ("high",), "low": ("low",), "close": ("close",),
    "volume": ("volume", "tick volume", "tickvol"),
}
CANDIDATE_FORMATS = (
    "ISO8601", "%d.%m.%Y %H:%M:%S.%f", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
    "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M",
    "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y%m%d %H%M%S",
)


class FormatRefused(ValueError):
    pass


def normalise_columns(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a frame with canonical column names (time, open, high, low, close, volume?)."""
    seen = {str(c).strip().lower(): c for c in raw.columns}
    out: dict[str, pd.Series] = {}
    for canon, names in ALIASES.items():
        hits = [seen[n] for n in names if n in seen]
        if len(hits) > 1 and canon != "time":
            raise FormatRefused(f"more than one column matches {canon!r}: {hits}")
        if hits:
            out[canon] = raw[hits[0]]
    missing = [c for c in ("time", "open", "high", "low", "close") if c not in out]
    if missing:
        raise FormatRefused(f"cannot find column(s) {missing}; columns seen: "
                            f"{[str(c) for c in raw.columns]}")
    return pd.DataFrame(out)


def parse_times(col: pd.Series, time_format: str | None = None) -> tuple[pd.Series, str]:
    """Parse a time column; return the times and the format that was used."""
    if pd.api.types.is_datetime64_any_dtype(col):
        return col, "already datetime"
    s = col.astype(str).str.strip()
    if time_format:
        try:
            return pd.to_datetime(s, format=time_format), time_format
        except (ValueError, TypeError) as e:
            raise FormatRefused(f"time_format {time_format!r} does not fit: {str(e)[:150]}") from e
    ok: list[tuple[str, pd.Series]] = []
    for fmt in CANDIDATE_FORMATS:
        try:
            ok.append((fmt, pd.to_datetime(s, format=fmt)))
        except (ValueError, TypeError):
            continue
    if len(ok) == 1:
        return ok[0][1], ok[0][0]
    sample = list(s.head(3))
    if not ok:
        raise FormatRefused(f"no known time format fits {sample}; pass time_format explicitly")
    raise FormatRefused(f"time format is ambiguous ({[f for f, _ in ok]}) for {sample}; "
                        "pass time_format explicitly")


def flat_stats(df: pd.DataFrame) -> dict[str, int]:
    """Count bars with high == low and the longest run of them (filler bars distort variance)."""
    flat = (df["high"] == df["low"]).to_numpy()
    run = best = 0
    for f in flat:
        run = run + 1 if f else 0
        best = max(best, run)
    return {"flat_bars": int(flat.sum()), "longest_flat_run": int(best)}
