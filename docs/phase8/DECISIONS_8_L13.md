
## Lab decision from the Phase 8A feasibility check (2026-10-27)

| # | Decision | Status |
|---|---|---|
| L13 | Challenger models (minimamba, neuralforecast, Chronos) cannot run in the Mac venv (see PROGRESS 8A feasibility). Proposed: build all 8A infrastructure and the frozen spec on the Mac as planned; run the neural challengers in a separate Linux environment (rented CPU/GPU, Colab, or the Claude sandbox if it has enough CPU time), exchanging data and results as Parquet/JSON files with their hashes recorded in the ledger. The Mac keeps HAR, GARCH, MCS, conformal and the web app. Alternative the owner may choose: change the EXP-001 question so that it needs no torch (not recommended: it drops Mamba, the point of the experiment). | Proposed |
