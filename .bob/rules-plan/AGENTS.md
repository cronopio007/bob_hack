# Project Architecture Rules (Non-Obvious Only)

- The pipeline is **strictly sequential and human-gated**: Think → (user approval) → Do → (user approval) → Docs. Skipping gates violates the core architectural contract (ADR-001).
- `reports/metrics.json` is the single shared state between the `Do` and `Docs` agents — any new metrics must be appended to `history[]`, not replace it, to preserve regression tracking.
- `src/` does not exist yet — it is the target output of the `Do` phase. Planning must account for the four required modules: `data_loader.py`, `features.py`, `model.py`, `evaluate.py`.
- The dataset has a ~14% null rate on 13 `object`-typed financial ratio columns — the feature engineering plan must explicitly address imputation strategy or downstream models will fail.
- Inference latency target of <50ms is a hard constraint that limits model complexity — tree ensemble depth and feature count must be bounded in the architecture plan.
- `docs/1_architecture_plan.md` and `docs/3_final_pipeline.md` do not exist yet — they are deliverables of Think and Docs phases respectively.
- Two separate i18n/locale systems are NOT present (unlike some projects) — this is a pure Python/Streamlit ML repo with no frontend build step.
