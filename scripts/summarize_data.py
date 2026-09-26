"""Extracts structural and statistical summary from data/data_ejm.parquet into data/data_summary.md."""

from pathlib import Path
import pandas as pd


def generate_summary(parquet_path: Path, output_path: Path) -> None:
    df = pd.read_parquet(parquet_path)
    rows, cols = df.shape

    target_col = "FLAG_MORA_TEMPRANA_8D_3M"
    if target_col in df.columns:
        counts = df[target_col].value_counts(dropna=False)
        pcts = df[target_col].value_counts(normalize=True, dropna=False) * 100
        target_rows = [
            f"| `{val}` | {count:,} | {pcts[val]:.2f}% |"
            for val, count in counts.items()
        ]
        target_md = (
            "| Valor | Conteo | Porcentaje |\n"
            "| :--- | :--- | :--- |\n"
            + "\n".join(target_rows)
        )
    else:
        target_md = f"_Columna `{target_col}` no presente en el dataset._"

    null_counts = df.isnull().sum()
    null_pcts = (null_counts / rows) * 100
    col_rows = [
        f"| `{col}` | `{df[col].dtype}` | {null_counts[col]:,} | {null_pcts[col]:.2f}% |"
        for col in df.columns
    ]
    schema_md = (
        "| Columna | Tipo de Dato | Nulos (Conteo) | Nulos (%) |\n"
        "| :--- | :--- | :--- | :--- |\n"
        + "\n".join(col_rows)
    )

    content = f"""# Resumen Estructural: `{parquet_path.name}`

## 1. Dimensiones del Dataset
- **Total de Filas:** {rows:,}
- **Total de Columnas:** {cols}

## 2. Distribución de Target (`{target_col}`)
{target_md}

## 3. Esquema de Variables y Análisis de Nulos
{schema_md}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Resumen guardado en: {output_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    generate_summary(
        parquet_path=base_dir / "data" / "data_ejm.parquet",
        output_path=base_dir / "data" / "data_summary.md",
    )
