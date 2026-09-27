# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project: Trinity-AI — Credit Risk Scoring (IBM Bob 2.0 Hackathon)

**Stack:** Python 3.11+, Streamlit, pandas, scikit-learn, Pydantic  
**No package manager config exists yet** — `requirements.txt` is empty. Install manually: `pip install streamlit pandas scikit-learn pydantic pyarrow`.

## Commands

```bash
# Run the dashboard (from project root)
streamlit run app/dashboard.py

# Generate data summary from parquet (from project root)
python scripts/summarize_data.py
```

No test framework, linter, or CI config is present.

## Architecture: Three-Agent Human-in-the-Loop Pipeline

The project enforces a **strict sequential flow** across three Bob modes (each has its own `.bob/rules-*/` directive):

```
Think (Estratega) → docs/1_architecture_plan.md → Do (Ejecutor) → src/ + reports/metrics.json → Docs (Auditor) → docs/3_final_pipeline.md
```

- **Think phase cannot end** without explicit user approval of `docs/1_architecture_plan.md`.
- **Do phase must NOT start** without a validated plan from Think.
- **Docs phase reads only** `src/` and `memory.md` — never invents information.

## Critical Data Contracts

- `reports/metrics.json` schema is fixed: `{ current_metrics: {accuracy, f1_score, latency_ms}, history: [{iteration, timestamp, accuracy, f1_score, latency_ms}] }`. Breaking this schema crashes the dashboard.
- Raw dataset: `data/data_ejm.parquet` (22,025 rows × 49 cols). Target: `FLAG_MORA_TEMPRANA_8D_3M` (binary, 10.32% positive — severely imbalanced; handle it explicitly).
- Several `VAR_12M_PROM_*` and `VAR_6M_PROM_*` columns are typed `object` with ~14%/7% nulls — must be cast and imputed before modeling.
- `data/raw_data.csv` is the expected input for `Do` pipeline modules (per ADR), but only the `.parquet` file is currently present.

## Code Style (from ADRs and code)

- **Python 3.11+**, strict type hints on all function signatures, Pydantic for data contracts.
- All paths resolved with `Path(__file__).resolve().parent.parent` (project root anchor) — never use relative string paths.
- Modular pipeline: `src/data_loader.py`, `src/features.py`, `src/model.py`, `src/evaluate.py` (not yet created; this is the target structure).
- All changes to code must be logged in `changelog.md` (Keep a Changelog format).
- `memory.md` is the project's persistent context store — append learnings there, never overwrite existing entries.

## Bob Mode Directives

Custom rule files live in `.bob/rules-think/`, `.bob/rules-do/`, `.bob/rules-docs/` (not the standard `rules-agent/rules-ask/rules-plan` directories).
