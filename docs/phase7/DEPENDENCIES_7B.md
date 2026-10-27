
## Python adopted in Phase 7B (checked 2026-10-27 in the sandbox, Python 3.12.3; `pip-audit` found nothing except the venv's own `pip` 24.0)
| Package | Pinned | Licence (package metadata, no legal review) | Used by |
|---|---|---|---|
| arch | 8.0.0 | NCSA (metadata field; no classifier) | `sx_lab.baselines.garch` (parameter estimation only) |
| optuna | 5.0.0 | MIT (classifier) | `sx_lab.search.optuna_search` |

Transitive and NOT pinned by us: scipy 1.18.1, statsmodels 0.15.0 (via arch); SQLAlchemy 2.1.6, alembic 1.20.1, colorlog, tqdm, PyYAML (via optuna). Optuna's database stack is heavier than this use needs (in-memory study only); swap for an in-house grid search if that bothers you. Source reading was partial (see PROGRESS 7B).
