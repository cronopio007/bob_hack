"""src/model.py — Entrenamiento LightGBM con early stopping sobre Validation.

Responsabilidades:
  - Entrenamiento del modelo primario (LightGBM) con scale_pos_weight=8.68.
  - Early stopping sobre el conjunto de validación (evita overfitting).
  - Devolución del modelo entrenado y del umbral óptimo (maximiza Recall ≥ 0.55).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes (ADR-004: scale_pos_weight = 19751 / 2274 ≈ 8.68)
# ---------------------------------------------------------------------------
SCALE_POS_WEIGHT: float = 8.68
RECALL_FLOOR: float = 0.55  # Restricción dura: Recall ≥ 0.55 (ADR-008)

# Hiperparámetros base (docs/1_architecture_plan.md §4.1)
BASE_PARAMS: dict[str, Any] = {
    "objective": "binary",
    "metric": "auc",
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 50,
    "lambda_l1": 0.1,
    "lambda_l2": 0.1,
    "colsample_bytree": 0.8,
    "scale_pos_weight": SCALE_POS_WEIGHT,
    "random_state": 42,
    "verbose": -1,
    "n_jobs": -1,
}


@dataclass
class TrainResult:
    """Resultado del entrenamiento con todos los artefactos necesarios."""

    model: lgb.LGBMClassifier
    best_iteration: int
    optimal_threshold: float
    val_scores: np.ndarray  # Probabilidades sobre val set
    feature_importances: pd.Series
    params_used: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Selección de umbral óptimo
# ---------------------------------------------------------------------------
def find_optimal_threshold(
    y_true: pd.Series,
    y_scores: np.ndarray,
    recall_floor: float = RECALL_FLOOR,
) -> float:
    """Determina el umbral que maximiza F1 sujeto a Recall ≥ recall_floor.

    Si ningún umbral satisface la restricción de Recall, devuelve el umbral
    de máximo Recall disponible con un warning explícito.

    Args:
        y_true: Etiquetas reales del conjunto de validación.
        y_scores: Probabilidades predichas (clase 1).
        recall_floor: Restricción dura de Recall mínimo.

    Returns:
        Umbral de clasificación óptimo (float entre 0 y 1).
    """
    precision_vals, recall_vals, thresholds = precision_recall_curve(y_true, y_scores)

    # precision_recall_curve devuelve n+1 puntos; thresholds tiene n elementos
    precision_vals = precision_vals[:-1]
    recall_vals = recall_vals[:-1]

    # F1 por umbral
    with np.errstate(invalid="ignore", divide="ignore"):
        f1_vals = np.where(
            (precision_vals + recall_vals) > 0,
            2 * precision_vals * recall_vals / (precision_vals + recall_vals),
            0.0,
        )

    # Filtrar por restricción dura de Recall
    valid_mask = recall_vals >= recall_floor
    if not valid_mask.any():
        logger.warning(
            "Ningún umbral alcanza Recall ≥ %.2f. "
            "Usando umbral de Recall máximo como fallback.",
            recall_floor,
        )
        best_idx = int(np.argmax(recall_vals))
    else:
        # Entre los umbrales válidos, maximizar F1
        best_idx = int(np.argmax(np.where(valid_mask, f1_vals, -np.inf)))

    optimal = float(thresholds[best_idx])
    logger.info(
        "Umbral optimo: %.4f -> Recall=%.4f | Precision=%.4f | F1=%.4f",
        optimal,
        recall_vals[best_idx],
        precision_vals[best_idx],
        f1_vals[best_idx],
    )
    return optimal


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    params: dict[str, Any] | None = None,
) -> TrainResult:
    """Entrena LightGBM con early stopping sobre validación.

    Args:
        X_train: Features de entrenamiento.
        y_train: Target de entrenamiento.
        X_val: Features de validación (usadas en early stopping).
        y_val: Target de validación.
        params: Hiperparámetros opcionales. Si None, usa BASE_PARAMS.

    Returns:
        TrainResult con modelo, umbral óptimo e importancias de features.

    Raises:
        ValueError: Si X_train está vacío o tiene cero features.
    """
    if X_train.empty or X_train.shape[1] == 0:
        raise ValueError("X_train vacío o sin features. Verificar pipeline de features.")

    effective_params = {**BASE_PARAMS, **(params or {})}
    logger.info(
        "Iniciando entrenamiento LightGBM | n_estimators=%d | scale_pos_weight=%.2f",
        effective_params["n_estimators"],
        effective_params["scale_pos_weight"],
    )

    model = lgb.LGBMClassifier(**effective_params)

    # Early stopping: detiene entrenamiento si val-AUC no mejora en 50 rondas
    callbacks = [
        lgb.early_stopping(stopping_rounds=50, verbose=False),
        lgb.log_evaluation(period=50),
    ]

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc",
        callbacks=callbacks,
    )

    best_iter: int = int(model.best_iteration_) if model.best_iteration_ > 0 else effective_params["n_estimators"]
    logger.info("Entrenamiento completado. Mejor iteración: %d", best_iter)

    # Probabilidades sobre val para calcular umbral
    val_scores: np.ndarray = model.predict_proba(X_val)[:, 1]
    optimal_threshold = find_optimal_threshold(y_val, val_scores)

    # Importancia de features (ganancia)
    feature_importances = pd.Series(
        model.feature_importances_,
        index=X_train.columns,
        name="importance",
    ).sort_values(ascending=False)

    logger.info("Top-5 features:\n%s", feature_importances.head(5).to_string())

    return TrainResult(
        model=model,
        best_iteration=best_iter,
        optimal_threshold=optimal_threshold,
        val_scores=val_scores,
        feature_importances=feature_importances,
        params_used=effective_params,
    )
