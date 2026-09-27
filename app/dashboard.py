"""Trinity-AI Dashboard: Enterprise Credit Risk MLOps & Governance Monitor."""

from pathlib import Path
import pandas as pd
import streamlit as st

# ==============================================================================
# CONFIGURACIÓN Y RUTAS
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
MEMORY_PATH = BASE_DIR / "memory.md"

st.set_page_config(
    page_title="Trinity-AI | Credit Risk MLOps",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_csv(filename: str) -> pd.DataFrame:
    """Carga segura de reportes CSV."""
    path = REPORTS_DIR / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def load_memory(path: Path) -> str:
    """Carga de memoria del proyecto."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "No se encontró el archivo memory.md."


# ==============================================================================
# HEADER & ESTADO DEL CICLO DE VIDA
# ==============================================================================
st.title("⚡ Trinity-AI: Autonomous Credit Risk MLOps")
st.caption(
    "IBM Bob 2.0 Hackathon | Human-in-the-Loop Architecture: Think (Architect) ➔ Do (Engineer) ➔ Docs (Auditor)"
)

# Estado de los 3 agentes
col_think, col_do, col_docs = st.columns(3)
with col_think:
    st.success(
        "🟢 **BOB THINK (Estratega)**\n\n"
        "**Estado:** ✅ Aprobado\n\n"
        "`docs/1_architecture_plan.md` & `docs/2_data_strategy.md`"
    )
with col_do:
    st.success(
        "🟢 **BOB DO (Ejecutor)**\n\n"
        "**Estado:** ✅ Pipeline Entrenado\n\n"
        "LightGBM en `src/` & 5 reportes generados en `reports/`"
    )
with col_docs:
    st.info(
        "🟡 **BOB DOCS (Auditor)**\n\n"
        "**Estado:** ⏳ Fase Activa\n\n"
        "Generando `docs/3_final_pipeline.md` (Gobernanza & Fair Lending)"
    )

st.divider()

# ==============================================================================
# BANNER DE KPIS BANCARIOS (DESDE METRICS_HISTORY.CSV)
# ==============================================================================
df_history = load_csv("metrics_history.csv")

if not df_history.empty:
    latest = df_history.iloc[-1]
    st.subheader("🎯 KPIs de Rendimiento del Modelo (Holdout Test)")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    # Manejo dinámico de columnas según cálculo del pipeline
    roc_val = latest.get("roc_auc", latest.get("ROC-AUC", 0.0))
    ks_val = latest.get("ks", latest.get("KS", 0.0))
    pr_val = latest.get("pr_auc", latest.get("PR-AUC", 0.0))
    f1_val = latest.get("f1_score", latest.get("F1-Score", 0.0))
    lat_val = latest.get("latency_ms", latest.get("Latency_ms", 0))

    k1.metric("ROC-AUC", f"{float(roc_val):.3f}", delta="Target ≥ 0.78")
    k2.metric("KS Bancario", f"{float(ks_val):.3f}", delta="Target ≥ 0.33")
    k3.metric("PR-AUC", f"{float(pr_val):.3f}", delta="Clase Minoritaria")
    k4.metric("F1-Score", f"{float(f1_val):.3f}", delta="Balance P/R")
    k5.metric("Latencia P95", f"{lat_val} ms", delta="< 50ms Core Banking", delta_color="inverse")
else:
    st.info("ℹ️ Ejecuta el pipeline para poblar las métricas en tiempo real.")

st.divider()

# ==============================================================================
# PESTAÑAS DE REPORTES EJECUTIVOS
# ==============================================================================
tab_quality, tab_iv, tab_importance, tab_cm, tab_evolution = st.tabs([
    "📋 Calidad de Datos & Nulos",
    "🎯 Information Value (IV)",
    "🏆 Top Drivers de Riesgo",
    "🧮 Matriz de Confusión",
    "📈 Histórico de Iteraciones",
])

# 1. Calidad de Datos
with tab_quality:
    st.subheader("Auditoría de Ingesta y Missing Values")
    df_quality = load_csv("data_quality.csv")
    if not df_quality.empty:
        st.dataframe(df_quality, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró 'reports/data_quality.csv'.")

# 2. Information Value (IV)
with tab_iv:
    st.subheader("Filtro Regulatorio: Information Value (IV) frente a Mora Temprana")
    df_iv = load_csv("feature_selection_iv.csv")
    if not df_iv.empty:
        col_iv_table, col_iv_chart = st.columns([3, 2])
        with col_iv_table:
            st.dataframe(df_iv, use_container_width=True, hide_index=True)
        with col_iv_chart:
            # Gráfica de los top scores de IV
            feature_col = [c for c in df_iv.columns if "feature" in c.lower() or "variable" in c.lower()][0]
            iv_col = [c for c in df_iv.columns if "iv" in c.lower()][0]
            top_iv = df_iv.sort_values(by=iv_col, ascending=False).head(10)
            st.bar_chart(top_iv.set_index(feature_col)[iv_col])
    else:
        st.warning("No se encontró 'reports/feature_selection_iv.csv'.")

# 3. Importancia de Features
with tab_importance:
    st.subheader("Top Drivers Predictivos (LightGBM Gain/Split)")
    df_imp = load_csv("feature_importance.csv")
    if not df_imp.empty:
        feat_col = df_imp.columns[0]
        val_col = df_imp.columns[1]
        top_imp = df_imp.sort_values(by=val_col, ascending=False).head(15)
        st.bar_chart(top_imp.set_index(feat_col)[val_col], use_container_width=True)
        st.dataframe(top_imp, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró 'reports/feature_importance.csv'.")

# 4. Matriz de Confusión
with tab_cm:
    st.subheader("Matriz de Confusión en Holdout Test")
    df_cm = load_csv("confusion_matrix.csv")
    if not df_cm.empty:
        st.dataframe(df_cm, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró 'reports/confusion_matrix.csv'.")

# 5. Histórico de Iteraciones
with tab_evolution:
    st.subheader("Evolución de Métricas en el Ciclo Trinity-AI")
    if not df_history.empty:
        metric_cols = [c for c in ["roc_auc", "ks", "pr_auc", "f1_score"] if c in df_history.columns]
        if metric_cols:
            st.line_chart(df_history[metric_cols], use_container_width=True)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró 'reports/metrics_history.csv'.")

st.divider()

# ==============================================================================
# CONTEXTO ACTIVO (MEMORY.MD)
# ==============================================================================
with st.expander("📖 Inspeccionar Memoria Persistente de Trinity-AI (`memory.md`)", expanded=False):
    st.markdown(load_memory(MEMORY_PATH))