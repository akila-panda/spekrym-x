
## Lab decisions from Phase 7B (Claude's choices, not yet reviewed by the owner)

| # | Decision | Status |
|---|---|---|
| L5 | `Forecast` interval in 7B is the training-set quantile band of target/prediction ratios (80% nominal), widened so the point lies inside. It is NOT conformal; Phase 8 replaces it. Empirical coverage is measured and stored in `track_record`. Point and interval are per-bar volatility (sqrt of mean squared return). Status `exploratory`. | Proposed |
| L6 | HAR is a level OLS on rv_6, rv_24, rv_120. Predictions are floored at the smallest training target; the count floored is reported. | Proposed |
| L7 | GARCH(1,1): `arch` estimates omega, alpha, beta on the training frame; forecasts use our own recursion (started from the first row's rv_120) so no library forecasting behaviour is assumed. A non-converged or non-stationary fit raises and is shown as FAILED, never hidden. | Proposed |
| L8 | Search: Optuna TPE (seeded) over HAR short window {3,6,12} and long window {72,120}, objective = validation QLIKE, every trial in the ledger as `lab.trial`. `variants_tried` counts trials including repeats. The dataset is built once with windows (3,6,12,24,72,120) so every trial shares one holdout. | Proposed |
| L9 | CLI exit code: `evaluate` returns non-zero only if the leak guard fails. A failed shuffled-label control is reported as "no measurable skill", not as an error. The CLI never opens the holdout. | Proposed |
