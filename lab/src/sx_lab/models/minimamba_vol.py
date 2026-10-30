"""MiniMamba variance forecaster (Phase 8B, EXP-001 challenger). CPU only.

Wraps ``minimamba==1.0.1`` ``MambaForFeatureExtraction`` (Mamba blocks over ``(batch, seq,
d_model)`` floats). Everything else is ours: a linear input projection, a linear head on the
LAST step, and a QLIKE training loss (the primary metric of the locked spec).

Causality: row ``i`` is predicted from the feature rows ``i-context+1 .. i`` only (the library
conv is causal: pad ``d_conv-1`` then trim; the scan is checked by ``test_minimamba_vol.py``,
which changes later rows and asserts earlier predictions do not move). ``target`` is read only
by ``fit``. Rows without a full context are left-padded with a copy of the earliest row
available (documented, causal). ``history`` may carry earlier rows' FEATURES (never targets).

Training hyperparameters are NOT in the locked spec; they are fixed here before any validation
score is seen (decision L21) and are never tuned: see ``TrainConfig``.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import asdict, dataclass
from typing import Self

import numpy as np
import pandas as pd
import torch
from minimamba import BaseMambaConfig, MambaForFeatureExtraction
from torch import nn

from sx_lab.baselines.naive import NotFittedError

EPS = 1e-12
_LOG_CLAMP = 12.0


@dataclass(frozen=True)
class TrainConfig:
    d_model: int = 64          # locked spec
    n_layer: int = 2           # locked spec
    context_bars: int = 48     # locked spec
    epochs: int = 8            # L21 (fixed, not tuned)
    batch_size: int = 64       # L21
    lr: float = 1e-3           # L21
    weight_decay: float = 1e-4  # L21
    grad_clip: float = 1.0     # L21
    seed: int = 1


def feature_columns(frame: pd.DataFrame) -> list[str]:
    cols = sorted(c for c in frame.columns
                  if c.startswith(("rv_", "range_var_")) or c in ("atr_14", "ret", "tod_sin",
                                                                   "tod_cos"))
    if not cols:
        raise KeyError("frame has none of the expected feature columns")
    return cols


def _transform(frame: pd.DataFrame, cols: list[str]) -> np.ndarray:
    x = frame[cols].to_numpy(dtype="float64").copy()
    for j, c in enumerate(cols):
        if c.startswith(("rv_", "range_var_", "atr_")):
            x[:, j] = np.log(np.maximum(x[:, j], EPS))
    if not np.isfinite(x).all():
        raise ValueError("NaN or infinite feature")
    return x


class _Net(nn.Module):
    def __init__(self, n_feat: int, cfg: TrainConfig):
        super().__init__()
        mc = BaseMambaConfig(d_model=cfg.d_model, n_layer=cfg.n_layer, use_fast_path=False,
                             device="cpu")
        self.inp = nn.Linear(n_feat, cfg.d_model)
        self.body = MambaForFeatureExtraction(mc)
        self.head = nn.Linear(cfg.d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, T, F) -> (B,)
        return self.head(self.body(self.inp(x))[:, -1, :]).squeeze(-1)


def _windows(x: np.ndarray, idx: np.ndarray, ctx: int) -> np.ndarray:
    """Context windows ending at ``idx`` (row positions); positions < 0 repeat row 0."""
    pos = np.clip(idx[:, None] + np.arange(-ctx + 1, 1)[None, :], 0, None)
    return x[pos]


class MiniMambaVol:
    name = "minimamba_seed"

    def __init__(self, cfg: TrainConfig | None = None):
        self.cfg = cfg or TrainConfig()
        self.name = f"minimamba_seed{self.cfg.seed}"
        self.net: _Net | None = None
        self.cols: list[str] = []
        self.mu = self.sd = self.a = self.b = None
        self.loss_by_epoch: list[float] = []
        self.train_rows = 0

    def fit(self, train: pd.DataFrame, log=None) -> Self:
        cfg = self.cfg
        torch.manual_seed(cfg.seed)
        self.cols = feature_columns(train)
        x = _transform(train, self.cols)
        self.mu, self.sd = x.mean(0), np.maximum(x.std(0), 1e-8)
        xs = (x - self.mu) / self.sd
        logy = np.log(train["target"].to_numpy(dtype="float64"))
        self.a, self.b = float(logy.mean()), float(max(logy.std(), 1e-8))
        self.net = _Net(len(self.cols), cfg)
        opt = torch.optim.AdamW(self.net.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
        order = np.arange(cfg.context_bars - 1, len(xs))      # full-context samples only
        self.train_rows = len(order)
        gen = np.random.default_rng(cfg.seed)
        yt = torch.tensor((logy - self.a) / self.b, dtype=torch.float32)
        self.net.train()
        for _ in range(cfg.epochs):
            gen.shuffle(order)
            total = 0.0
            for s in range(0, len(order), cfg.batch_size):
                idx = order[s:s + cfg.batch_size]
                w = torch.tensor(_windows(xs, idx, cfg.context_bars), dtype=torch.float32)
                out = self.net(w)
                d = ((yt[idx] - out) * self.b).clamp(max=_LOG_CLAMP)   # ln(y) - ln(f)
                loss = (torch.exp(d) - d - 1.0).mean()                 # QLIKE
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), cfg.grad_clip)
                opt.step()
                total += float(loss.detach()) * len(idx)
            self.loss_by_epoch.append(total / len(order))
            if log:
                log(f"seed {cfg.seed} epoch {len(self.loss_by_epoch)}/{cfg.epochs} "
                    f"train QLIKE {self.loss_by_epoch[-1]:.5f}")
        return self

    def predict_log(self, frame: pd.DataFrame, history: pd.DataFrame | None = None
                    ) -> np.ndarray:
        if self.net is None or self.mu is None:
            raise NotFittedError("call fit() first")
        full = pd.concat([history, frame]) if history is not None and len(history) else frame
        xs = (_transform(full, self.cols) - self.mu) / self.sd
        start = len(full) - len(frame)
        idx = np.arange(start, len(full))
        self.net.eval()
        out = []
        with torch.no_grad():
            for s in range(0, len(idx), 256):
                w = torch.tensor(_windows(xs, idx[s:s + 256], self.cfg.context_bars),
                                 dtype=torch.float32)
                out.append(self.net(w).numpy().astype("float64"))
        return self.a + self.b * np.concatenate(out)

    def predict(self, frame: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.Series:
        return pd.Series(np.exp(self.predict_log(frame, history)), index=frame.index,
                         name=self.name)

    def params(self) -> dict[str, object]:
        return {**asdict(self.cfg), "torch": torch.__version__, "features": self.cols,
                "threads": torch.get_num_threads(), "rows": self.train_rows}

    def state_bytes(self) -> bytes:
        if self.net is None:
            raise NotFittedError("call fit() first")
        buf = io.BytesIO()
        torch.save({"net": self.net.state_dict(), "cols": self.cols, "mu": self.mu,
                    "sd": self.sd, "a": self.a, "b": self.b, "cfg": asdict(self.cfg)}, buf)
        return buf.getvalue()

    @classmethod
    def from_state_bytes(cls, blob: bytes) -> Self:
        st = torch.load(io.BytesIO(blob), weights_only=False)
        m = cls(TrainConfig(**st["cfg"]))
        m.cols, m.mu, m.sd, m.a, m.b = st["cols"], st["mu"], st["sd"], st["a"], st["b"]
        m.net = _Net(len(m.cols), m.cfg)
        m.net.load_state_dict(st["net"])
        return m


class MiniMambaEnsemble:
    """THE MiniMamba forecast for EXP-001: mean of the seeds' log-variances (decision L21).
    There is no seed selection; per-seed scores are diagnostics only."""

    name = "minimamba"

    def __init__(self, members: list[MiniMambaVol]):
        self.members = members

    @classmethod
    def train(cls, train: pd.DataFrame, seeds: list[int], base: TrainConfig | None = None
              ) -> Self:
        base = base or TrainConfig()
        return cls([MiniMambaVol(TrainConfig(**{**asdict(base), "seed": s})).fit(train)
                    for s in seeds])

    def predict(self, frame: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.Series:
        logs = np.mean([m.predict_log(frame, history) for m in self.members], axis=0)
        return pd.Series(np.exp(logs), index=frame.index, name=self.name)

    def params(self) -> dict[str, object]:
        return {"seeds": [m.cfg.seed for m in self.members],
                "members": [m.params() for m in self.members]}


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()
