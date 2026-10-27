
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
