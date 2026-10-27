"""JSON payload for the web Premarket screen (API response of ``GET /premarket``).

Setups and candles use the contract wire format. The source label is always present, and a
non-live source is always labelled; the web side must show ``source.label`` on every surface.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sx_assistant.premarket.builder import PremarketAnalysis
from sx_core.clock import tf_delta
from sx_core.local_sessions import DEFAULT_LOCAL_SESSIONS, LocalSessionConfig

SCHEMA_VERSION = 1
DISCLAIMER = ("Observed levels and structure from closed bars. Not a forecast, not a trading "
              "signal. Paper trading only.")


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def session_bands(first: datetime, as_of: datetime,
                  cfg: LocalSessionConfig = DEFAULT_LOCAL_SESSIONS) -> list[dict[str, Any]]:
    """Session windows that have started by ``as_of`` (time ranges, not market data)."""
    out: list[dict[str, Any]] = []
    day: date = first.date() - timedelta(days=1)
    while day <= as_of.date():
        for name, (start, end) in cfg.windows_for_day(day).items():
            if end > first and start <= as_of:
                out.append({"id": f"{name}:{day.isoformat()}", "name": name,
                            "t_start": _iso(start), "t_end": _iso(end), "complete": end <= as_of})
        day += timedelta(days=1)
    return sorted(out, key=lambda b: (b["t_start"], b["id"]))


def build_payload(a: PremarketAnalysis) -> dict[str, Any]:
    labels = ["sample", "causal"] if not a.source.live else ["causal"]
    return {
        "schema_version": SCHEMA_VERSION,
        "instrument": a.instrument,
        "tf": a.tf,
        "as_of": _iso(a.as_of),
        "bar_seconds": int(tf_delta(a.tf).total_seconds()),
        "source": {"id": a.source.id, "name": a.source.name, "label": a.source.label,
                   "live": a.source.live},
        "status_labels": labels,
        "data_version": a.data_version,
        "disclaimer": DISCLAIMER,
        "candles": [c.to_wire() for c in a.candles],
        "setups": [s.to_wire() for s in a.setups],
        "session_bands": session_bands(a.candles[0].time, a.as_of),
        "checklist": [i.to_wire() for i in a.checklist],
        "timeline": [{"time": _iso(s.known_at), "setup_id": s.id, "text": s.plain_text}
                     for s in a.setups],
    }
