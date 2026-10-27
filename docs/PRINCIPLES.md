# Principles

These rules apply to every module, every contract and every screen. If a change breaks one, the change is wrong.

## 1. Nothing renders before it was knowable (causality)
Every signal, level, zone and forecast carries a `known_at` time. A chart, brief or replay at time `t` may only show objects with `known_at <= t`. Swing-based signals are delayed until their swing is confirmed. Every signal producer has a prefix-equality test: computing on `data[:t]` must give the same result for time `t` as computing on the full dataset.

Retrospective analysis (for example trendline fits) is allowed in the premarket view only, and is tagged **Retrospective**. It never feeds a model or a paper trade.

## 2. Paper only
No code path can place a live order. `paper/broker.py` has paper backends only. `SX_TRADING_MODE` must be `paper` or the process refuses to start. Risk gates apply to every order: news blackout, daily-loss halt, maximum open trades, kill switch.

## 3. Label what is not proven
Every surface carries its honest status: **Sample data**, **Exploratory**, **Not validated**, **Retrospective**, **Causal**. Scores are heuristic rankings, never win probabilities. No number is shown as a probability unless it comes from a calibrated model with a visible coverage record.

## 4. Freeze rules before paper runs
Suggestion rules are frozen and hash-checked before each paper run. The runner refuses to start if the hash changed. Tuning on paper results contaminates the forward test, so changed rules mean a new run.

## 5. The holdout is unreachable by default
`lab/partition.py` exposes only train and validation data. The holdout is reachable only through one explicit, logged call. Every hyperparameter trial and model variant is recorded in the ledger so the number of things tried is always known.

## 6. Libraries go through adapters
Output from smart-money-concepts, TA-Lib, trendln and similar libraries is normalized into `Setup` contracts. Causality tests run on every adapter. A library can be swapped without touching anything else.

## 7. LLMs propose, they do not decide
The analyst writes briefs and rationales from structured inputs only. It does not read screenshots, pick trades, or invent numbers. Every claim links to a setup or forecast id.

## 8. Everything is logged and replayable
Every decision, suggestion, order and fill goes to an append-only ledger (JSONL) with the data version and rule version that produced it.

## 9. Costs are real
Paper fills use bid and ask plus slippage. Mid-price results are diagnostics only.

## 10. Dependencies are earned
Every library is listed in `DEPENDENCIES.md` with version, licence, reason and last check. Pin versions, run `pip-audit`, and sandbox-install before adopting. Single-maintainer packages are flagged.
