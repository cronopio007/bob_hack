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