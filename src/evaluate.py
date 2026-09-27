"""src/evaluate.py — Evaluación rigurosa del modelo y persistencia de reportes.

Métricas calculadas (ADR-006 + ADR-008):
  - ROC-AUC, PR-AUC, KS (Kolmogorov-Smirnov)
  - Recall clase 1, Precision clase 1, F1-Score clase 1
  - Accuracy (reportada pero NO usada como KPI)
  - Latencia P95 de inferencia (restricción <50ms)

Salidas obligatorias (AGENTS-do.md §3):
  - reports/metrics_history.csv  — historial acumulativo append-only
  - reports/feature_importance.csv — top 15 features por ganancia LightGBM
  - reports/metrics.json — metadatos del sistema (contrato existente)
"""

from __future__ import annotations

import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    accuracy_score,
)

from src.model import TrainResult

logger = logging.getLogger(__name__)

REPORTS_DIR: Path = Path(__file__).resolve().parent.parent / "reports"
METRICS_JSON_PATH: Path = REPORTS_DIR / "metrics.json"
METRICS_CSV_PATH: Path = REPORTS_DIR / "metrics_history.csv"
FEATURE_IMPORTANCE_CSV_PATH: Path = REPORTS_DIR / "feature_importance.csv"
LATENCY_PERCENTILE: int = 95
LATENCY_N_RUNS: int = 200  # Número de inferencias para medir P95
FEATURE_IMPORTANCE_TOP_N: int = 15


# ---------------------------------------------------------------------------
# Tipos internos
# ---------------------------------------------------------------------------
MetricsDict = dict[str, float | int | str | None]


# ---------------------------------------------------------------------------
# KS (Kolmogorov-Smirnov)
# ---------------------------------------------------------------------------
def compute_ks(y_true: pd.Series, y_scores: np.ndarray) -> float:
    """Calcula el estadístico KS: separación máxima entre CDFs de buenos y malos.

    KS = max |CDF_buenos(t) - CDF_malos(t)| sobre todos los umbrales t.

    Returns:
        KS en el rango [0, 1]. Valor ≥ 0.33 es el target mínimo.
    """
    df_ks = pd.DataFrame({"score": y_scores, "target": y_true.values})
    df_ks = df_ks.sort_values("score", ascending=False).reset_index(drop=True)

    n_pos = int(df_ks["target"].sum())
    n_neg = len(df_ks) - n_pos

    if n_pos == 0 or n_neg == 0:
        logger.warning("KS indefinido: una clase tiene 0 registros.")
        return 0.0

    cumsum_pos = df_ks["target"].cumsum() / n_pos
    cumsum_neg = (1 - df_ks["target"]).cumsum() / n_neg

    ks = float((cumsum_pos - cumsum_neg).abs().max())
    return ks


# ---------------------------------------------------------------------------
# Latencia P95
# ---------------------------------------------------------------------------
def measure_latency_p95(
    model_result: TrainResult,
    X_sample: pd.DataFrame,
    n_runs: int = LATENCY_N_RUNS,
) -> float:
    """Mide la latencia P95 de inferencia individual (ms).

    Realiza n_runs predicciones sobre un único registro y calcula el percentil 95.

    Args:
        model_result: TrainResult con el modelo entrenado.
        X_sample: DataFrame con al menos 1 fila (se usa solo la primera).
        n_runs: Número de corridas para estabilizar el percentil.

    Returns:
        Latencia P95 en milisegundos.
    """
    single_row = X_sample.iloc[[0]]
    latencies_ms: list[float] = []

    for _ in range(n_runs):
        t0 = time.perf_counter()
        model_result.model.predict_proba(single_row)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    p95 = float(np.percentile(latencies_ms, LATENCY_PERCENTILE))
    logger.info("Latencia P%d: %.3f ms", LATENCY_PERCENTILE, p95)

    if p95 > 50.0:
        logger.warning(
            "AVISO: Latencia P95 = %.2f ms supera el limite de 50ms. "
            "Considerar reducir num_leaves o numero de features.",
            p95,
        )
    return p95


# ---------------------------------------------------------------------------
# Exportación CSV — métricas históricas (AGENTS-do.md §3a)
# ---------------------------------------------------------------------------
def export_metrics_csv(
    metrics: MetricsDict,
    output_path: Path = METRICS_CSV_PATH,
) -> None:
    """Append-only de una fila de métricas en reports/metrics_history.csv.

    Columnas fijas (AGENTS-do.md §3a):
        timestamp, model, roc_auc, ks, pr_auc, f1_score, precision, recall, latency_ms

    Si el archivo no existe lo crea con cabecera. Si ya existe, hace append sin
    reescribir el historial.

    Args:
        metrics: Diccionario devuelto por evaluate_model().
        output_path: Ruta al CSV de historial.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "timestamp":   metrics.get("timestamp", ""),
        "model":       metrics.get("iteration", ""),
        "roc_auc":     metrics.get("roc_auc", ""),
        "ks":          metrics.get("ks", ""),
        "pr_auc":      metrics.get("pr_auc", ""),
        "f1_score":    metrics.get("f1_score", ""),
        "precision":   metrics.get("precision_class1", ""),
        "recall":      metrics.get("recall_class1", ""),
        "latency_ms":  metrics.get("latency_ms", ""),
    }

    write_header = not output_path.exists()
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    logger.info("metrics_history.csv actualizado (append): %s", output_path)


# ---------------------------------------------------------------------------
# Exportación CSV — feature importance top-N (AGENTS-do.md §3b)
# ---------------------------------------------------------------------------
def export_feature_importance_csv(
    feature_importances: pd.Series,
    output_path: Path = FEATURE_IMPORTANCE_CSV_PATH,
    top_n: int = FEATURE_IMPORTANCE_TOP_N,
) -> None:
    """Sobreescribe reports/feature_importance.csv con las top N variables.

    Columnas fijas (AGENTS-do.md §3b): feature, importance

    Se sobreescribe en cada ejecución — refleja siempre el modelo más reciente.

    Args:
        feature_importances: pd.Series indexada por nombre de feature, ordenada
                             desc por ganancia (devuelta por train_model()).
        output_path: Ruta al CSV de importancias.
        top_n: Número de features a exportar.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_fi = (
        feature_importances.head(top_n)
        .reset_index()
        .rename(columns={"index": "feature", "importance": "importance"})
    )
    df_fi.columns = ["feature", "importance"]
    df_fi.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(
        "feature_importance.csv generado (top %d features): %s", top_n, output_path
    )


# ---------------------------------------------------------------------------
# Evaluación completa
# ---------------------------------------------------------------------------
def evaluate_model(
    model_result: TrainResult,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    iteration_name: str = "LightGBM_v1.0",
    notes: str = "",
) -> MetricsDict:
    """Evalúa el modelo sobre el conjunto de test y devuelve el diccionario de métricas.

    Además de calcular métricas, exporta obligatoriamente (AGENTS-do.md §3):
      - reports/metrics_history.csv (append)
      - reports/feature_importance.csv (top 15, sobreescribe)

    Usa el umbral óptimo calculado durante el entrenamiento (no 0.5).

    Args:
        model_result: TrainResult del módulo model.py.
        X_test: Features del conjunto de test (holdout).
        y_test: Target del conjunto de test.
        iteration_name: Etiqueta del experimento para reports/*.
        notes: Notas adicionales del experimento.

    Returns:
        Diccionario de métricas listo para serializar en metrics.json.
    """
    logger.info("Evaluando sobre test set (%d registros)...", len(X_test))

    # --- Inferencia ---
    y_scores: np.ndarray = model_result.model.predict_proba(X_test)[:, 1]
    threshold = model_result.optimal_threshold
    y_pred: np.ndarray = (y_scores >= threshold).astype(int)

    # --- Métricas de ranking (independientes del umbral) ---
    roc_auc = float(roc_auc_score(y_test, y_scores))
    pr_auc = float(average_precision_score(y_test, y_scores))
    ks = compute_ks(y_test, y_scores)

    # --- Métricas de clasificación (dependientes del umbral) ---
    recall_c1 = float(recall_score(y_test, y_pred, zero_division=0))
    precision_c1 = float(precision_score(y_test, y_pred, zero_division=0))
    f1_c1 = float(f1_score(y_test, y_pred, zero_division=0))
    accuracy = float(accuracy_score(y_test, y_pred))

    # --- Latencia P95 ---
    latency_p95 = measure_latency_p95(model_result, X_test)

    # --- Log de resultados ---
    logger.info(
        "\n"
        "===================================\n"
        "  RESULTADOS MODELO: %s\n"
        "-----------------------------------\n"
        "  ROC-AUC  : %.4f  (target >= 0.78)\n"
        "  PR-AUC   : %.4f  (target >= 0.50)\n"
        "  KS       : %.4f  (target >= 0.33)\n"
        "  Recall   : %.4f  (target >= 0.55) * restriccion dura\n"
        "  Precision: %.4f  (target >= 0.35)\n"
        "  F1-Score : %.4f  (target >= 0.45)\n"
        "  Accuracy : %.4f  (informativo)\n"
        "  Latencia : %.2f ms  (target <50ms)\n"
        "  Umbral   : %.4f\n"
        "===================================",
        iteration_name,
        roc_auc, pr_auc, ks,
        recall_c1, precision_c1, f1_c1,
        accuracy, latency_p95, threshold,
    )

    metrics: MetricsDict = {
        "iteration": iteration_name,
        "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "ks": round(ks, 4),
        "recall_class1": round(recall_c1, 4),
        "precision_class1": round(precision_c1, 4),
        "f1_score": round(f1_c1, 4),
        "accuracy": round(accuracy, 4),
        "latency_ms": round(latency_p95, 3),
        "threshold_used": round(threshold, 4),
        "best_iteration": model_result.best_iteration,
        "notes": notes,
    }

    # --- Exportaciones CSV obligatorias (AGENTS-do.md §3) ---
    export_metrics_csv(metrics)
    export_feature_importance_csv(model_result.feature_importances)

    return metrics


# ---------------------------------------------------------------------------
# Persistencia en reports/metrics.json
# ---------------------------------------------------------------------------
def update_metrics_json(
    metrics: MetricsDict,
    output_path: Path = METRICS_JSON_PATH,
) -> None:
    """Actualiza reports/metrics.json añadiendo el experimento al historial.

    Nunca sobreescribe el historial completo — solo append + actualiza
    current_metrics con los valores del último experimento.

    Args:
        metrics: Diccionario devuelto por evaluate_model().
        output_path: Ruta al archivo metrics.json.

    Raises:
        ValueError: Si el JSON existente no es parseable.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Leer estado actual
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                current: dict[str, Any] = json.load(f)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"reports/metrics.json está corrupto y no es parseable: {exc}"
                ) from exc
    else:
        current = {
            "project": "Trinity-AI",
            "task": "Credit Risk Assessment",
            "model_version": "v1.0.0",
            "history": [],
        }

    # Actualizar current_metrics con las métricas del nuevo experimento
    current["current_metrics"] = {
        "roc_auc": metrics["roc_auc"],
        "pr_auc": metrics["pr_auc"],
        "ks": metrics["ks"],
        "recall_class1": metrics["recall_class1"],
        "precision_class1": metrics["precision_class1"],
        "f1_score": metrics["f1_score"],
        "accuracy": metrics["accuracy"],
        "latency_ms": metrics["latency_ms"],
    }
    current["timestamp"] = metrics["timestamp"]
    current["model_version"] = "v1.0.0-lgbm"

    # Append al historial (nunca borrar)
    if "history" not in current:
        current["history"] = []
    current["history"].append(metrics)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    logger.info("metrics.json actualizado: %s", output_path)
