# spekrym-x — Development Plan and Handoff

**Purpose of this file:** everything a new Claude session (chat or Claude Code) needs to continue the build without the earlier conversation. Read this first, then `docs/PROGRESS.md`, then the docs it points to.

Last updated: 2026-10-28 (Phase 9C-1 analyst core built, P6 resolved; earlier: 9B Suggestions screen bug fixed, 9A holdout NULL; earlier: Phase 9B code built, no real scorer yet; Phase 9A real-data run in progress on the owner's Mac; earlier same day: Phase 8 closed, Phase 9 split into 9A/9B/9C, X16 and X17; EXP-001 run and shown; earlier: EXP-001 locked; earlier: Phase 8A built; earlier: Phases 0 to 7B; see `docs/PROGRESS.md`).

## 0. Start here (new session, 60 seconds)

**NEXT (2026-10-28, Phase 9C-2 built): persisted provider state, daily caps, brief reuse, `AnalystService` and `/analyst/*` API routes are built and pass 62 analyst tests in my sandbox; no real provider call has been made by me. Owner's 9C-1 run: `check` accepted both keys. Owner still has to confirm the free plans in `approved_models.json` (Gemini shows Free tier; Groq plan not yet seen), run `brief`, and ROTATE both keys (they were pasted in chat). Next: 9C-3 (bull/bear step, brief drawer in the web app, fixed evaluation set) only when the owner says go; A8 (data terms) is still open.**

**NEXT (2026-10-28, Phase 9C-1 built): P6 is RESOLVED (A1: zero-cost router, Groq and Gemini first). The analyst core is BUILT (interface, Groq and Gemini adapters, evidence packet, validator, router, offline demo; 46 mocked tests pass in my sandbox) but has NOT called the real providers. Owner runs the steps under 'Phase 9C-1 notes' in PROGRESS (add keys to `.env`, confirm free plan in `approved_models.json`, `check`, `brief`). The keys were pasted in chat: rotate them. Next: 9C-2 (second provider hardening, persisted quota and cooldown state, API route) and 9C-3 (bull/bear step, brief drawer, evaluation set) only when the owner says go; A8 (data terms) is open.**

**NEXT (2026-10-28, dataset management): Lab Data tab can delete (to trash), restore and lock in-use datasets (L24, see 'Dataset management' in PROGRESS). Owner tries it. P6 still blocks 9C.**

**NEXT (2026-10-28, 9B bug fix): 9A has been RUN: holdout opened once, NULL (AUC 0.506, shuffled p95 0.520). The Suggestions screen was empty because the API sent `forecast_id: null`; fixed with `to_wire()` (see 'Phase 9B fix and 9A result' in PROGRESS). Next: owner reloads the screen (9B done-when), decides S7 and P6; then 9C. Do not retrain or re-open the holdout.**

**NEXT (2026-10-28, Phase 9B built): Phase 9B CODE IS BUILT (suggestions engine, evidence rules, advisory gates, real `/suggestions` route, Suggestions screen; decisions S1 to S8). Verified in my sandbox only on synthetic fixtures (new Python tests 10 passed, API 37 passed, ruff clean, web 91 passed, build OK). It has NOT been run with a real scorer or reviewed in a browser. The owner's 9A `validate` was still running at the last log (4320/12864 setups); its output and the controls are unknown to me and the holdout is NOT opened (open it once, only after the validation output has been read). libomp on the Intel Mac was fixed by a symlink into the conda env (see 'Owner environment fix' in PROGRESS). The Command Line Tools were deleted and not reinstalled. Next: owner reviews the Suggestions screen (9B done-when), then 9C only after P6 is decided. Open question S7: should a null 9A result hide the suggestion list?**

**(Superseded) NEXT (2026-10-28, Phase 9A built): Phase 9A CODE IS BUILT (model, protocol P11, controls, scorer, Lab badge fix X17) and tested on synthetic fixtures only; it has NOT been run on real data. The owner runs `validate`, reads it, then opens the holdout once (see 'Phase 9A notes' at the end of docs/PROGRESS.md for the order). P11 is CONFIRMED. 9B (suggestions engine) starts only when the owner says go; it needs a 9A result (even a null one) to read. 9C stays blocked on P6. Plan file names differ from the code (`labels.py` vs `labels_triple_barrier.py`, `train.py` vs `train_lgbm.py`, `reasons.py` vs `explain_shap.py`): the code names are kept (M9).**

**(Superseded) NEXT (2026-10-28, docs-only update done): Phase 8 is CLOSED PENDING the owner's commit and close-out checks (X16). Phase 9 is split (X17): build 9A (`assistant/model`) next, only when the owner says go. 9C is blocked on P6. The Lab badge fix is CONFIRMED (presentation-only, see X17). The 9A evaluation protocol (P11) is still unconfirmed; ask first. See section 5a.**

**LATEST (2026-10-28, end of day): EXP-001 HAS BEEN RUN. Validation LOSS, holdout TIE (headline, L22); holdout spent; L21 to L23 confirmed. Phase 8C (web Lab EXP-001 tab, Forecast tab, API `/lab/exp001`) is BUILT, owner has not run it. Phase 9 is next only when the owner says go and decides P6 (Pydantic AI vs Anthropic SDK). See 'EXP-001 RESULT' and 'Phase 8C notes' at the end of docs/PROGRESS.md. Older notes below are superseded.**

**LATEST (2026-10-28, later): Phase 8B CODE IS BUILT (runner, MiniMamba wrapper, report, tests; 10 new tests pass in the sandbox) but EXP-001 has NOT been run. The owner runs `sx-lab exp001-validate`, reviews, then `exp001-holdout`; see 'Phase 8B build notes' at the end of docs/PROGRESS.md and decisions L21 to L23.** (Earlier today: EXP-001 is APPROVED AND LOCKED (spec 7a541633a9161018, real OANDA practice H1, 12,864 bars, holdout sealed). Phase 8A is done; Phase 8B is next only when the owner says go. Read 'START HERE FOR PHASE 8B' at the end of docs/PROGRESS.md first; it has the full 8B handoff and the open compute decision (rerun full suite, where MiniMamba trains, regenerate the OANDA token).** (Older note, now superseded: Phase 8A is BUILT but NOT complete. Code and tests are done (130 Lab+data tests passed in the sandbox; owner has not run them). Still open: no real data has ever been imported, and `lab/experiments/prereg/EXP-001.yaml` is a DRAFT that cannot lock until the owner fills `data.*`, reviews the PROPOSED values and approves it. Phase 8B must not start until the spec is locked (`sx-lab lock`). Phases 5, 6 and 7 are built (the status text below this note is older; trust `docs/PROGRESS.md`). Do not recreate a standalone `DEVELOPMENT_PLAN.md` upload; this file is the one.

**Status:** Phases 0 to 4 built, plus a pre-Phase-5 pass (2026-10-27): P10 built as X14, I10 approved, I15 definitions built (numbers still unapproved), issue 27 replay about 4 to 5 times faster. Phase 5 is split in two (owner request, 2026-10-27): **5A (backend: premarket builder + API) is BUILT and owner-verified** (454 passed, ruff clean, endpoints and live-mode refusal checked, 2026-10-27); next build is **5B (web hookup, multi-timeframe strip, ATR, static brief) is BUILT** (owner has not yet run it); next is the owner's visual review, then Phase 6 only when the owner says go. **Phase 5 data source (owner, 2026-10-27): frozen EUR/USD fixtures labelled `SAMPLE DATA — NOT LIVE` on every surface, behind a data-source interface so a verified provider can be added later; do not call the OANDA client working until it has fetched real candles.** **Chart zone pass (2026-10-27): FVG, order-block and BOS/CHoCH drawing BUILT, awaiting the owner's browser look.** **Phase 6 is split (2026-10-27): 6A (simulator core) is BUILT and owner-verified (473 passed, ruff clean, live-mode refusal checked, 2026-10-27); 6B (risk gates, frozen rules, runner) is BUILT and owner-verified (487 passed, ruff clean, freeze hash and changed-rules refusal checked, 2026-10-27); Phase 7 only when the owner says go.** **Housekeeping 2026-10-27:** owner's suite is 461 passed; the root `pyproject.toml` was missing and has been reconstructed (I25), which explains the 70 ruff findings; root `README` and `Makefile` are also missing. Open items: first run against the real OANDA practice API (issue 18, account access unconfirmed), the Phase 1 visual review (light mode bands, label overlap) and P8.

**Do first:** (1) read this file, `docs/PROGRESS.md`, `docs/PRINCIPLES.md`; (2) unzip the owner's repo zip into its own empty folder and trust the code over the docs; (3) make a venv (Python 3.12 or newer; the minimum is 3.12, X9) and run `pip install -e "core[dev]" -e data -e "assistant[dev,retro]"` and `pip install --no-deps smartmoneyconcepts==0.0.27` (no numba needed), then `pip install -e apps/api` and `pytest -q` and `ruff check .` to confirm the baseline (459 expected after 5B, 454 confirmed on the owner's Mac after 5A; 430 before it, 0 skipped as of 2026-10-27; it was 283 before the pre-Phase-5 pass) before changing anything.

**Before Phase 5:** read the Phase 4 notes and the pre-Phase-5 notes in `docs/PROGRESS.md`, and decisions X14, I10 to I18 in `docs/DECISIONS.md`. Use `previous_day_levels(candles, on, calendar)` for "the previous-day level on date X"; it already implements Monday-uses-Friday. Run long histories with the default `engine="fast"` and see `scripts/bench_smc_replay.py` for timings (768 bars of M15 took about 11 s on the sandbox; still quadratic).

**Owner's last verified state (2026-10-27, after Phase 4): Mac (Intel, Python 3.14.3), `pytest` 283 passed, 0 skipped. (Earlier, 2026-10-26, before Phase 4:)** Mac, Python 3.14 in `.venv`, `pytest` 176 passed, `ruff` clean. `.env` created from `.env.example`; the OANDA practice token is not yet in it. The owner is not sure OANDA offers practice accounts in Sri Lanka (not confirmed either way; see known issue 24).

---

## 1. What this project is

A **decision-support desk for a discretionary FX trader**. It prepares the trading day, flags setups with evidence, forecasts volatility, and lets the user test suggestions on a **paper** account. It never trades live and makes no profit claims.

It is a **brand-new, standalone project**. It imports nothing from any earlier project, and no earlier rules, verdicts or decisions apply. Do not reference the old "Judge", RELAY, D1–D12, or `NO_INTRADAY_EDGE` anywhere.

Two modules joined only by `core/` contracts and files:
- **Lab (Module A):** volatility and regime forecasting. Baselines (naive, HAR, GARCH) vs challengers (minimamba CPU Mamba, neuralforecast, Chronos zero-shot), conformal intervals, honest evaluation. Not a direction or buy/sell tool.
- **Assistant (Module B):** causal technical analysis, premarket brief and chart, setup scoring, suggestions with evidence, paper trading, review.

Source documents (already in the repo):
- `docs/PRINCIPLES.md` — ten rules. If a change breaks one, the change is wrong.
- `docs/DECISIONS.md` — confirmed (X1–X9), proposed (P1–P6, P8) and implementation notes (I1–I5).
- `docs/CONTRACTS.md` — Candle, Setup, Forecast, Suggestion, PaperOrder, LedgerEntry.
- `docs/UI_DESIGN.md` — tokens, shell, screens, components.
- `docs/LAB_DESIGN.md`, `docs/ASSISTANT_DESIGN.md`, `docs/DEPENDENCIES.md`.
- `docs/research/SPEKRYM_NEW_MODULES_RESEARCH.md` — library research. **Nothing in it has been installed or audited.** Its version numbers and claims are unverified.

---

## 2. Owner and environment

- Owner: a single discretionary trader in Sri Lanka (Asia/Colombo, UTC+5:30, no DST). Mac (**Intel x86_64**, seen from pip's wheel names on 2026-10-27; not Apple Silicon), **Python 3.14.3** in `.venv` at the repo root, Node v22.21.1, npm 10.9.4, GitHub Desktop, an IDE with a terminal. The owner's shell does not have a bare `pip`; give `source .venv/bin/activate` then `python -m pip ...` and `python -m pytest`.
- **No GPU.** Mamba runs through `minimamba` on CPU (MPS optional). The official `mamba-ssm` is deferred until a CUDA GPU exists.
- The owner has **not committed anything yet** (as of this file). Do not assume git history exists.
- Dev ports 5173 and 5174 are often occupied by old Vite servers; Vite falls back to 5175.
- The owner's repo folder is `spekrym-x/`. The web app is `apps/web/`.

### How files reach the owner (important)
Claude's chat sandbox cannot see the owner's Mac. Work is delivered as **zip files** the owner unzips into the repo root. Lessons already learned:
1. Every delivery must unzip correctly from the **repo root**: paths inside the zip start at `apps/...`, `docs/...`, etc.
2. Give the install command as `cd "$(git rev-parse --show-toplevel)" && unzip -o ~/Downloads/<file>.zip -d .` so it works from any folder.
3. The owner's terminal mangles very long multi-line pastes. Keep command blocks short, one concern per block.
4. In the sandbox shell, `mkdir -p a/{b,c}` does **not** brace-expand under `/bin/sh` and creates literal `{b,c}` folders. Run scripts with `bash`, or list directories explicitly.
5. The owner is not told to run `npm audit fix --force`.
6. The chat sandbox **can reach the npm and PyPI registries**. Before delivering any code, actually run `npm ci` (or `npm install`), `npm run typecheck`, `npm run build`, and the tests in the sandbox. Earlier deliveries were not run first and had visible bugs. Do not claim anything works unless it was run.

---

## 3. Current state (Phase 4 built plus pre-Phase-5 pass; Phases 0 to 3 below)

**Backend:** `core/` (Phase 2) and `data/` (Phase 3) have code. `assistant/ta` (Phase 4) also has code; `lab/`, the rest of `assistant/` and `apps/api` are still empty placeholders. Run Python checks from the repo root: `pip install -e "core[dev]" -e data -e "assistant[dev,retro]"` and `pip install --no-deps smartmoneyconcepts==0.0.27`, then `pytest` and `ruff check .`. `data/` is the only package that needs `httpx`.

**Pre-Phase-5 pass (2026-10-27):** `core/src/sx_core/trading_calendar.py` (per-instrument `TradingCalendar`, `reference_day`, X14); `ta/sessions.py` (`previous_day_levels`, calendar-aware previous-day pair); `ta/smc_fast.py` (I17); `ta/candle_metrics.py` (I15 definitions, not wired); `scripts/bench_smc_replay.py`.

**TA layer (Phase 4):** `assistant/src/sx_assistant/ta/`: `common.py`, `causal_wrapper.py` (replay and freeze at first sight), `sessions.py` (DST-aware session and previous-day levels), `smc_adapter.py` (swings, FVG, BOS/CHoCH, order blocks, liquidity sweeps), `candles_talib.py`, `levels_trendln.py` (Retrospective, optional extra), `normalize.py` (`analyze_causal`, `lifecycle_at`, `as_of`, `require_causal`). DST sessions live in `core/src/sx_core/local_sessions.py`. Fixtures: `tests/fixtures/ta/` made by `scripts/make_ta_fixtures.py` (hand-labelled).

**Data layer (Phase 3):** `data/src/sx_data/`: `oanda_parse.py`, `oanda_rest.py` (practice host only, M1 to H1), `resample.py` (closed bars, UTC; H4 and D at 00:00 UTC), `quality.py` (`feed_degraded`), `cache.py` (Parquet plus `data_version`), `pipeline.py` (M1 in, M15/H1/H4/D out), `cli.py` (`python -m sx_data.cli sync`). Everything was tested on frozen synthetic fixtures with mocked HTTP. **It has never talked to the real OANDA API.**

### Done
- Repo scaffold: all folders and empty placeholder files per the layout (`core/`, `data/`, `lab/`, `assistant/`, `apps/api`, `apps/web`, `scripts/`, `tests/`).
- Foundation docs and root config (zip 1): README, `.gitignore`, `.env.example` (with `SX_TRADING_MODE=paper`), Makefile, root `pyproject.toml`, and the docs listed above.
- Web app v0 (zip 2 plus patches 1 and 2), running at `localhost:5175` (or 5173):
  - Vite 5, React 18, TypeScript, Tailwind 3.4, `lightweight-charts` ^4.2.
  - Warm dark/light theme via CSS variables in `src/index.css`, toggled by `data-theme` on `<html>` (persisted in `localStorage` key `sx-theme`). App uses `useLayoutEffect` to set the theme so the chart reads current colours.
  - App shell: top bar (instrument, M15 badge, session text, Sample data badge, theme toggle), left nav (Premarket, Chart, Suggestions, Paper, Lab, Journal), bottom status line (`PAPER`, feed, last price).
  - Premarket and Chart screens share `src/screens/Workspace.tsx`: 6-step stepper (premarket only), session-objects list with hide/show, inspector (what it is, price, known-at time, invalidation, status badges), chart.
  - `src/components/Chart.tsx`: candlesticks (5-decimal price format), dashed price lines per level, event marker, session-band overlay (see Known issues).
  - `src/data/sample.ts`: frozen SAMPLE data. Seeded RNG (seed 42), 288 M15 bars from 2026-10-19 00:00 UTC, sessions on the last day (Asia 00–07, London 07–12 UTC), objects: previous-day high, Asia high/low, London high/low, a sweep event. Everything is labelled **Sample data**.
  - Placeholder screens for Suggestions, Paper, Lab, Journal.
  - `src/chart.ts` and `src/api.ts` are `export {}` stubs.
  - `npm run test` is a stub that prints "no tests yet".

### Known issues (state after Phase 1, 2026-10-26)
1. ~~Session bands do not render.~~ Fixed with `sessionBandsPrimitive.ts`; owner confirmed in dark mode. Light mode not yet confirmed.
2. ~~Level labels overlap.~~ Fixed in code (sample levels separated; `levelLabelsPrimitive.ts` de-collides with `layers/decollide.ts`). Unit tested; **not yet seen in a browser**.
3. `npm audit` now reports 8 dev-tooling vulnerabilities (5 moderate, 1 high, 2 critical), up from 5 after adding Vitest, Playwright and ESLint. All are dev dependencies (esbuild, tinypool, @vitest/mocker, postcss-selector-parser and similar). Review in Phase 10. Never run `npm audit fix --force` blindly.
4. **Light-theme contrast.** Measured against `--bg`: accent 4.01, bull 3.99, asia 4.10, london 3.40, warn 3.04 (all below 4.5:1 as small text; all at least 3:1). The "Sample data" badge uses warn at 11px, so it is below AA in light mode. Dark theme passes AA for every token. Colours are fixed by `docs/UI_DESIGN.md`, so this needs an owner decision (see P8 in `docs/DECISIONS.md`). `src/test/contrast.test.ts` pins the list.
5. Vitest is pinned to `^3` because Vitest 5 requires Vite 6 or newer and the app is on Vite 5.
6. The sample is a frozen single snapshot, so replay shows each level at its final value from its `known_at` onward (for example London high appears at 12:00). A real incremental feed arrives in Phase 5.
7. Replay and band clipping are implemented but not seen on the real chart. `setData` during replay restores the logical range; if the view jumps, look there first.
8. Print layout of step 6 uses `@media print` rules and is unseen.
9. The Playwright smoke test (`apps/web/e2e/smoke.spec.ts`) was written and typechecks, but it has never run because no browser could be installed in the sandbox. Run `npx playwright install chromium` then `npm run e2e`.
10. The stray folder `apps/web/src/{components,screens,data}` may still exist on the owner's machine. Delete with `rm -rf 'apps/web/src/{components,screens,data}'`.
11. (Phase 2) A stray Python file `apps/web/src/panels/__init__.py` was found inside the web source tree and removed from the repo copy. A zip cannot delete files, so delete it on your machine: `rm -r apps/web/src/panels`.
12. ~~(Phase 2) Python 3.11 minimum.~~ Resolved 2026-10-27: minimum is 3.12 (X9).
13. ~~Daily alignment.~~ Decided (X10): D bars open at 00:00 UTC, H4 at 00/04/08/12/16/20 UTC, built from M1 by `sx_data.resample`. OANDA's own H4 and D are never fetched.
18. (Phase 3) **Never run against the real OANDA API.** The sandbox cannot reach it (proxy returns 403), so the client, paging and parser were verified only against `httpx.MockTransport` and a mock that emulates the paging rules as recalled from OANDA's docs (`from` + `count` + `includeFirst`, 5000 max). First real run: put `OANDA_TOKEN` in `.env`, then `python -m sx_data.cli sync --days 2`, and report the output. Expect to fix small shape differences.
19. ~~(Phase 3) Python 3.11 cannot install the pinned numpy.~~ Resolved 2026-10-27: minimum raised to 3.12 in `core`, `data`, `assistant` and the ruff target (X9). There is no CI in the repo, so none was changed. numpy stays pinned at 2.5.4 (PyPI: wheels for cp312 to cp315 incl. macOS arm64). Not run on 3.11 (no longer supported) or 3.13.
20. (Phase 3) Gap rules in `quality.py` are assumptions, not a market calendar: weekly closure Friday 20:00 to Sunday 23:00 UTC, tolerance of 3 missing bars. Market holidays appear as unexpected gaps. The Sunday D bar covers only about two hours of trading (a partial but real bar).
21. (Phase 3) `Candle` carries only `bid_close` / `ask_close`, so resampled bars take them from the last M1 bar of the bucket. No contract change was made.
22. (Phase 3) `resample` needs a clean, single-instrument, single-timeframe, time-ordered series and raises otherwise. Run `check_quality` first; it never fixes data.
24. (Phase 3) **OANDA account access is unconfirmed for the owner.** Sri Lanka is not on OANDA's BVI eligible-country list (the page does not exclude it either). If no practice account is possible, options are another broker's demo (needs a new client module behind the same interface), Dukascopy historical data (`dukascopy.py`, planned), or proceeding on fixtures. Ask the owner which route.
23. ~~(Phase 3) Sessions are fixed UTC hours.~~ Resolved in Phase 4 (X13, P9 approved). Hours are my assumption: see I10.
25. (Phase 4) **The owner's Mac is Intel (x86_64), Python 3.14.3.** numba 0.68 and llvmlite 0.50 have no Intel-Mac wheels (PyPI lists arm64 only), so `pip install smartmoneyconcepts` fails there (llvmlite needs LLVM to build). `smartmoneyconcepts` never imports numba, so it is installed with `--no-deps` and numba is not needed (verified in a fresh sandbox venv without numba: 283 passed). TA-Lib, scipy, scikit-image and matplotlib have cp314 Intel wheels. The suite passed in the sandbox (Linux x86_64, Python 3.12) and on the owner's Mac (Intel, Python 3.14.3): 283 passed, 2026-10-27.
26. (Phase 4) The Phase 4 numbers come from **synthetic** fixtures. Detection quality on real EUR/USD data is unknown. The FVG detector emits gaps of any size (no minimum), so real data will give many tiny gaps; add a minimum size only with evidence.
27. (Phase 4, partly fixed 2026-10-27) **Replay cost is still quadratic, now about 4 to 5 times faster.** The default engine uses exact numpy ports of swings, BOS/CHoCH and the newest-bar FVG (`ta/smc_fast.py`, I17), checked against the library on every prefix. Measured (sandbox, seeded random M15, `scripts/bench_smc_replay.py`): 96 bars 0.41 s vs 1.83 s; 192 bars 1.06 s vs 5.65 s; 384 bars 3.1 s; 768 bars 10.9 s (library path not run at that size). About 80% of what is left is the library's own `ob` and `liquidity` loops; porting them (same oracle test) is the next step if Phase 5 needs it. Not linear, so very long histories should be windowed.
28. (Phase 4) **BOS and CHoCH are known late.** The library only labels a break once the next swing is confirmed, so `known_at` can be an hour or more after the breaking bar (the labelled day: break at 05:00, known 06:15). This is honest but may feel slow on a chart.
29. (Phase 4) Liquidity tolerance is a fixed fraction (1%) of the high-low range of the bars seen so far, so it changes as data accumulates. Objects are frozen at first sight, but the same level can be grouped differently on a longer window. Only sweeps (a cluster that was taken out) are emitted, not unswept equal highs.
30. ~~(Phase 4) No previous-day level on Monday or Saturday.~~ Fixed 2026-10-27 by X14: Monday uses Friday. Remaining assumptions: weekly close at 17:00 New York, no daily maintenance break, empty holiday list (holidays are skipped as incomplete days; list them to keep them from using up the lookback), Sunday-evening bars unused.
31. (Phase 4) Trendline output is a bounding box, not a sloped line (I16). Horizontal support/resistance clusters are not emitted; only trendlines. `trendln` is a heavy optional dependency. Premarket will need a sloped-line representation or a contract change (additive) in Phase 5.
32. (Phase 4) Session hours are approved (I10). The candle-pattern numbers and proximity (0.5 x ATR, ATR period 14) are still untuned and unapproved (I15). The explicit definitions now exist in `ta/candle_metrics.py` but are not wired in; emitted candle setups still come from TA-Lib. The mutation check "remove the ATR gate" was not detected by any test because a NaN ATR already makes the proximity test false; the gate is redundant but kept for clarity.
33. (Phase 4) `to_display_time` (Asia/Colombo) exists but is not wired into logs or the web app. The web app still uses its own time formatting.
34. (Phase 4) The Python `Setup` contract and the zod mirror still agree by hand only (issue 16); Phase 4 added no field, but the new `kind`/`direction` conventions (I11) are not enforced by either side.
35. (Phase 5A) `GET /` has no route and returns 404 (add a small landing route in 5B). Run the API with `python -m uvicorn sx_api.main:create_app --factory --port 8000` (needs `pip install -e apps/api`). Payload cache is in memory only. Only the sample source exists; no OANDA path is wired. `report_plotly.py` is still an empty file (5B). Premarket window is 3 calendar days (I20).
36. (Phase 5B, partly fixed in the chart pass 2026-10-27) The chart now draws FVG and order-block boxes and BOS/CHoCH lines (`zonesPrimitive.ts`). Swings, trendlines and candle patterns are still in the payload but not drawn (58 of them in the fixture). **Never seen in a real browser**: the primitive's drawing code is untested (jsdom has no canvas), so box edges, tag overlap with 50 zones and the faded look of mitigated zones are unverified. The payload has no mitigation time, so a mitigated zone still runs to the right edge (drawn faded). PNG/PDF brief export needs Chrome (kaleido). No as_of picker. Install for tests: `pip install -e "assistant[dev,retro,report]"`; the web needs `npm ci`. Run web + API together: API on 8000, `npm run dev` in `apps/web`; `VITE_DATA_SOURCE=sample` forces offline.
39. (Phase 6B) Gates and the runner are verified only on synthetic quotes. News blackouts are windows listed by hand in the rule file: no calendar feed exists, so an empty list means no blackout. The daily-loss gate counts realized P&L by UTC calendar day of the closing time (not the trading day, X14) and ignores open-position loss. `rules/frozen/paper_v1.json` limits (2 open, 100.0 loss per day) are my provisional numbers. The runner is the intended entry point, but Python cannot stop someone building `SimBroker` directly without gates; production code must go through `PaperRunner`. Still no API route or web screen for paper (Phase 10). `oanda_practice.py`, `ib_paper.py`, `ctrader_demo.py` are empty.
38. (Phase 6A) Fixtures are synthetic. The simulator sees quotes only (one per closed bar, from `bid_close`/`ask_close`), so intrabar highs and lows are never seen and a stop or target touched inside a bar is missed until the next quote. No commission, swap or partial fills. Slippage 0.00002 is a provisional default. A rejected order keeps its id, so the same suggestion and rules cannot be retried after a kill-switch reset (a new suggestion id is needed). The risk-gate hook exists but no real gate does until 6B, so nothing may call the broker in production without 6B. `/paper` API is still an empty placeholder.
37. (Housekeeping) Root `pyproject.toml` reconstructed (I25); rules inferred, not the original. Root `README` and `Makefile` still absent.
14. (Phase 2) `check_prefix_equality` checks every prefix by default. It is O(n) producer calls, each O(n) or worse, so very long series are slow. A `prefix_lengths` option exists but sampling can miss leaks (documented and tested). Use it only deliberately.
15. (Phase 2) The ledger `append` checks only the tail of the chain (cheap); `verify()` checks the whole file. Run `verify()` at startup and in CI. Concurrent writers from two processes are untested.
16. (Phase 2) Python and zod contracts agree today (checked once by hand). There is no permanent test yet; add a shared golden-fixture test (`tests/fixtures/contracts/*.json` already exist) when the web side is next touched.
17. (Phase 2) The dev tools mypy and pandas-stubs are not adopted. Add them to `docs/DEPENDENCIES.md` and CI in Phase 10 if wanted.

---

## 4. Rules for every session

1. Read this file, `docs/PROGRESS.md`, `docs/PRINCIPLES.md` and the contract records you need.
2. Build **one phase at a time**. Finish, verify, update `docs/PROGRESS.md`, report files created and changed, then stop and wait for the owner.
3. Run everything before delivering: typecheck, lint, tests, build. Report exact results.
4. Keep files small (under about 250 lines) and prefer frozen fixtures over inline arrays.
5. Honesty labels are mandatory on every surface: **Sample data**, **Exploratory**, **Not validated**, **Retrospective**, **Causal**. Scores are never shown as probabilities.
6. Causality is non-negotiable. Anything rendered or fed to a model must have `known_at <= t`.
7. No code path may place a live order. `SX_TRADING_MODE` must equal `paper` or the process refuses to start.
8. Do not invent library behaviour. The research doc is unverified; sandbox-install and read the source before adopting a library, and record the result in `docs/DEPENDENCIES.md`.
9. Do not add colours outside the tokens in `docs/UI_DESIGN.md`. The accent (terracotta) never means bullish or bearish.
10. Record any new decision in `docs/DECISIONS.md` and any contract change (additive only) in `docs/CONTRACTS.md`.

---

## 5. Phase plan

Each phase lists: goal, work, tests, done-when. Phases are ordered by dependency. The owner's original build order is preserved; Phase 1 hardens the UI first because it is already running.

### Phase 1 — Web app: fix, test and complete the shell (BUILT 2026-10-26, awaiting owner visual review; skipped items listed in PROGRESS.md)
**Goal:** a solid, tested front end on sample data.
- Fix known issues 1 and 2. Replace the DOM band overlay with a series primitive; add label de-collision.
- Command palette (Cmd+K): navigate screens, switch instrument and timeframe, toggle layers and theme. Use `cmdk`.
- Layer presets (Premarket, Execution, Clean, Everything) and **relevance ranking**: draw only the top N items near price by default.
- Inspector tabs: Insight, Evidence, Forecast (Forecast shows a labelled placeholder).
- Timeline strip under the chart (Asia range established, London tested PDH, and so on) derived from objects' `known_at`.
- Causal replay scrubber: moving it hides everything with `known_at` after the scrubbed time.
- Step 6 "Final session plan" page: one-page summary, printable.
- Contracts in TypeScript with `zod` in `src/contracts/` mirroring `docs/CONTRACTS.md`; validate sample data against them.
- Add `zustand` for UI state and `@tanstack/react-query` for data once the API exists.
- Light and dark contrast check; keyboard reachability; focus rings; accessible names.
- Test setup: Vitest and Testing Library. Playwright smoke test (load, switch screens, toggle theme).
- Done when: `npm run typecheck`, `npm test`, `npm run build` all pass; bands visible in both themes; screenshots reviewed by the owner.

### Phase 2 — `core/`: contracts, causality harness, ledger (BUILT 2026-10-26; see PROGRESS.md)
**Goal:** the shared foundation, with almost no dependencies.
- `contracts/`: pydantic models for Candle, Setup, Forecast, Suggestion, PaperOrder, LedgerEntry exactly per `docs/CONTRACTS.md`. Ids are deterministic hashes of semantic fields, never of price values.
- `clock.py`: market clock, session boundaries (Asia 00–07, London 07–12, NY 12–17 UTC; make configurable), `known_at` and `available_at` helpers.
- `causality.py`: **prefix-equality harness**. For any producer `f(candles) -> objects`, assert that objects with `known_at <= t` computed on `candles[:t]` equal those computed on the full series. Ship it as a reusable pytest helper.
- `storage.py`: Parquet read/write, `data_version` content hashing.
- `ledger.py`: append-only JSONL with hash chaining. Reads never mutate. Test append-only behaviour.
- `labels.py`: status label enum and helpers. `config.py`: env loading and the paper-mode guard.
- Tests under `core/` and `tests/causality/`. Done when pytest passes and a deliberately look-ahead producer is caught by the harness.

### Phase 3 — `data/`: market data layer (BUILT 2026-10-26; see PROGRESS.md; real-API run still pending)
**Goal:** reliable closed-bar data with bid/ask.
- `oanda_rest.py`: direct `httpx` client for the **practice** API (candles with bid, ask, mid; pagination; rate limits). No `oandapyV20`. Token from env, never logged.
- `resample.py`: M1 to higher timeframes, **closed bars only**, UTC, no synthetic zero bars for gaps.
- `quality.py`: duplicate, monotonic, gap checks; a `feed_degraded` flag.
- Cache to Parquet under `data/src/sx_data/cache/` (gitignored). Record `data_version`.
- `fixtures`: small frozen candle sets in `tests/fixtures/` (no live calls in tests; mock HTTP).
- Optional later: `dukascopy.py` (tickterial), `calendar_pilot.py` (forex-pytory behind a flag; scraping risk, run the comparison spike in `scripts/` before adopting).
- Done when: fetch, resample and quality checks work on fixtures and, with an OANDA practice token, on real data.

### Phase 4 — `assistant/ta`: causal technical analysis (BUILT 2026-10-27; see PROGRESS.md)
**Goal:** library output normalized into `Setup` contracts, all causal.
- `sessions.py`: Asia/London/NY ranges and previous-day levels.
- `causal_wrapper.py`: delays each swing-based signal until the swing is confirmed (set `known_at` accordingly).
- `smc_adapter.py`: wrap smart-money-concepts (FVG, swings, BOS/CHoCH, order blocks, liquidity). **First read its source** for look-ahead and maintenance; pin the version. Fall back to a small in-house implementation if it is unsuitable.
- `candles_talib.py`: TA-Lib patterns, counted only near a level or zone. Check TA-Lib installs on the owner's Mac (Intel).
- `levels_trendln.py`: support/resistance and trendlines, tagged **Retrospective**, premarket only.
- `normalize.py`: everything becomes `Setup` with `plain_text`, `invalidation`, `known_at`, lifecycle.
- Causality tests on **every** adapter via the Phase 2 harness. Hand-labelled day fixtures to check definitions.
- Done when: all adapters pass the harness and a labelled-day fixture matches expected setups.

**Phase 4 brief (read before building):**
- **Inputs available now:** `sx_data.resample` and the cache give closed M1/M15/H1/H4/D candles (`Candle` contracts, UTC). Test inputs: `tests/fixtures/eurusd_m15_96bars.json`, `eurusd_h1_week.json`, `oanda/eurusd_m1_oanda_shape.json` (all synthetic). The harness is `sx_core.causality` and the `assert_causal` pytest fixture (`conftest.py`); producers need `id`, `event_time`, `known_at` (see `tests/causality/producers.py` for a worked example, and `data/tests/test_resample.py` for a dict-based one).
- **Sessions (done):** DST-aware sessions are built (X13, I10): `sx_core.local_sessions` and `assistant/ta/sessions.py`. The old fixed-UTC `SessionConfig` still works.
- **Library rules:** sandbox-install and read the source of smart-money-concepts, TA-Lib and trendln before using them; pin versions; record results in `docs/DEPENDENCIES.md`. TA-Lib may need a system library; check it installs on Apple Silicon (the sandbox is Linux, so say what could not be verified on the Mac). Fall back to small in-house code if a library is unsuitable.
- **Output:** every object becomes a `Setup` (contract in `docs/CONTRACTS.md`, mirror in `apps/web/src/contracts/setup.ts`) with `known_at`, `plain_text`, `invalidation`, lifecycle and `status` (`causal` or `retrospective`). Retrospective output (trendlines) never feeds a model or paper trade.
- **Do not** touch the web app in Phase 4 (the API and web hookup is Phase 5), and do not start Phase 5.
- **Answered 2026-10-27:** P9 approved, real-feed run skipped (issue 18 stays open), Python 3.12.

### Phase 5 — `assistant/premarket` + API + connect the web app (SPLIT INTO 5A AND 5B, owner request 2026-10-27, to fit session limits)
**Goal:** replace sample data with API-served data end to end. **Data source (owner, 2026-10-27):** frozen EUR/USD fixtures labelled `SAMPLE DATA — NOT LIVE` on every surface, behind a data-source interface so a verified provider can be added later. Do not call the OANDA client working until it has fetched real candles. Build 5A, stop, wait for the owner, then 5B.

#### Phase 5A — backend: data-source interface, premarket builder, API (BUILT and owner-verified 2026-10-27; see PROGRESS.md; Python only; do not touch `apps/web`)
- `data_source.py` (interface) plus a fixture-backed implementation. Every payload carries `source: "sample"` and the label `SAMPLE DATA — NOT LIVE`.
- `assistant/premarket/builder.py`: premarket analysis from closed bars only, using the Phase 4 TA layer (`previous_day_levels`, sessions, `analyze_causal`, default `engine="fast"`). Window long histories.
- `bias_checklist.py`: D/H4 context as a checklist of facts, no probabilities, no buy/sell.
- `chart_payload.py`: boxes, lines, labels and events as JSON matching the web contracts (additive contract changes only, recorded in `docs/CONTRACTS.md`; trendline representation per issue 31 if needed).
- `apps/api` (FastAPI): `/health`, `/premarket`, placeholder `/suggestions`, `/paper`, `/lab` (clearly empty). Contract-validated JSON, CORS for the Vite dev ports, paper-mode guard at startup.
- Tests: payload validates against the contracts; every object has `known_at <= as_of`; prefix-equality on the builder; API tests with the test client; sample label present.
- Done when: `GET /premarket` returns contract-valid, labelled, causal JSON and the Python suite and ruff pass. Owner can run the API with one command and open `/premarket` in a browser.

#### Phase 5B — web hookup and extras (BUILT 2026-10-27, awaiting owner run and visual review; see PROGRESS.md)
- `apps/web`: `src/api.ts` plus TanStack Query; the sample source (`src/data/sample.ts`) stays behind a flag so the UI works offline, always labelled **Sample data**. Validate responses with the zod contracts. Replay honours `known_at`.
- Multi-timeframe strip (D/H4 bias from the checklist) and ATR-based distances in the inspector.
- `assistant/premarket/report_plotly.py`: static daily brief (PNG/PDF), labelled.
- Tests: Vitest for api client and flag, error and loading states; update the Playwright smoke test (run by the owner).
- Done when: the web Premarket screen shows the API's objects with `known_at` honoured by replay, labelled `SAMPLE DATA — NOT LIVE`.

### Phase 6 — `assistant/paper`: paper trading (SPLIT INTO 6A AND 6B, owner request 2026-10-27; P5 simulator-first taken as confirmed by the owner's "proceed", X15)
**Goal:** safe, realistic, replayable paper execution. Build 6A, stop, wait; then 6B.

#### Phase 6A — simulator core (BUILT and owner-verified 2026-10-27; Python only, no web, no API change)
- `paper/broker.py`: `Quote`, `OrderRequest`, `RiskGate` and `PaperBroker` interfaces (paper backends only).
- `paper/sim_broker.py`: bid/ask fills plus slippage, deterministic, no wall clock; `paper/orders.py`: idempotent ids, request validation, kill switch; `paper/tracker.py`: intended vs actual fill, slippage, P&L summary, ledger logging of every order event; `paper/replay.py`: quotes from closed candles and a scripted replay helper.
- The broker already accepts risk gates (empty by default); the real gates are 6B.
- Tests: scripted day (hand-computed fixture), replay twice identical, live-mode refused, idempotency, kill switch, invalid requests, gate hook, time order, no exit on the filling quote, cancel and close-all, tracker and ledger.
- Done when: a scripted day replays to identical fills twice (done) and a live-mode config is rejected at the broker (done).

#### Phase 6B — gates, frozen rules, runner (BUILT and owner-verified 2026-10-27; `oanda_practice.py` deliberately NOT built, issues 18/24)
- `suggestions/risk_gates.py`: news blackout, daily-loss halt, max open trades, implementing `RiskGate`; applied to **every** order (the runner must not let an order reach a broker without them).
- `rules/frozen/`: rule sets hashed before each run; a runner refuses to start if the hash differs; the run's rules version goes into every order and ledger entry.
- `oanda_practice.py` (only after the simulator is trusted, and only with a verified account, issue 18/24). `ib_paper.py` and `ctrader_demo.py` stay optional and later.
- Tests: gate enforcement on every order, hash refusal, kill switch through the runner, live-mode config rejected at startup, replay determinism with gates.
- Done when: a scripted day with gates replays to identical fills twice, and a changed rule file makes the runner refuse.

### Phase 7 — `lab/` foundations and baselines
**Goal:** a trustworthy evaluation harness before any fancy model.
- `partition.py`: chronological train / validation / holdout (default 60/20/20, see decision P2). Only train and validation are importable by default; the holdout is reachable through one explicit, logged call.
- `features/`: causal volatility and session features (realized vol, range, ATR, time-of-day). All pass causality tests.
- `baselines/`: naive, HAR, GARCH (`arch`).
- `evaluation/metrics.py` (QLIKE, RMSE, interval coverage), `negative_controls.py` (shuffled labels and a deliberately leaked feature must fail), `purged_cv_crosscheck.py`.
- `search/`: Optuna study where **every trial is written to the ledger** (variants-tried count).
- `cli.py`: `sx-lab run | evaluate | report`. Outputs go to `lab/outputs/` as Parquet and JSON `Forecast` records.
- Done when: baselines run on real data, negative controls fail as they should, and the variants count is visible.

### Phase 8 — `lab/` models and the first experiment
**Goal:** answer one question honestly: does Mamba beat HAR and GARCH on volatility?
- `models/minimamba_vol.py` (CPU, MPS optional). **Pin the exact version; read the source; sanity-check it** (shapes, causality of the scan, determinism). The README's claims are the author's own. `mamba_ssm_vol.py` stays a stub until a GPU exists.
- `nf_baselines.py` (NHITS, PatchTST, LSTM) and `chronos_zeroshot.py` as baselines only.
- `regime/markov_switching.py` (statsmodels, **filtered** probabilities only). `changepoints_offline.py` (ruptures) is offline labelling only.
- `calibration/conformal.py` (MAPIE or in-house split-conformal; verify time-series validity) with coverage tracking.
- `evaluation/model_confidence_set.py` (arch MCS/SPA).
- `lab/experiments/prereg/EXP-001.yaml`: write and commit the spec **before** running. Then `EXP-001_mamba_vs_har.md` with results. Expectation: a tie or a loss; a documented tie is a valid result.
- Web: Lab screen and the Forecast tab (interval, regime label, track record, variants tried, "Exploratory / Not validated").
- Done when: EXP-001 is run once under the pre-registered spec and reported with the model confidence set and coverage.

### Phase 9 — `assistant/model`, `analyst`, `suggestions` (SPLIT into 9A, 9B, 9C, see section 5a)
**Goal:** evidence-linked suggestions, clearly labelled as unvalidated. Original scope kept below; the split in section 5a says what is built when.
- `model/`: triple-barrier labels, features, LightGBM with time-ordered splits and a gap, SHAP reasons, `scorer.py` (score + reasons; heuristic ranking, **not** a probability).
- `analyst/`: typed LLM output (Pydantic AI or the Anthropic SDK; decide per P6). Reads structured inputs only; writes the premarket brief and rationale; never picks trades or invents numbers. `debate.py` bull/bear challenge step. Prompts in `prompts/`.
- `suggestions/engine.py`: combines Setups, score and Lab forecast into `Suggestion`. `evidence.py`: every claim links to a setup or forecast id. Gates from Phase 6 apply.
- Web: Suggestions screen with evidence links that highlight objects on the chart; analyst brief drawer with claim-to-object linking.
- Done when: a suggestion's every claim resolves to an id, and a claim without evidence is rejected.

### Phase 10 — Review, remaining screens, hardening
- `review/scorecard.py` (forward results vs frozen rules) and `journal.py`.
- Web: Paper, Journal screens; track record per setup type with sample size and status labels (no bare percentages).
- Playwright end-to-end: data to TA to suggestion to paper order.
- `scripts/pip_audit.sh`, `scripts/pin_versions.py`; run `pip-audit` and `npm audit`; pin everything; update `docs/DEPENDENCIES.md` with checked dates and licences.
- `docker-compose.yml` (api + web; IB Gateway optional). README quick-start. Visual regression snapshots.
- Done when: a fresh clone runs via the README and all test suites pass.

---

## 5a. Phase 9 split (owner, 2026-10-28, decision X17)

Each part is built, verified, documented and handed over before the next starts. 9A is built (code and synthetic tests; real-data run in progress on the owner's Mac). 9B is built (synthetic tests only; no real scorer yet). 9C is not started.

### Phase 9A: model and scorer (no LLM, does not need P6) — CODE BUILT 2026-10-28, real-data run pending (see PROGRESS 'Phase 9A notes'; known limits 9A-1 to 9A-10)
- **First:** sandbox-install `lightgbm` and `shap`, read what they do, check Python 3.12 to 3.14 and the owner's Intel Mac (LightGBM may need `brew install libomp`; unconfirmed), pin versions, record in `docs/DEPENDENCIES.md`. Adapters around both; no invented library behaviour.
- `assistant/model/labels.py`: triple-barrier labels (ATR-scaled barriers, time barrier). Labels use FUTURE bars by design and are training targets only; they never enter features. `features.py`: causal features from `Setup` objects, sessions, ATR, time of day, all with `known_at <= t` (prefix-equality harness applies).
- `train.py`: LightGBM with chronological splits, a purge and embargo gap at least the label horizon, and a sealed holdout reachable only through one logged call (reuse the Lab partition ideas; do not import Lab code across modules, share through `core/` or files). `reasons.py`: SHAP reasons. `scorer.py`: score plus reasons, a heuristic ranking, never a probability.
- Negative controls must FAIL as they should: shuffled labels and a deliberately leaked feature. Report variants tried. Labels: Exploratory, Not validated, Retrospective. A weak or null result is a valid result.
- Web fix (CONFIRMED by the owner, presentation-only, X17): on the Lab screen hide the premarket "Sample data" badge and "SAMPLE DATA - NOT LIVE" status text, because they describe the chart sample, not the Lab. Provenance stays in the data and on every other screen. The Lab screen shows the accurate label of what it displays (the EXP-001 data label; each dataset's own label). Any Lab view that shows sample or synthetic data must say so there. Test both directions.
- **Done when:** causality tests pass on every feature, negative controls fail correctly, a score always carries reasons and a label, no probability wording anywhere, and results come with the honest numbers (including a null result if that is what the data says).

### Phase 9B: suggestions engine and evidence — CODE BUILT 2026-10-28, owner review pending (see PROGRESS 'Phase 9B notes'; known limits 9B-1 to 9B-8)
- `suggestions/engine.py` combines Setups, the 9A score and the Lab result into a `Suggestion` (contract additive changes only, recorded in `docs/CONTRACTS.md`). `evidence.py`: every claim links to a setup or forecast id; a claim without evidence is rejected. The Phase 6 risk gates apply to every order path.
- Web: Suggestions screen with evidence links that highlight objects on the chart; labels Not validated on every suggestion; no bare percentages.
- **Done when:** a suggestion's every claim resolves to an id and a claim without evidence is rejected (tests), and the screen is reviewed by the owner.

### Phase 9C: analyst (needs P6 decided first)
- `analyst/`: typed LLM output through an adapter (Pydantic AI or the Anthropic SDK per P6; Claude leans SDK). Structured inputs only; writes the premarket brief and rationale; never picks trades or invents numbers; `debate.py` bull/bear challenge; prompts in `prompts/`. Needs an API key in `.env` (never logged).
- Web: analyst brief drawer with claim-to-object linking.
- **Done when:** every sentence of a brief that states a fact resolves to an id or is rejected; the analyst cannot emit a number that is not in its inputs (test with a poisoned input).

## 5b. LATER-PHASE BACKLOG (not built, not scheduled, NOT part of Phase 8)
Moved here when Phase 8 closed (X16): `nf_baselines.py` (NHITS, PatchTST, LSTM), `chronos_zeroshot.py`, `mamba_ssm_vol.py` (CUDA GPU needed), web display of the regime label and changepoints, an EXP-002 with a different MiniMamba recipe (early stopping, dropout, smaller model; own pre-registered spec). Also still open from earlier: first real-API checks beyond the OANDA practice download, light-theme contrast (P8), regenerating the OANDA token, reading OANDA's terms before sharing data files, npm audit review (Phase 10), code-splitting the 552 kB web bundle (Phase 10).

## 6. Open decisions (ask the owner when a phase needs them)
- **P1** Lab goal = volatility/regime (proposed, unconfirmed).
- **P2** Holdout in `lab/partition.py`: 60/20/20 (proposed).
- ~~P3~~ Confirmed 2026-10-26 (X11): EUR/USD first, then other majors.
- ~~P4~~ Confirmed 2026-10-26 (X12): M15 and H1 execution, H4 and D context.
- ~~P9~~ Approved 2026-10-27 (X13). ~~Python minimum~~ Raised to 3.12 (X9).
- ~~P10~~ Approved 2026-10-27 (X14), with the note that day boundaries stay at 00:00 UTC (X10) and only the Friday close uses the New York time zone. Owner approved the deviation 2026-10-27.
- **I15 numbers** (doji, pin bar, engulfing thresholds, ATR proximity): provisional configurable defaults, kept by the owner 2026-10-27; not calibrated.
- **P8** Light-theme contrast (still open).
- **P5** Paper backends: simulator, then OANDA practice, IB later.
- **P6** LLM layer: Pydantic AI vs Anthropic SDK directly. **Blocks 9C only; decide before 9C.** Claude leans SDK behind an adapter.
- ~~P11~~ Confirmed 2026-10-28: 9A evaluation protocol (chronological train / validation / sealed holdout, documented purge gap, one logged opening, separate reporting). Built as M1 to M10 in `docs/DECISIONS.md`.
- GPU availability for the official Mamba reference.
- Whether to use forex-pytory for the calendar or a plain JSON feed.

## 7. Risk register
| Risk | Mitigation |
|---|---|
| Look-ahead in TA output (swings, structure) | Causal wrapper, prefix-equality tests on every adapter |
| Library claims are unverified | Sandbox install, source read, pinned versions, `pip-audit` |
| Single-maintainer libraries | Adapters isolate them; swap without touching the rest |
| Mamba ties or loses to HAR | Expected; document it, it is still a result |
| Suggestions mistaken for validated signals | Persistent "Not validated" labels, no probability language |
| Tuning on paper results | Frozen, hash-checked rules; new run for any rule change |
| UI gives false confidence | Status badges always visible; variants-tried count shown |
| Delivery mistakes (wrong folder, untested code) | Section 2 delivery rules; run before delivering |

## 8. Definition of done (every phase)
Typecheck, lint and tests green (actually run); new logic has tests; causal surfaces respect `known_at`; honesty labels present; no new colours; `docs/PROGRESS.md` updated; owner given a short list of files created and changed plus exact commands to install and run.

---

## Phase 7 split and Lab known issues (added 2026-10-27)

**Phase 7A: BUILT 2026-10-27** (partition, features, metrics, naive baselines; see `docs/PROGRESS.md`). **Phase 7B: not started** (HAR, GARCH via `arch`, negative controls, purged-CV cross-check, Optuna search logged to the ledger, `sx-lab` CLI, `Forecast` JSON outputs). 7B must first install `arch` and `optuna` in a sandbox, read the source, pin versions and record them in `docs/DEPENDENCIES.md`.

Lab known issues:
- L-1 All Lab numbers use a SYNTHETIC fixture. Nothing is known about real EUR/USD; "baselines run on real data" is still open (OANDA never run, issues 18 and 24).
- L-2 Features assume continuous bars. Real H1 data has weekend gaps, so "h bars" would not mean h hours across a weekend and the first Monday returns span the gap. A gap policy is needed before real data; not built.
- L-3 Holdout governance is a process rule kept in the ledger, not security. Two processes racing could both pass the check; single-process use is assumed. Appending new data changes the holdout rows, which is a new evaluation by design.
- L-4 Persistence divides nothing but can return zero in a flat window, and QLIKE then refuses to run (by design: no silent clipping).
- L-5 Feature definitions (ATR as mean true range over close, Parkinson range variance, windows 6/24/120) are my choices and untuned; ATR was not cross-checked against `apps/web/src/layers/atr.ts` or TA-Lib.
- L-6 Sandbox ran pandas 3.0.2 / numpy 2.4.4, repo pins 3.1.0 / 2.5.4.
- L-7 Root `pyproject.toml` `testpaths` does not list `lab/tests`; run `pytest lab/tests` or add it (command in the delivery message).

**Phase 7B: BUILT 2026-10-27** (HAR, GARCH, negative controls, purged-CV cross-check, Optuna search logged to the ledger, `Forecast` records, CLI; see `docs/PROGRESS.md`). Phase 7 "done when" is partly met: real data is still missing. Phase 8 not started.

More Lab known issues:
- L-8 Purged CV refits on stitched (non-contiguous) rows; GARCH's recursion is distorted at the joins, so its CV score is not comparable to its validation score.
- L-9 On the synthetic fixture the single validation split and purged CV rank the models differently. Do not publish any ranking from one split.
- L-10 The `Forecast` interval is not conformal (L5). `nominal_coverage` is not a guarantee.
- L-11 The shuffled-label control fails for HAR on the fixture (no measurable skill over a constant on 147 rows). Informative, not a bug.
- L-12 The search space has only 6 distinct combinations; TPE repeats some. `variants_tried` reports both total and distinct trials.
- L-13 `arch` and `optuna` were only partly source-read; licences are from metadata (arch: NCSA). Transitive packages are not pinned.
- L-14 The CLI never opens the holdout and has no lock/open command yet; that arrives with EXP-001 (Phase 8).
- L-15 No mutation checks were run on 7B.

---

## Phase 8 split (owner request, 2026-10-27)

Phase 8 is divided in two so each piece fits a session and so the experiment spec is frozen BEFORE any challenger model exists. Nothing below is built yet. Phase 8 question is unchanged: **does Mamba beat HAR and GARCH on volatility?** A documented tie or loss is a valid result.

### Phase 8A: experiment infrastructure and the frozen spec (no neural models) — BUILT 2026-10-27, spec NOT locked (see section 0 and PROGRESS)
**Goal:** everything EXP-001 needs except the challengers, plus the pre-registration committed first.
- **Feasibility spike (first, before any code):** can the challengers run at all on the owner's machine? `minimamba` needs PyTorch, and the owner's Mac is Intel (x86_64, Python 3.14.3). I believe recent PyTorch releases have no Intel-Mac wheels; this is UNVERIFIED. Check in the sandbox and on the Mac, and record the answer in `docs/DEPENDENCIES.md`. If it cannot run locally, decide where EXP-001 runs (Linux box, rented CPU/GPU, Colab) before building 8B.
- **Real data path:** EXP-001 must not run on the synthetic fixture. Decide the data source (OANDA practice is unconfirmed, issues 18 and 24; alternatives: Dukascopy export, another broker's demo, owner-supplied CSV/Parquet) and add an importer through `sx_data`/`sx_core.storage` with quality checks. Add the **weekend/gap policy** for features and targets (known issue L-2).
- `calibration/conformal.py`: split-conformal intervals with coverage tracking, verified for time-series validity (exchangeability caveat written down and tested). Replaces the non-conformal interval of decision L5 in `records.py`.
- `evaluation/model_confidence_set.py`: arch MCS (and SPA if useful). Read the `arch` source for the bootstrap block length and seed handling before adopting.
- `regime/markov_switching.py` (statsmodels, **filtered** probabilities only, causality-tested with the Phase 2 harness) and `regime/changepoints_offline.py` (ruptures, offline labelling only, tagged Retrospective).
- CLI: `sx-lab lock` and `sx-lab open-holdout` wrapping `LabPartition.lock_evaluation` / `open_holdout` (the CLI still never opens the holdout by itself).
- `lab/experiments/prereg/EXP-001.yaml` written, **owner-approved, hashed and locked in the ledger** before 8B starts: data window, horizon, models and their pinned versions, primary metric (QLIKE), secondary (RMSE, coverage), MCS level, number of variants allowed, stopping rule, what counts as a win, tie or loss.
- Tests: conformal coverage on frozen fixtures, MCS on a known-answer fixture, regime filtered-only causality, spec-hash refusal.
- **Done when:** the spec is locked, conformal and MCS tests pass, the real-data path loads a quality-checked dataset, and the feasibility spike has a recorded answer.

### Phase 8B: challengers and the one experiment run (CODE BUILT 2026-10-28; run pending; see PROGRESS)
**Goal:** run EXP-001 once under the locked spec and report it honestly.
- `models/minimamba_vol.py` (CPU, MPS optional): **pin the exact version, read the source, sanity-check** shapes, scan causality and determinism. `mamba_ssm_vol.py` stays a stub until a CUDA GPU exists.
- `models/nf_baselines.py` (NHITS, PatchTST, LSTM) and `models/chronos_zeroshot.py` as baselines only; **include them only if the owner approves the heavy dependencies in 8A's spec**.
- Runner that refuses to start if the spec hash differs from the lock, if the data label is SAMPLE/synthetic, or if the holdout was already opened.
- Run EXP-001 **once**; every trial and seed goes to the ledger (variants-tried count). Open the holdout exactly once, through the logged call.
- `lab/experiments/EXP-001_mamba_vs_har.md`: results with the model confidence set, coverage and variants tried. Status labels `Exploratory` and `Not validated`.
- Web: Lab screen and the Forecast tab (interval, regime label, track record, variants tried, honesty labels; zod mirror of `Forecast` if not yet present). Web checks run as in Phase 5B.
- **Done when:** EXP-001 is run once under the pre-registered spec and reported with the model confidence set and coverage; web Lab and Forecast tab show it with labels.

### Owner decisions needed before 8A starts
1. Real data source for EXP-001 (see above). Without it, 8A can be built and tested but 8B cannot be run honestly.
2. Where the neural models will run (feasibility spike result).
3. Whether neuralforecast and Chronos are in scope for EXP-001 (heavy dependencies) or only minimamba vs HAR/GARCH.
4. Approval of the proposed spec defaults L11 and L12 in `docs/DECISIONS.md`.

---

## Phase 8A known issues (added 2026-10-27)

- L-2 (weekend/gap features): RESOLVED in code by decision L16 (`features/gaps.py`), verified only on a synthetic fixture with an injected weekend. Real FX files are unseen.
- L-10 (interval not conformal): the conformal band exists and `sx-lab run` uses it; `make_forecasts` without `conformal` still gives the old non-conformal band.
- L-7 (`testpaths`): the root `pyproject.toml` now lists `lab/tests` and `data/tests`.
- 8A-1 `EXP-001.yaml` is a draft. PROPOSED values (not owner-reviewed): MiniMamba settings (d_model 64, 2 layers, context 48), `max_variants` 20, MCS reps/seed/block size, conformal alpha 0.2 and calibration rule, outcome rules (win/tie/loss), stopping rule wording, gap policy L16.
- 8A-2 Holidays: an unexpected gap longer than 3 bars (for example a market holiday or an outage) makes `make_gap_aware_dataset` REFUSE the whole file. There is no override or holiday list yet. Decide before real data (list the holidays, split the file, or raise the tolerance with evidence).
- 8A-3 `GapRules` closure window (Friday 20:00 to Sunday 23:00 UTC) is an assumption; the first bar after a weekend is dropped as a row.
- 8A-4 Conformal coverage is verified only by simulation (exchangeable data: holds; variance shift: degrades). On real volatility the guarantee does not apply and horizon-24 targets overlap; the embargo between calibration and report rows reduces but does not remove this.
- 8A-5 MCS verified on a known-answer synthetic only; only `MCS.__init__` of `arch` 8.0.0 was source-read, not the full test statistic code.
- 8A-6 Regime model: 2 regimes fixed, parameters fitted once on the training window (no walk-forward refit), may fail to converge on real data (it then raises). Not wired into any screen or Forecast.
- 8A-7 `sx-lab lock` / `open-holdout` were tested only on a fixture-derived file. The holdout is still a process rule, not security (L-3). `lock` does not run `Ledger.verify()`.
- 8A-8 The zip has no `.env.example`, so one core test fails in the sandbox; root README and Makefile are still absent.
- 8A-9 FOUND AND FIXED 2026-10-27: `ruptures` 1.1.10 cannot install on Python 3.14.3 (owner's pip error). Now an optional extra; change points use in-house PELT. Still unverified: `pip-audit` on statsmodels and pyyaml, and PyYAML 6.0.3 on the Mac (the owner's pip run stopped before it). statsmodels 0.15.0 is confirmed installed on the Mac.
- 8A-10 No training code exists. `models/minimamba_vol.py` is still empty (8B).
- 8A-11 (2026-10-28) Import aliases and time formats are unverified against a real Dukascopy file; the first real file decides what to add. A flat-bar warning (high == low runs of 3 or more) prints at import but does not refuse; how filler bars affect QLIKE (zero targets) is not handled yet.
- 8A-12 The importer no longer reads bid_close/ask_close/complete columns; every bar is assumed closed (recorded in provenance).
- (Superseded 2026-10-28: the data is imported and EXP-001 is locked; 8B is unblocked but waits for the owner to say go and to choose where MiniMamba trains. See PROGRESS.)
- 8A-13 (2026-10-28) `sx_data.cli history` has never run against the live OANDA API. First live run may expose: wrong token or region (HTTP 401/403 message), history depth, payload differences from the recalled v20 shape, or practice-feed gaps. Compare its quality line before locking. OHLC are MID prices, not bid or ask.
- 8A-14 The owner's token was pasted in a chat; regenerate it. Use the variable name `OANDA_TOKEN` (not `OANDA_API_TOKEN`).
- (Done 2026-10-28: history downloaded for 2024-10-01 to 2026-10-26, EXP-001 approved and locked.)

---

## Phase 9A known issues (added 2026-10-28)
Full list with reasons: `docs/PROGRESS.md` 'Phase 9A notes' (9A-1 to 9A-10). Headlines: no real-data result yet; labels are mid-price diagnostics without costs; setups come from overlapping windows (slightly different from one full replay); provisional barrier/grid/look-back numbers are unreviewed; holdout is a process rule; the scorer is not wired to the API or web (9B); lightgbm's `libomp` need on the Intel Mac is unconfirmed; `pip install -e "assistant[dev,model]"` is now required for the model tests (they fail loudly at import without it). Lab badge (X17) is done: premarket sample labels are hidden on the Lab screen only (M10).

