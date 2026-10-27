
## Phase 8A answers (owner decisions, 2026-10-27)

Numbering follows the existing log (L10 confirmed; L11 and L12 proposed; L13 proposed). Adjust L14 and L15 if those numbers are already taken.

### L12: EXP-001 default specification: CONFIRMED
Recorded as the experiment's initial configuration, not as universally optimal settings.

| Item | Value |
|---|---|
| Forecast input timeframe | H1 bars |
| Forecast horizon | 24 hours |
| Primary metric | QLIKE |
| Model confidence set level | 10% |
| Partition | chronological 60/20/20 train/validation/holdout |
| Holdout access | one explicit, logged evaluation call, only after the spec and model selection are frozen |

Safeguards:
- Leakage controls at every partition boundary must cover the 24-bar horizon (purge or embargo of at least 24 bars).
- Logging access to the holdout is necessary but not sufficient. A second open must be refused by the runner, and results seen on the holdout must not feed back into model or spec changes. A changed spec is a new experiment with a new ID.
- To check before freezing: `lab/src/sx_lab/partition.py` must implement exactly this split and the purge. This is not yet verified.

### L13: Where neural models run: AMENDED (supersedes the Proposed text)
- Mac (Intel x86_64): data preparation, Naive/HAR/GARCH baselines, evaluation, reporting, development.
- Linux: initial target for MiniMamba execution.
- MPS/GPU: not a requirement for EXP-001.
- Spike finding (see PROGRESS entry): PyTorch 2.14.1 and minimamba 1.0.1 do run on the Mac from a conda-forge environment. Throughput is about 3,000 tokens/s for a tiny model, so the Mac is a viable fallback or smoke-test host for small configurations.
- Revisit trigger: if the frozen spec fixes a small model (about 64 dimensions, 2 layers) and short context (24 to 64 bars), running on the Mac becomes practical. Larger configs, long context or a large search budget stay on Linux.
- conda-forge Intel-Mac builds may stop being published. Whatever environment runs the experiment must have exact versions and hashes recorded in the ledger.

### L14: Real data source for EXP-001: PROPOSED to CONFIRMED
- OANDA practice is the primary operational source (bid, ask, mid; closed candles; UTC timestamps).
- Dukascopy is retained for historical research and cross-checking, subject to data-quality and timestamp validation.
- Phase 8A uses a frozen, versioned dataset. Neither provider is treated as verified just because its module exists.
- Before the first real-data experiment, verify actual output, coverage, missing bars, timezone handling and reproducibility. The runner must refuse sample or synthetic data (L11).

### L15: Model scope for EXP-001: CONFIRMED
| Model | Role |
|---|---|
| Naive | required reference baseline |
| HAR | strong interpretable volatility baseline |
| GARCH | classical volatility baseline |
| MiniMamba | initial neural challenger |

NeuralForecast and Chronos are deferred. Their install and runtime compatibility are unverified. The research question stays: does MiniMamba improve volatility forecasting over HAR and GARCH on the specified evaluation? A tie or a loss is a valid result.

### 8A scope boundary
In scope: infrastructure, data provenance, chronological partitions, evaluation safeguards, the experiment specification and dependency verification.
Out of scope: model training. No training until those foundations are tested and EXP-001.yaml is owner-approved and hash-locked.
