# Project Coding Rules (Non-Obvious Only)

- `reports/metrics.json` schema is a hard contract — `current_metrics` and `history` array keys must be preserved exactly or the Streamlit dashboard silently shows zeros.
- `data/data_ejm.parquet` has `object`-typed columns (`VAR_12M_PROM_*`, `VAR_6M_PROM_*`) that are actually numeric stored as strings — cast with `pd.to_numeric(..., errors='coerce')` before any sklearn pipeline.
- The target `FLAG_MORA_TEMPRANA_8D_3M` is 10.32% positive — any model trained without imbalance handling (SMOTE, `class_weight='balanced'`, etc.) will silently optimize for the majority class.
- Pipeline modules belong in `src/` as separate files (`data_loader.py`, `features.py`, `model.py`, `evaluate.py`) — monolithic scripts or notebooks are explicitly prohibited by project ADR.
- All paths must use `Path(__file__).resolve().parent.parent` as the project root anchor — never `os.getcwd()` or relative strings.
- Log every code change in `changelog.md` (Keep a Changelog format) and append project learnings to `memory.md` (never overwrite).
- The `Do` phase must not start until `docs/1_architecture_plan.md` exists and is explicitly approved.
- Latency target is <50ms inference — algorithmic choices and feature counts must be evaluated against this constraint.
