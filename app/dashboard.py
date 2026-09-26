"""Trinity-AI Dashboard: Modern Human-in-the-Loop MLOps Monitor."""

import json
from pathlib import Path
import pandas as pd
import streamlit as st

# Configuration & Paths
BASE_DIR = Path(__file__).resolve().parent.parent
METRICS_PATH = BASE_DIR / "reports" / "metrics.json"
MEMORY_PATH = BASE_DIR / "memory.md"

st.set_page_config(
    page_title="Trinity-AI | MLOps Control",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_metrics(path: Path) -> dict:
    """Loads metrics safely from reports/metrics.json."""
    if not path.exists():
        return {
            "current_metrics": {"accuracy": 0.0, "f1_score": 0.0, "latency_ms": 0},
            "history": [],
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_memory(path: Path) -> str:
    """Loads project memory from memory.md."""
    if not path.exists():
        return "No memory file found."
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Header
st.title("⚡ Trinity-AI: Autonomous MLOps Pipeline")
st.caption("IBM Bob 2.0 Hackathon | Human-in-the-loop Governance (Think ➔ Do ➔ Docs)")

# Section 1: Trinity Lifecycle Status
st.subheader("Lifecycle Status")
col_think, col_do, col_docs = st.columns(3)

with col_think:
    st.info("🟡 **THINK (Estratega)**\n\n**Estado:** En Progreso\n\nPlanificando en `docs/1_architecture_plan.md`")

with col_do:
    st.warning("⚪ **DO (Ejecutor)**\n\n**Estado:** En Espera\n\nModular en `src/` & baseline `data/raw_data.csv`")

with col_docs:
    st.success("⚪ **DOCS (Auditor)**\n\n**Estado:** En Espera\n\nGenerará `docs/3_final_pipeline.md`")

st.divider()

# Section 2: KPIs & Metric Evolution
metrics_data = load_metrics(METRICS_PATH)
current_kpis = metrics_data.get("current_metrics", {})
history = metrics_data.get("history", [])

st.subheader("Model Performance KPIs")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Accuracy", value=f"{current_kpis.get('accuracy', 0.0):.2%}", delta="Baseline")
kpi2.metric(label="F1-Score", value=f"{current_kpis.get('f1_score', 0.0):.2f}", delta="Baseline")
kpi3.metric(label="Latency (Inference)", value=f"{current_kpis.get('latency_ms', 0)} ms", delta="- Target <50ms", delta_color="inverse")

st.subheader("Métricas: Evolución Histórica")
if history:
    df_history = pd.DataFrame(history)
    chart_cols = [c for c in ["accuracy", "f1_score"] if c in df_history.columns]
    
    if "iteration" in df_history.columns:
        df_chart = df_history.set_index("iteration")[chart_cols]
    else:
        df_chart = df_history[chart_cols]

    tab_chart, tab_data = st.tabs(["Gráfica de Tendencia", "Datos Crudos"])
    with tab_chart:
        st.line_chart(df_chart, use_container_width=True)
    with tab_data:
        st.dataframe(df_history, use_container_width=True)
else:
    st.info("Aún no hay registros de evolución histórica en `reports/metrics.json`.")

st.divider()

# Section 3: Project Memory Viewer
with st.expander("📖 Inspeccionar Contexto Activo (`memory.md`)", expanded=False):
    st.markdown(load_memory(MEMORY_PATH))
