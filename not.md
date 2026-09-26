# 1. Inicializar Git (si no lo has hecho)
git init

# 2. Crear un .gitignore blindado para Python y Bob IDE
cat << 'EOF' > .gitignore
# Ambientes y Python
__pycache__/
*.py[cod]
*$py.class
.venv/
env/
venv/

# Datos pesados y reportes temporales
*.pkl
*.parquet

# Sistema y cache de CLI
.DS_Store
*.log
EOF

# 3. Generar requirements.txt base y un dataset sintético para Bob Think
agy prompt "Genera un requirements.txt parsimónico con: streamlit, scikit-learn, pandas, pydantic. Además, crea un script rápido en Python que genere data/raw_data.csv con 100 filas de datos financieros sintéticos (edad, ingresos, score_crediticio, moroso) y ejecútalo para que el CSV quede listo." --auto-approve

# 4. Primer Commit limpio
git add .
git commit -m "feat: initial war room architecture with .agy rules and raw dataset"

Versión 1 de Trinity-AI construida con éxito. Todos los componentes han sido generados bajo los
  principios de parsimonia, modularidad y tipado estricto.

  ### Componentes Generados

  1. Directiva Think: AGENTS-think.md
      • Decisión Arquitectónica: Restringe el rol a ideación y negociación de variables/target.
      Prohíbe formalmente código ejecutable y obliga a registrar contratos en
      docs/1_architecture_plan.md.
  2. Directiva Do: AGENTS-do.md
      • Decisión Arquitectónica: Impone pipeline modular en src/, ingestión desde data/raw_data.csv,
      exportación a reports/metrics.json y trazabilidad continua en changelog.md.
  3. Directiva Docs: AGENTS-docs.md
      • Decisión Arquitectónica: Auditoría técnica y redacción orientada a gobernanza/Fair Lending
      basada estrictamente en src/ y memory.md, produciendo docs/3_final_pipeline.md.
  4. Skill Pattern Matcher: SKILL.md
      • Decisión Arquitectónica: Metadata YAML compatible con IBM Bob IDE. Analiza dependencias
      externas para sugerir patrones limpios (Strategy, Repository, Pipelines idempotentes).
  5. Skill Learnings: SKILL.md
      • Decisión Arquitectónica: Extractor incremental de lecciones y decisiones hacia memory.md
      para evitar pérdida de contexto en la ventana de tokens.
  6. Memoria de Proyecto: memory.md
      • Decisión Arquitectónica: Inicializada con el estado actual en Fase Think (Ideación de Modelo
      de Riesgo Crediticio), ADRs y checklist de entrega.
  7. Métricas Semilla: metrics.json
      • Decisión Arquitectónica: Esquema estructurado con métricas actuales (accuracy: 0.72,
      f1_score: 0.68, latency_ms: 45) y array de histórico para seguimiento de regresión.
  8. Dashboard Streamlit: dashboard.py
      • Decisión Arquitectónica: Tablero reactivo que visualiza el ciclo de vida de los 3 agentes,
      KPIs principales, evolución de métricas y visor colapsable de memory.md.


  Para lanzar el dashboard en local: