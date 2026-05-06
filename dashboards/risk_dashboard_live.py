"""AYCO Contract Risk Dashboard — DWS Live Data."""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import psycopg2
import os

st.set_page_config(page_title="AYCO Risk Intelligence", page_icon="🛡️", layout="wide")

# ── DWS Connection ──
DWS_HOST = os.getenv("DWS_HOST", "192.168.100.223")
DWS_PORT = os.getenv("DWS_PORT", "8000")
DWS_DB = os.getenv("DWS_DB", "ayco_db")
DWS_USER = os.getenv("DWS_USER", "ayco_admin")
DWS_PASS = os.getenv("DWS_PASS", "AycoD3mo2026!")

@st.cache_data(ttl=60)
def query_dws(sql: str) -> pd.DataFrame:
    """Execute query against DWS and return DataFrame."""
    try:
        conn = psycopg2.connect(
            host=DWS_HOST, port=DWS_PORT, dbname=DWS_DB,
            user=DWS_USER, password=DWS_PASS,
            connect_timeout=5
        )
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DWS connection failed: {e}")
        return pd.DataFrame()

# ── Load Data ──
with st.spinner("Consultando DWS..."):
    df = query_dws("""
        SELECT contract_number, vendor_name, monto_total, risk_score, risk_level,
               alertas, recomendaciones, analyzed_at
        FROM risk_results ORDER BY risk_score DESC
    """)

if df.empty:
    st.warning("No se pudieron cargar datos de DWS. Verifica conectividad.")
    st.stop()

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
    st.caption(f"DWS Live @ {DWS_HOST}:{DWS_PORT} • {datetime.now().strftime('%H:%M CST')}")
with col2:
    st.metric("Total Contratos", len(df))
    auto = st.checkbox("Auto-refresh", value=False)

# ── KPI Row ──
k1, k2, k3, k4 = st.columns(4)
criticos = df[df["risk_level"] == "Crítico"]
altos = df[df["risk_level"].isin(["Alto", "Crítico"])]
activos = len(df)

k1.metric("Contratos Analizados", activos)
k2.metric("Avg Risk Score", f"{df['risk_score'].mean():.1f}",
          delta=f"{altos['risk_score'].mean():.0f} avg críticos",
          delta_color="inverse")
k3.metric("Monto Total", f"${df['monto_total'].sum()/1e6:.1f}M MXN")
k4.metric("Alertas Críticas", len(criticos),
          delta=f"{len(df[df['risk_level']=='Alto'])} altos", delta_color="inverse")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["📊 Risk Distribution", "📋 Vendor Exposure", "🔍 Contract Detail"])

with tab1:
    col_left, col_right = st.columns(2)
    with col_left:
        fig = px.pie(df, names="risk_level", values="monto_total",
                     color="risk_level",
                     color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                     title="Risk Distribution by Amount")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
        st.plotly_chart(fig, use_container_width=True)
    with col_right:
        counts = df.groupby("risk_level").size().reset_index(name="count")
        fig2 = px.bar(counts, x="risk_level", y="count", color="risk_level",
                      color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                      title="Contracts by Risk Level")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    top = df.nlargest(10, "monto_total").sort_values("monto_total")
    fig3 = px.bar(top, x="monto_total", y="vendor_name", color="risk_level", orientation="h",
                  color_discrete_map={"Bajo":"#00d4aa","Medio":"#ffd700","Alto":"#ff8c00","Crítico":"#ff4444"},
                  title="Top 10 Vendors by Contract Amount")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.dataframe(df.sort_values("risk_score", ascending=False),
                 use_container_width=True, hide_index=True,
                 column_config={
                     "contract_number": "Contrato",
                     "vendor_name": "Proveedor",
                     "monto_total": st.column_config.NumberColumn("Monto MXN", format="$%d"),
                     "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100, format="%d"),
                     "risk_level": "Nivel",
                     "alertas": st.column_config.NumberColumn("Alertas", format="%d"),
                     "analyzed_at": "Analizado",
                 })

st.caption(f"Huawei Cloud • DWS Live @ {DWS_HOST}:{DWS_PORT} • {len(df)} registros • AYCO Demo — Mayo 2026")
