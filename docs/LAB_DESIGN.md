# Lab design (Module A)

Purpose: forecast volatility and regime so a trader can size stops, judge whether a target is realistic, and avoid quiet or choppy conditions. Not a buy/sell or direction tool.

## Pipeline
Candles (closed bars) -> causal volatility and session features -> models -> calibrated intervals -> `Forecast` contracts in `lab/outputs/`.

## Models
- Baselines: naive, HAR, GARCH (`arch`). These are the bar to beat.
- Challengers: `minimamba` (CPU), neuralforecast models, Chronos zero-shot (baseline only).
- Regime: Markov switching with filtered probabilities only. Change-point detection is offline labelling only.

## Evaluation
QLIKE and RMSE, interval coverage, Model Confidence Set. Negative controls (shuffled labels, a deliberately leaked feature) must fail. Every trial and variant is counted in the ledger.

## First experiment
`EXP-001`: minimamba vs HAR and GARCH on QLIKE with a Model Confidence Set, train and validation only. Pre-register the spec before running. Expectation: it ties or loses, and a documented tie is a valid result.
