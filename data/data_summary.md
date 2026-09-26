# Resumen Estructural: `data_ejm.parquet`

## 1. Dimensiones del Dataset
- **Total de Filas:** 22,025
- **Total de Columnas:** 49

## 2. Distribución de Target (`FLAG_MORA_TEMPRANA_8D_3M`)
| Valor | Conteo | Porcentaje |
| :--- | :--- | :--- |
| `0` | 19,751 | 89.68% |
| `1` | 2,274 | 10.32% |

## 3. Esquema de Variables y Análisis de Nulos
| Columna | Tipo de Dato | Nulos (Conteo) | Nulos (%) |
| :--- | :--- | :--- | :--- |
| `FECHA` | `datetime64[ns]` | 0 | 0.00% |
| `CODIGO` | `float64` | 0 | 0.00% |
| `FLAG_MORA_TEMPRANA_8D_3M` | `int64` | 0 | 0.00% |
| `NRO_ENTS_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_DIRECTA_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_DIRECT_1000_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_LT_TC_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_CONS_TC_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_CONS_DISPEFECT_TC_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_HIP_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_CONV_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_EMP_SF` | `float64` | 0 | 0.00% |
| `NRO_ENTS_CONS_SF` | `float64` | 0 | 0.00% |
| `NRO_EN_12M_ES_REPORTADO` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_30_ATRASO_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_60_ATRASO_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_90_ATRASO_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_120_ATRASO_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_DEF_O_PEOR_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_DUD_O_PEOR_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_ES_PER_O_PEOR_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_DIRECTA_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_DIRECT_1000_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_LT_TC_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_CONS_TC_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_CONS_DISPEFECT_TC_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_HIP_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_CONV_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_EMP_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_NRO_ENTS_CONS_SF` | `float64` | 0 | 0.00% |
| `VAR_12M_PROM_DIRECTA_CNS_TC` | `object` | 3,041 | 13.81% |
| `VAR_12M_MAX_DIRECTA_CNS_TC` | `object` | 0 | 0.00% |
| `VAR_12M_MED_DIRECTA_CNS_TC` | `object` | 0 | 0.00% |
| `VAR_12M_PROM_DIRECTA` | `object` | 3,041 | 13.81% |
| `VAR_12M_MAX_DIRECTA` | `object` | 0 | 0.00% |
| `VAR_12M_MED_DIRECTA` | `object` | 0 | 0.00% |
| `VAR_12M_PROM_DIRECTA_CNS` | `object` | 3,041 | 13.81% |
| `VAR_12M_MAX_DIRECTA_CNS` | `object` | 0 | 0.00% |
| `VAR_12M_MED_DIRECTA_CNS` | `object` | 0 | 0.00% |
| `VAR_12M_PROM_DEUDA` | `object` | 3,041 | 13.81% |
| `VAR_12M_MAX_DEUDA` | `object` | 0 | 0.00% |
| `VAR_12M_MED_DEUDA` | `object` | 0 | 0.00% |
| `VAR_6M_PROM_DIRECTA_CNS_TC` | `object` | 1,455 | 6.61% |
| `VAR_6M_MAX_DIRECTA_CNS_TC` | `object` | 0 | 0.00% |
| `VAR_6M_MED_DIRECTA_CNS_TC` | `object` | 0 | 0.00% |
| `VAR_6M_PROM_DIRECTA` | `object` | 1,455 | 6.61% |
| `VAR_6M_MAX_DIRECTA` | `object` | 0 | 0.00% |
| `VAR_6M_MED_DIRECTA` | `object` | 0 | 0.00% |
