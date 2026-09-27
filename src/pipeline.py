"""src/pipeline.py -- Orquestador de extremo a extremo del pipeline Trinity-AI.

Uso:
    python -m src.pipeline

Flujo:
    data_loader -> audit(quality+IV) -> features -> model -> evaluate(+CSV) -> audit(confusion)

Salidas obligatorias en reports/ (AGENTS-do.md Contrato Estricto):
    reports/data_quality.csv
    reports/feature_selection_iv.csv
    reports/confusion_matrix.csv
    reports/feature_importance.csv
    reports/metrics_history.csv
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("trinity_ai.pipeline")

# ---------------------------------------------------------------------------
# Rutas del proyecto (ancladas al directorio raíz)
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
PARQUET_PATH: Path = BASE_DIR / "data" / "data_ejm.parquet"


def run_pipeline() -> None:
    """Ejecuta el pipeline completo de 6 pasos.

    Flujo:
        [1] Carga & validacion
        [2] Auditoria de calidad de datos  -> data_quality.csv
        [3] Information Value              -> feature_selection_iv.csv
        [4] Features, imputacion & split
        [5] Entrenamiento LightGBM
        [6] Evaluacion & reportes          -> confusion_matrix.csv
                                              feature_importance.csv
                                              metrics_history.csv

    Raises:
        SystemExit: Si cualquier paso critico falla.
    """
    logger.info("=" * 60)
    logger.info("TRINITY-AI - Pipeline de Mora Temprana Crediticia")
    logger.info("=" * 60)

    # ── Paso 1: Carga y validacion ─────────────────────────────────────────
    logger.info("[1/6] Cargando y validando dataset...")
    try:
        from src.data_loader import load_dataset, ALL_FEATURE_COLS, TARGET_COL
        df = load_dataset(PARQUET_PATH)
    except FileNotFoundError as exc:
        logger.error("Dataset no encontrado: %s", exc)
        sys.exit(1)
    except ValueError as exc:
        logger.error("Fallo de validacion de schema: %s", exc)
        sys.exit(1)

    # ── Paso 2: Auditoria de calidad de datos ─────────────────────────────
    logger.info("[2/6] Auditando calidad de datos...")
    try:
        from src.audit import audit_data_quality
        audit_data_quality(df)
    except Exception as exc:
        logger.error("Error en audit_data_quality: %s", exc, exc_info=True)
        sys.exit(1)

    # ── Paso 3: Information Value (IV) ────────────────────────────────────
    logger.info("[3/6] Calculando Information Value (IV)...")
    try:
        from src.audit import compute_iv
        compute_iv(df, target_col=TARGET_COL, feature_cols=ALL_FEATURE_COLS)
    except Exception as exc:
        logger.error("Error en compute_iv: %s", exc, exc_info=True)
        sys.exit(1)

    # ── Paso 4: Features, imputacion y split temporal ─────────────────────
    logger.info("[4/6] Construyendo features y particionando datos...")
    try:
        from src.features import build_features
        split = build_features(df)
    except Exception as exc:
        logger.error("Error en features.py: %s", exc, exc_info=True)
        sys.exit(1)

    logger.info(
        "Features: %d columnas | Train: %d | Val: %d | Test: %d",
        len(split.feature_cols),
        len(split.X_train),
        len(split.X_val),
        len(split.X_test),
    )

    # ── Paso 5: Entrenamiento LightGBM ────────────────────────────────────
    logger.info("[5/6] Entrenando modelo LightGBM...")
    try:
        from src.model import train_model
        train_result = train_model(
            X_train=split.X_train,
            y_train=split.y_train,
            X_val=split.X_val,
            y_val=split.y_val,
        )
    except Exception as exc:
        logger.error("Error en model.py: %s", exc, exc_info=True)
        sys.exit(1)

    # ── Paso 6: Evaluacion + reportes CSV ─────────────────────────────────
    logger.info("[6/6] Evaluando sobre Test set y generando reportes...")
    try:
        import numpy as np
        from src.evaluate import evaluate_model, update_metrics_json
        from src.audit import export_confusion_matrix

        metrics = evaluate_model(
            model_result=train_result,
            X_test=split.X_test,
            y_test=split.y_test,
            iteration_name="LightGBM_v1.0_baseline",
            notes=(
                f"Baseline run. best_iteration={train_result.best_iteration}, "
                f"scale_pos_weight=8.68, split=70/15/15 temporal."
            ),
        )
        update_metrics_json(metrics)

        # Matriz de confusion con umbral optimo del modelo
        y_scores = train_result.model.predict_proba(split.X_test)[:, 1]
        y_pred = (y_scores >= train_result.optimal_threshold).astype(int)
        export_confusion_matrix(split.y_test, y_pred)

    except Exception as exc:
        logger.error("Error en evaluacion/reportes: %s", exc, exc_info=True)
        sys.exit(1)

    # ── Resumen final ──────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Pipeline completado exitosamente.")
    logger.info(
        "Metricas clave -> ROC-AUC: %.4f | KS: %.4f | Recall: %.4f | PR-AUC: %.4f",
        metrics["roc_auc"],
        metrics["ks"],
        metrics["recall_class1"],
        metrics["pr_auc"],
    )
    logger.info("Reportes generados en reports/:")
    logger.info("  - data_quality.csv")
    logger.info("  - feature_selection_iv.csv")
    logger.info("  - confusion_matrix.csv")
    logger.info("  - feature_importance.csv")
    logger.info("  - metrics_history.csv")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
