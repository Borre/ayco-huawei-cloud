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
</style>
""", unsafe_allow_html=True)

# ─── DWS Connection ────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_dws_connection():
    """Connect to DWS using env vars (set in ECS user_data or .env)."""
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
    """Execute a read-only query and return DataFrame."""
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
    st.image(
        "https://www.huaweicloud.com/favicon.ico",
        width=40,
    )
    st.caption("Huawei Cloud")

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
else:
    st.warning("⚠️ No data in DWS yet. Run the ETL pipeline first.")

# ─── Charts Row ────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Risk Distribution by Level")
    risk_dist_query = """
        SELECT risk_level, COUNT(*) AS count, ROUND(AVG(risk_score), 1) AS avg_score
        FROM risk_results GROUP BY risk_level ORDER BY avg_score DESC
    """
    risk_df = run_query(risk_dist_query)
    if not risk_df.empty:
        color_map = {"BAJO": "#00d4aa", "MEDIO": "#ffd700", "ALTO": "#ff8c00", "CRITICO": "#ff4444"}
        fig = px.bar(
            risk_df, x="risk_level", y="count", color="risk_level",
            color_discrete_map=color_map, text="avg_score",
            labels={"count": "Contracts", "risk_level": "Risk Level"},
        )
        fig.update_traces(texttemplate="Avg: %{text}", textposition="outside")
        fig.update_layout(
            showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed",
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("💰 Vendor Exposure (Top 10)")
    vendor_query = """
        SELECT vendor_name, COUNT(*) AS contracts,
               ROUND(SUM(monto_total)/1000000.0, 1) AS exposure_m,
               ROUND(AVG(risk_score), 1) AS avg_risk
        FROM risk_results GROUP BY vendor_name
        ORDER BY exposure_m DESC LIMIT 10
    """
    vendor_df = run_query(vendor_query)
    if not vendor_df.empty:
        fig = px.bar(
            vendor_df, x="vendor_name", y="exposure_m", color="avg_risk",
            color_continuous_scale=["#00d4aa", "#ffd700", "#ff4444"],
            labels={"exposure_m": "Exposure (M MXN)", "vendor_name": ""},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e8eaed", coloraxis_showscale=False,
            margin=dict(t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

# ─── Bottom Row: Full Table ────────────────────────────────
st.subheader("📋 Contract Risk Details")
detail_query = """
    SELECT contract_number, vendor_name,
           '$' || TO_CHAR(monto_total, 'FM999,999,999') AS monto_total,
           risk_score, risk_level,
           alertas, llm_provider,
           TO_CHAR(analyzed_at, 'YYYY-MM-DD HH24:MI') AS analyzed_at
    FROM risk_results
    ORDER BY risk_score DESC
"""
detail_df = run_query(detail_query)
if not detail_df.empty:
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=10, format="%.1f"
            ),
            "risk_level": st.column_config.TextColumn("Level"),
        },
    )

# ─── Footer ────────────────────────────────────────────────
st.divider()
st.caption(
    "AYCO Contract Risk Intelligence Dashboard | "
    "Data: Huawei Cloud DWS | AI: DeepSeek v4 Flash via MaaS | "
    "Observability: Langfuse | "
    f"© {datetime.now().year} Grupo Salinas — AYCO"
)

# ─── Run instructions:
#   pip install streamlit psycopg2-binary pandas plotly
#   DWS_ENDPOINT=10.x.x.x DWS_PASSWORD=xxx streamlit run dashboards/risk_dashboard.py --server.port 8501
