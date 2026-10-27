
## Lab decisions from Phase 7A (owner approved P1 and P2, 2026-10-27)

| # | Decision | Status |
|---|---|---|
| L1 (was P1) | Lab goal is volatility and regime forecasting, not direction. Direction is a separate research question. | Confirmed (owner, 2026-10-27) |
| L2 (was P2) | Chronological 60/20/20 train/validation/holdout. Holdout is opened by one logged call, only after the evaluation spec hash is locked in the ledger, and once per holdout content; later calls are refused. | Confirmed (owner, 2026-10-27) |
| L3 | Embargo: `embargo >= horizon` rows are dropped before validation and before the holdout so overlapping target windows cannot straddle a boundary. Default embargo = horizon; smaller is refused. Claude's choice, not yet reviewed. | Proposed |
| L4 | Variance scale: features, target and forecasts are per-bar means of squared close-to-close log returns. Target = mean over bars t+1..t+h from the bar-t close. Horizon must be one of the feature windows. Claude's choice, not yet reviewed. | Proposed |
