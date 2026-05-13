"""
AYCO Contract Risk Intelligence — Streamlit Dashboard v2.0
Huawei Cloud DWS + DeepSeek | Grupo Salinas Demo
"""

import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re
import json
import base64
import traceback
import logging
import urllib.request
from datetime import datetime

# ─── MaaS / DeepSeek / Dify Config for Chat BI ───────────
MAAS_ENDPOINT = os.getenv("MAAS_ENDPOINT", "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions")
MAAS_MODEL = os.getenv("MAAS_MODEL", "DeepSeek-V3")
MAAS_API_KEY = os.getenv("MAAS_API_KEY", "")
DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DIFY_ENDPOINT = os.getenv("DIFY_ENDPOINT", "http://101.44.185.139/v1/chat-messages")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

# Module-level error state (survives Streamlit reruns within same session)
_LAST_DWS_ERROR: str | None = None

def _set_error(msg: str) -> None:
    global _LAST_DWS_ERROR
    _LAST_DWS_ERROR = msg
    logging.error(f"[DWS] {msg}")

def get_last_error() -> str | None:
    return _LAST_DWS_ERROR

# ─── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="AYCO Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Premium Dark Theme ───────────────────────────────────
st.markdown("""
<style>
    /* Self-hosted: no external font dependency — Google Fonts blocked in Huawei Cloud LATAM */
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-400-normal.woff2') format('woff2');
        font-weight: 400; font-style: normal; font-display: swap;
    }
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-500-normal.woff2') format('woff2');
        font-weight: 500; font-style: normal; font-display: swap;
    }
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-600-normal.woff2') format('woff2');
        font-weight: 600; font-style: normal; font-display: swap;
    }
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-700-normal.woff2') format('woff2');
        font-weight: 700; font-style: normal; font-display: swap;
    }
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-300-normal.woff2') format('woff2');
        font-weight: 300; font-style: normal; font-display: swap;
    }
    @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-latin-800-normal.woff2') format('woff2');
        font-weight: 800; font-style: normal; font-display: swap;
    }
    * { font-family: 'Inter', system-ui, -apple-system, sans-serif; }
    .main { background-color: #0a0e17; }
    .stApp { background: #0a0e17; }
    .block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1280px; }
    h1, h2, h3, h4, .metric-label, p, span, div { color: #e8eaed; }
    h2, h3 { letter-spacing: -0.01em; }
    div[data-testid="stMetricValue"] { color: #00d4aa !important; font-size: 2rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; color: #8b95a5 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    .stTabs [data-baseweb="tab-list"] { gap: 0; background: #0f1420; border-radius: 12px; padding: 4px; }
    .stTabs [data-baseweb="tab"] {
        color: #8b95a5; background: transparent; border-radius: 10px; padding: 8px 20px;
        font-weight: 500; font-size: 0.9rem; border: none; transition: all 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #e8eaed; }
    .stTabs [aria-selected="true"] { background: #1a1f2e !important; color: #00d4aa !important; font-weight: 600 !important; }
    .stDataFrame { border-radius: 12px; border: 1px solid #1e2a3a; }
    .stDataFrame [data-testid="stTable"] { background: #0f1420; }
    div[data-testid="stVerticalBlock"] > div[style*="flex"] { gap: 0.5rem; }
    .kpi-card {
        background: linear-gradient(135deg, #0f1420 0%, #1a1f2e 100%);
        border: 1px solid #1e2a3a; border-radius: 8px; padding: 1rem 1.1rem;
        min-height: 118px;
    }
    .kpi-card .kpi-label { color: #8b95a5; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }
    .kpi-card .kpi-value { color: #e8eaed; font-size: 1.8rem; line-height: 1.15; font-weight: 800; margin-top: 0.35rem; }
    .kpi-card .kpi-note { color: #8b95a5; font-size: 0.78rem; margin-top: 0.45rem; }
    .section-note {
        color: #8b95a5; font-size: 0.82rem; margin-top: -0.35rem; margin-bottom: 0.75rem;
    }
    .kpi-critical { border-left: 3px solid #ff4444; }
    .kpi-warning { border-left: 3px solid #ff8c00; }
    .kpi-ok { border-left: 3px solid #00d4aa; }
    .plot-container { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── Data Layer ───────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_dws_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DWS_ENDPOINT") or os.getenv("DWS_HOST", "127.0.0.1"),
            port=int(os.getenv("DWS_PORT", "8000")),
            dbname=os.getenv("DWS_DATABASE") or os.getenv("DWS_DB", "ayco_db"),
            user=os.getenv("DWS_USER", "ayco_admin"),
            password=os.getenv("DWS_PASSWORD") or os.getenv("DWS_PASS", ""),
            connect_timeout=5,
            options="-c client_encoding=UTF8",
        )
    except Exception as e:
        _set_error(f"DWS connection failed: {e}")
        return None

def run_query(query: str, use_cache: bool = True) -> pd.DataFrame:
    conn = get_dws_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(query, conn)
        if use_cache:
            conn.commit()  # keep connection alive
        return df
    except Exception as e:
        _set_error(f"Query failed: {str(e)[:200]}")
        return pd.DataFrame()

# ─── Global Filter Infrastructure ──────────────────────────

def get_filters():
    """Return active filter values from session state. Call AFTER sidebar renders."""
    return {
        'min_monto': st.session_state.get('filter_min_monto', 0),
        'estados': st.session_state.get('filter_estados', []),
    }

def build_filter_where(min_monto: float = 0, estados: list = None) -> str:
    """Build SQL WHERE clause for risk_results table. Use {filter_where} placeholder in queries."""
    clauses = []
    if min_monto > 0:
        clauses.append(f"monto_total >= {int(min_monto * 1_000_000)}")
    if estados:
        escaped = "', '".join(str(e) for e in estados)
        clauses.append(f"state IN ('{escaped}')")
    return " AND ".join(clauses)

# ─── Data Functions ────────────────────────────────────────

@st.cache_data(ttl=60)
def load_kpi_data(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        WITH normalized AS (
            SELECT *, REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_norm
            FROM risk_results
            {filter_clause}
        )
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT vendor_name) as vendors,
            SUM(CASE WHEN risk_norm='CRITICO' THEN 1 ELSE 0 END) as criticos,
            SUM(CASE WHEN risk_norm='ALTO' THEN 1 ELSE 0 END) as altos,
            SUM(CASE WHEN garantia_pct=0 THEN 1 ELSE 0 END) as sin_garantia,
            ROUND(AVG(risk_score)::numeric, 1) as avg_score,
            ROUND(SUM(monto_total)::numeric, 0) as exposure,
            ROUND(AVG(plazo_dias)::numeric, 0) as avg_plazo,
            ROUND((SUM(CASE WHEN risk_norm IN ('CRITICO','ALTO') THEN monto_total ELSE 0 END) 
                   / NULLIF(SUM(monto_total),0) * 100)::numeric, 1) as pct_exposure_risk
        FROM normalized
    """)

@st.cache_data(ttl=60)
def load_risk_distribution(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        WITH normalized AS (
            SELECT *, REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_norm
            FROM risk_results
            {filter_clause}
        )
        SELECT risk_norm as risk_level, COUNT(*) as count, 
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as exposure_mxn_m
        FROM normalized 
        GROUP BY risk_norm 
        ORDER BY MIN(risk_score)
    """)

@st.cache_data(ttl=60)
def load_vendor_data(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        WITH normalized AS (
            SELECT *, REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_norm
            FROM risk_results
            {filter_clause}
        )
        SELECT vendor_name, COUNT(*) as contracts,
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as total_mxn_m,
               CASE MAX(CASE risk_norm WHEN 'CRITICO' THEN 4 WHEN 'ALTO' THEN 3 WHEN 'MEDIO' THEN 2 WHEN 'BAJO' THEN 1 ELSE 0 END)
                   WHEN 4 THEN 'CRITICO'
                   WHEN 3 THEN 'ALTO'
                   WHEN 2 THEN 'MEDIO'
                   WHEN 1 THEN 'BAJO'
                   ELSE 'SIN_DATO'
               END as max_risk_level
        FROM normalized 
        GROUP BY vendor_name 
        ORDER BY total_mxn_m DESC
        LIMIT 15
    """)

@st.cache_data(ttl=60)
def load_contract_detail(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        SELECT contract_number, vendor_name, risk_score,
               REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_level,
               monto_total/1e6 as mxn_m, plazo_dias, garantia_pct,
               alertas, recomendaciones, analyzed_at
        FROM risk_results
        {filter_clause}
        ORDER BY risk_score DESC
    """)

@st.cache_data(ttl=60)
def load_scatter_data(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        SELECT contract_number, vendor_name, risk_score,
               REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_level,
               monto_total/1e6 as mxn_m, plazo_dias, garantia_pct
        FROM risk_results
        {filter_clause}
    """)

@st.cache_data(ttl=300)
def load_geo_data(min_monto: float = 0, estados: tuple = ()):
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"AND {where}" if where else ""
    return run_query(f"""
        WITH normalized AS (
            SELECT *, REPLACE(UPPER(COALESCE(risk_level, 'SIN_DATO')), 'Í', 'I') AS risk_norm
            FROM risk_results
        )
        SELECT state, COUNT(*) as contracts,
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as exposure_mxn_m,
               SUM(CASE WHEN risk_norm='CRITICO' THEN 1 ELSE 0 END) as criticos,
               SUM(CASE WHEN risk_norm='ALTO' THEN 1 ELSE 0 END) as altos
        FROM normalized
        WHERE state IS NOT NULL {filter_clause}
        GROUP BY state
    """)

@st.cache_data(ttl=60)
def load_last_analyzed() -> datetime | None:
    """Returns the most recent contract analysis timestamp, or None if empty."""
    df = run_query("""
        SELECT MAX(analyzed_at) as last_ts FROM risk_results
    """)
    if df.empty or df.iloc[0]["last_ts"] is None:
        return None
    return df.iloc[0]["last_ts"]

def time_ago(dt: datetime) -> str:
    """Human-readable 'hace X minutos/horas/días' in Spanish."""
    delta = datetime.now() - dt
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "ahora"
    if minutes < 60:
        return f"hace {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"hace {hours}h"
    days = hours // 24
    return f"hace {days}d"


@st.cache_data(ttl=60)
def load_pending_count(min_monto: float = 0, estados: tuple = ()):
    """Count contracts still awaiting analysis (analyzed_at IS NULL). Pipeline health metric."""
    return run_query("""
        SELECT COUNT(*) as pending
        FROM risk_results
        WHERE analyzed_at IS NULL
    """)

@st.cache_data(ttl=60)
def load_critical_contracts(min_monto: float = 0, estados: tuple = ()):
    """Contracts with risk_score >= 8 (CRÍTICO), ordered by score DESC."""
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"AND {where}" if where else ""
    return run_query(f"""
        SELECT contract_number, vendor_name, risk_score,
               monto_total/1e6 as mxn_m, alertas
        FROM risk_results
        WHERE risk_score >= 8 {filter_clause}
        ORDER BY risk_score DESC, monto_total DESC
        LIMIT 5
    """)

@st.cache_data(ttl=60)
def load_vendor_risk_heatmap(min_monto: float = 0, estados: tuple = ()):
    """Cross-tab: vendor × risk_level → contract count for heatmap."""
    where = build_filter_where(min_monto, list(estados))
    filter_clause = f"WHERE {where}" if where else ""
    return run_query(f"""
        SELECT vendor_name,
               SUM(CASE WHEN risk_score < 4 THEN 1 ELSE 0 END) as bajo,
               SUM(CASE WHEN risk_score >= 4 AND risk_score < 6 THEN 1 ELSE 0 END) as medio,
               SUM(CASE WHEN risk_score >= 6 AND risk_score < 8 THEN 1 ELSE 0 END) as alto,
               SUM(CASE WHEN risk_score >= 8 THEN 1 ELSE 0 END) as critico,
               COUNT(*) as total
        FROM risk_results
        {filter_clause}
        GROUP BY vendor_name
        HAVING COUNT(*) > 0
        ORDER BY SUM(CASE WHEN risk_score >= 8 THEN 1 ELSE 0 END) DESC,
                 SUM(CASE WHEN risk_score >= 6 THEN 1 ELSE 0 END) DESC
        LIMIT 15
    """)

# ─── Filter-Aware Wrappers ─────────────────────────────────
# These read session_state and pass filter values to the
# @st.cache_data functions above. Cache key varies by filter.

def _load_kpi_data():
    f = get_filters()
    return load_kpi_data(f['min_monto'], tuple(f['estados']))

def _load_risk_distribution():
    f = get_filters()
    return load_risk_distribution(f['min_monto'], tuple(f['estados']))

def _load_vendor_data():
    f = get_filters()
    return load_vendor_data(f['min_monto'], tuple(f['estados']))

def _load_contract_detail():
    f = get_filters()
    return load_contract_detail(f['min_monto'], tuple(f['estados']))

def _load_scatter_data():
    f = get_filters()
    return load_scatter_data(f['min_monto'], tuple(f['estados']))

def _load_geo_data():
    f = get_filters()
    return load_geo_data(f['min_monto'], tuple(f['estados']))

def _load_pending_count():
    f = get_filters()
    return load_pending_count(f['min_monto'], tuple(f['estados']))

def _load_critical_contracts():
    f = get_filters()
    return load_critical_contracts(f['min_monto'], tuple(f['estados']))

def _load_vendor_risk_heatmap():
    f = get_filters()
    return load_vendor_risk_heatmap(f['min_monto'], tuple(f['estados']))

# Mexico state coordinates (centroids)
MEX_STATE_COORDS = {
    "CDMX": (19.4326, -99.1332), "JAL": (20.6597, -103.3496),
    "NLE": (25.6866, -100.3161), "QRO": (20.5888, -100.3899),
    "PUE": (19.0414, -98.2063), "GTO": (21.0190, -101.2574),
    "SON": (29.0730, -110.9559), "CHIH": (28.6330, -106.0691),
    "BC": (30.8406, -115.2838), "TAMPS": (24.2669, -98.8363),
    "TAB": (17.9892, -92.9475), "OAX": (17.0732, -96.7266),
    "QROO": (19.8761, -88.2669), "SLP": (22.1565, -100.9855),
    "CHIS": (16.7570, -93.1188),
}

# ─── Color Constants ──────────────────────────────────────
RISK_COLORS = {"BAJO": "#00d4aa", "MEDIO": "#ffd700", "ALTO": "#ff8c00", "CRITICO": "#ff4444"}
RISK_ORDER = ["BAJO", "MEDIO", "ALTO", "CRITICO"]
CHART_BG = "rgba(0,0,0,0)"
PLOT_BG = "rgba(0,0,0,0)"
GRID_COLOR = "#1e2a3a"
TEXT_COLOR = "#e8eaed"

def format_mxn(value: float) -> str:
    if value is None:
        return "N/A"
    value = float(value)
    if abs(value) >= 1e9:
        return f"${value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.0f}M"
    return f"${value:,.0f}"

def format_llm_list(raw, fallback: str = "N/A") -> str:
    """Parse alertas/recomendaciones from DWS (stored as JSON array or Python list).
    Returns HTML bullet list, or raw string if not parseable."""
    import json as _json
    if raw is None or raw == "":
        return f'<span style="color:#8b95a5;">{fallback}</span>'
    # Already a Python list (pandas may have parsed it)
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        # Force-decode unicode escapes: \u00f3 → ó, \u00e1 → á, etc.
        decoded = raw
        if '\\u' in raw:
            try:
                decoded = raw.encode('utf-8').decode('unicode_escape')
            except (UnicodeDecodeError, UnicodeEncodeError):
                decoded = raw
        try:
            items = _json.loads(decoded)
            if not isinstance(items, list):
                return str(decoded)
        except (_json.JSONDecodeError, ValueError):
            return str(decoded)
    else:
        return str(raw)
    if not items:
        return f'<span style="color:#8b95a5;">{fallback}</span>'
    bullets = "".join(f'<li style="margin-bottom:2px;color:#e8eaed;font-size:0.82rem;">{item}</li>' for item in items)
    return f'<ul style="margin:0;padding-left:1.2rem;list-style-type:disc;">{bullets}</ul>'

def kpi_card(label: str, value: str, note: str = "", state: str = "ok"):
    state_class = {"critical": "kpi-critical", "warning": "kpi-warning", "ok": "kpi-ok"}.get(state, "kpi-ok")
    st.markdown(
        f"""
        <div class="kpi-card {state_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def chart_layout(fig, height=400):
    fig.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_COLOR, size=12, family="Inter"),
        margin=dict(t=30, b=10, l=10, r=10),
        height=height,
        legend=dict(font=dict(color=TEXT_COLOR)),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        coloraxis_showscale=False,
    )
    return fig

# ─── CSV Export Helper ────────────────────────────────────
def csv_download_link(df: pd.DataFrame, filename: str, label: str = "⬇ Descargar CSV"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="color:#00d4aa;text-decoration:none;font-weight:600;font-size:0.8rem;">{label}</a>'

# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════
col1, col2 = st.columns([5, 2])
with col1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:2rem;">🛡️</span>
        <h1 style="margin:0;font-size:1.8rem;font-weight:700;color:#e8eaed;">AYCO Contract Risk Intelligence</h1>
    </div>
    """, unsafe_allow_html=True)
with col2:
    last_ts = load_last_analyzed()
    status_line = f"🟢 {time_ago(last_ts)}" if last_ts else "🟡 sin datos"
    st.markdown(f"""
    <div style="text-align:right;padding-top:0.8rem;">
        <span style="font-size:0.8rem;color:#00d4aa;font-weight:600;">Último análisis: {status_line}</span><br>
        <span style="font-size:0.7rem;color:#8b95a5;">Huawei Cloud DWS · DeepSeek</span>
    </div>
    """, unsafe_allow_html=True)

# ─── KPI Banner ───────────────────────────────────────────
kpi = _load_kpi_data()
if not kpi.empty:
    r = kpi.iloc[0]
    total = int(r["total"] or 0)
    high_count = int(r["criticos"] or 0) + int(r["altos"] or 0)
    pct_risk = float(r["pct_exposure_risk"] or 0)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Exposición Total", format_mxn(r["exposure"]), "MXN en contratos analizados", "ok")
    with c2:
        kpi_card("Exposición en Riesgo", f"{pct_risk:.1f}%", f"{high_count}/{total} contratos alto o crítico", "critical" if pct_risk >= 30 else "warning")
    with c3:
        kpi_card("Score Promedio", f"{float(r['avg_score'] or 0):.1f}/10", f"Plazo prom. {int(r['avg_plazo'] or 0)} días", "warning")
    with c4:
        kpi_card("Sin Garantía", f"{int(r['sin_garantia'] or 0)}", f"{int(r['vendors'] or 0)} vendors únicos", "critical" if int(r["sin_garantia"] or 0) else "ok")
    with c5:
        pend = _load_pending_count()
        pending_n = int(pend.iloc[0]["pending"]) if not pend.empty else 0
        kpi_card("Pendientes", str(pending_n), "Contratos sin analizar", "warning" if pending_n > 0 else "ok")
else:
    st.warning("⚠️ No se pudo cargar datos de KPIs. Verifica la conexión DWS y que existan datos en `risk_results`.")

# ─── Critical Contracts Banner ─────────────────────────────
criticals = _load_critical_contracts()
if not criticals.empty and len(criticals) > 0:
    n = len(criticals)
    banner_text = " · ".join([
        f"<b>{row['contract_number'] or 'N/A'}</b> — {(row['vendor_name'] or 'Desconocido')[:30]} "
        f"(Score: {float(row['risk_score'] or 0):.1f}, ${float(row['mxn_m'] or 0):.1f}M)"
        for _, row in criticals.iterrows()
    ])
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #2d1111 0%, #1a0a0a 100%);
                border:1px solid #ff4444;border-radius:12px;padding:0.9rem 1.2rem;
                margin-bottom:1rem;display:flex;align-items:center;gap:12px;">
        <span style="font-size:1.6rem;">🚨</span>
        <div style="flex:1;">
            <div style="font-weight:700;color:#ff4444;font-size:0.95rem;margin-bottom:2px;">
                {n} contrato{'s' if n > 1 else ''} crítico{'s' if n > 1 else ''} {'requieren' if n > 1 else 'requiere'} atención inmediata
            </div>
            <div style="font-size:0.78rem;color:#e8a0a0;line-height:1.5;">
                {banner_text}
            </div>
        </div>
        <span style="font-size:0.7rem;color:#ff6666;">Ve a <b>📋 Contratos</b> →</span>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "📋 Contratos",
    "🏢 Vendors",
    "🔍 Análisis Profundo",
    "💬 Chat BI",
])

# ═══════════════════════════════════════════════
#  TAB 1: OVERVIEW
# ═══════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        # Treemap: exposición por vendor coloreado por riesgo
        st.subheader("💰 Exposición por Vendor — Treemap")
        st.markdown('<div class="section-note">Concentración de exposición; el color indica score promedio.</div>', unsafe_allow_html=True)
        vdata = _load_vendor_data()
        if not vdata.empty:
            # Truncate long vendor names to prevent treemap text overflow
            vdata['vendor_label'] = vdata['vendor_name'].apply(
                lambda x: ((str(x)[:22].rsplit(' ', 1)[0] + '...') if len(str(x)) > 25 else str(x)) if pd.notna(x) else 'Desconocido'
            )
            fig_tree = px.treemap(
                vdata,
                path=["vendor_label"],
                values="total_mxn_m",
                color="avg_score",
                color_continuous_scale=["#00d4aa", "#ffd700", "#ff8c00", "#ff4444"],
                range_color=[1, 10],
                hover_data={"total_mxn_m": ":.1f", "avg_score": ":.1f", "contracts": True},
            )
            fig_tree.update_traces(
                texttemplate="<b>%{label}</b><br>$%{value:.1f}M",
                textposition="middle center",
                hovertemplate="<b>%{customdata[0]}</b><br>Exposición: $%{customdata[1]:.1f}M<br>Score: %{customdata[2]:.1f}/10<br>Contratos: %{customdata[3]}<extra></extra>",
                textfont=dict(size=12, color="white"),
                customdata=vdata[['vendor_name', 'total_mxn_m', 'avg_score', 'contracts']].values,
            )
            fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=420, paper_bgcolor=CHART_BG)
            st.plotly_chart(fig_tree, width='stretch', config={"displayModeBar": False})

    with col_right:
        # Donut + horizontal bars
        st.subheader("🎯 Distribución de Riesgo")
        st.markdown('<div class="section-note">Composición del portafolio por nivel normalizado de riesgo.</div>', unsafe_allow_html=True)
        dist = _load_risk_distribution()
        if not dist.empty:
            # Donut chart
            colors_donut = [RISK_COLORS.get(l, "#666") for l in dist["risk_level"]]
            fig_donut = go.Figure()
            fig_donut.add_trace(go.Pie(
                labels=dist["risk_level"], values=dist["count"],
                hole=0.55, marker_colors=colors_donut,
                textinfo="label+percent", textfont=dict(size=13, color="white"),
                hovertemplate="<b>%{label}</b><br>Contratos: %{value}<br>Score prom: %{customdata[0]:.1f}/10<br>Exposición: $%{customdata[1]:.1f}M<extra></extra>",
                customdata=dist[["avg_score", "exposure_mxn_m"]],
                sort=False,
            ))
            total_contracts = int(kpi.iloc[0]["total"]) if not kpi.empty else int(dist["count"].sum())
            fig_donut.add_annotation(text=f"<b>{total_contracts}</b><br><span style='font-size:11px'>contratos</span>",
                                     x=0.5, y=0.5, showarrow=False, font=dict(size=22, color=TEXT_COLOR))
            fig_donut.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor=CHART_BG, showlegend=False)
            st.plotly_chart(fig_donut, width='stretch', config={"displayModeBar": False})

    # Geo map: Mexico risk by state
    st.subheader("🗺️  Mapa de Riesgo por Estado — México")
    st.markdown('<div class="section-note">Vista territorial de exposición y contratos de mayor severidad.</div>', unsafe_allow_html=True)
    geo_data = _load_geo_data()
    if not geo_data.empty:
        geo_data["lat"] = geo_data["state"].map(lambda s: MEX_STATE_COORDS.get(s, (19.43, -99.13))[0])
        geo_data["lon"] = geo_data["state"].map(lambda s: MEX_STATE_COORDS.get(s, (19.43, -99.13))[1])
        geo_data["size"] = geo_data["exposure_mxn_m"].clip(lower=1)  # min marker size

        fig_geo = px.scatter_geo(
            geo_data, lat="lat", lon="lon",
            size="size", color="avg_score",
            color_continuous_scale=["#00d4aa", "#ffd700", "#ff8c00", "#ff4444"],
            range_color=[1, 10],
            size_max=40,
            hover_name="state",
            hover_data={
                "contracts": True, "avg_score": ":.1f",
                "exposure_mxn_m": ":.1f", "criticos": True, "altos": True,
            },
            projection="natural earth",
            center={"lat": 23.5, "lon": -102},  # Center on Mexico
        )
        fig_geo.update_traces(
            marker=dict(opacity=0.85, line=dict(width=1.5, color="#1e2a3a")),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Contratos: %{customdata[0]} · Score: %{customdata[1]:.1f}<br>"
                "Exposición: $%{customdata[2]:.1f}M<br>"
                "Críticos: %{customdata[3]} · Altos: %{customdata[4]}<extra></extra>"
            ),
        )
        fig_geo.update_geos(
            bgcolor="rgba(0,0,0,0)",
            landcolor="#111827",
            subunitcolor="#1e2a3a",
            showcountries=True,
            scope="north america",
            showframe=False,
            fitbounds="locations",
        )
        fig_geo.update_layout(
            height=350,
            margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor=CHART_BG,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_geo, width='stretch', config={"displayModeBar": False})

# ═══════════════════════════════════════════════
#  TAB 2: CONTRATOS
# ═══════════════════════════════════════════════
with tab2:
    contracts = _load_contract_detail()
    if not contracts.empty:
        # Filters
        filt_col1, filt_col2, filt_col3 = st.columns([2, 1.5, 1])
        with filt_col1:
            search = st.text_input("🔍 Buscar vendor o contrato", placeholder="Ej: Constructora...", key="search_contracts")
        with filt_col2:
            risk_filter = st.multiselect("Nivel de Riesgo", options=RISK_ORDER, default=RISK_ORDER, key="risk_filter_contracts")
        with filt_col3:
            score_min = st.slider("Score Mínimo", 0.0, 10.0, 0.0, 0.5, key="score_min")

        # Apply filters
        filtered = contracts.copy()
        if search:
            mask = filtered["vendor_name"].str.contains(search, case=False, na=False, regex=False)
            mask |= filtered["contract_number"].str.contains(search, case=False, na=False, regex=False)
            filtered = filtered[mask]
        if risk_filter:
            filtered = filtered[filtered["risk_level"].isin(risk_filter)]
        if score_min > 0:
            filtered = filtered[filtered["risk_score"] >= score_min]

        # Summary line + filtered CSV export
        sum_col1, sum_col2 = st.columns([4, 1])
        with sum_col1:
            st.caption(f"Mostrando {len(filtered)} de {len(contracts)} contratos")
        with sum_col2:
            st.markdown(csv_download_link(filtered, "ayco_contracts.csv", "⬇ CSV filtrado"), unsafe_allow_html=True)

        # Color-coded dataframe
        def color_risk(val):
            color = RISK_COLORS.get(val, "#fff")
            return f'background-color: {color}22; color: {color}; font-weight: 700; padding: 2px 8px; border-radius: 4px;'

        def color_score(val):
            if val >= 8: return 'color: #ff4444; font-weight: 700;'
            if val >= 6: return 'color: #ff8c00; font-weight: 600;'
            if val >= 4: return 'color: #ffd700;'
            return 'color: #00d4aa;'

        display_cols = {
            "contract_number": "Contrato",
            "vendor_name": "Vendor",
            "risk_score": "Score",
            "risk_level": "Riesgo",
            "mxn_m": "Monto (M MXN)",
            "plazo_dias": "Plazo (d)",
            "garantia_pct": "Garantía %",
            "analyzed_at": "Analizado",
        }
        styled = filtered[list(display_cols.keys())].rename(columns=display_cols)
        styled["Score"] = styled["Score"].round(1)
        styled["Monto (M MXN)"] = styled["Monto (M MXN)"].round(1)

        st.dataframe(
            styled.style
            .map(color_risk, subset=["Riesgo"])
            .map(color_score, subset=["Score"])
            .format({"Monto (M MXN)": "${:.1f}M", "Garantía %": "{:.0f}%"}),
            width='stretch',
            hide_index=True,
            height=min(38 * len(filtered) + 38, 600),
            column_config={
                "Contrato": st.column_config.TextColumn(width="small"),
                "Score": st.column_config.NumberColumn(width="small"),
                "Riesgo": st.column_config.TextColumn(width="small"),
                "Monto (M MXN)": st.column_config.NumberColumn(width="small"),
                "Plazo (d)": st.column_config.NumberColumn(width="small"),
                "Garantía %": st.column_config.NumberColumn(width="small"),
            },
        )

        # Expandable contract detail
        if len(filtered) > 0:
            st.subheader("🔎 Detalle de Contrato")
            selected = st.selectbox(
                "Selecciona un contrato para ver análisis completo",
                filtered["contract_number"].tolist(),
                format_func=lambda x: f"{x} — {filtered[filtered['contract_number']==x]['vendor_name'].iloc[0]} (Score: {filtered[filtered['contract_number']==x]['risk_score'].iloc[0]})",
                key="contract_detail_select",
            )
            if selected:
                row = contracts[contracts["contract_number"] == selected].iloc[0]
                det1, det2 = st.columns([1, 1])
                with det1:
                    st.markdown(f"""
                    <div style="background:#0f1420;border:1px solid #1e2a3a;border-radius:12px;padding:1rem;margin-bottom:0.5rem;">
                        <span style="color:#8b95a5;font-size:0.7rem;text-transform:uppercase;">Alertas</span><br>
                        {format_llm_list(row['alertas'], 'Ninguna')}
                    </div>
                    <div style="background:#0f1420;border:1px solid #1e2a3a;border-radius:12px;padding:1rem;">
                        <span style="color:#8b95a5;font-size:0.7rem;text-transform:uppercase;">Recomendaciones</span><br>
                        {format_llm_list(row['recomendaciones'], 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
                with det2:
                    metrics_html = f"""
                    <div style="background:#0f1420;border:1px solid #1e2a3a;border-radius:12px;padding:1rem;">
                        <table style="width:100%;font-size:0.85rem;color:#e8eaed;">
                            <tr><td style="color:#8b95a5;">Score</td><td style="text-align:right;font-weight:700;color:{RISK_COLORS.get(row['risk_level'],'#fff')};">{row['risk_score']:.1f}/10</td></tr>
                            <tr><td style="color:#8b95a5;">Nivel</td><td style="text-align:right;font-weight:700;color:{RISK_COLORS.get(row['risk_level'],'#fff')};">{row['risk_level']}</td></tr>
                            <tr><td style="color:#8b95a5;">Monto</td><td style="text-align:right;">${row['mxn_m']:.1f}M MXN</td></tr>
                            <tr><td style="color:#8b95a5;">Plazo</td><td style="text-align:right;">{int(row['plazo_dias'])} días</td></tr>
                            <tr><td style="color:#8b95a5;">Garantía</td><td style="text-align:right;">{row['garantia_pct']:.0f}%</td></tr>
                            <tr><td style="color:#8b95a5;">Analizado</td><td style="text-align:right;">{str(row['analyzed_at'])[:10] if row['analyzed_at'] else 'N/A'}</td></tr>
                        </table>
                    </div>
                    """
                    st.markdown(metrics_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay datos de contratos disponibles. Verifica la conexión DWS y que la tabla `risk_results` contenga registros.")

# ═══════════════════════════════════════════════
with tab3:
    vendors = _load_vendor_data()
    if not vendors.empty:
        col_v1, col_v2 = st.columns([1, 1])

        with col_v1:
            st.subheader("🏢 Top Vendors por Exposición")
            top10 = vendors.head(10)
            fig_vbar = px.bar(
                top10, x="total_mxn_m", y="vendor_name",
                orientation='h', color="avg_score",
                color_continuous_scale=["#00d4aa", "#ffd700", "#ff8c00", "#ff4444"],
                range_color=[1, 10],
                text="total_mxn_m",
            )
            fig_vbar.update_traces(
                texttemplate="$%{text:.1f}M",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Exposición: $%{x:.1f}M<br>Score prom: %{marker.color:.1f}/10<br>Contratos: %{customdata[0]}<extra></extra>",
                customdata=top10[["contracts"]],
            )
            chart_layout(fig_vbar, height=380)
            fig_vbar.update_xaxes(title="Monto Total (M MXN)", gridcolor=GRID_COLOR)
            fig_vbar.update_yaxes(title=None)
            st.plotly_chart(fig_vbar, width='stretch', config={"displayModeBar": False})

        with col_v2:
            st.subheader("⚖️ Score de Riesgo por Vendor")
            # Sort by avg_score descending
            scored = vendors.sort_values("avg_score", ascending=True).tail(12)
            fig_vscore = px.bar(
                scored, x="avg_score", y="vendor_name",
                orientation='h', color="avg_score",
                color_continuous_scale=["#00d4aa", "#ffd700", "#ff4444"],
                range_color=[1, 10],
                text="avg_score",
            )
            fig_vscore.update_traces(
                texttemplate="%{text:.1f}",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Score prom: %{x:.1f}/10<br>Contratos: %{customdata[0]}<extra></extra>",
                customdata=scored[["contracts"]],
            )
            chart_layout(fig_vscore, height=380)
            fig_vscore.update_xaxes(title="Risk Score Promedio", gridcolor=GRID_COLOR, range=[0, 10.5])
            fig_vscore.update_yaxes(title=None)
            st.plotly_chart(fig_vscore, width='stretch', config={"displayModeBar": False})

        # Vendor table
        st.subheader("📋 Detalle de Vendors")
        display_v = vendors.copy()
        display_v["avg_score"] = display_v["avg_score"].round(1)
        display_v["total_mxn_m"] = display_v["total_mxn_m"].round(1)

        def v_color_score(val):
            if val >= 8: return 'color: #ff4444; font-weight: 700;'
            if val >= 6: return 'color: #ff8c00; font-weight: 600;'
            if val >= 4: return 'color: #ffd700;'
            return 'color: #00d4aa;'

        st.dataframe(
            display_v.rename(columns={
                "vendor_name": "Vendor", "contracts": "Contratos",
                "avg_score": "Score Prom.", "total_mxn_m": "Exposición (M MXN)",
                "max_risk_level": "Riesgo Máx.",
            }).style.map(v_color_score, subset=["Score Prom."]).format({"Exposición (M MXN)": "${:.1f}M"}),
            width='stretch',
            hide_index=True,
            height=38 * len(display_v) + 38,
        )
    else:
        st.warning("⚠️ No hay datos de vendors disponibles. Verifica la conexión DWS y que la tabla `risk_results` contenga registros.")

# ═══════════════════════════════════════════════
#  TAB 4: ANÁLISIS PROFUNDO
# ═══════════════════════════════════════════════
with tab4:
    st.subheader("🔬 Factores de Riesgo — Radar View")

    # Aggregate risk factors across all contracts
    risk_dist = _load_risk_distribution()
    scatter_data = _load_scatter_data()

    col_bl, col_br = st.columns([1, 1.3])
    with col_bl:
        st.subheader("📈 Distribución de Risk Scores")
        if not scatter_data.empty:
            fig_hist = px.histogram(
                scatter_data, x="risk_score", nbins=12,
                color_discrete_sequence=["#00d4aa"],
                opacity=0.8,
            )
            fig_hist.update_traces(
                hovertemplate="Score: %{x:.1f}<br>Contratos: %{y}<extra></extra>",
                marker_line=dict(color="#00d4aa", width=1),
            )
            chart_layout(fig_hist, height=320)
            # Threshold line: scores ≥6 = ALTO/CRÍTICO (zona de riesgo)
            fig_hist.add_vline(x=6.0, line_dash="dash", line_color="#ff8c00",
                               line_width=2, opacity=0.7)
            fig_hist.add_annotation(x=6.0, y=0.92, yref="paper",
                                    text="← Zona segura | Zona de riesgo →",
                                    showarrow=False, font=dict(size=9, color="#ff8c00"),
                                    bgcolor="rgba(10,14,23,0.8)")
            fig_hist.update_xaxes(title="Risk Score", tickvals=[1,2,3,4,5,6,7,8,9,10])
            fig_hist.update_yaxes(title="Contratos")
            st.plotly_chart(fig_hist, width='stretch', config={"displayModeBar": False})

    with col_br:
        st.subheader("🎯 Monto vs Riesgo — Bubble Chart")
        if not scatter_data.empty:
            fig_bubble = px.scatter(
                scatter_data, x="mxn_m", y="risk_score",
                size="plazo_dias", color="risk_level",
                color_discrete_map=RISK_COLORS,
                category_orders={"risk_level": RISK_ORDER},
                hover_name="vendor_name",
                hover_data={"contract_number": True, "garantia_pct": ":.1f", "plazo_dias": True},
                size_max=55,
            )
            fig_bubble.update_traces(
                marker=dict(opacity=0.85, line=dict(width=1, color="#1e2a3a")),
                hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>Monto: $%{x:.1f}M · Score: %{y:.1f}<br>Plazo: %{customdata[2]}d · Garantía: %{customdata[1]:.1f}%<extra></extra>",
            )
            chart_layout(fig_bubble, height=320)
            fig_bubble.update_xaxes(title="Monto (M MXN)", gridcolor=GRID_COLOR)
            fig_bubble.update_yaxes(title="Risk Score", gridcolor=GRID_COLOR, range=[0, 10.5])
            st.plotly_chart(fig_bubble, width='stretch', config={"displayModeBar": False})

    if not scatter_data.empty:
        # ── Risk Heatmap: vendors × score bins ──
        st.subheader("🔥 Risk Heatmap — Vendors × Score")
        st.markdown('<div class="section-note">Concentración de contratos por vendor y nivel de riesgo. Más oscuro = más contratos.</div>', unsafe_allow_html=True)
        hm_data = _load_vendor_risk_heatmap()
        if not hm_data.empty:
            # Truncate vendor names for display
            hm_data['vendor_label'] = hm_data['vendor_name'].apply(
                lambda x: ((str(x)[:22].rsplit(' ', 1)[0] + '...') if len(str(x)) > 25 else str(x)) if pd.notna(x) else 'Desconocido'
            )
            # Build heatmap matrix
            z = hm_data[['bajo', 'medio', 'alto', 'critico']].values
            y_labels = hm_data['vendor_label'].tolist()
            x_labels = ['BAJO <4', 'MEDIO 4-6', 'ALTO 6-8', 'CRÍTICO ≥8']
            # Custom colorscale: green → yellow → orange → red (discrete)
            hm_colors = [[0, '#0f1420'], [0.25, '#00d4aa'], [0.5, '#ffd700'],
                         [0.75, '#ff8c00'], [1, '#ff4444']]

            fig_hm = go.Figure(data=go.Heatmap(
                z=z,
                x=x_labels,
                y=y_labels,
                colorscale=hm_colors,
                zmin=0, zmax=max(z.max(), 1),
                text=z.astype(str),
                texttemplate="%{text}",
                textfont=dict(size=11, color='white'),
                hovertemplate="<b>%{y}</b><br>%{x}: <b>%{z}</b> contratos<extra></extra>",
                xgap=2, ygap=2,
            ))
            fig_hm.update_layout(
                height=max(300, 28 * len(y_labels) + 60),
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor=CHART_BG, plot_bgcolor=PLOT_BG,
                xaxis=dict(side='top', tickfont=dict(color=TEXT_COLOR, size=11)),
                yaxis=dict(tickfont=dict(color=TEXT_COLOR, size=11), autorange='reversed'),
            )
            st.plotly_chart(fig_hm, width='stretch', config={"displayModeBar": False})

    # Sunburst / Hierarchical view
    if not scatter_data.empty and not risk_dist.empty:
        st.subheader("🌳 Jerarquía de Riesgo — Sunburst")
        # Simple hierarchy: Risk Level → Vendor
        sunburst_data = scatter_data.copy()
        # Filter out empty vendor names — sunburst requires leaf values
        sunburst_data = sunburst_data[sunburst_data['vendor_name'].notna() & (sunburst_data['vendor_name'] != '')]
        if sunburst_data.empty:
            st.info("ℹ️ No hay datos con vendor válido para el sunburst.")
        else:
            fig_sun = px.sunburst(
                sunburst_data,
                path=["risk_level", "vendor_name"],
                values="mxn_m",
                color="risk_level",
                color_discrete_map=RISK_COLORS,
                hover_data={"risk_score": ":.1f"},
            )
            fig_sun.update_traces(
                hovertemplate="<b>%{label}</b><br>Exposición: $%{value:.1f}M<br>Score: %{customdata[0]:.1f}/10<extra></extra>",
                textfont=dict(size=13, color="white"),
            )
            fig_sun.update_layout(height=450, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor=CHART_BG)
            st.plotly_chart(fig_sun, width='stretch', config={"displayModeBar": False})

    # ── Top 5 contratos prioritarios ──
    if not scatter_data.empty:
        st.subheader("⚠️ Top 5 Contratos que Requieren Atención")
        st.markdown('<div class="section-note">Ordenados por mayor puntuación de riesgo. Accionables inmediatamente.</div>', unsafe_allow_html=True)
        top5 = scatter_data.nlargest(5, 'risk_score')
        cards_html = ""
        for _, row in top5.iterrows():
            color = RISK_COLORS.get(row['risk_level'], '#fff')
            cards_html += f"""
            <div style="background:#0f1420;border:1px solid #1e2a3a;border-left:4px solid {color};
                        border-radius:8px;padding:0.7rem 1rem;margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-weight:600;color:#e8eaed;font-size:0.9rem;">
                        {row['contract_number']} — {(row['vendor_name'] or 'Desconocido')[:35]}
                    </span>
                    <span style="font-weight:700;font-size:1.1rem;color:{color};">{row['risk_score']:.1f}/10</span>
                </div>
                <div style="display:flex;gap:20px;margin-top:3px;font-size:0.75rem;color:#8b95a5;">
                    <span>💰 ${row['mxn_m']:.1f}M</span>
                    <span>📅 {int(row['plazo_dias'])} días</span>
                    <span>🔒 {row['garantia_pct']:.0f}% garantía</span>
                </div>
            </div>
            """
        st.markdown(cards_html, unsafe_allow_html=True)

    # Risk factor breakdown table
    st.subheader("📊 Exposición por Nivel de Riesgo")
    if not risk_dist.empty:
        total_exp = risk_dist["exposure_mxn_m"].sum()
        risk_dist["pct_exp"] = (risk_dist["exposure_mxn_m"] / total_exp * 100).round(1)
        risk_dist["exposure_mxn_m"] = risk_dist["exposure_mxn_m"].round(1)

        fig_table = go.Figure(data=[go.Table(
            header=dict(
                values=["<b>Nivel</b>", "<b>Contratos</b>", "<b>Score Prom.</b>", "<b>Exposición</b>", "<b>% del Total</b>"],
                fill_color="#0f1420",
                font=dict(color=TEXT_COLOR, size=13, family="Inter"),
                align="left",
                height=40,
            ),
            cells=dict(
                values=[
                    risk_dist["risk_level"],
                    risk_dist["count"].astype(int),
                    risk_dist["avg_score"],
                    risk_dist["exposure_mxn_m"].apply(lambda x: f"${x:.1f}M"),
                    risk_dist["pct_exp"].apply(lambda x: f"{x:.1f}%"),
                ],
                fill_color="#0f1420",
                font=dict(color=TEXT_COLOR, size=12, family="Inter"),
                align="left",
                height=32,
            ),
        )])
        fig_table.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor=CHART_BG)
        st.plotly_chart(fig_table, width='stretch', config={"displayModeBar": False})

# ═══════════════════════════════════════════════
#  TAB 5: CHAT BI
# ═══════════════════════════════════════════════

# ─── SQL Safety ───────────────────────────────────────────
_DANGEROUS_SQL = re.compile(
    r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|'
    r'REPLACE|MERGE|COMMENT|RENAME|LOCK|UNLOCK|CALL|IMPORT|EXPORT|COPY|'
    r'PG_SLEEP|PG_TERMINATE_BACKEND|DBLINK)\b',
    re.IGNORECASE,
)

def _validate_sql(sql: str) -> tuple[bool, str]:
    """Return (is_safe, reason). Block anything that isn't SELECT."""
    stripped = sql.strip().rstrip(';').strip()
    if not stripped.upper().startswith('SELECT') and not stripped.upper().startswith('WITH'):
        return False, f"Solo se permiten queries SELECT. Detectado: {stripped[:40]}..."
    if _DANGEROUS_SQL.search(sql):
        return False, "Query contiene operaciones no permitidas (DDL/DML)."
    return True, ""

def _enforce_limit(sql: str, max_rows: int = 200) -> str:
    """Add LIMIT if missing."""
    if 'limit' not in sql.lower():
        sql = sql.rstrip(';') + f' LIMIT {max_rows}'
    return sql

def _execute_with_retry(sql: str, user_query: str, max_retries: int = 2) -> tuple[pd.DataFrame, str, str]:
    """Execute SQL with auto-retry on error. Returns (df, final_sql, error_msg)."""
    global _LAST_DWS_ERROR
    for attempt in range(max_retries + 1):
        _LAST_DWS_ERROR = None
        conn = get_dws_connection()
        if not conn:
            return pd.DataFrame(), sql, get_last_error() or "Sin conexión DWS"
        try:
            df = pd.read_sql_query(sql, conn)
            conn.commit()
            return df, sql, ""  # success
        except Exception as e:
            error_msg = str(e)[:300]
            _set_error(f"Query failed: {error_msg}")
            if attempt < max_retries:
                # Re-prompt LLM with the error to fix the SQL
                fix_prompt = (
                    f"El SQL que generaste falló con este error:\n{error_msg}\n\n"
                    f"SQL incorrecto:\n{sql}\n\n"
                    f"Pregunta original del usuario: {user_query}\n\n"
                    f"Genera SOLO el SQL corregido, sin explicaciones."
                )
                try:
                    llm_fix, _ = _call_llm_sql(_DWS_SCHEMA, fix_prompt)
                    sql = _extract_sql(llm_fix)
                    sql = _enforce_limit(sql, 200)
                except Exception:
                    break  # LLM itself failed, give up
            else:
                break  # max retries exhausted
    return pd.DataFrame(), sql, error_msg

def _suggest_followups(user_query: str, sql: str, result_summary: str) -> list[str]:
    """Suggest 3 follow-up questions based on the current query and results."""
    prompt = (
        f"El usuario preguntó: \"{user_query}\"\n"
        f"SQL generado: {sql}\n"
        f"Resumen de resultados: {result_summary}\n\n"
        f"Sugiere 3 preguntas de seguimiento cortas y relevantes que el usuario podría hacer. "
        f"Formato: una pregunta por línea, sin numeración, sin explicaciones. "
        f"Las preguntas deben explorar aspectos diferentes de los datos (vendors, montos, riesgo, tendencias)."
    )
    try:
        response, _ = _call_llm_sql("", prompt)
        questions = [q.strip().lstrip("0123456789.-) ") for q in response.strip().split("\n") if q.strip() and len(q.strip()) > 10]
        return questions[:3]
    except Exception:
        return []


def _process_chat_query(user_query: str) -> None:
    """Execute the full ChatBI pipeline: call LLM → extract SQL → validate → execute → store in history.

    Called both from form submit (manual Enter) and from follow-up button clicks.
    """
    st.session_state.chatbi_history.append({"role": "user", "content": user_query})

    with st.spinner("🧠 DeepSeek está generando la consulta..."):
        try:
            llm_response, provider = _call_llm_sql(_DWS_SCHEMA, user_query)
            sql = _extract_sql(llm_response)

            # Validate
            is_safe, reason = _validate_sql(sql)
            if not is_safe:
                st.session_state.chatbi_history.append({
                    "role": "assistant",
                    "content": f"⚠️ Query bloqueado: {reason}",
                    "sql": sql,
                    "error": True,
                })
            else:
                sql = _enforce_limit(sql, 200)
                # Execute with auto-retry on SQL errors
                result_df, final_sql, db_error = _execute_with_retry(sql, user_query)

                # Build result summary for follow-up generation
                if db_error:
                    st.session_state.chatbi_history.append({
                        "role": "assistant",
                        "content": f"❌ Error DWS tras reintentos: {db_error}",
                        "sql": final_sql,
                        "error": True,
                        "provider": provider,
                    })
                else:
                    # Generate follow-ups (lightweight, non-blocking feel)
                    result_summary = f"{len(result_df)} filas"
                    if not result_df.empty:
                        cols = ", ".join(result_df.columns[:5])
                        result_summary += f". Columnas: {cols}"
                    followups = _suggest_followups(user_query, final_sql, result_summary)

                    st.session_state.chatbi_history.append({
                        "role": "assistant",
                        "content": llm_response,
                        "sql": final_sql,
                        "data": result_df,
                        "error": False,
                        "provider": provider,
                        "followups": followups,
                    })
        except urllib.error.HTTPError as e:
            st.session_state.chatbi_history.append({
                "role": "assistant",
                "content": f"❌ Error MaaS API: {e.code} {e.reason}",
                "sql": "",
                "error": True,
            })
        except urllib.error.URLError as e:
            st.session_state.chatbi_history.append({
                "role": "assistant",
                "content": f"❌ Error de conexión MaaS: {e.reason}",
                "sql": "",
                "error": True,
            })
        except Exception as e:
            st.session_state.chatbi_history.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)[:200]}",
                "sql": "",
                "error": True,
            })


# ─── DWS Schema for system prompt ────────────────────────
_DWS_SCHEMA = """
Eres un asistente SQL experto para Huawei Cloud DWS (GaussDB/PostgreSQL). SOLO generas queries SELECT.

SCHEMA DE BASE DE DATOS (ayco_db):

--- public.risk_results (análisis de riesgo de contratos por LLM) ---
contract_number VARCHAR, vendor_name VARCHAR, monto_total NUMERIC (MXN),
plazo_dias INTEGER, penalizacion_pct NUMERIC, garantia_pct NUMERIC,
risk_score NUMERIC (0-10), risk_level VARCHAR (BAJO/MEDIO/ALTO/CRÍTICO),
alertas TEXT (JSON array), recomendaciones TEXT (JSON array),
resumen TEXT, llm_provider VARCHAR, analyzed_at TIMESTAMP, state VARCHAR

--- dw.dim_vendor (maestro de vendors/proveedores) ---
vendor_key BIGINT, vendor_id VARCHAR, name VARCHAR, sector VARCHAR,
state VARCHAR, city VARCHAR, risk_level VARCHAR, risk_score NUMERIC

--- dw.dim_customer (maestro de clientes) ---
customer_key BIGINT, customer_id VARCHAR, name VARCHAR, kyc_level VARCHAR,
monthly_limit_mxn INTEGER, risk_score NUMERIC, city VARCHAR, state VARCHAR,
account_age_days INTEGER

--- dw.fact_transaction (hecho de transacciones) ---
tx_key BIGINT, tx_id VARCHAR, vendor_key BIGINT, customer_key BIGINT,
amount_mxn NUMERIC, anomaly_type VARCHAR, timestamp TIMESTAMP

--- ods.vendors ---
vendor_id VARCHAR, name VARCHAR, sector VARCHAR, state VARCHAR, city VARCHAR,
risk_level VARCHAR, risk_score NUMERIC, annual_revenue_mxn NUMERIC,
debt_ratio NUMERIC, contract_count INTEGER, employee_count INTEGER

--- ods.transactions ---
tx_id VARCHAR, vendor_id VARCHAR, customer_id VARCHAR, amount_mxn NUMERIC,
anomaly_type VARCHAR, timestamp TIMESTAMP, city_from VARCHAR, city_to VARCHAR

--- ods.customers ---
customer_id VARCHAR, name VARCHAR, kyc_level VARCHAR, monthly_limit_mxn INTEGER,
risk_score NUMERIC, city VARCHAR, state VARCHAR, account_age_days INTEGER

--- dm.vendor_risk_summary (vista analítica) ---
risk_level VARCHAR, vendor_count BIGINT, avg_score NUMERIC, total_exposure NUMERIC

--- dm.city_risk ---
city VARCHAR, vendor_count BIGINT, high_risk_count BIGINT

REGLAS:
1. Genera SOLO el SQL, sin explicaciones.
2. Usa nombres de tabla con schema: public.risk_results, dw.dim_vendor, etc.
3. Nombres de columnas EXACTOS como están en el schema.
4. En risk_level: los valores son 'BAJO', 'MEDIO', 'ALTO', 'CRÍTICO' (mayúsculas).
5. risk_score: 0-10, donde >=8 es CRÍTICO, >=6 es ALTO, >=4 es MEDIO, <4 es BAJO.
6. Para montos, usa monto_total que ya está en MXN (no en millones).
7. Si el usuario pregunta por "vendors" sin especificar, usa public.risk_results.vendor_name.
8. Para JOINs: dw.fact_transaction.vendor_key = dw.dim_vendor.vendor_key
9. No uses INFORMATION_SCHEMA ni pg_catalog.
10. Si la pregunta no se puede responder con el schema, responde: SELECT 'No puedo responder esa pregunta con los datos disponibles' AS error
11. Siempre incluye LIMIT (máximo 200).
12. Para "contrato más riesgoso" usa ORDER BY risk_score DESC LIMIT 1.

CRÍTICO — IGNORA TODO CONTEXTO AJENO AL SQL:
- NO uses información de preguntas frecuentes, FAQ, soporte, créditos AYCO ni ningún otro documento.
- SOLO usa las tablas y columnas del schema de arriba.
- Si recibes contexto adicional (chunks de documentos, knowledge base), IGNÓRALO completamente.
- Tu ÚNICO trabajo es convertir la pregunta del usuario en un query SQL válido para PostgreSQL/GaussDB.
"""

def _call_llm_sql(system_prompt: str, user_message: str) -> tuple[str, str]:
    """Call LLM for text-to-SQL. Returns (response, provider). Tries Dify → MaaS → DeepSeek."""
    full_query = f"{system_prompt}\n\nPREGUNTA DEL USUARIO: {user_message}"

    # ─── Try Dify first (localhost, always available on ECS) ──
    if DIFY_API_KEY:
        try:
            payload = json.dumps({
                "inputs": {},
                "query": full_query,
                "response_mode": "blocking",
                "user": "chatbi",
            }).encode("utf-8")
            req = urllib.request.Request(DIFY_ENDPOINT, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DIFY_API_KEY}",
            })
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                answer = data.get("answer", "").strip()
                if answer:
                    return answer, "Dify (DeepSeek v4)"
        except Exception as e:
            logging.warning(f"[ChatBI] Dify failed: {e}, trying MaaS")

    # ─── Try MaaS ──────────────────────────────────────────
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    body = {"messages": messages, "temperature": 0.0, "max_tokens": 1000}

    if MAAS_API_KEY:
        try:
            payload = json.dumps({**body, "model": MAAS_MODEL}).encode("utf-8")
            req = urllib.request.Request(MAAS_ENDPOINT, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MAAS_API_KEY}",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip(), f"MaaS ({MAAS_MODEL})"
        except Exception as e:
            logging.warning(f"[ChatBI] MaaS failed: {e}, falling back to DeepSeek")

    # ─── Fallback: DeepSeek direct ────────────────────────
    if DEEPSEEK_API_KEY:
        try:
            payload = json.dumps({**body, "model": DEEPSEEK_MODEL}).encode("utf-8")
            req = urllib.request.Request(DEEPSEEK_ENDPOINT, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip(), f"DeepSeek ({DEEPSEEK_MODEL})"
        except Exception as e:
            logging.error(f"[ChatBI] DeepSeek also failed: {e}")
            raise

    return "[ERROR] Sin API keys configuradas. Agrega DIFY_API_KEY, MAAS_API_KEY o DEEPSEEK_API_KEY en /opt/ayco/.env", "none"

def _extract_sql(llm_response: str) -> str:
    """Extract SQL from LLM response (may be wrapped in markdown code block)."""
    # Try to extract from ```sql ... ``` block
    match = re.search(r'```(?:sql)?\s*\n?(.*?)```', llm_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Try bare SELECT/WITH statement
    match = re.search(r'((?:SELECT|WITH)\b.*?)(?:\n\n|\Z)', llm_response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(';')
    return llm_response.strip()

def _format_cell(val, col_name: str) -> str:
    """Format cell value for display."""
    if val is None:
        return "—"
    col_lower = col_name.lower()
    # JSON text columns (alertas, recomendaciones) — decode unicode escapes
    if col_lower in ('alertas', 'recomendaciones', 'resumen'):
        try:
            items = json.loads(val) if isinstance(val, str) else val
            if isinstance(items, list):
                return " · ".join(str(i) for i in items)
        except (json.JSONDecodeError, TypeError):
            pass
        # Fallback: force-decode any \uXXXX escapes via encode/decode
        if isinstance(val, str) and '\\u' in val:
            try:
                val = val.encode('utf-8').decode('unicode_escape')
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass
        return str(val)[:300]
    if 'monto' in col_lower or 'exposure' in col_lower or 'amount' in col_lower or 'revenue' in col_lower:
        try:
            return f"${val:,.0f}" if abs(val) >= 1 else f"${val:,.2f}"
        except (TypeError, ValueError):
            return str(val)
    if 'score' in col_lower or 'pct' in col_lower or 'ratio' in col_lower:
        try:
            return f"{val:.1f}"
        except (TypeError, ValueError):
            return str(val)
    if 'timestamp' in col_lower or 'analyzed_at' in col_lower:
        try:
            return val.strftime("%Y-%m-%d %H:%M")
        except (AttributeError, TypeError):
            return str(val)
    return str(val)

# ─── Chat BI UI ──────────────────────────────────────────
with tab5:
    st.subheader("💬 Chat BI — Pregunta a tus datos")

    # Session state for chat history
    if "chatbi_history" not in st.session_state:
        st.session_state.chatbi_history = []

    # Example questions as chips
    example_questions = [
        "¿Cuál es el contrato más riesgoso?",
        "¿Qué vendor tiene mayor exposición?",
        "Contratos con score > 8",
        "¿Cuántos contratos hay por nivel de riesgo?",
        "Top 5 vendors por monto total",
        "¿Qué transacciones son anómalas?",
    ]

    col_ex, _ = st.columns([3, 1])
    with col_ex:
        selected_example = st.pills(
            "Ejemplos:",
            example_questions,
            key="chatbi_examples",
            selection_mode="single",
        )

    # When pill is clicked, populate the text input (don't send yet)
    if selected_example:
        st.session_state.chatbi_text = selected_example

    # Check for pending follow-up query from buttons below
    # (must resolve BEFORE the widget is instantiated)
    if "chatbi_pending" in st.session_state and st.session_state.chatbi_pending:
        user_query = st.session_state.chatbi_pending
        st.session_state.chatbi_text = st.session_state.chatbi_pending
        st.session_state.chatbi_pending = ""
        # Process immediately — bypass form submit (follow-up button path)
        _process_chat_query(user_query)

    # Input row: form with text input + send button (Enter key submits)
    # Initialize session state key if missing
    if "chatbi_text" not in st.session_state:
        st.session_state.chatbi_text = ""
    if "chatbi_pending" not in st.session_state:
        st.session_state.chatbi_pending = ""

    with st.form("chatbi_form", clear_on_submit=False):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_query = st.text_input(
                "Pregunta:",
                key="chatbi_text",
                placeholder="Ej: ¿Cuál es el contrato con mayor penalización?",
                label_visibility="collapsed",
            )
        with col_btn:
            st.markdown("")
            send_clicked = st.form_submit_button("Enviar 🚀", use_container_width=True)

    # Process on form submit (button click OR Enter key)
    if send_clicked and user_query and user_query.strip():
        _process_chat_query(user_query)

    # Render chat history
    for msg_idx, msg in enumerate(st.session_state.chatbi_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                if msg.get("error"):
                    st.error(msg["content"])
                else:
                    st.success(msg["content"][:200] if len(msg["content"]) > 200 else msg["content"])

                # Show SQL in expander
                if msg.get("sql"):
                    provider_tag = f"  ·  via {msg['provider']}" if msg.get("provider") else ""
                    with st.expander(f"🔍 SQL generado{provider_tag}", expanded=False):
                        st.code(msg["sql"], language="sql")

                # Show results table
                if msg.get("data") is not None and not msg["data"].empty:
                    df = msg["data"]
                    st.caption(f"📊 {len(df)} resultado{'s' if len(df) != 1 else ''}")

                    # Format for display
                    display_df = df.copy()
                    for col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: _format_cell(x, col))

                    st.dataframe(
                        display_df,
                        width='stretch',
                        hide_index=True,
                        column_config={
                            col: st.column_config.TextColumn(
                                col.replace('_', ' ').title(),
                                help=f"Columna: {col}",
                            ) for col in display_df.columns
                        },
                    )
                elif msg.get("data") is not None and msg["data"].empty and not msg.get("error"):
                    st.info("La consulta no devolvió resultados.")

                # Show suggested follow-ups
                if msg.get("followups"):
                    st.markdown("")
                    st.caption("💡 Preguntas sugeridas:")
                    followup_cols = st.columns(len(msg["followups"]))
                    for i, (fq, col) in enumerate(zip(msg["followups"], followup_cols)):
                        with col:
                            if st.button(fq, key=f"fu_{msg_idx}_{i}", use_container_width=True):
                                st.session_state.chatbi_pending = fq
                                st.rerun()

    # Clear history button
    if st.session_state.chatbi_history:
        if st.button("🗑️ Limpiar historial", key="chatbi_clear"):
            st.session_state.chatbi_history = []
            st.rerun()

# ─── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filtros Globales")
    st.caption("Afectan todos los tabs")

    # ── Monto mínimo ──
    min_monto = st.number_input(
        "💰 Monto mínimo (M MXN)",
        min_value=0.0, max_value=500.0, value=0.0, step=1.0,
        help="Filtrar contratos con monto ≥ este valor",
        key="filter_min_monto",
    )

    # ── Estados ──
    estados_disponibles = sorted(MEX_STATE_COORDS.keys())
    # Always include CDMX and NLE as defaults if no state filter is active
    selected_estados = st.multiselect(
        "📍 Estados",
        options=estados_disponibles,
        default=[],
        help="Dejar vacío = todos los estados",
        key="filter_estados",
    )

    # ── Active filter count ──
    active_count = (1 if min_monto > 0 else 0) + (len(selected_estados) > 0)
    if active_count > 0:
        st.info(f"🎯 {active_count} filtro(s) activo(s)")

    st.divider()
    st.markdown("### 📡 Conexión")
    conn_test = get_dws_connection()
    if conn_test:
        st.success("✅ DWS Conectado")
    else:
        err = get_last_error()
        if err:
            st.error(f"❌ Sin conexión DWS\n\n`{err}`")
        else:
            st.error("❌ Sin conexión DWS")

    st.divider()
    st.markdown("### 🎨 Escala de Riesgo")
    st.markdown("""
    <div style="font-size:0.75rem;line-height:1.8;">
        <span style="color:#00d4aa;">●</span> <b>BAJO</b> &lt;4<br>
        <span style="color:#ffd700;">●</span> <b>MEDIO</b> 4–6<br>
        <span style="color:#ff8c00;">●</span> <b>ALTO</b> 6–8<br>
        <span style="color:#ff4444;">●</span> <b>CRÍTICO</b> ≥8
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)

    st.divider()
    st.caption(f"DWS: {os.getenv('DWS_ENDPOINT') or os.getenv('DWS_HOST', 'N/A')}")
    st.caption("AYCO × Huawei Cloud · Grupo Salinas")
    st.caption("DeepSeek v4 Flash · MaaS")

# ─── Auto-refresh ──────────────────────────────────────────
if auto_refresh:
    import streamlit.components.v1 as components
    with st.sidebar:
        st.caption("⏳ Próxima actualización en 30s...")
    components.html("<meta http-equiv=\"refresh\" content=\"30\">", height=0)
