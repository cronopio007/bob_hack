
**out**: requirements.txt is empty — dependencies must be inferred from imports (streamlit, pandas, scikit-learn, pydantic, pyarrow). Nothing to pip install -r from.

reports/metrics.json is a silent-fail hard contract — the Streamlit dashboard checks path.exists() and returns zeros if the schema keys are missing. Appending to history[] is required (not replacing it).

data/raw_data.csv doesn't exist despite being the mandated ADR input — only data/data_ejm.parquet is present.

Severe class imbalance (10.32% positive) in the target FLAG_MORA_TEMPRANA_8D_3M — silently produces misleading accuracy without explicit handling.

13 object-typed numeric columns with up to 14% nulls — will cause silent sklearn failures without casting and imputation.

Human gate between phases is architecturally enforced — the Think phase cannot proceed to Do without explicit user approval; this is a core ADR, not a soft guideline.

.bob/ uses non-standard rule directories (rules-think/, rules-do/, rules-docs/) instead of the typical rules-agent/rules-ask/rules-plan — both sets now exist.

**in**: Hola Bob, actúa bajo la persona de Bob Think definida en @.bob/rules-think/AGENTS-think.md.

Tenemos el objetivo de construir un modelo de Machine Learning para predecir mora temprana en créditos financieros.
- Target: 'FLAG_MORA_TEMPRANA_8D_3M'
- Contexto de memoria: @memory.md

Por favor:
1. Analiza el problema de negocio y el severo desbalance de clases típico en este target.
2. Plantea la estrategia algorítmica (LightGBM vs XGBoost con manejo de hiperparámetros como scale_pos_weight).
3. Define las métricas de evaluación clave (ROC-AUC, PR-AUC y KS, explicando por qué Accuracy no sirve aquí).
4. Redacta y crea formalmente los archivos 'docs/1_architecture_plan.md' y 'docs/2_data_strategy.md' con el contrato técnico para que Bob Do pueda implementarlo.

in: Hola Bob, actúa bajo el rol de Bob Do definido en @.bob/rules-do/AGENTS-do.md.

Los contratos técnicos han sido aprobados en @docs/1_architecture_plan.md y @docs/2_data_strategy.md.

RESTRICCIÓN DE ENTORNO: 
- El entorno de ejecución oficial es el conda env 'dsenv'. Si ejecutas comandos o pruebas en terminal, hazlo dentro de este entorno (ej: `conda run -n dsenv python ...` o asumiendo el entorno activado).

Tu misión ahora es implementar el pipeline modular en 'src/':
1. 'src/data_loader.py': Carga de 'data/data_ejm.parquet' y validación de tipos con Pydantic.
2. 'src/features.py': Cast de object a float64 (Grupo D), imputación estratificada por cuartil de NRO_ENTS_SF y Time-Based Split (70/15/15) por FECHA.
3. 'src/model.py': Entrenamiento de LightGBM con scale_pos_weight=8.68 y early stopping en el set de Validation.
4. 'src/evaluate.py': Cálculo riguroso de ROC-AUC, PR-AUC, KS (Kolmogorov-Smirnov), F1-Score, Recall, Precision y latencia P95. Actualización de 'reports/metrics.json' (historial y métricas actuales).
5. 'src/pipeline.py': Script principal que conecta todo de extremo a extremo.

Asegúrate de:
- Usar Type Hints estrictos.
- Registrar los módulos creados en 'changelog.md'.
- Dejar todo listo para ser ejecutado con: `conda run -n dsenv python -m src.pipeline`.