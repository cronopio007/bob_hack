"""src/audit.py -- Auditoria regulatoria bancaria del pipeline Trinity-AI.

Responsabilidades (AGENTS-do.md Contrato Estricto de Reportes):
  1. audit_data_quality()     -> reports/data_quality.csv
  2. compute_iv()             -> reports/feature_selection_iv.csv
  3. export_confusion_matrix()-> reports/confusion_matrix.csv

Todas las funciones son independientes del modelo y pueden ejecutarse
antes o despues del entrenamiento segun corresponda.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas de salida
# ---------------------------------------------------------------------------
REPORTS_DIR: Path = Path(__file__).resolve().parent.parent / "reports"
DATA_QUALITY_CSV: Path = REPORTS_DIR / "data_quality.csv"
FEATURE_IV_CSV: Path = REPORTS_DIR / "feature_selection_iv.csv"
CONFUSION_MATRIX_CSV: Path = REPORTS_DIR / "confusion_matrix.csv"

# Constantes de IV (Basel/credito estandar)
IV_THRESHOLDS: list[tuple[float, str]] = [
    (0.02, "Impredecible"),
    (0.10, "Debil"),
    (0.30, "Mediano"),
    (float("inf"), "Fuerte"),
]
IV_MIN_SELECCION: float = 0.02   # IV minimo para marcar como seleccionada
IV_N_BINS: int = 10              # bins para discretizar variables continuas


# ---------------------------------------------------------------------------
# 1. Auditoria de calidad de datos
# ---------------------------------------------------------------------------
def audit_data_quality(
    df: pd.DataFrame,
    output_path: Path = DATA_QUALITY_CSV,
) -> pd.DataFrame:
    """Genera reports/data_quality.csv con analisis de nulos y tipos.

    Columnas de salida (AGENTS-do.md §Contrato 1):
        columna, tipo_dato, nulos_conteo, nulos_pct, alerta_calidad

    Criterio de alerta:
        - "CRITICO"  si nulos_pct > 30%
        - "AVISO"    si nulos_pct > 5%
        - "OK"       en caso contrario

    Args:
        df: DataFrame crudo devuelto por load_dataset() (post-cast Grupo D).
        output_path: Ruta de escritura del CSV.

    Returns:
        DataFrame con el reporte de calidad (para consumo interno/tests).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_rows: int = len(df)
    rows: list[dict] = []

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round(null_count / total_rows * 100, 2) if total_rows > 0 else 0.0
        dtype_str = str(df[col].dtype)

        if null_pct > 30.0:
            alerta = "CRITICO"
        elif null_pct > 5.0:
            alerta = "AVISO"
        else:
            alerta = "OK"

        rows.append({
            "columna":       col,
            "tipo_dato":     dtype_str,
            "nulos_conteo":  null_count,
            "nulos_pct":     null_pct,
            "alerta_calidad": alerta,
        })

    df_quality = pd.DataFrame(rows)
    df_quality.to_csv(output_path, index=False, encoding="utf-8")

    criticos = (df_quality["alerta_calidad"] == "CRITICO").sum()
    avisos   = (df_quality["alerta_calidad"] == "AVISO").sum()
    logger.info(
        "data_quality.csv generado: %d columnas | %d CRITICO | %d AVISO -> %s",
        len(df_quality), criticos, avisos, output_path,
    )
    return df_quality


# ---------------------------------------------------------------------------
# 2. Information Value (IV) y seleccion de variables
# ---------------------------------------------------------------------------
def _iv_score(feature: pd.Series, target: pd.Series, n_bins: int) -> float:
    """Calcula el IV de una variable numerica usando binning por cuantiles.

    IV = sum((pct_events - pct_non_events) * WOE)
    donde WOE = ln(pct_events / pct_non_events) por bin.

    Devuelve 0.0 ante divisiones por cero o columnas sin variacion.
    """
    # Rellenar NaN con la mediana para no perder bins
    feat_filled = feature.fillna(feature.median())

    # Discretizar en n_bins cuantiles; duplicates='drop' maneja empates
    try:
        binned = pd.qcut(feat_filled, q=n_bins, labels=False, duplicates="drop")
    except ValueError:
        return 0.0

    df_bin = pd.DataFrame({"bin": binned, "target": target.values})
    n_events     = int(target.sum())
    n_non_events = len(target) - n_events

    if n_events == 0 or n_non_events == 0:
        return 0.0

    iv = 0.0
    for _, grp in df_bin.groupby("bin", observed=True):
        ev  = int(grp["target"].sum())
        nev = len(grp) - ev

        pct_ev  = max(ev,  1) / n_events
        pct_nev = max(nev, 1) / n_non_events

        woe = np.log(pct_ev / pct_nev)
        iv += (pct_ev - pct_nev) * woe

    return round(float(iv), 6)


def _iv_label(iv: float) -> str:
    """Devuelve la etiqueta de poder predictivo segun umbrales bancarios."""
    for threshold, label in IV_THRESHOLDS:
        if iv < threshold:
            return label
    return "Fuerte"


def compute_iv(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str],
    output_path: Path = FEATURE_IV_CSV,
    n_bins: int = IV_N_BINS,
) -> pd.DataFrame:
    """Calcula IV y correlacion de cada feature numerica contra el target.

    Columnas de salida (AGENTS-do.md §Contrato 2):
        feature, iv_score, poder_predictivo, correlacion_target, seleccionada

    Criterio de seleccion: iv_score >= 0.02 (Debil o superior).

    Args:
        df: DataFrame completo con features ya en float64.
        target_col: Nombre de la columna target binaria.
        feature_cols: Lista de columnas a evaluar (excluye FECHA, CODIGO, target).
        output_path: Ruta de escritura del CSV.
        n_bins: Numero de bins para la discretizacion del IV.

    Returns:
        DataFrame del reporte IV ordenado por iv_score desc.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target: pd.Series = df[target_col].astype(int)
    rows: list[dict] = []

    numeric_cols = [
        c for c in feature_cols
        if c in df.columns and pd.api.types.is_numeric_dtype(df[c])
    ]

    for col in numeric_cols:
        iv = _iv_score(df[col], target, n_bins)
        corr = float(df[col].fillna(df[col].median()).corr(target.astype(float)))
        corr = round(corr, 6) if not np.isnan(corr) else 0.0

        rows.append({
            "feature":             col,
            "iv_score":            iv,
            "poder_predictivo":    _iv_label(iv),
            "correlacion_target":  corr,
            "seleccionada":        iv >= IV_MIN_SELECCION,
        })

    df_iv = (
        pd.DataFrame(rows)
        .sort_values("iv_score", ascending=False)
        .reset_index(drop=True)
    )
    df_iv.to_csv(output_path, index=False, encoding="utf-8")

    n_sel = int(df_iv["seleccionada"].sum())
    logger.info(
        "feature_selection_iv.csv generado: %d features evaluadas | %d seleccionadas (IV >= %.2f) -> %s",
        len(df_iv), n_sel, IV_MIN_SELECCION, output_path,
    )
    return df_iv


# ---------------------------------------------------------------------------
# 3. Matriz de confusion
# ---------------------------------------------------------------------------
def export_confusion_matrix(
    y_true: pd.Series,
    y_pred: np.ndarray,
    output_path: Path = CONFUSION_MATRIX_CSV,
) -> pd.DataFrame:
    """Genera reports/confusion_matrix.csv con la matriz de confusion en test.

    Columnas de salida (AGENTS-do.md §Contrato 3):
        actual, predicho, conteo, tasa_pct

    Filas: TN (0|0), FP (0|1), FN (1|0), TP (1|1)

    Args:
        y_true: Etiquetas reales del test set.
        y_pred: Predicciones binarias (0/1) con el umbral optimo.
        output_path: Ruta de escritura del CSV.

    Returns:
        DataFrame de 4 filas con la matriz de confusion.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(y_true)
    y_true_arr = np.asarray(y_true, dtype=int)

    rows: list[dict] = []
    for actual in [0, 1]:
        for predicho in [0, 1]:
            mask = (y_true_arr == actual) & (y_pred == predicho)
            conteo = int(mask.sum())
            tasa_pct = round(conteo / total * 100, 4) if total > 0 else 0.0
            rows.append({
                "actual":    actual,
                "predicho":  predicho,
                "conteo":    conteo,
                "tasa_pct":  tasa_pct,
            })

    df_cm = pd.DataFrame(rows)
    df_cm.to_csv(output_path, index=False, encoding="utf-8")

    tn, fp, fn, tp = [r["conteo"] for r in rows]
    logger.info(
        "confusion_matrix.csv generado: TN=%d | FP=%d | FN=%d | TP=%d -> %s",
        tn, fp, fn, tp, output_path,
    )
    return df_cm
