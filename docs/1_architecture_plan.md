# Plan de Arquitectura: Modelo de Mora Temprana Crediticia
**Proyecto:** Trinity-AI | **Fase:** Think → Do  
**Versión:** 1.0.0 | **Fecha:** 2026-09-26  
**Estado:** ✅ Aprobado para delegación a Bob Do

---

## 1. Objetivo de Negocio

Construir un modelo de clasificación binaria que prediga la probabilidad de que un crédito incurra en mora temprana (`FLAG_MORA_TEMPRANA_8D_3M = 1`), definida como atraso ≥ 8 días dentro de los primeros 3 meses de vida del crédito.

**Caso de uso operativo:** Activación de estrategias preventivas de cobranza y renegociación antes de que la mora madure en incumplimiento formal, reduciendo la pérdida esperada (Expected Loss).

**Restricción operativa crítica:** Latencia de inferencia < 50ms por registro (requerimiento de integración en tiempo real con core bancario).

---

## 2. Definición del Problema ML

| Parámetro | Valor |
| :--- | :--- |
| **Tipo de problema** | Clasificación binaria supervisada |
| **Target** | `FLAG_MORA_TEMPRANA_8D_3M` (int64: 0 = No mora, 1 = Mora) |
| **Dataset fuente** | `data/data_ejm.parquet` |
| **Dimensiones** | 22,025 filas × 49 columnas |
| **Distribución de clases** | 0: 19,751 (89.68%) / 1: 2,274 (10.32%) — ratio 8.68:1 |

---

## 3. Análisis de Desbalance y Estrategia de Compensación

El ratio 8.68:1 es moderado para el dominio crediticio. **Se rechaza SMOTE** por las siguientes razones:
- Introduce correlaciones sintéticas artificiales en el espacio de features financieras correlacionadas.
- Degrada la calibración de probabilidades (necesaria para scoring de riesgo).
- Rompe la distribución temporal del dataset.

**Estrategia adoptada:** Peso de clase interno al algoritmo.
- `scale_pos_weight = 19751 / 2274 ≈ 8.68` en LightGBM/XGBoost.
- Este parámetro penaliza el error en la clase minoritaria sin alterar la distribución de datos.

---

## 4. Algoritmo Principal y de Contraste

### 4.1 Algoritmo Principal: LightGBM

**Justificación:**
1. Velocidad de inferencia: ~1–5ms/registro (muy por debajo del límite de 50ms).
2. Manejo nativo de valores faltantes (crítico: 13.81% de nulos en columnas `PROM_*`).
3. Gradient-based One-Side Sampling (GOSS) + Exclusive Feature Bundling (EFB): entrenamiento 10x más rápido que XGBoost en datasets de este tamaño.
4. Soporte nativo para SHAP values (explicabilidad regulatoria).

**Hiperparámetros de arranque para Bob Do (ajustar vía Optuna/GridSearchCV):**

| Parámetro | Valor Inicial | Rango de Búsqueda |
| :--- | :--- | :--- |
| `n_estimators` | 500 | [200, 1000] |
| `learning_rate` | 0.05 | [0.01, 0.1] |
| `num_leaves` | 31 | [20, 100] |
| `min_child_samples` | 50 | [20, 100] |
| `lambda_l1` | 0.1 | [0.0, 1.0] |
| `lambda_l2` | 0.1 | [0.0, 1.0] |
| `colsample_bytree` | 0.8 | [0.6, 1.0] |
| `scale_pos_weight` | **8.68** | Fijo (calculado del dataset) |

### 4.2 Algoritmo de Contraste: XGBoost

Usado únicamente para validación cruzada de resultados. Mismos features, mismo split temporal, `scale_pos_weight=8.68`. Si LightGBM supera en PR-AUC y KS, se descarta XGBoost de producción.

---

## 5. Features: Clasificación y Contrato

Las 47 features predictivas (excluidos `CODIGO` y `FECHA`) se agrupan en tres categorías:

### Grupo A — Exposición Crediticia (float64, sin nulos)
Prefijo `NRO_ENTS_*`: número de entidades del sistema financiero (SF) con las que el cliente tiene créditos activos.
- `NRO_ENTS_SF`, `NRO_ENTS_DIRECTA_SF`, `NRO_ENTS_DIRECT_1000_SF`, `NRO_ENTS_LT_TC_SF`, `NRO_ENTS_CONS_TC_SF`, `NRO_ENTS_CONS_DISPEFECT_TC_SF`, `NRO_ENTS_HIP_SF`, `NRO_ENTS_CONV_SF`, `NRO_ENTS_EMP_SF`, `NRO_ENTS_CONS_SF`

### Grupo B — Comportamiento de Mora (float64, sin nulos)
Prefijo `VAR_12M_ES_*`: variación en el estado de crédito a distintos días de atraso en los últimos 12 meses.
- `VAR_12M_ES_30_ATRASO_SF` … `VAR_12M_ES_PER_O_PEOR_SF`
- `NRO_EN_12M_ES_REPORTADO`

### Grupo C — Variación de Entidades (float64, sin nulos)
Prefijo `VAR_12M_NRO_*` y `VAR_6M_*`: variaciones en número de entidades a 6 y 12 meses.

### Grupo D — Ratios Financieros Promedio (object → cast a float64, con nulos)
Prefijos `VAR_12M_PROM_*`, `VAR_12M_MAX_*`, `VAR_12M_MED_*`, `VAR_6M_PROM_*`, `VAR_6M_MAX_*`, `VAR_6M_MED_*`.
- **Problema:** Almacenadas como `object` (strings numéricos). Deben convertirse con `pd.to_numeric(..., errors='coerce')`.
- **Nulos:** Hasta 13.81% en columnas `PROM_*` de 12M, 6.61% en `PROM_*` de 6M.
- **Estrategia de imputación:** Mediana por grupo de `NRO_ENTS_SF` (imputer estratificado, no imputer global).

**Columnas a EXCLUIR del modelo:**
- `FECHA`: Variable de identificación temporal, no predictiva. Solo se usa para el split.
- `CODIGO`: Identificador único del crédito. Nunca como feature.

---

## 6. Estrategia de Validación

### 6.1 Partición Temporal (Time-Based Split)

❌ **Prohibido usar split aleatorio (train_test_split con shuffle).** Los datos tienen estructura temporal; un split aleatorio introduce leakage del futuro al pasado.

**Estrategia:**
- Ordenar el dataset por `FECHA` de forma ascendente.
- **Train:** 70% más antiguo de registros.
- **Validation:** 15% intermedio (para ajuste de umbral y Optuna).
- **Test:** 15% más reciente (holdout final, se usa una sola vez).

### 6.2 Validación Cruzada Interna

Usar `TimeSeriesSplit(n_splits=5)` de scikit-learn dentro del conjunto de entrenamiento para la búsqueda de hiperparámetros con Optuna.

---

## 7. Métricas de Éxito

> **Accuracy está prohibida como métrica principal.** Un modelo que predice siempre clase 0 obtiene 89.68% de accuracy — número engañoso que no mide capacidad discriminativa.

| Métrica | Target Mínimo | Target Óptimo | Justificación |
| :--- | :--- | :--- | :--- |
| **ROC-AUC** | 0.78 | ≥ 0.83 | Discriminación global independiente del umbral |
| **PR-AUC** | 0.50 | ≥ 0.60 | Más informativa con clases desbalanceadas; penaliza FP y FN en la clase positiva |
| **KS** | 0.33 | ≥ 0.40 | Estándar bancario: separa distribuciones de scores buenos/malos |
| **Recall (clase 1)** | 0.55 | ≥ 0.70 | Sensibilidad: fracción de moras reales detectadas. Crítico porque un FN (mora no detectada) implica pérdida financiera directa |
| **Precision (clase 1)** | 0.35 | ≥ 0.50 | Valor predictivo positivo: de las alertas generadas, cuántas son reales. Controla el costo operativo de cobranza innecesaria |
| **F1-Score (clase 1)** | 0.45 | ≥ 0.55 | Media armónica de Precision y Recall; reportado en `reports/metrics.json` para seguimiento iterativo |
| **Latencia P95** | < 50ms | < 20ms | Inferencia individual, medido en hardware de staging |

> **Relación Recall–Precision:** Son inversamente proporcionales bajo un umbral fijo. El umbral óptimo se determinará sobre la curva PR del conjunto de Validation priorizando Recall ≥ 0.55 como restricción dura (no dejar escapar moras), con Precision como variable de ajuste operativo.

**Umbral de clasificación:** Determinado post-entrenamiento sobre la curva PR del conjunto de Validation, priorizando Recall ≥ 0.55 como restricción dura. No usar 0.5 por defecto.

---

## 8. Pipeline Modular Requerido (Contrato para Bob Do)

Bob Do debe implementar exactamente estos módulos en `src/`:

```
src/
├── data_loader.py      # Carga y validación de schema desde data/data_ejm.parquet
├── features.py         # Cast de object→float64, imputación, exclusión de FECHA/CODIGO
├── model.py            # Entrenamiento LightGBM + XGBoost contraste, Optuna
└── evaluate.py         # ROC-AUC, PR-AUC, KS, F1; escritura en reports/metrics.json
```

Cada módulo expone **una función principal con type hints completos y validación Pydantic** en sus contratos de entrada/salida.

---

## 9. Restricciones No Negociables

1. **No SMOTE, no oversampling sintético** — solo `scale_pos_weight`.
2. **No shuffle en split** — siempre temporal por `FECHA`.
3. **No accuracy como KPI** — usar ROC-AUC + KS como métricas primarias de negocio.
4. **Imputación estratificada** para Grupo D (mediana por segmento, no mediana global).
5. **Latencia < 50ms** — si un modelo supera este límite en staging, debe reducirse `num_leaves` o el número de features.
6. **Trazabilidad obligatoria** — cada experimento debe quedar registrado en `reports/metrics.json` dentro del array `history[]`.

---

## 10. Aprobación y Delegación

> **✅ Este plan ha sido revisado y validado por el usuario.**  
> Bob Do queda autorizado para iniciar la implementación modular en `src/` siguiendo estrictamente los contratos definidos en este documento y en `docs/2_data_strategy.md`.
