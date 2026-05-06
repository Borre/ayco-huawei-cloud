"""
ayco-api: FastAPI backend for AYCO Contract Risk pipeline.

Endpoints:
  POST /api/upload          — Upload PDF → OBS → trigger FunctionGraph pipeline
  GET  /api/status/{job_id} — Poll OBS for pipeline results
  GET  /api/dws/quality     — Data quality metrics from DWS
  GET  /api/dws/layers      — ODS/DW/DM row counts from DWS
  GET  /api/dws/contracts   — Contract list from risk_results
  GET  /api/dashboard/kpis  — Live aggregate KPIs from DWS
  GET  /api/risk/breakdown  — Risk level distribution from DWS
  GET  /api/langfuse/metrics — Live traces/latency/tokens from Langfuse
  GET  /api/health          — Health check

Environment:
  HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY  — Huawei Cloud credentials
  DWS_HOST, DWS_PORT, DWS_DB, DWS_USER, DWS_PASSWORD  — DWS connection
  OBS_ENDPOINT, OBS_RAW_BUCKET, OBS_RESULTS_BUCKET    — OBS config
  LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST — Langfuse credentials
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone, timedelta

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from urllib.request import Request, urlopen
from base64 import b64encode

# ─── Config ────────────────────────────────────────────
OBS_ENDPOINT = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
OBS_RAW_BUCKET = os.environ.get("OBS_RAW_BUCKET", "ayco-contracts-raw")
OBS_RESULTS_BUCKET = os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results")
OBS_ACCESS_KEY = os.environ.get("HUAWEI_ACCESS_KEY", "")
OBS_SECRET_KEY = os.environ.get("HUAWEI_SECRET_KEY", "")

DWS_HOST = os.environ.get("DWS_HOST", "46.250.161.25")
DWS_PORT = int(os.environ.get("DWS_PORT", "8000"))
DWS_DB = os.environ.get("DWS_DB", "ayco_db")
DWS_USER = os.environ.get("DWS_USER", "ayco_admin")
DWS_PASSWORD = os.environ.get("DWS_PASSWORD", "")

LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://us.cloud.langfuse.com")

app = FastAPI(title="AYCO API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dify Chat Proxy config
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "http://101.44.185.139")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-Y8MxfRygyUWOAfyTlo1MQSJx")


# ─── OBS Client (lazy init) ────────────────────────────
_obs_client = None


def _get_obs():
    global _obs_client
    if _obs_client is None:
        from obs import ObsClient
        _obs_client = ObsClient(
            access_key_id=OBS_ACCESS_KEY,
            secret_access_key=OBS_SECRET_KEY,
            server=f"https://{OBS_ENDPOINT}",
        )
    return _obs_client


# ─── DWS Connection ────────────────────────────────────
def _get_dws_conn():
    return psycopg2.connect(
        host=DWS_HOST,
        port=DWS_PORT,
        dbname=DWS_DB,
        user=DWS_USER,
        password=DWS_PASSWORD,
        connect_timeout=5,
        options="-c client_encoding=UTF8",
    )


# ─── Health ────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.1.0",
    }


# ─── Dashboard KPIs (NEW — live from DWS) ──────────────
@app.get("/api/dashboard/kpis")
def dashboard_kpis():
    """Live aggregate KPIs: contracts, vendors, exposure, risk avg, critical count."""
    try:
        conn = _get_dws_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS total_contracts,
                    COUNT(DISTINCT vendor_name) AS unique_vendors,
                    COALESCE(SUM(CASE WHEN risk_level = 'CRITICO' THEN 1 ELSE 0 END), 0) AS critical_count,
                    COALESCE(SUM(CASE WHEN risk_level = 'ALTO' THEN 1 ELSE 0 END), 0) AS high_count,
                    COALESCE(SUM(monto_total), 0) AS total_exposure_mxn,
                    ROUND(COALESCE(AVG(risk_score), 0)::numeric, 1) AS avg_risk_score,
                    ROUND(COALESCE(MAX(risk_score), 0)::numeric, 1) AS max_risk_score
                FROM public.risk_results
            """)
            row = cur.fetchone()
        conn.close()

        return {
            "status": "ok",
            "source": "DWS — public.risk_results",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kpis": {
                "total_contracts": int(row[0]),
                "unique_vendors": int(row[1]),
                "critical_count": int(row[2]),
                "high_count": int(row[3]),
                "total_exposure_mxn": float(row[4]),
                "avg_risk_score": float(row[5]),
                "max_risk_score": float(row[6]),
                "reduction_pct": "99.6",  # static claim — "de 3 días a 4 min"
                "daily_cost_usd": 31,     # static claim — infra cost
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando DWS: {str(e)}",
        )


# ─── Risk Breakdown (NEW — live from DWS) ──────────────
@app.get("/api/risk/breakdown")
def risk_breakdown():
    """Risk level distribution with counts, avg scores, and total exposure."""
    try:
        conn = _get_dws_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    risk_level,
                    COUNT(*) AS count,
                    ROUND(AVG(risk_score)::numeric, 1) AS avg_score,
                    ROUND(SUM(monto_total)::numeric, 2) AS total_exposure_mxn
                FROM public.risk_results
                GROUP BY risk_level
                ORDER BY AVG(risk_score) DESC
            """)
            rows = cur.fetchall()

            # Overall risk gauge
            cur.execute("SELECT ROUND(AVG(risk_score)::numeric, 1) FROM public.risk_results")
            avg_row = cur.fetchone()
            global_avg = float(avg_row["round"]) if avg_row and avg_row["round"] else 0.0

        conn.close()

        breakdown = []
        risk_order = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}
        for r in rows:
            breakdown.append({
                "risk_level": r["risk_level"],
                "count": int(r["count"]),
                "avg_score": float(r["avg_score"]),
                "total_exposure_mxn": float(r["total_exposure_mxn"]),
            })
        breakdown.sort(key=lambda x: risk_order.get(x["risk_level"], 99))

        return {
            "status": "ok",
            "source": "DWS — public.risk_results",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "global_risk_score": global_avg,
            "breakdown": breakdown,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando DWS: {str(e)}",
        )


# ─── Langfuse Metrics (NEW — proxy to Langfuse API) ────
@app.get("/api/langfuse/metrics")
def langfuse_metrics():
    """Live Langfuse traces, latency, tokens, cost — today's data."""
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        return {
            "status": "unconfigured",
            "message": "LANGFUSE_PUBLIC_KEY y LANGFUSE_SECRET_KEY no están configurados en el servidor.",
            "traces_today": None,
            "avg_latency_ms": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
        }

    try:
        auth_str = b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()
        base_url = LANGFUSE_HOST.rstrip("/")

        # Get today's traces (first page for count + latest data)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        url = f"{base_url}/api/public/traces?page=1&limit=50&fromTimestamp={today}T00:00:00Z"

        req = Request(url)
        req.add_header("Authorization", f"Basic {auth_str}")
        req.add_header("Accept", "application/json")

        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        traces = data.get("data", [])
        meta = data.get("meta", {})

        # Calculate metrics from today's traces
        total_tokens = 0
        latencies = []
        for t in traces:
            usage = t.get("usage", {}) or {}
            total_tokens += (usage.get("input", 0) or 0) + (usage.get("output", 0) or 0)
            if t.get("latency"):
                latencies.append(t["latency"])

        traces_today = meta.get("totalItems", len(traces))
        avg_latency = round(sum(latencies) / len(latencies)) if latencies else 0
        estimated_cost = round(total_tokens * 0.000002, 4)  # ~$2/M tokens (DeepSeek pricing)

        return {
            "status": "ok",
            "source": f"Langfuse — {LANGFUSE_HOST}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "traces_today": traces_today,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
            "pagination_total": meta.get("totalItems", 0),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error consultando Langfuse: {str(e)}",
            "traces_today": None,
            "avg_latency_ms": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
        }


# ─── Upload ────────────────────────────────────────────
@app.post("/api/upload")
async def upload_contract(file: UploadFile = File(...)):
    """Receive PDF, upload to OBS raw bucket to trigger FunctionGraph pipeline."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    # Generate contract_number from filename + timestamp
    base = file.filename.rsplit(".", 1)[0].replace(" ", "-")[:40]
    ts = datetime.now(timezone.utc).strftime("%m%d%H%M")
    contract_number = f"AYCO-{ts}-{base[:20]}"
    obs_key = f"{contract_number}.pdf"

    content = await file.read()
    if len(content) > 15 * 1024 * 1024:  # 15MB limit
        raise HTTPException(status_code=400, detail="PDF excede 15MB máximo")

    try:
        obs = _get_obs()
        resp = obs.putContent(OBS_RAW_BUCKET, obs_key, content)
        if resp.status >= 300:
            raise HTTPException(
                status_code=502,
                detail=f"Error subiendo a OBS: HTTP {resp.status}",
            )
        obs.close()
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="OBS SDK no disponible en el servidor",
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error de conexión a OBS: {str(e)}",
        )

    return {
        "job_id": contract_number,
        "filename": file.filename,
        "obs_key": obs_key,
        "status": "uploaded",
        "message": "PDF subido a OBS. Pipeline FunctionGraph disparado.",
    }


# ─── Status (poll OBS for results) ─────────────────────
@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    """Poll OBS for pipeline results: risk_{job_id}.json."""
    result_key = f"risk_{job_id}.json"

    try:
        obs = _get_obs()
        resp = obs.getObject(OBS_RESULTS_BUCKET, result_key)
        if resp.status >= 300:
            obs.close()
            return {"job_id": job_id, "status": "processing",
                    "message": "Pipeline en progreso. El análisis toma ~5-8 segundos."}

        content = resp.body.buffer if hasattr(resp.body, 'buffer') else resp.body
        if isinstance(content, (bytes, bytearray)):
            result = json.loads(content.decode("utf-8"))
        else:
            result = json.loads(content)

        obs.close()

        return {
            "job_id": job_id,
            "status": "completed",
            "result": {
                "contract_number": result.get("contract_number", job_id),
                "risk_score": result.get("risk_score"),
                "risk_level": result.get("risk_level"),
                "alertas": result.get("alertas", []),
                "recomendaciones": result.get("recomendaciones", []),
                "resumen": result.get("resumen", ""),
                "llm_provider": result.get("llm_provider", "unknown"),
            },
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="OBS SDK no disponible")
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Pipeline en progreso...",
        }


# ─── DWS: Data Quality Metrics ─────────────────────────
@app.get("/api/dws/quality")
def dws_quality():
    """Real data quality metrics from DWS."""
    queries = {
        "completitud": """
            SELECT
                COUNT(*) AS total,
                COUNT(risk_score) AS con_score,
                COUNT(*) - COUNT(risk_score) AS sin_score,
                ROUND(COUNT(risk_score)::numeric / NULLIF(COUNT(*), 0) * 100, 1) AS pct
            FROM public.risk_results
        """,
        "consistencia": """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN risk_score BETWEEN 0 AND 10 THEN 1 ELSE 0 END) AS en_rango,
                SUM(CASE WHEN risk_score < 0 OR risk_score > 10 THEN 1 ELSE 0 END) AS fuera_rango
            FROM public.risk_results
        """,
        "duplicados": """
            SELECT COUNT(*) AS duplicados FROM (
                SELECT contract_number, COUNT(*) AS cnt
                FROM public.risk_results
                GROUP BY contract_number
                HAVING COUNT(*) > 1
            ) sub
        """,
        "constraints": """
            SELECT risk_level, COUNT(*)
            FROM public.risk_results
            WHERE risk_level NOT IN ('BAJO','MEDIO','ALTO','CRITICO')
            GROUP BY risk_level
        """,
    }

    try:
        conn = _get_dws_conn()
        results = {}
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            for name, sql in queries.items():
                cur.execute(sql)
                rows = cur.fetchall()
                results[name] = [dict(r) for r in rows]

        conn.close()
        return {
            "status": "ok",
            "source": "DWS — public.risk_results",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando DWS: {str(e)}",
        )


# ─── DWS: Layer Counts (ODS/DW/DM) ────────────────────
@app.get("/api/dws/layers")
def dws_layers():
    """Real row counts from ODS, DW, and DM schemas."""
    queries = {
        "ods": [
            ("vendors", "SELECT COUNT(*) FROM ods.vendors"),
            ("customers", "SELECT COUNT(*) FROM ods.customers"),
            ("transactions", "SELECT COUNT(*) FROM ods.transactions"),
        ],
        "dw": [
            ("dim_vendor", "SELECT COUNT(*) FROM dw.dim_vendor"),
            ("dim_customer", "SELECT COUNT(*) FROM dw.dim_customer"),
            ("fact_transaction", "SELECT COUNT(*) FROM dw.fact_transaction"),
        ],
        "dm": [
            ("vendor_risk_summary", "SELECT COUNT(*) FROM dm.vendor_risk_summary"),
            ("city_risk", "SELECT COUNT(*) FROM dm.city_risk"),
            ("anomaly_summary", "SELECT COUNT(*) FROM dm.anomaly_summary"),
        ],
    }

    try:
        conn = _get_dws_conn()
        results = {}
        with conn.cursor() as cur:
            for layer, tables in queries.items():
                layer_data = {}
                for name, sql in tables:
                    try:
                        cur.execute(sql)
                        layer_data[name] = cur.fetchone()[0]
                    except Exception:
                        layer_data[name] = None
                results[layer] = layer_data

        conn.close()
        return {
            "status": "ok",
            "source": "DWS — ods / dw / dm schemas",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "layers": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando DWS: {str(e)}",
        )


# ─── DWS: Contract List ───────────────────────────────
@app.get("/api/dws/contracts")
def dws_contracts(limit: int = 20):
    """Real contract list from DWS risk_results, ordered by risk_score DESC."""
    try:
        conn = _get_dws_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT contract_number, vendor_name, state, monto_total,
                       plazo_dias, penalizacion_pct, garantia_pct,
                       risk_score, risk_level, alertas, recomendaciones,
                       llm_provider, analyzed_at
                FROM public.risk_results
                ORDER BY risk_score DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

        conn.close()

        contracts = []
        for r in rows:
            c = dict(r)
            if c.get("monto_total"):
                c["monto_total"] = float(c["monto_total"])
            if c.get("risk_score"):
                c["risk_score"] = float(c["risk_score"])
            if c.get("analyzed_at"):
                c["analyzed_at"] = c["analyzed_at"].isoformat()
            contracts.append(c)

        return {
            "status": "ok",
            "source": "DWS — public.risk_results",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(contracts),
            "contracts": contracts,
        }
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando DWS: {str(e)}",
        )


# ─── Dify Chat Proxy ────────────────────────────────
@app.get("/api/chat")
def chat_proxy(query: str = ""):
    """Proxy to Dify chat-messages API. Returns HTML page with AI response."""
    if not query:
        return HTMLResponse("<html><body style=\"background:#0a0e1a;color:#e2e8f0;font-family:system-ui;padding:2rem;\"><h2>AYCO Deep Analysis</h2><p>No query provided.</p></body></html>")

    try:
        payload = json.dumps({
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": "ayco-demo",
        }).encode("utf-8")

        req = Request(
            f"{DIFY_BASE_URL}/v1/chat-messages",
            data=payload,
            headers={
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read().decode("utf-8"))
        answer = data.get("answer", "Sin respuesta del modelo.")
        conversation_id = data.get("conversation_id", "")

    except Exception as e:
        answer = f"Error conectando a Dify: {str(e)}"
        conversation_id = ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AYCO Deep Analysis</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0e1a;
    color: #e2e8f0;
    font-family: system-ui, -apple-system, sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 2rem;
  }}
  .card {{
    max-width: 800px;
    width: 100%;
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 2rem;
  }}
  .header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #1e293b;
  }}
  .header h1 {{ font-size: 1.25rem; color: #f8fafc; }}
  .header span {{ font-size: 0.75rem; color: #64748b; background: #1e293b; padding: 2px 8px; border-radius: 4px; }}
  .query-box {{
    background: #1e293b;
    border-left: 3px solid #38bdf8;
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    color: #94a3b8;
  }}
  .answer {{
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1.5rem;
    line-height: 1.8;
    font-size: 0.95rem;
    white-space: pre-wrap;
  }}
  .answer strong {{ color: #f8fafc; }}
  .footer {{
    margin-top: 1.5rem;
    font-size: 0.7rem;
    color: #475569;
    text-align: right;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <svg width="32" height="32" viewBox="0 0 32 32"><rect width="32" height="32" rx="6" fill="#1e293b"/><text x="16" y="22" text-anchor="middle" fill="#38bdf8" font-size="16" font-weight="bold">AI</text></svg>
    <h1>AYCO Contract Risk Analysis</h1>
    <span>DeepSeek v3.1</span>
  </div>
  <div class="query-box">Query: {query}</div>
  <div class="answer">{answer}</div>
  <div class="footer">Dify conversation_id: {conversation_id}</div>
</div>
</body>
</html>"""

    return HTMLResponse(html)


# ─── Entrypoint ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
