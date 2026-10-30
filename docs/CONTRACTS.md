# Contracts

Shared data shapes. Python side: pydantic models in `core/src/sx_core/contracts/`. Web side: zod schemas in `apps/web/src/contracts/`. Both must agree. Changes are additive; never rename a field without a migration.

## Conventions
- Times are UTC. Wire format is ISO-8601 strings. Field names are snake_case.
- Every produced record carries the versions that made it: `data_version`, `rules_version`, `model_version` where relevant.
- Every market-derived record has `event_time` (when it happened) and `known_at` (when a live system could first have known it).
- Ids are deterministic hashes of semantic fields, never of measured price values, so ids stay stable.
- `status` labels: `sample`, `exploratory`, `not_validated`, `retrospective`, `causal`.

## Candle
```
Candle {
  instrument: str          # "EUR_USD"
  tf: "M1"|"M5"|"M15"|"M30"|"H1"|"H4"|"D"
  time: datetime           # bar open, UTC
  open, high, low, close: float
  volume: float
  bid_close?: float        # optional bid/ask for cost-real fills
  ask_close?: float
  complete: bool           # closed bars only enter analysis
}
```

## Setup
A detected structure or pattern. Output of the TA adapters.
```
Setup {
  id: str
  kind: "swing"|"bos"|"choch"|"fvg"|"order_block"|"liquidity_sweep"
        |"session_level"|"support_resistance"|"candle_pattern"
  instrument, tf
  direction: "bullish"|"bearish"|"neutral"
  geometry: { price_low, price_high, t_start, t_end? }   # box or line
  event_time, known_at
  lifecycle: "fresh"|"tested"|"mitigated"|"broken"
  source: { library, version, adapter }
  plain_text: str          # one-line plain-language description
  invalidation: str        # what would invalidate it
  status: "causal"|"retrospective"
}
```

## Forecast
Output of the Lab.
```
Forecast {
  id, instrument, tf
  issued_at, horizon_end
  target: "realized_vol"|"range"
  point: float
  interval: { low, high, nominal_coverage }     # conformal
  regime?: "quiet"|"normal"|"expanding"|"extreme"
  model: { name, version, params_hash }
  baseline_comparison?: { baseline, metric, delta }
  track_record: { n, empirical_coverage, variants_tried }
  status: "exploratory"|"not_validated"
}
```

## Suggestion
```
Suggestion {
  id, instrument, tf, created_at
  setup_ids: [str]         # evidence
  forecast_id?: str
  side: "long"|"short"
  entry, stop, target: float
  score: float             # heuristic ranking, NOT a probability
  reasons: [ { text, evidence_id } ]
  gates: [ { name, passed, detail } ]
  rules_version: str
  status: "not_validated"
}
```

## PaperOrder
```
PaperOrder {
  id                       # idempotent client order id
  suggestion_id
  backend: "sim"|"oanda_practice"|"ib_paper"
  side, units, entry, stop, target
  intended_fill, actual_fill?, slippage?
  state: "pending"|"filled"|"closed"|"rejected"|"cancelled"
  opened_at?, closed_at?, pnl?
  rules_version
}
```

## LedgerEntry
Append-only JSONL.
```
LedgerEntry { ts, kind, payload, data_version, rules_version?, hash }
```

## Python implementation notes (Phase 2)
No field was added, renamed or removed. Conventions the Python side enforces:
- Models are immutable, reject unknown fields, and reject NaN and infinity.
- Datetimes must be timezone-aware; they are converted to UTC and serialised as `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`.
- `to_wire()` omits unset optional fields (zod rejects `null` for `.optional()`); free-form `payload` contents are kept as written.
- Ids: `setup:`, `fc:`, `sug:`, `ord:` plus 16 hex characters; built in `sx_core.contracts.ids` from non-price fields only.
- Ledger chain: see I1 in `docs/DECISIONS.md`. A ledger line is the canonical JSON of the entry, keys sorted.
- Frozen golden records for every contract: `tests/fixtures/contracts/*.json`.

## Phase 4 notes (Setup producers in `assistant/ta`)
No field was added, renamed or removed. Conventions the producers follow:
- `swing` and `session_level`: `direction` is `bearish` for a high and `bullish` for a low (orientation, not a forecast; I11). `geometry` is a line (`price_low == price_high`).
- `fvg` and `order_block`: `geometry` is the zone box; `event_time` is the middle candle (FVG) or the block candle; `known_at` is when the zone could first be seen.
- `bos` and `choch`: `event_time` is the breaking bar; `known_at` is later, when the library can first label the break (the next swing must be confirmed). `geometry` is a line at the broken level from the broken swing to the breaking bar.
- `liquidity_sweep`: `direction` is `neutral`; `event_time` is the sweeping bar.
- `candle_pattern`: `geometry` is the pattern bar's range box.
- `support_resistance` (trendln): `status` is `retrospective`; `geometry` is the bounding box of a sloped line (I16); `known_at` is the close of the last bar of the window.
- Ids use the discriminators in each adapter (for example `asia_high:2026-10-19`, `p:20261019T0245`); never a price.
- Producers always emit `lifecycle = fresh`; lifecycle at a time `t` is computed by `sx_assistant.ta.normalize.lifecycle_at` (I13).

## Premarket payload (API, Phase 5A; additive, no contract changed)
`GET /premarket?instrument=EUR_USD&as_of=<UTC ISO>` returns `{schema_version:1, instrument, tf, as_of, bar_seconds, source:{id,name,label,live}, status_labels:["sample","causal"], data_version, disclaimer, candles:[Candle], setups:[Setup], session_bands:[{id,name,t_start,t_end,complete}], checklist:[{id,tf,text,known_at}], timeline:[{time,setup_id,text}]}`. Every setup, checklist item and timeline entry has `known_at <= as_of`. `source.label` must be shown on every surface (`SAMPLE DATA — NOT LIVE` for the fixture). `as_of` after the newest closed bar, without a timezone, or unparsable gives 422; unknown instrument 404. `/suggestions`, `/paper`, `/lab` return `{status:"not_built", items:[]}`. The zod mirror of this payload is Phase 5B.

The zod mirror of the premarket payload is `apps/web/src/contracts/premarket.ts` (Phase 5B). It also rejects any setup or checklist item with `known_at` after `as_of`. A frozen copy of a real API response is `apps/web/src/test/fixtures/premarket_payload.json` (made from the sample fixture at as_of 2026-10-26T12:00Z); regenerate it if the payload changes.

## Suggestions API envelope (Phase 9B; additive, the `Suggestion` record above is unchanged)
`GET /suggestions?instrument=&as_of=` returns `{status: "ok"|"no_result"|"model_unavailable", instrument, tf: "H1", as_of, source{id,name,label,live}, labels[], scorer{stage: "none"|"validated"|"complete", reading, validation|null, holdout|null}, items[{suggestion, labels, model_version, note}], evidence[Setup], candles[last 72 H1 bars], rejected[{setup_id, why}], note}`. Rules: every `reasons[].evidence_id` is one of that suggestion's `setup_ids` or its `forecast_id`; every `setup_ids` entry is in `evidence`; `status` is always `not_validated`; `score` is a rank from 0 to 100 against validation-period scores, never a probability. Mirror: `apps/web/src/contracts/suggestions.ts` (both rules are enforced there).
