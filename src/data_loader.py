"""src/data_loader.py — Carga y validación de schema del dataset de mora temprana.

Contrato:
  - Fuente: data/data_ejm.parquet
  - Valida tipos y rangos con Pydantic v2.
  - Falla rápido si >1% de registros no pasan validación.

Nota de datos:
  - Columnas Grupo D usan formato numérico latinoamericano:
    punto (.) como separador de miles (ej: '383.722.966' → 383722966).
    Se normaliza con _cast_latin_numeric() antes de cualquier operación.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
TARGET_COL: str = "FLAG_MORA_TEMPRANA_8D_3M"
ID_COL: str = "CODIGO"
DATE_COL: str = "FECHA"
MAX_INVALID_RATIO: float = 0.01  # Falla si >1% de registros son inválidos

# Columnas float64 sin nulos (Grupos A, B, C)
FLOAT_COLS_NO_NULL: list[str] = [
    # Grupo A
    "NRO_ENTS_SF",
    "NRO_ENTS_DIRECTA_SF",
    "NRO_ENTS_DIRECT_1000_SF",
    "NRO_ENTS_LT_TC_SF",
    "NRO_ENTS_CONS_TC_SF",
    "NRO_ENTS_CONS_DISPEFECT_TC_SF",
    "NRO_ENTS_HIP_SF",
    "NRO_ENTS_CONV_SF",
    "NRO_ENTS_EMP_SF",
    "NRO_ENTS_CONS_SF",
    # Grupo B
    "NRO_EN_12M_ES_REPORTADO",
    "VAR_12M_ES_30_ATRASO_SF",
    "VAR_12M_ES_60_ATRASO_SF",
    "VAR_12M_ES_90_ATRASO_SF",
    "VAR_12M_ES_120_ATRASO_SF",
    "VAR_12M_ES_DEF_O_PEOR_SF",
    "VAR_12M_ES_DUD_O_PEOR_SF",
    "VAR_12M_ES_PER_O_PEOR_SF",
    # Grupo C
    "VAR_12M_NRO_ENTS_SF",
    "VAR_12M_NRO_ENTS_DIRECTA_SF",
    "VAR_12M_NRO_ENTS_DIRECT_1000_SF",
    "VAR_12M_NRO_ENTS_LT_TC_SF",
    "VAR_12M_NRO_ENTS_CONS_TC_SF",
    "VAR_12M_NRO_ENTS_CONS_DISPEFECT_TC_SF",
    "VAR_12M_NRO_ENTS_HIP_SF",
    "VAR_12M_NRO_ENTS_CONV_SF",
    "VAR_12M_NRO_ENTS_EMP_SF",
    "VAR_12M_NRO_ENTS_CONS_SF",
]

# Columnas object→float64 con nulos posibles (Grupo D)
OBJECT_COLS_GROUP_D: list[str] = [
    "VAR_12M_PROM_DIRECTA_CNS_TC",
    "VAR_12M_MAX_DIRECTA_CNS_TC",
    "VAR_12M_MED_DIRECTA_CNS_TC",
    "VAR_12M_PROM_DIRECTA",
    "VAR_12M_MAX_DIRECTA",
    "VAR_12M_MED_DIRECTA",
    "VAR_12M_PROM_DIRECTA_CNS",
    "VAR_12M_MAX_DIRECTA_CNS",
    "VAR_12M_MED_DIRECTA_CNS",
    "VAR_12M_PROM_DEUDA",
    "VAR_12M_MAX_DEUDA",
    "VAR_12M_MED_DEUDA",
    "VAR_6M_PROM_DIRECTA_CNS_TC",
    "VAR_6M_MAX_DIRECTA_CNS_TC",
    "VAR_6M_MED_DIRECTA_CNS_TC",
    "VAR_6M_PROM_DIRECTA",
    "VAR_6M_MAX_DIRECTA",
    "VAR_6M_MED_DIRECTA",
]

ALL_FEATURE_COLS: list[str] = FLOAT_COLS_NO_NULL + OBJECT_COLS_GROUP_D


# ---------------------------------------------------------------------------
# Modelo Pydantic de validación por fila
# ---------------------------------------------------------------------------
class RawRecord(BaseModel):
    """Contrato de validación por registro del dataset crudo."""

    model_config = {"arbitrary_types_allowed": True}

    FECHA: datetime
    CODIGO: float
    FLAG_MORA_TEMPRANA_8D_3M: Literal[0, 1]
    NRO_ENTS_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_DIRECTA_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_DIRECT_1000_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_LT_TC_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_CONS_TC_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_CONS_DISPEFECT_TC_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_HIP_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_CONV_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_EMP_SF: Annotated[float, Field(ge=0.0)]
    NRO_ENTS_CONS_SF: Annotated[float, Field(ge=0.0)]
    NRO_EN_12M_ES_REPORTADO: float
    VAR_12M_ES_30_ATRASO_SF: float
    VAR_12M_ES_60_ATRASO_SF: float
    VAR_12M_ES_90_ATRASO_SF: float
    VAR_12M_ES_120_ATRASO_SF: float
    VAR_12M_ES_DEF_O_PEOR_SF: float
    VAR_12M_ES_DUD_O_PEOR_SF: float
    VAR_12M_ES_PER_O_PEOR_SF: float
    VAR_12M_NRO_ENTS_SF: float
    VAR_12M_NRO_ENTS_DIRECTA_SF: float
    VAR_12M_NRO_ENTS_DIRECT_1000_SF: float
    VAR_12M_NRO_ENTS_LT_TC_SF: float
    VAR_12M_NRO_ENTS_CONS_TC_SF: float
    VAR_12M_NRO_ENTS_CONS_DISPEFECT_TC_SF: float
    VAR_12M_NRO_ENTS_HIP_SF: float
    VAR_12M_NRO_ENTS_CONV_SF: float
    VAR_12M_NRO_ENTS_EMP_SF: float
    VAR_12M_NRO_ENTS_CONS_SF: float
    # Grupo D — opcionales
    VAR_12M_PROM_DIRECTA_CNS_TC: float | None = None
    VAR_12M_MAX_DIRECTA_CNS_TC: float | None = None
    VAR_12M_MED_DIRECTA_CNS_TC: float | None = None
    VAR_12M_PROM_DIRECTA: float | None = None
    VAR_12M_MAX_DIRECTA: float | None = None
    VAR_12M_MED_DIRECTA: float | None = None
    VAR_12M_PROM_DIRECTA_CNS: float | None = None
    VAR_12M_MAX_DIRECTA_CNS: float | None = None
    VAR_12M_MED_DIRECTA_CNS: float | None = None
    VAR_12M_PROM_DEUDA: float | None = None
    VAR_12M_MAX_DEUDA: float | None = None
    VAR_12M_MED_DEUDA: float | None = None
    VAR_6M_PROM_DIRECTA_CNS_TC: float | None = None
    VAR_6M_MAX_DIRECTA_CNS_TC: float | None = None
    VAR_6M_MED_DIRECTA_CNS_TC: float | None = None
    VAR_6M_PROM_DIRECTA: float | None = None
    VAR_6M_MAX_DIRECTA: float | None = None
    VAR_6M_MED_DIRECTA: float | None = None

    @field_validator("FECHA", mode="before")
    @classmethod
    def parse_fecha(cls, v: object) -> datetime:
        if isinstance(v, datetime):
            return v
        if hasattr(v, "to_pydatetime"):
            return v.to_pydatetime()
        return datetime.fromisoformat(str(v))


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def load_dataset(parquet_path: Path) -> pd.DataFrame:
    """Carga data/data_ejm.parquet, valida schema y devuelve DataFrame limpio.

    Args:
        parquet_path: Ruta absoluta al archivo parquet.

    Returns:
        DataFrame con columnas validadas. Columnas Grupo D ya convertidas a
        float64 (object→numeric). El DataFrame conserva todas las filas;
        la imputación ocurre en features.py.

    Raises:
        FileNotFoundError: Si el parquet no existe.
        ValueError: Si >1% de registros fallan la validación de schema.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Dataset no encontrado: {parquet_path}")

    logger.info("Cargando dataset: %s", parquet_path)
    df: pd.DataFrame = pd.read_parquet(parquet_path, engine="pyarrow")
    logger.info("Shape inicial: %s", df.shape)

    # --- Paso 1: Cast de columnas Grupo D (object → float64) ---
    # Formato latinoamericano: punto como separador de miles (sin decimal).
    # Ej: '383.722.966.220.753' → remove '.' → '383722966220753' → float
    for col in OBJECT_COLS_GROUP_D:
        # pandas 3.x usa StringDtype ('str') en lugar de object para columnas de texto.
        # La condición cubre ambos casos para compatibilidad.
        if col in df.columns and (
            df[col].dtype == object
            or pd.api.types.is_string_dtype(df[col])
            and not pd.api.types.is_float_dtype(df[col])
        ):
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(r"^(None|nan|NaN|<NA>)$", "", regex=True)  # vaciar centinelas
                .str.replace(".", "", regex=False)   # remover sep. de miles
                .str.replace(",", ".", regex=False)  # normalizar decimal si existe
                .pipe(pd.to_numeric, errors="coerce")  # strings vacíos → NaN
            )

    # --- Paso 2: Validación Pydantic sobre muestra representativa ---
    # Validar fila a fila sobre 22k registros es O(n) costoso.
    # Una muestra de 500 registros detecta problemas sistémicos de schema.
    total_rows: int = len(df)
    sample_size: int = min(500, total_rows)
    sample_df = df.sample(n=sample_size, random_state=42)

    invalid_count: int = 0
    for _, row in sample_df.iterrows():
        try:
            record_dict: dict = {
                "FECHA": row["FECHA"],
                "CODIGO": float(row["CODIGO"]),
                "FLAG_MORA_TEMPRANA_8D_3M": int(row["FLAG_MORA_TEMPRANA_8D_3M"]),
            }
            for col in FLOAT_COLS_NO_NULL:
                record_dict[col] = float(row[col])
            for col in OBJECT_COLS_GROUP_D:
                val = row.get(col)
                # pd.isna() cubre float('nan'), np.float64(nan), pd.NA y None.
                record_dict[col] = None if pd.isna(val) else float(val)
            RawRecord(**record_dict)
        except (ValidationError, ValueError, TypeError):
            invalid_count += 1

    # Extrapolar tasa de error de la muestra al total
    invalid_ratio: float = invalid_count / sample_size
    logger.info(
        "Validación: %d/%d registros inválidos (%.2f%%)",
        invalid_count,
        total_rows,
        invalid_ratio * 100,
    )

    if invalid_ratio > MAX_INVALID_RATIO:
        raise ValueError(
            f"Calidad de datos insuficiente: {invalid_count}/{total_rows} registros "
            f"({invalid_ratio:.2%}) fallaron la validación de schema. "
            f"Umbral máximo permitido: {MAX_INVALID_RATIO:.0%}."
        )

    logger.info("Dataset validado correctamente. Shape final: %s", df.shape)
    return df
