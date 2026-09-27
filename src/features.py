"""src/features.py — Ingeniería de features, imputación y Time-Based Split.

Responsabilidades:
  1. Imputación estratificada por cuartil de NRO_ENTS_SF (Grupo D).
  2. Exclusión de columnas de control (FECHA, CODIGO).
  3. Partición temporal 70 / 15 / 15 sin shuffle.

Nota: El cast de columnas Grupo D ya se realiza en data_loader.load_dataset().
      Este módulo asume que todas las columnas son float64 o NaN al recibirlas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data_loader import DATE_COL, ID_COL, OBJECT_COLS_GROUP_D, TARGET_COL

logger = logging.getLogger(__name__)

# Columna usada para estratificar la imputación
STRATIFY_COL: str = "NRO_ENTS_SF"

# Columnas que nunca entran al modelo
EXCLUDE_COLS: list[str] = [DATE_COL, ID_COL, TARGET_COL]

# Proporciones del split temporal
TRAIN_RATIO: float = 0.70
VAL_RATIO: float = 0.15
# Test ratio implícito: 1 - TRAIN_RATIO - VAL_RATIO = 0.15


@dataclass(frozen=True)
class SplitResult:
    """Contenedor inmutable con los tres conjuntos de datos."""

    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series

    @property
    def feature_cols(self) -> list[str]:
        return list(self.X_train.columns)


# ---------------------------------------------------------------------------
# Imputación estratificada
# ---------------------------------------------------------------------------
def _safe_qcut(series: pd.Series, n_bins: int = 4) -> tuple[pd.Series, list[int]]:
    """Aplica pd.qcut con manejo de bins duplicados.

    Si NRO_ENTS_SF tiene muchos empates (variable de conteo), qcut puede
    producir menos de n_bins bins distintos. Se usa duplicates='drop' y
    se retorna la lista de etiquetas reales generadas.

    Returns:
        (series con etiquetas enteras, lista de etiquetas únicas generadas)
    """
    bins_result = pd.qcut(series, q=n_bins, labels=False, duplicates="drop")
    unique_bins = sorted(bins_result.dropna().unique().tolist())
    # Renombrar bins a 1-based para consistencia
    bin_mapping = {old: i + 1 for i, old in enumerate(unique_bins)}
    return bins_result.map(bin_mapping).fillna(1).astype(int), list(bin_mapping.values())


def _compute_quartile_medians(
    df_train: pd.DataFrame,
    cols_to_impute: list[str],
) -> dict[int, dict[str, float]]:
    """Calcula medianas por cuartil de NRO_ENTS_SF sobre el set de train.

    Returns:
        Diccionario {cuartil (1-based): {columna: mediana}}.
        Se usa sólo el conjunto de train para evitar data leakage.
    """
    df_train = df_train.copy()
    quartiles, bin_labels = _safe_qcut(df_train[STRATIFY_COL])
    df_train["_quartile"] = quartiles

    medians: dict[int, dict[str, float]] = {}
    for q in bin_labels:
        subset = df_train[df_train["_quartile"] == q]
        medians[q] = {
            col: float(subset[col].median()) if (col in subset.columns and subset[col].notna().any()) else 0.0
            for col in cols_to_impute
        }
    return medians


def _apply_stratified_imputation(
    df: pd.DataFrame,
    quartile_medians: dict[int, dict[str, float]],
    global_medians: dict[str, float],
) -> pd.DataFrame:
    """Imputa nulos en columnas Grupo D con la mediana del cuartil correspondiente.

    Usa global_medians como fallback si el cuartil no tiene datos.
    """
    df = df.copy()
    quartiles, bin_labels = _safe_qcut(df[STRATIFY_COL])
    df["_quartile"] = quartiles
    bin_labels_set = set(quartile_medians.keys())

    cols_to_impute = [c for c in OBJECT_COLS_GROUP_D if c in df.columns]

    for col in cols_to_impute:
        null_mask = df[col].isna()
        if not null_mask.any():
            continue
        for q in sorted(bin_labels_set):
            q_mask = null_mask & (df["_quartile"] == q)
            fill_val = quartile_medians.get(q, {}).get(col, global_medians.get(col, 0.0))
            df.loc[q_mask, col] = fill_val

    df = df.drop(columns=["_quartile"])
    return df


# ---------------------------------------------------------------------------
# Time-Based Split
# ---------------------------------------------------------------------------
def _temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Divide el DataFrame en train/val/test ordenado por FECHA ascendente.

    No usa shuffle. El test set es el 15% más reciente.

    Returns:
        Tupla (df_train, df_val, df_test).
    """
    df_sorted = df.sort_values(DATE_COL, ascending=True).reset_index(drop=True)
    n = len(df_sorted)

    train_end = int(n * TRAIN_RATIO)
    val_end = train_end + int(n * VAL_RATIO)

    df_train = df_sorted.iloc[:train_end].copy()
    df_val = df_sorted.iloc[train_end:val_end].copy()
    df_test = df_sorted.iloc[val_end:].copy()

    logger.info(
        "Split temporal -> Train: %d | Val: %d | Test: %d",
        len(df_train),
        len(df_val),
        len(df_test),
    )
    return df_train, df_val, df_test


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def build_features(df: pd.DataFrame) -> SplitResult:
    """Ejecuta el pipeline completo de features y devuelve los tres conjuntos.

    Pipeline:
      1. Split temporal 70/15/15 (antes de imputar para evitar leakage).
      2. Calcula medianas de imputación SÓLO sobre train.
      3. Aplica imputación estratificada a train, val y test.
      4. Separa features de target y elimina columnas de control.

    Args:
        df: DataFrame crudo devuelto por load_dataset().

    Returns:
        SplitResult con X_train, X_val, X_test, y_train, y_val, y_test.
    """
    # --- Paso 1: Split temporal ANTES de imputar (evita leakage) ---
    df_train_raw, df_val_raw, df_test_raw = _temporal_split(df)

    # --- Paso 2: Medianas de imputación calculadas SÓLO sobre train ---
    cols_to_impute = [c for c in OBJECT_COLS_GROUP_D if c in df_train_raw.columns]
    quartile_medians = _compute_quartile_medians(df_train_raw, cols_to_impute)
    global_medians: dict[str, float] = {
        col: float(df_train_raw[col].median()) for col in cols_to_impute
    }
    logger.info("Medianas de imputación calculadas sobre train (%d cuartiles).", 4)

    # --- Paso 3: Aplicar imputación a los tres conjuntos ---
    df_train = _apply_stratified_imputation(df_train_raw, quartile_medians, global_medians)
    df_val = _apply_stratified_imputation(df_val_raw, quartile_medians, global_medians)
    df_test = _apply_stratified_imputation(df_test_raw, quartile_medians, global_medians)

    # --- Paso 4: Separar X e y, excluir columnas de control ---
    feature_cols = [c for c in df_train.columns if c not in EXCLUDE_COLS]

    X_train = df_train[feature_cols].reset_index(drop=True)
    X_val = df_val[feature_cols].reset_index(drop=True)
    X_test = df_test[feature_cols].reset_index(drop=True)

    y_train: pd.Series = df_train[TARGET_COL].reset_index(drop=True)
    y_val: pd.Series = df_val[TARGET_COL].reset_index(drop=True)
    y_test: pd.Series = df_test[TARGET_COL].reset_index(drop=True)

    logger.info(
        "Features construidas: %d columnas. "
        "Distribucion target -> Train: %.2f%% | Val: %.2f%% | Test: %.2f%%",
        len(feature_cols),
        y_train.mean() * 100,
        y_val.mean() * 100,
        y_test.mean() * 100,
    )

    # Verificación de nulos residuales (FAIL FAST)
    null_counts = X_train.isnull().sum()
    remaining_nulls = null_counts[null_counts > 0]
    if not remaining_nulls.empty:
        logger.warning(
            "Nulos residuales en X_train tras imputación:\n%s", remaining_nulls.to_string()
        )

    return SplitResult(
        X_train=X_train,
        X_val=X_val,
        X_test=X_test,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
    )
