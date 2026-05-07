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
import base64
from datetime import datetime

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main { background-color: #0a0e17; }
    .stApp { background: #0a0e17; }
    h1, h2, h3, h4, .metric-label, p, span, div { color: #e8eaed; }
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
        border: 1px solid #1e2a3a; border-radius: 16px; padding: 1.25rem;
    }
    .kpi-critical { border-left: 3px solid #ff4444; }
    .kpi-warning { border-left: 3px solid #ff8c00; }
    .kpi-ok { border-left: 3px solid #00d4aa; }
    .plot-container { border-radius: 12px; overflow: hidden; }
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
        )
    except Exception:
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
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_kpi_data():
    return run_query("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT vendor_name) as vendors,
            SUM(CASE WHEN risk_level='CRITICO' THEN 1 ELSE 0 END) as criticos,
            SUM(CASE WHEN risk_level='ALTO' THEN 1 ELSE 0 END) as altos,
            SUM(CASE WHEN garantia_pct=0 THEN 1 ELSE 0 END) as sin_garantia,
            ROUND(AVG(risk_score)::numeric, 1) as avg_score,
            ROUND(SUM(monto_total)::numeric, 0) as exposure,
            ROUND(AVG(plazo_dias)::numeric, 0) as avg_plazo,
            ROUND((SUM(CASE WHEN risk_level IN ('CRITICO','ALTO') THEN monto_total ELSE 0 END) 
                   / NULLIF(SUM(monto_total),0) * 100)::numeric, 1) as pct_exposure_risk
        FROM risk_results
    """)

@st.cache_data(ttl=60)
def load_risk_distribution():
    return run_query("""
        SELECT risk_level, COUNT(*) as count, 
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as exposure_mxn_m
        FROM risk_results 
        GROUP BY risk_level 
        ORDER BY MIN(risk_score)
    """)

@st.cache_data(ttl=60)
def load_vendor_data():
    return run_query("""
        SELECT vendor_name, COUNT(*) as contracts,
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as total_mxn_m,
               MAX(risk_level) as max_risk_level
        FROM risk_results 
        GROUP BY vendor_name 
        ORDER BY total_mxn_m DESC
        LIMIT 15
    """)

@st.cache_data(ttl=60)
def load_contract_detail():
    return run_query("""
        SELECT contract_number, vendor_name, risk_score, risk_level,
               monto_total/1e6 as mxn_m, plazo_dias, garantia_pct,
               alertas, recomendaciones, analyzed_at
        FROM risk_results 
        ORDER BY risk_score DESC
    """)

@st.cache_data(ttl=60)
def load_scatter_data():
    return run_query("""
        SELECT contract_number, vendor_name, risk_score, risk_level,
               monto_total/1e6 as mxn_m, plazo_dias, garantia_pct
        FROM risk_results
    """)

@st.cache_data(ttl=300)
def load_geo_data():
    return run_query("""
        SELECT state, COUNT(*) as contracts,
               ROUND(AVG(risk_score)::numeric, 1) as avg_score,
               ROUND(SUM(monto_total)/1e6::numeric, 1) as exposure_mxn_m,
               SUM(CASE WHEN risk_level='CRITICO' THEN 1 ELSE 0 END) as criticos,
               SUM(CASE WHEN risk_level='ALTO' THEN 1 ELSE 0 END) as altos
        FROM risk_results
        WHERE state IS NOT NULL
        GROUP BY state
    """)

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
col1, col2 = st.columns([5, 1])
with col1:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">🛡️</span>
        <h1 style="margin:0;font-size:1.8rem;font-weight:700;color:#e8eaed;">AYCO Contract Risk Intelligence</h1>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="text-align:right;padding-top:0.5rem;">
        <span style="font-size:0.75rem;color:#8b95a5;">Huawei Cloud DWS</span><br>
        <span style="font-size:0.75rem;color:#8b95a5;">DeepSeek v4 · {datetime.now().strftime('%H:%M UTC')}</span>
    </div>
    """, unsafe_allow_html=True)

# ─── KPI Banner ───────────────────────────────────────────
kpi = load_kpi_data()
if not kpi.empty:
    r = kpi.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Contratos", int(r["total"]))
    c2.metric("Exposición", f"${r['exposure']/1e9:.2f}B", delta=f"${r['exposure']/1e6:.0f}M MXN")
    c3.metric("Score Promedio", f"{r['avg_score']}/10")
    c4, c5, c6 = st.columns(3)
    c4.metric("Críticos + Altos", f"{int(r['criticos'])+int(r['altos'])}/{int(r['total'])}",
              delta=f"{r['pct_exposure_risk']}% exposición en riesgo", delta_color="inverse")
    c5.metric("Sin Garantía", int(r["sin_garantia"]))
    c6.metric("Vendors", int(r["vendors"]), delta=f"Plazo prom. {int(r['avg_plazo'])}d")

# ═══════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📋 Contratos",
    "🏢 Vendors",
    "🔍 Análisis Profundo",
])

# ═══════════════════════════════════════════════
#  TAB 1: OVERVIEW
# ═══════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        # Treemap: exposición por vendor coloreado por riesgo
        st.subheader("💰 Exposición por Vendor — Treemap")
        vdata = load_vendor_data()
        if not vdata.empty:
            fig_tree = px.treemap(
                vdata,
                path=["vendor_name"],
                values="total_mxn_m",
                color="avg_score",
                color_continuous_scale=["#00d4aa", "#ffd700", "#ff8c00", "#ff4444"],
                range_color=[1, 10],
                hover_data={"total_mxn_m": ":.1f", "avg_score": ":.1f", "contracts": True},
            )
            fig_tree.update_traces(
                texttemplate="<b>%{label}</b><br>$%{value:.1f}M",
                textposition="middle center",
                hovertemplate="<b>%{label}</b><br>Exposición: $%{customdata[0]:.1f}M<br>Score: %{customdata[1]:.1f}/10<br>Contratos: %{customdata[2]}<extra></extra>",
                textfont=dict(size=13, color="white"),
            )
            fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=420, paper_bgcolor=CHART_BG)
            st.plotly_chart(fig_tree, width='stretch', config={"displayModeBar": False})

    with col_right:
        # Donut + horizontal bars
        st.subheader("🎯 Distribución de Riesgo")
        dist = load_risk_distribution()
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
            fig_donut.add_annotation(text=f"<b>{int(kpi.iloc[0]['total'])}</b><br><span style='font-size:11px'>contratos</span>",
                                     x=0.5, y=0.5, showarrow=False, font=dict(size=22, color=TEXT_COLOR))
            fig_donut.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor=CHART_BG, showlegend=False)
            st.plotly_chart(fig_donut, width='stretch', config={"displayModeBar": False})

    # Geo map: Mexico risk by state
    st.subheader("🗺️  Mapa de Riesgo por Estado — México")
    geo_data = load_geo_data()
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

    # Bottom row: Risk score distribution histogram + scatter
    col_bl, col_br = st.columns([1, 1.3])
    with col_bl:
        st.subheader("📈 Distribución de Risk Scores")
        scatter_data = load_scatter_data()
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

# ═══════════════════════════════════════════════
#  TAB 2: CONTRATOS
# ═══════════════════════════════════════════════
with tab2:
    contracts = load_contract_detail()
    if not contracts.empty:
        # Filters
        filt_col1, filt_col2, filt_col3, filt_col4 = st.columns([2, 1.5, 1, 1])
        with filt_col1:
            search = st.text_input("🔍 Buscar vendor o contrato", placeholder="Ej: Constructora...", key="search_contracts")
        with filt_col2:
            risk_filter = st.multiselect("Nivel de Riesgo", options=RISK_ORDER, default=RISK_ORDER, key="risk_filter_contracts")
        with filt_col3:
            score_min = st.slider("Score Mínimo", 0.0, 10.0, 0.0, 0.5, key="score_min")
        with filt_col4:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(csv_download_link(contracts, "ayco_contracts.csv", "⬇ CSV"), unsafe_allow_html=True)

        # Apply filters
        filtered = contracts.copy()
        if search:
            mask = filtered["vendor_name"].str.contains(search, case=False, na=False)
            mask |= filtered["contract_number"].str.contains(search, case=False, na=False)
            filtered = filtered[mask]
        if risk_filter:
            filtered = filtered[filtered["risk_level"].isin(risk_filter)]
        if score_min > 0:
            filtered = filtered[filtered["risk_score"] >= score_min]

        # Summary line
        st.caption(f"Mostrando {len(filtered)} de {len(contracts)} contratos")

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
                        <span style="color:#e8eaed;font-size:0.85rem;">{row['alertas'] or 'Ninguna'}</span>
                    </div>
                    <div style="background:#0f1420;border:1px solid #1e2a3a;border-radius:12px;padding:1rem;">
                        <span style="color:#8b95a5;font-size:0.7rem;text-transform:uppercase;">Recomendaciones</span><br>
                        <span style="color:#e8eaed;font-size:0.85rem;">{row['recomendaciones'] or 'N/A'}</span>
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

# ═══════════════════════════════════════════════
#  TAB 3: VENDORS
# ═══════════════════════════════════════════════
with tab3:
    vendors = load_vendor_data()
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

# ═══════════════════════════════════════════════
#  TAB 4: ANÁLISIS PROFUNDO
# ═══════════════════════════════════════════════
with tab4:
    st.subheader("🔬 Factores de Riesgo — Radar View")

    # Aggregate risk factors across all contracts
    risk_dist = load_risk_distribution()
    scatter_data = load_scatter_data()

    if not risk_dist.empty:
        # Radar chart: risk distribution by level (count + exposure)
        categories = risk_dist["risk_level"].tolist()
        counts = risk_dist["count"].tolist()
        exposures = risk_dist["exposure_mxn_m"].tolist()

        # Normalize for radar
        max_count = max(counts) if counts else 1
        max_exp = max(exposures) if exposures else 1
        counts_norm = [c/max_count*10 for c in counts]
        exposures_norm = [e/max_exp*10 for e in exposures]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=counts_norm, theta=categories,
            fill='toself', name='Contratos', marker_color='#00d4aa',
            opacity=0.7, line=dict(width=2),
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=exposures_norm, theta=categories,
            fill='toself', name='Exposición ($)', marker_color='#ff8c00',
            opacity=0.5, line=dict(width=2),
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#0f1420",
                radialaxis=dict(visible=True, range=[0, 10], gridcolor=GRID_COLOR, showticklabels=False),
                angularaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(color=TEXT_COLOR, size=13)),
            ),
            paper_bgcolor=CHART_BG, height=350,
            margin=dict(t=30, b=10, l=10, r=10),
            legend=dict(font=dict(color=TEXT_COLOR), orientation="h", yanchor="bottom", y=1.1),
        )
        st.plotly_chart(fig_radar, width='stretch', config={"displayModeBar": False})

    # Sunburst / Hierarchical view
    if not scatter_data.empty and not risk_dist.empty:
        st.subheader("🌳 Jerarquía de Riesgo — Sunburst")
        # Simple hierarchy: Risk Level → Vendor
        sunburst_data = scatter_data.copy()
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

# ─── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Config")
    st.caption(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}")
    st.caption(f"DWS: {os.getenv('DWS_ENDPOINT') or os.getenv('DWS_HOST', 'N/A')}")

    st.divider()
    st.markdown("### 📡 Conexión")
    conn_test = get_dws_connection()
    if conn_test:
        st.success("✅ DWS Conectado")
    else:
        st.error("❌ Sin conexión DWS")

    st.divider()
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)

    st.divider()
    st.caption("AYCO × Huawei Cloud · Grupo Salinas")
    st.caption("DeepSeek v4 Flash · MaaS")

# ─── Auto-refresh ──────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()
