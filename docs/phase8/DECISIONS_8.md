
## Lab decisions from the Phase 8 split (2026-10-27)

| # | Decision | Status |
|---|---|---|
| L10 | Phase 8 is split into 8A (infrastructure, conformal, MCS, regime, data path, frozen pre-registration) and 8B (challengers, one EXP-001 run, results, web Lab screen). | Confirmed (owner request, 2026-10-27) |
| L11 | The EXP-001 runner refuses to start on data labelled SAMPLE/synthetic, if the spec hash differs from the ledger lock, or if the holdout was already opened. | Proposed |
| L12 | Proposed spec defaults for EXP-001 (owner to approve or change in 8A): H1 bars, horizon 24, primary metric QLIKE, secondary RMSE and interval coverage, model confidence set at 10%, split 60/20/20 with embargo = horizon (L2, L3), holdout opened once, an explicit cap on variants tried. | Proposed |
