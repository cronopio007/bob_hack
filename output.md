# Output: Registro de Respuestas de Bob — Trinity-AI

---

## [2026-09-26 12:10] Decisión: Incorporación de Recall y Precision al flujo de métricas

**Pregunta del usuario:** ¿Estás de acuerdo en agregar Recall y Precision al flujo de trabajo de métricas?

**Respuesta de Bob Think:** Totalmente de acuerdo. La justificación es la siguiente:

### Por qué Recall y Precision son necesarias aquí

En un modelo de mora crediticia, los errores no tienen costo simétrico:

| Error | Nombre técnico | Consecuencia en negocio |
| :--- | :--- | :--- |
| Predecir "no mora" cuando sí mora | **Falso Negativo (FN)** | El crédito entra en default sin intervención → pérdida financiera directa |
| Predecir "mora" cuando no mora | **Falso Positivo (FP)** | Se activa cobranza preventiva innecesaria → costo operativo, fricción con el cliente |

**Recall (Sensibilidad)** = TP / (TP + FN) → mide cuántas moras reales captura el modelo. Si es bajo, el modelo deja escapar impagos. Es la restricción dura del negocio.

**Precision (Valor Predictivo Positivo)** = TP / (TP + FP) → mide cuántas de las alertas generadas son moras reales. Si es baja, el área de cobranza se satura con falsos positivos.

La relación Recall–Precision es inversa bajo un umbral fijo. Con desbalance 1:8.68, un umbral de 0.5 maximiza Precision pero destruye Recall — exactamente el error operativo más costoso.

### Cambios aplicados

**`docs/1_architecture_plan.md` — Sección 7. Métricas de Éxito:**
- Añadidas filas **Recall (clase 1)** (target mínimo: 0.55, óptimo: ≥ 0.70) y **Precision (clase 1)** (target mínimo: 0.35, óptimo: ≥ 0.50).
- Criterio de umbral actualizado: el umbral óptimo se determina priorizando **Recall ≥ 0.55 como restricción dura**, con Precision como variable de ajuste operativo.

**`docs/2_data_strategy.md` — Sección 5. Esquema `reports/metrics.json`:**
- Añadidos campos `"recall_class1"` y `"precision_class1"` al esquema JSON de cada entrada del array `history[]`.

**`memory.md`:**
- Registrado **ADR-008**: Recall es restricción dura (FN implica pérdida directa); Precision controla costo operativo de cobranza. Umbral determinado sobre curva PR priorizando Recall.

### Resumen de métricas completas del pipeline (orden de prioridad)

1. **ROC-AUC** — discriminación global (target ≥ 0.78)
2. **KS** — estándar bancario de separación de distribuciones (target ≥ 0.33)
3. **Recall clase 1** — restricción dura: no dejar escapar moras (target ≥ 0.55)
4. **PR-AUC** — calidad del ranking en la clase positiva (target ≥ 0.50)
5. **Precision clase 1** — eficiencia operativa de las alertas (target ≥ 0.35)
6. **F1-Score clase 1** — síntesis de Precision + Recall (target ≥ 0.45)
7. **Latencia P95** — restricción de integración (< 50ms)

---

---

## [2026-09-27 04:00] Bob Do — Implementación del Pipeline Modular `src/`

**Misión:** Implementar el pipeline completo en `src/` según los contratos de `docs/1_architecture_plan.md` y `docs/2_data_strategy.md`.

### Módulos implementados

| Módulo | Responsabilidad |
| :--- | :--- |
| `src/__init__.py` | Paquete Python del pipeline |
| `src/data_loader.py` | Carga de `data/data_ejm.parquet`, cast latinoamericano de Grupo D, validación Pydantic sobre muestra de 500 registros |
| `src/features.py` | Imputación estratificada por cuartil de `NRO_ENTS_SF`, split temporal 70/15/15, `SplitResult` dataclass |
| `src/model.py` | Entrenamiento LightGBM (`scale_pos_weight=8.68`), early stopping 50 rondas, `find_optimal_threshold()` (Recall ≥ 0.55) |
| `src/evaluate.py` | ROC-AUC, PR-AUC, KS, Recall, Precision, F1, Latencia P95; `update_metrics_json()` append-only |
| `src/pipeline.py` | Orquestador de extremo a extremo con FAIL FAST en cada paso |

### Hallazgos durante implementación

**Formato numérico latinoamericano (no documentado):** Las columnas Grupo D usan punto (`.`) como separador de miles — no como decimal. `pd.to_numeric()` directamente devuelve `NaN`. Corrección aplicada: eliminar los puntos antes del cast:
```python
df[col].str.replace('.', '', regex=False).pipe(pd.to_numeric, errors='coerce')
```

**pandas 3.x StringDtype:** En pandas 3.0+, columnas de texto se almacenan con `StringDtype` (dtype `str`), no `object`. La condición `df[col].dtype == object` falla silenciosamente. Corrección: usar `pd.api.types.is_string_dtype()`.

**`pd.qcut` con empates en variable de conteo:** `NRO_ENTS_SF` tiene muchos valores repetidos (enteros pequeños). `pd.qcut(q=4, labels=[1,2,3,4])` lanza `ValueError` cuando hay menos de 4 bins distintos. Corrección: `_safe_qcut()` con `labels=False` + `duplicates='drop'` + remapeo 1-based.

**`numpy.float64(nan)` no es `float`:** `isinstance(np.float64(nan), float)` devuelve `False`. Corrección: usar `pd.isna(val)` que cubre `float('nan')`, `np.float64(nan)`, `pd.NA` y `None`.

### Resultado de ejecución verificada

```
conda run -n dsenv python -m src.pipeline
```

Pipeline ejecutado de extremo a extremo. `reports/metrics.json` actualizado:

| Métrica | Resultado Baseline | Target Mínimo | Estado |
| :--- | :--- | :--- | :--- |
| ROC-AUC | 0.6246 | ≥ 0.78 | ⚠️ Por debajo |
| PR-AUC | 0.1587 | ≥ 0.50 | ⚠️ Por debajo |
| KS | 0.2051 | ≥ 0.33 | ⚠️ Por debajo |
| Recall clase 1 | **0.6161** | ≥ 0.55 | ✅ OK |
| Precision clase 1 | 0.1411 | ≥ 0.35 | ⚠️ Por debajo |
| F1-Score | 0.2296 | ≥ 0.45 | ⚠️ Por debajo |
| Latencia P95 | **4.128 ms** | < 50ms | ✅ OK |

**Nota sobre métricas bajas:** `best_iteration=6` indica que el early stopping se activó muy temprano. Probable causa: el split temporal crea un drift de distribución severo entre train (datos más antiguos) y val (datos más recientes). **Acciones sugeridas para siguiente iteración:**
1. Investigar si hay concepto drift entre los periodos de train y val/test.
2. Ajustar hiperparámetros: reducir `learning_rate` a 0.01, aumentar `n_estimators` a 1000.
3. Considerar ingeniería de features adicional (Fase 2 de `docs/2_data_strategy.md`).

### Archivos creados/modificados

- `src/__init__.py`, `src/data_loader.py`, `src/features.py`, `src/model.py`, `src/evaluate.py`, `src/pipeline.py`
- `changelog.md` — creado con historial de decisiones
- `reports/metrics.json` — actualizado con resultados reales del baseline

---
