# EXP-001: MiniMamba vs HAR and GARCH(1,1), H1 EUR/USD volatility

Labels: **Exploratory | Not validated | Retrospective**. This is an evaluation on one
instrument and one period. It is not a trading signal and makes no profit claim.

Spec hash `7a541633a9161018c7f46aa80a5664293e26193c06e4439f27a542ffb7dca33c`, data `dv:8db0760d82acfc2a`, label: **OANDA PRACTICE FEED - NOT INDEPENDENTLY VERIFIED**.

## Result: TIE

Judged on the holdout (L22). Validation outcome: LOSS.

## Validation (n = 2498)

| model | QLIKE | RMSE | in MCS | MCS p-value |
|---|---|---|---|---|
| har | 0.24743 | 5.332e-07 | yes | 1.000 |
| minimamba | 0.31305 | 6.892e-07 | no | 0.039 |
| persistence | 0.36010 | 6.429e-07 | no | 0.021 |
| historical_mean | 0.36906 | 6.648e-07 | no | 0.000 |
| garch11 | 0.39908 | 7.259e-07 | no | 0.000 |

Model confidence set: level 0.1, 1000 reps, block 24, seed 20261027. Included: har. Excluded: garch11, historical_mean, minimamba, persistence.

**Outcome (validation): LOSS**

Interval coverage (split-conformal, nominal 0.80):

- har: measured 0.725 on 1225 rows (calibrated on 1249; worst rolling-50 0.00; mean width ratio 1.15)
- minimamba: measured 0.781 on 1225 rows (calibrated on 1249; worst rolling-50 0.16; mean width ratio 2.02)

## Holdout (opened once) (n = 2498)

| model | QLIKE | RMSE | in MCS | MCS p-value |
|---|---|---|---|---|
| minimamba | 0.38809 | 5.036e-07 | yes | 1.000 |
| har | 0.39296 | 4.875e-07 | yes | 0.909 |
| historical_mean | 0.58021 | 6.943e-07 | no | 0.000 |
| garch11 | 0.62018 | 7.722e-07 | no | 0.000 |
| persistence | 0.63444 | 5.420e-07 | no | 0.020 |

Model confidence set: level 0.1, 1000 reps, block 24, seed 20261027. Included: har, minimamba. Excluded: garch11, historical_mean, persistence.

**Outcome (holdout): TIE**

Interval coverage (split-conformal, nominal 0.80):

- har: measured 0.590 on 2498 rows (calibrated on 1249; worst rolling-50 0.00; mean width ratio 1.15)
- minimamba: measured 0.721 on 2498 rows (calibrated on 1249; worst rolling-50 0.00; mean width ratio 2.02)

## Variants tried

3 logged trials for EXP-001 (cap in spec: 20).
Per-seed validation QLIKE (diagnostic only): seed1 0.33482, seed2 0.39336, seed3 0.32987

## What was decided outside the locked spec (read before trusting this)
- **L21** Training hyperparameters were not in the spec; they were fixed in code before any
  validation score was seen and never tuned: 8 epochs, batch 64, AdamW lr 0.001,
  weight decay 0.0001, gradient clip 1.0, QLIKE training loss, no early
  stopping, no dropout.
- **L21** "MiniMamba" is the mean of the log-variance forecasts of seeds 1, 2, 3 (no seed
  selection). Per-seed scores are diagnostics only.
- **L22** The spec does not say whether win/tie/loss is judged on validation or holdout. This
  report states both; the headline is the HOLDOUT outcome once it exists, because validation
  was scored first and the holdout is the untouched sample.
- Rows without a full 48-bar context use earlier rows' features as history (train tail for
  validation, validation tail for the holdout); the frame is compacted across market gaps.
- Split-conformal intervals assume exchangeability, which volatility does not satisfy, so
  measured coverage is reported, never assumed.

## Environment

`{"arch": "8.0.0", "minimamba": "1.0.1", "numpy": "2.5.4", "pandas": "3.1.0", "platform": "macOS-15.7.9-x86_64-i386-64bit-Mach-O", "python": "3.14.10", "statsmodels": "0.15.0", "torch": "2.14.1"}`
