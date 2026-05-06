"""
AYCO Contract Risk Dashboard — Streamlit (Optimized for Demo)
Connects directly to DWS (PostgreSQL-compatible) via psycopg2.
"""

import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="AYCO Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium Styling ──────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0e17; }
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%); }
    h1, h2, h3, h4, .metric-label, p, span { color: #e8eaed !important; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetricValue"] { color: #00d4aa !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricDelta"] { color: #ff6b6b !important; }
    .stDataFrame { background: #1a1f2e; border-radius: 12px; border: 1px solid #2d3748; }
    .css-1kyxreq { background: #1a1f2e; border-radius: 12px; padding: 1rem; }
    .dify-button {
        background: linear-gradient(90deg, #00d4aa 0%, #00f2c3 100%);
        color: #0a0e17 !important;
        padding: 6px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        box-shadow: 0 4px 6px rgba(0, 212, 170, 0.2);
        transition: all 0.3s ease;
    }
    .dify-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 212, 170, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ─── Data & Helpers ────────────────────────────────────────
STATE_COORDS = {
    "CDMX": [19.4326, -99.1332], "JAL": [20.6597, -103.3496],
    "NLE": [25.6866, -100.3161], "QRO": [20.5888, -100.3899],
    "PUE": [19.0414, -98.2063], "GTO": [21.0190, -101.2574],
    "SON": [29.0730, -110.9559], "CHIH": [28.6330, -106.0691],
    "BC": [30.8406, -115.2838], "TAMPS": [24.2669, -98.8363],
    "TAB": [17.9892, -92.9475], "OAX": [17.0732, -96.7266]
}

@st.cache_resource(ttl=600)
def get_dws_connection():
    """Robust DWS connection with environment fallback."""
    try:
        return psycopg2.connect(
            host=os.getenv("DWS_ENDPOINT") or os.getenv("DWS_HOST", "127.0.0.1"),
            port=int(os.getenv("DWS_PORT", "8000")),
            dbname=os.getenv("DWS_DATABASE") or os.getenv("DWS_DB", "ayco_db"),
            user=os.getenv("DWS_USER", "ayco_admin"),
            password=os.getenv("DWS_PASSWORD") or os.getenv("DWS_PASS", ""),
            connect_timeout=3,
        )
    except Exception:
        return None

def run_query(query: str) -> pd.DataFrame:
    """Execute query with error handling."""
    conn = get_dws_connection()
    if not conn:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame()

# ─── Header ───────────────────────────────────────────────
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    st.title("🛡️ AYCO Contract Risk Intelligence")
    st.caption(f"Huawei Cloud DWS + DeepSeek v4 Flash | Live Monitoring")
with col3:
    # Use a robust SVG placeholder if internet logo fails
    st.markdown("### ☁️")
    st.caption("Huawei Cloud")

# ─── KPI Row ──────────────────────────────────────────────
kpi_df = run_query("""
    SELECT COUNT(*) as total, ROUND(AVG(risk_score), 1) as avg_risk,
           SUM(monto_total) as exposure
    FROM risk_results
""")

if not kpi_df.empty and kpi_df.iloc[0]['total'] > 0:
    row = kpi_df.iloc[0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Contratos", int(row["total"]))
    m2.metric("Riesgo Promedio", f"{row['avg_risk']}/10")
    m3.metric("Exposición", f"${row['exposure']/1e6:.1f}M")
    m4.metric("Status", "✅ Conectado")
else:
    st.info("📡 Esperando datos del pipeline... El dashboard se actualizará automáticamente.")

# ─── Main Charts ──────────────────────────────────────────
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("🎯 Nivel de Riesgo")
    dist_df = run_query("SELECT risk_level, COUNT(*) as count FROM risk_results GROUP BY risk_level")
    if not dist_df.empty:
        fig = px.pie(dist_df, names="risk_level", values="count", 
                     color="risk_level",
                     color_discrete_map={"BAJO": "#00d4aa", "MEDIO": "#ffd700", "ALTO": "#ff8c00", "CRITICO": "#ff4444"},
                     hole=0.4)
        fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🗺️ Mapa de Riesgo Geoespacial")
    map_df = run_query("SELECT state, AVG(risk_score) as risk, COUNT(*) as count FROM risk_results GROUP BY state")
    if not map_df.empty:
        map_df["lat"] = map_df["state"].map(lambda x: STATE_COORDS.get(x, [19.43, -99.13])[0])
        map_df["lon"] = map_df["state"].map(lambda x: STATE_COORDS.get(x, [19.43, -99.13])[1])
        fig_map = px.scatter_geo(map_df, lat="lat", lon="lon", color="risk", size="count",
                                color_continuous_scale=["#00d4aa", "#ffd700", "#ff4444"],
                                projection="natural earth", height=300)
        fig_map.update_geos(
            bgcolor="rgba(0,0,0,0)", 
            landcolor="#1a1f2e",  
            subunitcolor="#2d3748",
            showcountries=True
        )
        fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig_map, use_container_width=True)

# ─── Secondary Charts ─────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📊 Riesgo por Estado")
    state_df = run_query("SELECT state, AVG(risk_score) as avg_risk FROM risk_results GROUP BY state ORDER BY avg_risk DESC")
    if not state_df.empty:
        fig_state = px.bar(state_df, x="state", y="avg_risk", color="avg_risk", 
                           color_continuous_scale=["#00d4aa", "#ff4444"])
        fig_state.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", height=250)
        st.plotly_chart(fig_state, use_container_width=True)

with col_b:
    st.subheader("💰 Top 5 Exposición")
    vendor_df = run_query("SELECT vendor_name, monto_total/1e6 as m_mxn FROM risk_results ORDER BY m_mxn DESC LIMIT 5")
    if not vendor_df.empty:
        fig_vendor = px.bar(vendor_df, x="m_mxn", y="vendor_name", orientation='h', color_discrete_sequence=['#00d4aa'])
        fig_vendor.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", height=250)
        st.plotly_chart(fig_vendor, use_container_width=True)

# ─── Detail Table ─────────────────────────────────────────
st.subheader("📋 Detalle de Contratos")
detail_df = run_query("SELECT contract_number, vendor_name, risk_score, risk_level FROM risk_results ORDER BY risk_score DESC")
if not detail_df.empty:
    for _, r in detail_df.iterrows():
        c = st.columns([1, 2, 1, 1, 1.5])
        c[0].write(r['contract_number'])
        c[1].write(r['vendor_name'])
        c[2].write(f"Score: {r['risk_score']}")
        l_color = {"CRITICO": "#ff4444", "ALTO": "#ff8c00", "MEDIO": "#ffd700", "BAJO": "#00d4aa"}.get(r['risk_level'], "#fff")
        c[3].markdown(f'<span style="color:{l_color}; font-weight:bold;">{r["risk_level"]}</span>', unsafe_allow_html=True)
        frontend_url = os.getenv("FRONTEND_URL", "http://149.232.129.39")
        url = f"{frontend_url}/contract-ai/"
        c[4].markdown(f'<a href="{url}" target="_blank" class="dify-button">Contract AI 🤖</a>', unsafe_allow_html=True)

# ─── Auto-refresh ───
if st.sidebar.checkbox("Auto-refresh (10s)", value=True):
    import time
    time.sleep(10)
    st.rerun()
