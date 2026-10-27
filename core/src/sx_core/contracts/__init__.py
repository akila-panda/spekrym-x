"""Shared contracts. Mirror of ``apps/web/src/contracts`` (zod) and ``docs/CONTRACTS.md``."""

from sx_core.contracts._base import Contract, Direction, Side, Tf, UtcDatetime, format_utc
from sx_core.contracts.candle import Candle
from sx_core.contracts.forecast import (
    BaselineComparison,
    Forecast,
    Interval,
    ModelRef,
    Regime,
    TrackRecord,
)
from sx_core.contracts.ids import (
    forecast_id,
    make_id,
    order_id,
    setup_id,
    suggestion_id,
)
from sx_core.contracts.ledger_entry import LedgerEntry
from sx_core.contracts.paper_order import PaperOrder
from sx_core.contracts.setup import Geometry, Setup, Source
from sx_core.contracts.suggestion import Gate, Reason, Suggestion

__all__ = [
    "BaselineComparison", "Candle", "Contract", "Direction", "Forecast", "Gate", "Geometry",
    "Interval", "LedgerEntry", "ModelRef", "PaperOrder", "Reason", "Regime", "Setup", "Side",
    "Source", "Suggestion", "Tf", "TrackRecord", "UtcDatetime", "forecast_id", "format_utc",
    "make_id", "order_id", "setup_id", "suggestion_id",
]
