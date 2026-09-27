# Project Documentation Context (Non-Obvious Only)

- `app/dashboard.py` is NOT a standalone app — it depends on `reports/metrics.json` being present with the correct schema; if absent it falls back to zero-values silently.
- `not.md` at the project root is a developer scratch file (not documentation) — it contains raw shell commands and project notes, not authoritative specs.
- `memory.md` is the authoritative source of all Architectural Decision Records (ADRs) and project state — check it before answering questions about why something was built a certain way.
- The three Bob modes (`Think`, `Do`, `Docs`) map to custom rule files in `.bob/rules-think/`, `.bob/rules-do/`, `.bob/rules-docs/` — NOT the standard `rules-agent/rules-ask/rules-plan` structure.
- `data/raw_data.csv` is referenced in ADRs as the pipeline input but does NOT exist yet — only `data/data_ejm.parquet` is present (22k rows, 49 cols, imbalanced binary target).
- `requirements.txt` is empty — actual dependencies must be inferred from import statements in the source files.
