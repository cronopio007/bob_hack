# Estrategia de Datos: Dataset de Mora Temprana
**Proyecto:** Trinity-AI | **Fase:** Think → Do  
**Versión:** 1.0.0 | **Fecha:** 2026-09-26  
**Complementa:** `docs/1_architecture_plan.md`

---

## 1. Fuente de Datos

| Atributo | Valor |
| :--- | :--- |
| **Archivo fuente** | `data/data_ejm.parquet` |
| **Formato** | Apache Parquet (columnar, comprimido) |
| **Dimensiones** | 22,025 filas × 49 columnas |
| **Lectura recomendada** | `pd.read_parquet("data/data_ejm.parquet", engine="pyarrow")` |
| **Identificador de crédito** | `CODIGO` (float64) |
| **Dimensión temporal** | `FECHA` (datetime64[ns]) |

---

## 2. Catálogo Completo de Variables

### 2.1 Variables de Control (Excluir del modelo)

| Columna | Tipo | Descripción | Acción |
| :--- | :--- | :--- | :--- |
| `FECHA` | datetime64[ns] | Fecha de corte del registro | Solo para split temporal |
| `CODIGO` | float64 | ID del crédito | Excluir de features |
| `FLAG_MORA_TEMPRANA_8D_3M` | int64 | **Target** binario | Variable objetivo |

### 2.2 Grupo A — Exposición Crediticia en el SF (float64, 0 nulos)

Número de entidades del Sistema Financiero (SF) con las que el cliente tiene productos activos al momento del corte.

| Columna | Descripción |
| :--- | :--- |
| `NRO_ENTS_SF` | Total de entidades en el SF |
| `NRO_ENTS_DIRECTA_SF` | Entidades con crédito directo |
| `NRO_ENTS_DIRECT_1000_SF` | Entidades con crédito directo > 1,000 |
| `NRO_ENTS_LT_TC_SF` | Entidades con líneas de TC en el SF |
| `NRO_ENTS_CONS_TC_SF` | Entidades con consumo en TC |
| `NRO_ENTS_CONS_DISPEFECT_TC_SF` | Entidades con disposición efectivo en TC |
| `NRO_ENTS_HIP_SF` | Entidades con crédito hipotecario |
| `NRO_ENTS_CONV_SF` | Entidades con crédito de convenio |
| `NRO_ENTS_EMP_SF` | Entidades con crédito empresarial |
| `NRO_ENTS_CONS_SF` | Entidades con crédito de consumo |

### 2.3 Grupo B — Comportamiento de Mora Histórica (float64, 0 nulos)

Variación en el estado de calificación crediticia (escala de riesgo regulatoria) durante los últimos 12 meses.

| Columna | Descripción |
| :--- | :--- |
| `NRO_EN_12M_ES_REPORTADO` | N° veces reportado al SF en 12M |
| `VAR_12M_ES_30_ATRASO_SF` | Variación en entidades con 30+ días de atraso (12M) |
| `VAR_12M_ES_60_ATRASO_SF` | Variación en entidades con 60+ días de atraso (12M) |
| `VAR_12M_ES_90_ATRASO_SF` | Variación en entidades con 90+ días de atraso (12M) |
| `VAR_12M_ES_120_ATRASO_SF` | Variación en entidades con 120+ días de atraso (12M) |
| `VAR_12M_ES_DEF_O_PEOR_SF` | Variación en calificación Deficiente o peor (12M) |
| `VAR_12M_ES_DUD_O_PEOR_SF` | Variación en calificación Dudoso o peor (12M) |
| `VAR_12M_ES_PER_O_PEOR_SF` | Variación en calificación Pérdida o peor (12M) |

### 2.4 Grupo C — Variación de Entidades a 12M (float64, 0 nulos)

Cambio en el número de entidades por tipo de producto en los últimos 12 meses.

| Columna | Descripción |
| :--- | :--- |
| `VAR_12M_NRO_ENTS_SF` | Δ total entidades SF en 12M |
| `VAR_12M_NRO_ENTS_DIRECTA_SF` | Δ entidades crédito directo en 12M |
| `VAR_12M_NRO_ENTS_DIRECT_1000_SF` | Δ entidades crédito directo >1,000 en 12M |
| `VAR_12M_NRO_ENTS_LT_TC_SF` | Δ entidades líneas TC en 12M |
| `VAR_12M_NRO_ENTS_CONS_TC_SF` | Δ entidades consumo TC en 12M |
| `VAR_12M_NRO_ENTS_CONS_DISPEFECT_TC_SF` | Δ entidades disposición efectivo TC en 12M |
| `VAR_12M_NRO_ENTS_HIP_SF` | Δ entidades hipotecario en 12M |
| `VAR_12M_NRO_ENTS_CONV_SF` | Δ entidades convenio en 12M |
| `VAR_12M_NRO_ENTS_EMP_SF` | Δ entidades empresarial en 12M |
| `VAR_12M_NRO_ENTS_CONS_SF` | Δ entidades consumo en 12M |

### 2.5 Grupo D — Ratios Financieros Promedio/Máximo/Mediana (object → float64, CON NULOS)

> ⚠️ **Atención crítica para Bob Do:** Estas columnas están almacenadas como `object` (strings) en el parquet. Deben convertirse **antes** de cualquier operación numérica.

**Ventana 12 meses:**

| Columna | Nulos | Tipo real | Descripción |
| :--- | :--- | :--- | :--- |
| `VAR_12M_PROM_DIRECTA_CNS_TC` | 3,041 (13.81%) | float64 | Promedio deuda directa+consumo+TC en 12M |
| `VAR_12M_MAX_DIRECTA_CNS_TC` | 0 | float64 | Máximo deuda directa+consumo+TC en 12M |
| `VAR_12M_MED_DIRECTA_CNS_TC` | 0 | float64 | Mediana deuda directa+consumo+TC en 12M |
| `VAR_12M_PROM_DIRECTA` | 3,041 (13.81%) | float64 | Promedio deuda directa en 12M |
| `VAR_12M_MAX_DIRECTA` | 0 | float64 | Máximo deuda directa en 12M |
| `VAR_12M_MED_DIRECTA` | 0 | float64 | Mediana deuda directa en 12M |
| `VAR_12M_PROM_DIRECTA_CNS` | 3,041 (13.81%) | float64 | Promedio deuda directa+consumo en 12M |
| `VAR_12M_MAX_DIRECTA_CNS` | 0 | float64 | Máximo deuda directa+consumo en 12M |
| `VAR_12M_MED_DIRECTA_CNS` | 0 | float64 | Mediana deuda directa+consumo en 12M |
| `VAR_12M_PROM_DEUDA` | 3,041 (13.81%) | float64 | Promedio deuda total en 12M |
| `VAR_12M_MAX_DEUDA` | 0 | float64 | Máximo deuda total en 12M |
| `VAR_12M_MED_DEUDA` | 0 | float64 | Mediana deuda total en 12M |

**Ventana 6 meses:**

| Columna | Nulos | Tipo real | Descripción |
| :--- | :--- | :--- | :--- |
| `VAR_6M_PROM_DIRECTA_CNS_TC` | 1,455 (6.61%) | float64 | Promedio deuda directa+consumo+TC en 6M |
| `VAR_6M_MAX_DIRECTA_CNS_TC` | 0 | float64 | Máximo deuda directa+consumo+TC en 6M |
| `VAR_6M_MED_DIRECTA_CNS_TC` | 0 | float64 | Mediana deuda directa+consumo+TC en 6M |
| `VAR_6M_PROM_DIRECTA` | 1,455 (6.61%) | float64 | Promedio deuda directa en 6M |
| `VAR_6M_MAX_DIRECTA` | 0 | float64 | Máximo deuda directa en 6M |
| `VAR_6M_MED_DIRECTA` | 0 | float64 | Mediana deuda directa en 6M |

---

## 3. Estrategia de Preprocesamiento

### 3.1 Conversión de Tipos (Grupo D)

```
Para cada columna con dtype == object en Grupo D:
    df[col] = pd.to_numeric(df[col], errors='coerce')
```
El `errors='coerce'` convierte valores no parseable en `NaN` (manejado en el paso siguiente).

### 3.2 Imputación de Nulos

**Estrategia: Mediana estratificada por cuartil de `NRO_ENTS_SF`**

Justificación: Los clientes con más entidades en el SF tienen perfiles de deuda distintos. Imputar con la mediana global mezclaría perfiles crediticios opuestos, introduciendo sesgo.

| Tipo de nulo | Estrategia |
| :--- | :--- |
| `PROM_*` de 12M (13.81%) | Mediana del cuartil de `NRO_ENTS_SF` al que pertenece el registro |
| `PROM_*` de 6M (6.61%) | Mediana del cuartil de `NRO_ENTS_SF` al que pertenece el registro |
| Grupos A, B, C | Sin imputación necesaria (0 nulos) |

### 3.3 Ingeniería de Features Adicional (Opcional — Fase 2)

Las siguientes features derivadas pueden enriquecer el modelo en iteraciones posteriores:
- `RATIO_MORA_30_VS_ENTIDADES = VAR_12M_ES_30_ATRASO_SF / (NRO_ENTS_SF + 1)`
- `DELTA_DEUDA_6M_VS_12M = VAR_6M_PROM_DIRECTA - VAR_12M_PROM_DIRECTA`
- `FLAG_ALTO_RIESGO = (VAR_12M_ES_90_ATRASO_SF > 0).astype(int)`

> Bob Do implementará estas features **solo si** el modelo base (sin ellas) no alcanza los targets de ROC-AUC ≥ 0.78 y KS ≥ 0.33.

---

## 4. Estrategia de Split Temporal

```
Dataset ordenado por FECHA (ascendente)
├── Train:      índices [0 ... 15,417]    → ~70% = 15,418 registros
├── Validation: índices [15,418 ... 18,720] → ~15% = 3,303 registros
└── Test:       índices [18,721 ... 22,024] → ~15% = 3,304 registros (holdout, usar 1 sola vez)
```

**Regla de oro:** El conjunto de Test solo se evalúa **una vez**, al final del proceso, para reportar métricas finales en `reports/metrics.json`.

---

## 5. Esquema de Salida Esperado en `reports/metrics.json`

Todo experimento completado por Bob Do debe añadir una entrada al array `history[]` con la siguiente estructura:

```json
{
  "iteration": "LightGBM_v1.0_baseline",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "roc_auc": 0.00,
  "pr_auc": 0.00,
  "ks": 0.00,
  "recall_class1": 0.00,
  "precision_class1": 0.00,
  "f1_score": 0.00,
  "accuracy": 0.00,
  "latency_ms": 0,
  "threshold_used": 0.00,
  "notes": "Descripción breve del experimento"
}
```

Y actualizar `current_metrics` con los valores del último experimento exitoso.

---

## 6. Contrato de Validación de Schema (Pydantic)

Bob Do debe implementar un modelo Pydantic en `src/data_loader.py` que valide el schema del parquet al momento de carga. El contrato mínimo es:

```
RawRecord:
  FECHA: datetime
  CODIGO: float
  FLAG_MORA_TEMPRANA_8D_3M: Literal[0, 1]
  NRO_ENTS_SF: float (≥ 0)
  ... [todos los campos float64 del Grupo A, B, C: ≥ 0.0]
  ... [todos los campos del Grupo D: Optional[float]]
```

Si la validación falla en más del 1% de registros, Bob Do debe lanzar un `ValueError` explícito y tipado con el conteo de errores.

---

*Documento generado por Bob Think — Estratega MLOps. Versión 1.0.0.*
