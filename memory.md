# MEMORY DEL PROYECTO: TRINITY-AI

## Estado Actual
- **Fase Activa**: `Do` (Implementación del Pipeline ML — Think completado ✅)
- **Fecha de Inicialización**: 2026-09-26
- **Objetivo**: Desarrollar un sistema de scoring y clasificación de riesgo crediticio con explicabilidad y baja latencia (<50ms).

## Resumen de Fases de Trinity-AI
| Fase | Agente | Estado | Entregable Principal |
| :--- | :--- | :--- | :--- |
| **Think** | Estratega MLOps | ✅ Completado | `docs/1_architecture_plan.md` + `docs/2_data_strategy.md` |
| **Do** | Ingeniero MLOps | 🟡 En Progreso | `src/` & `reports/` (5 CSVs + metrics.json) |
| **Docs** | Redactor Técnico | ⚪ Pendiente | `docs/3_final_pipeline.md` |

## Decisiones Arquitectónicas Registradas
- **ADR-001**: Adopción de arquitectura Human-in-the-loop desacoplada en tres agentes especialistas (`Think`, `Do`, `Docs`).
- **ADR-002**: Estándar de desarrollo en Python 3.11+ con contratos estrictos Pydantic y Type Hints en todos los módulos.
- **ADR-003**: Persistencia centralizada de métricas e historial en `reports/metrics.json` para monitoreo reactivo desde Streamlit.
- **ADR-004**: Algoritmo principal **LightGBM** con `scale_pos_weight=8.68` (ratio 19751/2274). Se rechaza SMOTE por degradación de calibración de probabilidades en datos financieros correlacionados.
- **ADR-005**: Split temporal estricto por `FECHA` (70/15/15). Prohibido `train_test_split` con shuffle — introduce leakage temporal.
- **ADR-006**: Métricas primarias de negocio: **ROC-AUC ≥ 0.78** y **KS ≥ 0.33**. Accuracy explícitamente prohibida como KPI (un modelo trivial obtiene 89.68% prediciendo siempre clase 0).
- **ADR-007**: Columnas `object` del Grupo D (ratios financieros) deben convertirse con `pd.to_numeric(..., errors='coerce')` antes de cualquier operación. Imputación por mediana estratificada por cuartil de `NRO_ENTS_SF`.

## Aprendizajes y Patrones Clave
- [2026-09-26 10:55] **[Inicialización]**: Estructura base configurada bajo estándares de parsimonia y modularidad para la IBM Bob 2.0 Hackathon.
- [2026-09-26 12:00] **[Think Completado]**: Fase Think finalizada con aprobación explícita del usuario. Target confirmado: `FLAG_MORA_TEMPRANA_8D_3M` (10.32% positivos). LightGBM seleccionado sobre XGBoost por latencia y manejo nativo de nulos. Se documentaron 22,025 registros × 49 features en dos documentos de contrato técnico.
- [2026-09-26 12:10] **[ADR-008 — Métricas Extendidas]**: A solicitud del usuario, se incorporaron Recall y Precision (clase 1) al flujo de métricas. Recall es restricción dura (>= 0.55 mínimo) por el costo asimétrico de FN en mora crediticia. Precision controla el costo operativo de cobranza. Umbral de clasificación determinado priorizando Recall sobre Precision en la curva PR.
- [2026-09-27 04:00] **[Do — Datos Latinoamericanos]**: Las columnas Grupo D usan punto como separador de miles (`'383.722.966'` -> `383722966`); `pd.to_numeric()` directo produce `NaN` en el 100% de los valores. Corrección obligatoria: `str.replace('.', '', regex=False)` antes del cast.
- [2026-09-27 04:00] **[Do — pandas 3.x StringDtype]**: En pandas >= 3.0 las columnas de texto tienen dtype `str` (no `object`); `df[col].dtype == object` falla silenciosamente. Usar `pd.api.types.is_string_dtype()` para detección compatible con versiones futuras.
- [2026-09-27 04:00] **[Do — qcut con empates]**: `NRO_ENTS_SF` es variable de conteo de enteros pequeños con muchos empates; `pd.qcut(q=4, labels=[1,2,3,4])` lanza `ValueError` cuando produce menos de 4 bins distintos. Solución: `_safe_qcut()` con `labels=False` + `duplicates='drop'` + remapeo 1-based.
- [2026-09-27 04:00] **[Do — numpy.float64 no es float]**: `isinstance(np.float64('nan'), float)` devuelve `False`, rompiendo silenciosamente la detección de nulos. Usar siempre `pd.isna(val)` en lugar de comprobaciones de tipo explícitas para valores opcionales.
- [2026-09-27 04:00] **[Do — Early Stopping prematuro]**: El baseline produjo `best_iteration=6`, indicando probable concepto drift temporal severo entre los periodos de train (70% antiguo) y val (15% intermedio). Siguiente iteración debe reducir `learning_rate` a 0.01 y evaluar distribución temporal de la variable target por periodo.
- [2026-09-27 04:00] **[Do — Pipeline Verificado]**: Pipeline ejecutado de extremo a extremo en `dsenv`. Latencia P95 = 4.128ms (OK < 50ms). Recall baseline = 0.6161 (OK >= 0.55). ROC-AUC = 0.6246 y KS = 0.2051 (bajo targets — requiere iteración 2).
- [2026-09-27 06:00] **[Do — Encoding Windows cp1252]**: El `StreamHandler` de PowerShell en Windows usa cp1252 y falla ante caracteres Unicode (->  = >=  * en strings de logging). Solución permanente: reemplazar todos los caracteres no-ASCII en mensajes de `logger.*()` por equivalentes ASCII puros; en ejecución puntual usar `$env:PYTHONUTF8="1"`.
- [2026-09-27 06:00] **[Do — conda run + UnicodeEncodeError]**: `conda run -n base` en PowerShell redirige stdout por el pipe interno de conda, que también aplica cp1252 y produce timeout/crash ante caracteres Unicode en el output del proceso. Invocar directamente el ejecutable Python del entorno (`& "C:\...\anaconda3\python.exe"`) evita el intermediario y es la forma fiable en Windows.
- [2026-09-27 06:00] **[Do — requirements.txt base instalado]**: Entorno `base` ahora tiene todas las dependencias del proyecto. Versiones clave verificadas: pandas 2.3.3, numpy 2.3.5, scikit-learn 1.7.2, lightgbm 4.7.0, pyarrow 21.0.0, pydantic 2.12.4. `requirements.txt` generado con rangos `>=` para reproducibilidad sin pin estricto.
- [2026-09-27 06:00] **[Do — LightGBM 4.7 eval_set deprecated]**: LightGBM >= 4.4 depreca el argumento `eval_set` en `fit()`; la API correcta es `eval_X` / `eval_y`. El pipeline sigue funcionando con el argumento antiguo (warning no-fatal), pero debe migrarse en Iteración 2.
- [2026-09-27 06:00] **[Do — Notebook Human-in-the-Loop]**: `demo_pipeline_walkthrough.ipynb` creado como artefacto de auditoría de 6 celdas. La celda 6 requiere edición manual de `HUMAN_DECISION` ("APPROVED"/"REJECTED") antes de persistir en `metrics.json` — patrón correcto para flujos regulatorios bancarios donde un humano debe firmar el modelo.
- [2026-09-27 06:00] **[Do — Contrato CSV v1.2]**: `src/evaluate.py` extendido con `export_metrics_csv()` (append-only, columnas fijas para Streamlit) y `export_feature_importance_csv()` (sobreescritura, top-15 LightGBM). Ambas se llaman automáticamente desde `evaluate_model()` — no requieren cambios en `pipeline.py`.
- [2026-09-27 06:00] **[Do — Auditoria Regulatoria v1.3]**: Nuevo módulo `src/audit.py` con tres funciones independientes: `audit_data_quality()` (49 cols, 0 CRITICO, 6 AVISO), `compute_iv()` (IV por bins cuantiles, 30/46 features seleccionadas con IV >= 0.02; top feature `NRO_ENTS_DIRECTA_SF` IV=0.135), `export_confusion_matrix()` (TN=1709, FP=1260, FN=129, TP=207 en test baseline). Pipeline escalado de 4 a 6 pasos; auditoria de calidad e IV ejecutan ANTES del split para operar sobre el dataset completo.

## Tareas Pendientes Inmediatas
1. ✅ ~~Definir la variable target y features prioritarias con el usuario en la fase `Think`.~~
2. ✅ ~~Consolidar el plan en `docs/1_architecture_plan.md`.~~
3. ✅ ~~Implementar pipeline modular en `src/` (data_loader, features, model, evaluate, pipeline).~~
4. ✅ ~~Crear notebook Human-in-the-Loop `demo_pipeline_walkthrough.ipynb`.~~
5. ✅ ~~Extender `src/evaluate.py` con exportación CSV obligatoria (metrics_history + feature_importance).~~
6. ✅ ~~Crear `src/audit.py` con auditoria de calidad, IV y matriz de confusión. Pipeline a 6 pasos.~~
7. **[Bob Do — Iteración 2]** Investigar concepto drift temporal: comparar distribución de `FLAG_MORA_TEMPRANA_8D_3M` por periodo `FECHA` en train vs val vs test.
8. **[Bob Do — Iteración 2]** Re-entrenar con `learning_rate=0.01`, `n_estimators=1000`, `early_stopping_rounds=100` y migrar `eval_set` -> `eval_X/eval_y` (LightGBM 4.7). Target: ROC-AUC >= 0.78 y KS >= 0.33.
9. **[Bob Docs]** Una vez alcanzados los targets de métricas, iniciar `docs/3_final_pipeline.md` leyendo `src/` y `reports/`.
