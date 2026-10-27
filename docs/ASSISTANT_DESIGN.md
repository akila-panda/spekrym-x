# Assistant design (Module B)

Purpose: structured preparation and honest forward testing, not an auto-trader.

## Pipeline
Candles -> causal TA adapters -> `Setup` contracts -> premarket chart and brief -> scorer + analyst -> `Suggestion` with evidence -> risk gates -> `PaperBroker` -> ledger -> scorecard.

## Layers
- `ta/`: library output normalized to `Setup`; causal wrapper delays swing signals until confirmed; retrospective tools are premarket only.
- `premarket/`: builds the chart payload and the 6-step brief from closed bars.
- `model/`: triple-barrier labels, LightGBM scorer with SHAP reasons, time-ordered splits with a gap. Score is a heuristic ranking.
- `analyst/`: typed LLM output from structured inputs; bull/bear challenge step.
- `suggestions/`: combine setups, score and Lab forecast; every claim links to an id; risk gates on every order.
- `paper/`: internal simulator (bid/ask fills, slippage), OANDA practice, IB paper. Idempotent order ids, kill switch.
- `review/`: scorecard of forward results against frozen rules, and a journal.
