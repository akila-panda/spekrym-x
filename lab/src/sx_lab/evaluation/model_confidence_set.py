"""Model confidence set (Hansen, Lunde, Nason) through ``arch.bootstrap.MCS`` (Phase 8A).

We wrap the library and do not assume behaviour beyond what the tests pin. Facts read from the
installed ``arch`` 8.0.0 source: the bootstrap indices are drawn once at construction (so a
given seed is deterministic), the default block size is ``int(sqrt(T))``, ``losses`` must have
at least two columns, and ``compute()`` fills ``included`` / ``excluded`` / ``pvalues``.

Overlapping horizon-h targets make per-row losses autocorrelated up to lag h, so the block
size must be at least the horizon; the wrapper refuses a smaller one. The MCS is a statement
about the evaluation sample only (Exploratory), never a ranking to trade on.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from arch.bootstrap import MCS

from sx_lab.evaluation.metrics import qlike_losses


class McsError(ValueError):
    pass


@dataclass(frozen=True)
class McsResult:
    level: float
    included: tuple[str, ...]
    excluded: tuple[str, ...]
    pvalues: dict[str, float]
    block_size: int
    reps: int
    seed: int
    method: str
    n: int


def qlike_loss_frame(forecasts: pd.DataFrame, realized: pd.Series) -> pd.DataFrame:
    """One QLIKE loss column per model (columns of ``forecasts``), aligned on the index."""
    if not forecasts.index.equals(realized.index):
        raise McsError("forecasts and realized values must share the same index")
    return pd.DataFrame({c: qlike_losses(forecasts[c].to_numpy(), realized.to_numpy())
                         for c in forecasts.columns}, index=forecasts.index)


def model_confidence_set(losses: pd.DataFrame, *, horizon: int, level: float = 0.10,
                         reps: int = 1000, block_size: int | None = None, seed: int,
                         method: str = "R") -> McsResult:
    if losses.shape[1] < 2:
        raise McsError("need at least two models")
    if not np.isfinite(losses.to_numpy()).all():
        raise McsError("NaN or infinite loss")
    block = block_size if block_size is not None else max(horizon, int(np.sqrt(len(losses))))
    if block < horizon:
        raise McsError(f"block_size {block} is below the horizon {horizon}")
    mcs = MCS(losses, size=level, reps=reps, block_size=block, method=method,  # type: ignore[arg-type]
              bootstrap="stationary", seed=seed)
    mcs.compute()
    pv = mcs.pvalues["Pvalue"]
    return McsResult(level, tuple(map(str, mcs.included)), tuple(map(str, mcs.excluded)),
                     {str(k): float(v) for k, v in pv.items()}, block, reps, seed, method,
                     len(losses))
