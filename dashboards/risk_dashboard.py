"""
AYCO Contract Risk Dashboard — Streamlit
Connects directly to DWS (PostgreSQL-compatible) via psycopg2.
Runs on port 8501, same ECS as Dify (ayco-dify).
Zero external dependencies beyond pip packages.
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
    initial_sidebar_state="collapsed",
)

# ─── Huawei Cloud / AYCO Branding ─────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0e17; }
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%); }
    h1, h2, h3, h4, .metric-label, p, span { color: #e8eaed !important; }
    div[data-testid="stMetricValue"] { color: #00d4aa !important; font-size: 2rem !important; }
    div[data-testid="stMetricDelta"] { color: #ff6b6b !important; }
    .stDataFrame { background: #1a1f2e; border-radius: 12px; }
    .css-1kyxreq { background: #1a1f2e; border-radius: 12px; padding: 1rem; }
    .dify-button {
        background-color: #00d4aa;
        color: #0a0e17 !important;
        padding: 4px 12px;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin-top: 5px;
    }
    .dify-button:hover {
        background-color: #00f2c3;
        transform: scale(1.05);
        transition: 0.2s;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data & Helpers ────────────────────────────────────────
STATE_COORDS = {
    "CDMX": [19.4326, -99.1332],
    "JAL": [20.6597, -103.3496],
    "NLE": [25.6866, -100.3161],
    "QRO": [20.5888, -100.3899],
    "PUE": [19.0414, -98.2063],
    "GTO": [21.0190, -101.2574],
    "SON": [29.0730, -110.9559],
    "CHIH": [28.6330, -106.0691],
    "BC": [30.8406, -115.2838],
    "TAMPS": [24.2669, -98.8363],
}

@st.cache_resource(ttl=300)
def get_dws_connection():
    """Connect to DWS using env vars."""
    return psycopg2.connect(
        host=os.getenv("DWS_ENDPOINT", "10.1.1.10"),
        port=int(os.getenv("DWS_PORT", "8000")),
        dbname=os.getenv("DWS_DATABASE", "ayco_db"),
        user=os.getenv("DWS_USER", "ayco_admin"),
        password=os.getenv("DWS_PASSWORD", ""),
        connect_timeout=5,
    )

@st.cache_data(ttl=30)
def run_query(query: str) -> pd.DataFrame:
    """Execute a read-only query."""
    conn = get_dws_connection()
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()

# ─── Header ───────────────────────────────────────────────
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.title("🛡️ AYCO Contract Risk Intelligence")
    st.caption(
        f"Powered by Huawei Cloud DWS + DeepSeek v4 Flash via MaaS | "
        f"Last refresh: {datetime.now().strftime('%H:%M:%S CST')}"
    )
with col3:
    st.image("https://www.huaweicloud.com/favicon.ico", width=40)
    st.caption("Huawei Cloud")

# ─── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh data (10s)", value=False)
    st.divider()
    st.info("💡 Tip: Click 'Consultar AI' to open Dify with contract context.")

# ─── KPI Row ──────────────────────────────────────────────
kpi_query = """
    SELECT
        COUNT(*)                                                    AS total_contracts,
        ROUND(AVG(risk_score), 1)                                   AS avg_risk,
        COUNT(CASE WHEN risk_level = 'CRITICO' THEN 1 END)          AS critical_count,
        COUNT(CASE WHEN risk_level IN ('ALTO','CRITICO') THEN 1 END) AS high_risk_count,
        ROUND(SUM(monto_total) / 1000000.0, 1)                     AS total_exposure_m
    FROM risk_results
"""
kpi_df = run_query(kpi_query)

if not kpi_df.empty:
    row = kpi_df.iloc[0]
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Contracts", int(row["total_contracts"]))
    m2.metric("Avg Risk Score", f"{row['avg_risk']:.1f}/10")
    m3.metric("🚨 Critical", int(row["critical_count"]), delta=f"{int(row['high_risk_count'])} high-risk", delta_color="inverse")
    m4.metric("Total Exposure", f"${row['total_exposure_m']:.1f}M")
    m5.metric("Pipeline Status", "✅ Live")

# ─── Charts Row ────────────────────────────────────────────
col_left, col_mid, col_right = st.columns([1, 1.2, 1.2])

with col_left:
    st.subheader("🎯 Average Risk")
    if not kpi_df.empty:
        avg_risk = float(row["avg_risk"])
        color = "#00d4aa" if avg_risk < 4 else "#ffd700" if avg_risk < 7 else "#ff4444"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_risk,
            gauge={
                'axis': {'range': [None, 10]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 4], 'color': 'rgba(0, 212, 170, 0.1)'},
                    {'range': [4, 7], 'color': 'rgba(255, 215, 0, 0.1)'},
                    {'range': [7, 10], 'color': 'rgba(255, 68, 68, 0.1)'}],
            }
        ))
        fig_gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", height=250, margin=dict(t=30, b=0))
        st.plotly_chart(fig_gauge, use_container_width=True)

with col_mid:
    st.subheader("📊 Risk Distribution")
    risk_df = run_query("SELECT risk_level, COUNT(*) AS count FROM risk_results GROUP BY risk_level")
    if not risk_df.empty:
        fig = px.bar(risk_df, x="risk_level", y="count", color="risk_level",
                     color_discrete_map={"BAJO": "#00d4aa", "MEDIO": "#ffd700", "ALTO": "#ff8c00", "CRITICO": "#ff4444"})
        fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed", height=250, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🗺️ Geospatial Risk")
    map_df = run_query("SELECT state, AVG(risk_score) as avg_risk, COUNT(*) as count FROM risk_results GROUP BY state")
    if not map_df.empty:
        map_df["lat"] = map_df["state"].map(lambda x: STATE_COORDS.get(x, [19.43, -99.13])[0])
        map_df["lon"] = map_df["state"].map(lambda x: STATE_COORDS.get(x, [19.43, -99.13])[1])
        fig_map = px.scatter_mapbox(map_df, lat="lat", lon="lon", color="avg_risk", size="count",
                                    color_continuous_scale=["#00d4aa", "#ffd700", "#ff4444"],
                                    zoom=3, mapbox_style="carto-darkmatter", height=250)
        fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)
        st.plotly_chart(fig_map, use_container_width=True)

# ─── Detailed Table ───────────────────────────────────────
st.subheader("📋 Contract Risk Intelligence Details")
detail_df = run_query("""
    SELECT contract_number, vendor_name, state, 
           monto_total, risk_score, risk_level, llm_provider
    FROM risk_results ORDER BY risk_score DESC
""")

if not detail_df.empty:
    dify_ip = os.getenv("DIFY_PUBLIC_IP", "localhost")
    
    # Custom Table Header
    h_cols = st.columns([1.5, 2, 0.8, 1.2, 0.8, 1, 1.5, 1.2])
    cols_labels = ["Contract #", "Vendor", "State", "Amount", "Score", "Level", "Provider", "Action"]
    for i, label in enumerate(cols_labels):
        h_cols[i].markdown(f"**{label}**")
    st.divider()

    for _, r in detail_df.iterrows():
        c = st.columns([1.5, 2, 0.8, 1.2, 0.8, 1, 1.5, 1.2])
        c[0].write(r['contract_number'])
        c[1].write(r['vendor_name'])
        c[2].write(r['state'])
        c[3].write(f"${r['monto_total']/1e6:.1f}M")
        c[4].write(f"{r['risk_score']:.1f}")
        
        l_color = {"CRITICO": "#ff4444", "ALTO": "#ff8c00", "MEDIO": "#ffd700", "BAJO": "#00d4aa"}.get(r['risk_level'], "#fff")
        c[5].markdown(f'<span style="color:{l_color}; font-weight:bold;">{r["risk_level"]}</span>', unsafe_allow_html=True)
        c[6].write(r['llm_provider'])
        
        # Dify Link
        q = f"Analiza el contrato {r['contract_number']} de {r['vendor_name']}. ¿Qué riesgos específicos encontraste?"
        url = f"http://{dify_ip}/chat?query={q}"
        c[7].markdown(f'<a href="{url}" target="_blank" class="dify-button">Consultar AI 🤖</a>', unsafe_allow_html=True)

# ─── Auto-refresh ───
if auto_refresh:
    import time
    time.sleep(10)
    st.rerun()
