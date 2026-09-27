# Changelog — Trinity-AI: Credit Risk Scoring Pipeline

Formato basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

---

## [1.3.0] — 2026-09-27

### Added
- `src/audit.py` — Nuevo modulo de auditoria regulatoria bancaria (AGENTS-do.md Contrato Estricto):
  - `audit_data_quality()`: genera `reports/data_quality.csv` con columnas `(columna, tipo_dato, nulos_conteo, nulos_pct, alerta_calidad)`. Alertas: CRITICO (>30%), AVISO (>5%), OK.
  - `compute_iv()`: calcula Information Value por binning cuantil (10 bins) para cada feature numerica contra el target. Exporta `reports/feature_selection_iv.csv` con columnas `(feature, iv_score, poder_predictivo, correlacion_target, seleccionada)`. Criterio IV: Impredecible/<0.02, Debil/0.02-0.1, Mediano/0.1-0.3, Fuerte/>0.3.
  - `export_confusion_matrix()`: genera `reports/confusion_matrix.csv` con 4 filas TN/FP/FN/TP y columnas `(actual, predicho, conteo, tasa_pct)`.
- `reports/data_quality.csv` — Auditoria de calidad sobre las 49 columnas del dataset (0 CRITICO, 6 AVISO).
- `reports/feature_selection_iv.csv` — IV de 46 features; 30 seleccionadas (IV >= 0.02).
- `reports/confusion_matrix.csv` — Matriz de confusion del modelo baseline en test: TN=1709, FP=1260, FN=129, TP=207.

### Changed
- `src/pipeline.py` — Refactorizado de 4 a 6 pasos; integra auditoria pre/post entrenamiento:
  - [2/6] `audit_data_quality(df)` — ejecutado sobre el DataFrame crudo post-carga.
  - [3/6] `compute_iv(df, ...)` — ejecutado sobre el DataFrame completo antes del split.
  - [6/6] `export_confusion_matrix(y_test, y_pred)` — ejecutado con el umbral optimo tras evaluacion.

---

## [1.2.0] — 2026-09-27

### Changed
- `src/evaluate.py` — Refactorizado para cumplir contrato AGENTS-do.md §3 (exportación CSV obligatoria):
  - Nuevas constantes: `REPORTS_DIR`, `METRICS_CSV_PATH`, `FEATURE_IMPORTANCE_CSV_PATH`, `FEATURE_IMPORTANCE_TOP_N=15`.
  - Nueva función `export_metrics_csv()`: append-only en `reports/metrics_history.csv` con columnas `(timestamp, model, roc_auc, ks, pr_auc, f1_score, precision, recall, latency_ms)`.
  - Nueva función `export_feature_importance_csv()`: sobreescribe `reports/feature_importance.csv` con top-15 variables LightGBM (columnas `feature, importance`).
  - `evaluate_model()` llama ambas funciones automáticamente tras calcular métricas.
  - Añadido `import csv` (stdlib).

### Added
- `reports/metrics_history.csv` — Historial acumulativo de métricas por ejecución (append-only).
- `reports/feature_importance.csv` — Top-15 variables predictivas por ganancia LightGBM (sobreescritura por ejecución).

---

## [1.1.0] — 2026-09-27

### Added
- `demo_pipeline_walkthrough.ipynb` — Notebook de auditoría Human-in-the-Loop para la fase `Do`.
  - **Celda 1**: Setup del entorno `dsenv`, verificación de versiones e imports limpios desde `src/`.
  - **Celda 2**: Carga de `data/data_ejm.parquet` con validación Pydantic v2 y análisis de nulos por grupo de columnas.
  - **Celda 3**: Preprocesamiento (Grupo D cast + split temporal 70/15/15 sin shuffle) con gráficos de distribución de clases en Train/Val/Test.
  - **Celda 4**: Entrenamiento LightGBM con `scale_pos_weight=8.68`, early stopping y gráfico Top-15 Feature Importances.
  - **Celda 5**: Evaluación exhaustiva sobre test set — Curva ROC, Curva Precision-Recall (con marcador del umbral óptimo) y Curva KS Bancario con separación acumulada.
  - **Celda 6**: Celda de decisión humana con checklist automático de umbrales; guarda en `reports/metrics.json` con tag `Human_Validated_Approved` o `Human_Validated_Rejected`.

---


## [1.0.0] — 2026-09-26

### Added
- `src/__init__.py` — Paquete Python del pipeline Trinity-AI.
- `src/data_loader.py` — Carga de `data/data_ejm.parquet` con validación Pydantic v2.
  - Conversión automática de columnas Grupo D (`object` → `float64`) con `pd.to_numeric(..., errors='coerce')`.
  - Validación de schema por registro; falla con `ValueError` si >1% de registros son inválidos.
  - Modelo Pydantic `RawRecord` con constraints de tipo y rango para las 49 columnas.
- `src/features.py` — Ingeniería de features, imputación y Time-Based Split.
  - Imputación estratificada por cuartil de `NRO_ENTS_SF` (medianas calculadas SÓLO sobre train para evitar leakage).
  - Partición temporal 70/15/15 sin shuffle (`FECHA` ascendente) — ADR-005.
  - `SplitResult` dataclass inmutable con `X_train`, `X_val`, `X_test`, `y_train`, `y_val`, `y_test`.
- `src/model.py` — Entrenamiento LightGBM.
  - `scale_pos_weight=8.68` (ratio 19751/2274) — ADR-004.
  - Early stopping en 50 rondas sobre val-AUC.
  - `find_optimal_threshold()`: umbral óptimo sobre curva PR del Validation, priorizando Recall ≥ 0.55 como restricción dura — ADR-008.
  - `TrainResult` dataclass con modelo, umbral, importancias y parámetros usados.
- `src/evaluate.py` — Evaluación rigurosa y persistencia de métricas.
  - Calcula: ROC-AUC, PR-AUC, KS (Kolmogorov-Smirnov), Recall clase 1, Precision clase 1, F1-Score, Accuracy, Latencia P95.
  - `compute_ks()`: implementación directa del estadístico KS crediticio.
  - `measure_latency_p95()`: 200 inferencias individuales para medir P95 real.
  - `update_metrics_json()`: append-only al historial de `reports/metrics.json` — no sobreescribe historia.
- `src/pipeline.py` — Orquestador de extremo a extremo.
  - Conecta: `load_dataset` → `build_features` → `train_model` → `evaluate_model` → `update_metrics_json`.
  - FAIL FAST en cada paso: `sys.exit(1)` con mensaje explícito ante cualquier error crítico.
  - Ejecutable con: `conda run -n dsenv python -m src.pipeline`.
- `docs/1_architecture_plan.md` — Plan de arquitectura aprobado (Bob Think).
- `docs/2_data_strategy.md` — Estrategia de datos y contratos Pydantic (Bob Think).
- `changelog.md` — Este archivo.

### Changed
- `reports/metrics.json` — Schema expandido para incluir `roc_auc`, `pr_auc`, `ks`, `recall_class1`, `precision_class1`, `threshold_used` (ADR-008).
- `memory.md` — ADR-004 a ADR-008 registrados; estado de fases actualizado a `Do` en progreso.

### Decisions
- **ADR-004**: LightGBM como algoritmo primario; XGBoost como contraste.
- **ADR-005**: Split temporal estricto por `FECHA`. Sin shuffle.
- **ADR-006**: KPIs primarios: ROC-AUC y KS. Accuracy prohibida.
- **ADR-007**: Cast `object`→`float64` con `pd.to_numeric(..., errors='coerce')`.
- **ADR-008**: Recall ≥ 0.55 como restricción dura en selección de umbral.
