"""AYCO Contract Risk Dashboard — DWS Live Data.
Enhanced with Data Quality + Governance tabs for Demo 2.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import psycopg2
import os

st.set_page_config(page_title="AYCO Risk Intelligence", page_icon="🛡️", layout="wide")

# ── DWS Connection ──
DWS_HOST = os.getenv("DWS_HOST", "46.250.161.25")
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


# ── Branding ──
st.markdown("""
<style>
    .main { background-color: #0a0e17; }
    .stApp { background: linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%); }
    h1, h2, h3, h4, .stMetric label, p, span { color: #e8eaed !important; }
    div[data-testid="stMetricValue"] { color: #00d4aa !important; font-size: 1.8rem !important; }
    .stDataFrame { border-radius: 8px; }
    div[data-testid="stTabs"] button { color: #e8eaed !important; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: #00d4aa !important; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──
with st.spinner("Consultando DWS..."):
    df = query_dws("""
        SELECT contract_number, vendor_name, monto_total, plazo_dias,
               penalizacion_pct, garantia_pct, risk_score, risk_level,
               alertas, recomendaciones, resumen, llm_provider, analyzed_at
        FROM risk_results ORDER BY risk_score DESC
    """)

if df.empty:
    st.warning("No se pudieron cargar datos de DWS. Verifica conectividad.")
    st.stop()

# ── Header ──
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🛡️ AYCO Contract Risk Intelligence")
    st.caption(f"DWS Live @ {DWS_HOST}:{DWS_PORT} • {datetime.now().strftime('%H:%M CST')} • {len(df)} contratos")
with col2:
    auto = st.checkbox("Auto-refresh (60s)", value=False)
    if auto:
        st.rerun()

# ── KPI Row ──
k1, k2, k3, k4 = st.columns(4)
criticos = len(df[df["risk_level"].str.upper().isin(["CRITICO", "CRÍTICO"])])
altos = len(df[df["risk_level"].str.upper().isin(["ALTO"])])
monto_total = df["monto_total"].sum()

k1.metric("Contratos Analizados", len(df))
k2.metric("Avg Risk Score", f"{df['risk_score'].mean():.1f}/10",
          delta=f"{criticos} críticos", delta_color="inverse")
k3.metric("Exposición Total", f"${monto_total/1e6:.1f}M MXN")
k4.metric("Alertas Activas", criticos + altos,
          delta=f"{criticos} críticas", delta_color="inverse")

# ── Tabs ──
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Risk Distribution",
    "📋 Vendor Exposure",
    "🔍 Contract Detail",
    "✅ Data Quality",
    "🏗️ Governance"
])

# ────────────────────────────────────────
# TAB 1: Risk Distribution
# ────────────────────────────────────────
with tab1:
    col_left, col_right = st.columns(2)
    with col_left:
        fig = px.pie(df, names="risk_level", values="monto_total",
                     color="risk_level",
                     color_discrete_map={
                         "Bajo": "#00d4aa", "BAJO": "#00d4aa",
                         "Medio": "#ffd700", "MEDIO": "#ffd700",
                         "Alto": "#ff8c00", "ALTO": "#ff8c00",
                         "Crítico": "#ff4444", "CRITICO": "#ff4444"
                     },
                     title="Distribución de Riesgo por Monto")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
        st.plotly_chart(fig, use_container_width=True)
    with col_right:
        fig2 = px.histogram(df, x="risk_score", nbins=10, color="risk_level",
                            color_discrete_map={
                                "Bajo": "#00d4aa", "BAJO": "#00d4aa",
                                "Medio": "#ffd700", "MEDIO": "#ffd700",
                                "Alto": "#ff8c00", "ALTO": "#ff8c00",
                                "Crítico": "#ff4444", "CRITICO": "#ff4444"
                            },
                            title="Distribución de Risk Scores")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
        st.plotly_chart(fig2, use_container_width=True)

    # Scatter: penalización vs garantía
    fig3 = px.scatter(df, x="penalizacion_pct", y="garantia_pct",
                      size="monto_total", color="risk_level",
                      hover_name="vendor_name",
                      hover_data=["contract_number", "risk_score", "monto_total"],
                      color_discrete_map={
                          "Bajo": "#00d4aa", "BAJO": "#00d4aa",
                          "Medio": "#ffd700", "MEDIO": "#ffd700",
                          "Alto": "#ff8c00", "ALTO": "#ff8c00",
                          "Crítico": "#ff4444", "CRITICO": "#ff4444"
                      },
                      title="Penalización vs Garantía (tamaño = monto)")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
    st.plotly_chart(fig3, use_container_width=True)

# ────────────────────────────────────────
# TAB 2: Vendor Exposure
# ────────────────────────────────────────
with tab2:
    # Top vendors by amount
    top = df.nlargest(10, "monto_total").sort_values("monto_total")
    fig3 = px.bar(top, x="monto_total", y="vendor_name", color="risk_level",
                  orientation="h",
                  color_discrete_map={
                      "Bajo": "#00d4aa", "BAJO": "#00d4aa",
                      "Medio": "#ffd700", "MEDIO": "#ffd700",
                      "Alto": "#ff8c00", "ALTO": "#ff8c00",
                      "Crítico": "#ff4444", "CRITICO": "#ff4444"
                  },
                  title="Top 10 Proveedores por Exposición")
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
    st.plotly_chart(fig3, use_container_width=True)

    # DM summary from DWS
    with st.spinner("Consultando dm.contract_vendor_risk_summary..."):
        dm_summary = query_dws("SELECT * FROM dm.contract_vendor_risk_summary ORDER BY avg_risk DESC")
    if not dm_summary.empty:
        st.subheader("Vista Analítica — dm.contract_vendor_risk_summary")
        st.dataframe(dm_summary, use_container_width=True, hide_index=True,
                     column_config={
                         "vendor_name": "Proveedor",
                         "contracts": "Contratos",
                         "avg_risk": st.column_config.NumberColumn("Risk Promedio", format="%.1f"),
                         "highest_risk_level": "Nivel Máximo",
                         "total_exposure": st.column_config.NumberColumn("Exposición MXN", format="$%.0f"),
                     })

# ────────────────────────────────────────
# TAB 3: Contract Detail
# ────────────────────────────────────────
with tab3:
    st.subheader("Detalle de Contratos")
    selected = st.selectbox("Seleccionar contrato", df["contract_number"].tolist())
    if selected:
        row = df[df["contract_number"] == selected].iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk Score", f"{row['risk_score']}/10")
        c2.metric("Monto", f"${row['monto_total']:,.0f}")
        c3.metric("Plazo", f"{row['plazo_dias']} días")

        st.markdown(f"**Proveedor:** {row['vendor_name']}")
        st.markdown(f"**Nivel de Riesgo:** {row['risk_level']}")
        st.markdown(f"**Penalización:** {row['penalizacion_pct']}% | **Garantía:** {row['garantia_pct']}%")
        st.markdown(f"**Alertas:** {row['alertas']}")
        st.markdown(f"**Recomendaciones:** {row['recomendaciones']}")
        st.markdown(f"**Resumen:** {row['resumen']}")
        st.caption(f"Analizado por {row['llm_provider']} el {row['analyzed_at']}")

    st.divider()
    st.dataframe(df.sort_values("risk_score", ascending=False),
                 use_container_width=True, hide_index=True,
                 column_config={
                     "contract_number": "Contrato",
                     "vendor_name": "Proveedor",
                     "monto_total": st.column_config.NumberColumn("Monto MXN", format="$%,.0f"),
                     "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=10, format="%.1f"),
                     "risk_level": "Nivel",
                     "plazo_dias": "Plazo (días)",
                     "penalizacion_pct": st.column_config.NumberColumn("Penalización %", format="%.1f%%"),
                     "garantia_pct": st.column_config.NumberColumn("Garantía %", format="%.1f%%"),
                     "llm_provider": "LLM",
                     "analyzed_at": "Analizado",
                 })

# ────────────────────────────────────────
# TAB 4: Data Quality
# ────────────────────────────────────────
with tab4:
    st.subheader("✅ Métricas de Calidad de Datos")
    st.caption("Validaciones ejecutadas en vivo contra DWS — capa ODS")

    # Completeness
    with st.spinner("Validando completitud..."):
        completeness = query_dws("""
            SELECT
              COUNT(*) AS total,
              COUNT(contract_number) AS contract_number,
              COUNT(vendor_name) AS vendor_name,
              COUNT(monto_total) AS monto_total,
              COUNT(risk_score) AS risk_score,
              COUNT(risk_level) AS risk_level,
              COUNT(alertas) AS alertas,
              COUNT(recomendaciones) AS recomendaciones
            FROM risk_results
        """)

    if not completeness.empty:
        row = completeness.iloc[0]
        total = row["total"]
        fields = ["contract_number", "vendor_name", "monto_total", "risk_score", "risk_level", "alertas", "recomendaciones"]
        comp_data = []
        for f in fields:
            filled = row[f]
            pct = (filled / total * 100) if total > 0 else 0
            comp_data.append({"Campo": f, "Llenos": int(filled), "Vacíos": int(total - filled), "Completitud %": round(pct, 1)})

        comp_df = pd.DataFrame(comp_data)

        col_left, col_right = st.columns([2, 1])
        with col_left:
            fig_comp = px.bar(comp_df, x="Campo", y="Completitud %",
                              color="Completitud %",
                              color_continuous_scale=["#ff4444", "#ffd700", "#00d4aa"],
                              range_color=[90, 100],
                              title="Completitud por Campo")
            fig_comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
            st.plotly_chart(fig_comp, use_container_width=True)
        with col_right:
            avg_comp = comp_df["Completitud %"].mean()
            st.metric("Completitud Promedio", f"{avg_comp:.1f}%")
            st.metric("Campos 100%", f"{len(comp_df[comp_df['Completitud %'] == 100])}/{len(comp_df)}")

    # Consistency checks
    st.divider()
    st.subheader("Validaciones de Consistencia")

    checks = [
        ("Scores en rango [0, 10]", "SELECT COUNT(*) FROM risk_results WHERE risk_score BETWEEN 0 AND 10"),
        ("Scores fuera de rango", "SELECT COUNT(*) FROM risk_results WHERE risk_score < 0 OR risk_score > 10"),
        ("Duplicados por contract_number", "SELECT COUNT(*) - COUNT(DISTINCT contract_number) FROM risk_results"),
        ("Montos positivos", "SELECT COUNT(*) FROM risk_results WHERE monto_total > 0"),
        ("Plazo > 0 días", "SELECT COUNT(*) FROM risk_results WHERE plazo_dias > 0"),
        ("Proveedor no vacío", "SELECT COUNT(*) FROM risk_results WHERE vendor_name IS NOT NULL AND vendor_name != ''"),
    ]

    check_results = []
    for label, sql in checks:
        result = query_dws(sql)
        val = int(result.iloc[0, 0]) if not result.empty else 0
        if "fuera" in label.lower() or "duplicados" in label.lower():
            status = "✅ PASS" if val == 0 else f"⚠️ {val} encontrados"
        else:
            status = "✅ PASS" if val > 0 else "❌ FAIL"
        check_results.append({"Validación": label, "Resultado": val, "Estado": status})

    st.dataframe(pd.DataFrame(check_results), use_container_width=True, hide_index=True)

    # Freshness
    st.divider()
    with st.spinner("Verificando frescura de datos..."):
        freshness = query_dws("""
            SELECT
              MIN(analyzed_at) AS primer_analisis,
              MAX(analyzed_at) AS ultimo_analisis,
              COUNT(*) AS total
            FROM risk_results
        """)
    if not freshness.empty:
        fr = freshness.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Primer Análisis", str(fr["primer_analisis"])[:19] if fr["primer_analisis"] else "N/A")
        c2.metric("Último Análisis", str(fr["ultimo_analisis"])[:19] if fr["ultimo_analisis"] else "N/A")
        c3.metric("Total Registros", int(fr["total"]))

# ────────────────────────────────────────
# TAB 5: Governance — Layered Architecture
# ────────────────────────────────────────
with tab5:
    st.subheader("🏗️ Arquitectura en Capas — ODS → DW → DM")
    st.caption("Los datos 'maduran' de crudos a analíticos. Cada capa agrega validación y transformación.")

    # ODS layer
    st.markdown("### 📥 Capa ODS — Datos Crudos")
    with st.spinner("Consultando ODS..."):
        ods_vendors = query_dws("SELECT vendor_id, name, state, sector, risk_score, risk_level FROM ods.vendors LIMIT 10")
    if not ods_vendors.empty:
        st.dataframe(ods_vendors, use_container_width=True, hide_index=True)
        ods_count = query_dws("SELECT 'vendors' AS tabla, COUNT(*) AS registros FROM ods.vendors UNION ALL SELECT 'customers', COUNT(*) FROM ods.customers UNION ALL SELECT 'transactions', COUNT(*) FROM ods.transactions")
        if not ods_count.empty:
            st.caption(f"Registros ODS: {', '.join([f'{r.tabla}: {r.registros}' for _, r in ods_count.iterrows()])}")

    # DW layer
    st.markdown("### 🔄 Capa DW — Esquema Estrella")
    with st.spinner("Consultando DW..."):
        dw_vendors = query_dws("SELECT vendor_key, vendor_id, name, state, sector, risk_score, risk_level FROM dw.dim_vendor LIMIT 10")
    if not dw_vendors.empty:
        st.dataframe(dw_vendors, use_container_width=True, hide_index=True)
        dw_tables = query_dws("""
            SELECT 'dim_vendor' AS tabla, COUNT(*) AS registros FROM dw.dim_vendor
            UNION ALL SELECT 'dim_customer', COUNT(*) FROM dw.dim_customer
            UNION ALL SELECT 'fact_transaction', COUNT(*) FROM dw.fact_transaction
        """)
        if not dw_tables.empty:
            st.caption(f"Registros DW: {', '.join([f'{r.tabla}: {r.registros}' for _, r in dw_tables.iterrows()])}")

    # DM layer
    st.markdown("### 📈 Capa DM — Vistas Analíticas")
    with st.spinner("Consultando DM..."):
        dm_city = query_dws("SELECT * FROM dm.city_risk ORDER BY avg_risk DESC LIMIT 10")
    if not dm_city.empty:
        fig_city = px.bar(dm_city, x="city", y="avg_risk", color="avg_risk",
                          color_continuous_scale=["#00d4aa", "#ffd700", "#ff4444"],
                          title="Risk Promedio por Ciudad (dm.city_risk)")
        fig_city.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
        st.plotly_chart(fig_city, use_container_width=True)

    # Comparison
    st.divider()
    st.markdown("### 🔍 Comparación ODS vs DW vs DM")
    comp_data = []
    for schema, tables in [("ods", ["vendors", "customers", "transactions"]),
                           ("dw", ["dim_vendor", "dim_customer", "fact_transaction"]),
                           ("dm", ["contract_vendor_risk_summary", "vendor_risk_summary", "city_risk", "anomaly_summary"])]:
        for t in tables:
            r = query_dws(f"SELECT COUNT(*) AS cnt FROM {schema}.{t}")
            cnt = int(r.iloc[0, 0]) if not r.empty else 0
            comp_data.append({"Schema": schema, "Tabla": t, "Registros": cnt})

    comp_df = pd.DataFrame(comp_data)
    fig_comp = px.bar(comp_df, x="Tabla", y="Registros", color="Schema",
                      color_discrete_map={"ods": "#ff8c00", "dw": "#ffd700", "dm": "#00d4aa"},
                      title="Registros por Capa y Tabla")
    fig_comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8eaed")
    st.plotly_chart(fig_comp, use_container_width=True)

# ── Footer ──
st.divider()
st.caption(f"Huawei Cloud la-north-2 • DWS @ {DWS_HOST}:{DWS_PORT} • {len(df)} contratos • AYCO Demo — Mayo 2026")
