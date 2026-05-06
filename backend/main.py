"""
ayco-api: FastAPI backend for AYCO Contract Risk pipeline.

Endpoints:
  POST /api/upload          — Upload PDF → OBS → trigger FunctionGraph pipeline
  GET  /api/status/{job_id} — Poll OBS for pipeline results
  GET  /api/dws/quality     — Data quality metrics from DWS
  GET  /api/dws/layers      — ODS/DW/DM row counts from DWS
  GET  /api/dws/contracts   — Contract list from risk_results
  GET  /api/health          — Health check

Environment:
  HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY  — Huawei Cloud credentials
  DWS_HOST, DWS_PORT, DWS_DB, DWS_USER, DWS_PASSWORD  — DWS connection
  OBS_ENDPOINT, OBS_RAW_BUCKET, OBS_RESULTS_BUCKET    — OBS config
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(title="AYCO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        "version": "1.0.0",
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
        # Likely file not found yet — pipeline still running
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

        # Serialize Decimal and datetime
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


# ─── Entrypoint ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
