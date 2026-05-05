"""AYCO Contract Risk Dashboard — Demo version with mock data."""
import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime

st.set_page_config(page_title="AYCO Risk Intelligence", page_icon="🛡️", layout="wide")

# ── Mock Data Generator ──
@st.cache_data(ttl=9999)
def generate_mock_data():
    vendors = ["Constructora del Sur", "TechSoluciones MX", "Transportes Monterrey",
               "Grupo Alimenticio del Bajío", "Desarrollos Urbanos Norte", "Seguridad Privada Azteca",
               "Limpieza Industrial León", "Consultoría Estratégica CDMX", "Muebles y Oficinas del Centro",
               "Distribuidora de Insumos Médicos", "Publicidad y Marketing Digital", "Servicios de TI Guadalajara",
               "Mantenimiento Industrial Torreón", "Capacitación Corporativa", "Logística y Paquetería Express"]
    
    risk_levels = ["Bajo", "Medio", "Alto", "Crítico"]
    weights = [0.35, 0.30, 0.25, 0.10]
    statuses = ["Activo", "Por vencer", "Vencido", "En litigio"]
    status_weights = [0.45, 0.25, 0.15, 0.15]
    
    data = []
    for i, vendor in enumerate(vendors, 1):
        risk = random.choices(risk_levels, weights=weights, k=1)[0]
        score = {"Bajo": random.randint(10,30), "Medio": random.randint(31,55), 
                 "Alto": random.randint(56,80), "Crítico": random.randint(81,100)}[risk]
        data.append({
            "id": f"AYC-CONT-{i:04d}",
            "vendor": vendor,
            "monto": random.randint(50000, 5000000),
            "risk_score": score,
            "risk_level": risk,
            "status": random.choices(statuses, weights=status_weights, k=1)[0],
            "dias_restantes": random.randint(5, 365),
            "penalizacion_pct": random.randint(1, 15),
            "plazo_meses": random.choice([6, 12, 24, 36]),
        })
    return pd.DataFrame(data)

df = generate_mock_data()

# ── Branding ──
st.markdown("""
<style>
    .main { background-color: #0a0e17; }
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%); }
    h1, h2, h3, .stMetric label, p, span { color: #e8eaed !important; }
    div[data-testid="stMetricValue"] { color: #00d4aa !important; font-size: 1.8rem !important; }
    .stDataFrame { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ AYCO Contract Risk Intelligence")
    st.caption(f"Huawei Cloud DWS ⊕ DeepSeek ⊕ Streamlit | {datetime.now().strftime('%H:%M CST')}")
with col2:
    st.metric("Total Contratos", len(df))
    auto = st.checkbox("Auto-refresh", value=False)

# ── KPI Row ──
k1, k2, k3, k4 = st.columns(4)
k1.metric("Contratos Activos", len(df[df["status"] == "Activo"]))
k2.metric("Avg Risk Score", f"{df['risk_score'].mean():.1f}", 
          delta=f"{df[df['risk_level'].isin(['Alto','Crítico'])]['risk_score'].mean():.0f} avg críticos",
          delta_color="inverse")
k3.metric("Monto Total", f"${df['monto'].sum()/1e6:.1f}M MXN")
k4.metric("Alertas Críticas", len(df[df["risk_level"] == "Crítico"]), 
          delta=f"{len(df[df['risk_level']=='Alto'])} altos", delta_color="inverse")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["📊 Risk Distribution", "📋 Vendor Exposure", "🔍 Contract Detail"])

with tab1:
    col_left, col_right = st.columns(2)
    with col_left:
        fig = px.pie(df, names="risk_level", values="monto", 
                     color="risk_level",
                     color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                     title="Risk Distribution by Amount")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
        st.plotly_chart(fig, use_container_width=True)
    with col_right:
        fig2 = px.bar(df.groupby("risk_level").size().reset_index(name="count"), 
                      x="risk_level", y="count", color="risk_level",
                      color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                      title="Contracts by Risk Level")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    top = df.nlargest(10, "monto").sort_values("monto")
    fig3 = px.bar(top, x="monto", y="vendor", color="risk_level", orientation="h",
                  color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                  title="Top 10 Vendors by Contract Amount")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.dataframe(df.sort_values("risk_score", ascending=False), 
                 use_container_width=True, hide_index=True,
                 column_config={
                     "monto": st.column_config.NumberColumn("Monto MXN", format="$%d"),
                     "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d"),
                     "dias_restantes": st.column_config.NumberColumn("Días Restantes", format="%d"),
                 })

st.caption("Huawei Cloud | DWS ⊕ DeepSeek MaaS ⊕ Langfuse Observability | AYCO Demo — Mayo 2026")
