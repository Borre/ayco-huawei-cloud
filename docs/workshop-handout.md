# AYCO Contract Risk Analysis — Workshop Handout

## Huawei Cloud LATAM × Grupo Salinas | May 8, 2026

**Presenter:** Eduardo — Huawei Cloud LATAM
**Region:** la-north-2 (Mexico City 2)
**Duration:** 45 min

---

## Executive Summary

AYCO (Grupo Salinas) processes thousands of vendor contracts annually. Manual contract risk analysis takes 3 days per contract. This workshop demonstrates an end-to-end AI-powered contract risk scoring platform running entirely on Huawei Cloud: OCR extraction via FunctionGraph, risk analysis via DeepSeek v4 Flash on MaaS, data warehousing on GaussDB (DWS), serverless aggregation with DLI Spark, RAG chatbot with Dify, and full LLM observability with Langfuse.

**Key metrics:** 16 vendors analyzed, 20 contracts scored, 3 days → 4 seconds, $31 USD/day infrastructure cost.

---

## Architecture

```
                          ┌──────────────────────────────────────┐
     Contract PDF ──────→ │  OBS (ayco-contracts-raw)            │
                          │         │                            │
                          │         ▼ FunctionGraph              │
                          │  ┌──────────────────┐               │
                          │  │ ocr_trigger      │ OCR API call  │
                          │  │ parse_contract   │ Structure txt │
                          │  │ llm_inference    │ DeepSeek MaaS │
                          │  └──────┬───────────┘               │
                          │         │                            │
                          │         ▼                            │
                          │  ┌──────────────────┐               │
                          │  │ DWS (GaussDB)     │              │
                          │  │ ods → dw → dm     │              │
                          │  │ public.risk_results│             │
                          │  └──────┬───────────┘               │
                          │         │ PostgreSQL wire protocol   │
                          │         ▼                            │
    ┌─────────────────────┤  ┌──────────────────┐               │
    │ Frontend (Astro)    │  │ Streamlit Dash   │               │
    │ nginx :80           │  │ :8501            │               │
    │ /api/dify/ → proxy  │  └──────────────────┘               │
    └─────────┬───────────┘                                      │
              │ SSE streaming                                    │
              ▼                                                  │
    ┌──────────────────┐                                        │
    │ Dify (ECS)        │                                       │
    │ ├─ Weaviate (RAG) │                                       │
    │ ├─ DeepSeek MaaS  │                                       │
    │ └─ PostgreSQL     │                                       │
    └──────────┬────────┘                                       │
               │                                                 │
               ▼                                                 │
    ┌──────────────────┐                                        │
    │ Langfuse Cloud   │   Observabilidad LLM                   │
    │ Traces, cost,    │                                        │
    │ latency, tokens  │                                        │
    └──────────────────┘                                        │
                          └──────────────────────────────────────┘
```

## Infrastructure (la-north-2)

| Resource | Spec | Endpoint |
|----------|------|----------|
| VPC | 55d7ebd4-7286-4c30-aa09-b6fc863eb3bf | — |
| Subnet | 41121f0f-5386-40b0-815d-a574d75070fd | — |
| ECS ayco-dify | 4 vCPU, 8GB, Ubuntu 22.04 | 101.44.185.139 |
| ECS ayco-web | 2 vCPU, 4GB, Ubuntu 22.04 | 149.232.129.39 |
| DWS (GaussDB 9.1) | Standard node | 46.250.161.25:8000 |
| OBS Buckets | ayco-contracts-{raw,text,results} | — |
| FunctionGraph | ocr_trigger, parse_contract, llm_inference | — |
| DLI | Spark serverless | — |
| KMS | Encryption key for OBS | — |

## DWS Schema

```
Schema    Table              Rows     Indexes
────────────────────────────────────────────
ods       vendors            2,300    —
ods       customers          500      —
ods       transactions       5,000    —
dw        dim_vendor         2,300    —
dw        dim_customer       500      —
dw        fact_transaction   5,000    —
public    risk_results       20       4 btree

risk_results (20 rows):
  contract_number  VARCHAR(50)  PRIMARY KEY
  vendor_name      VARCHAR(200)
  monto_total      NUMERIC(15,2)
  penalizacion_pct NUMERIC(5,2)
  garantia_pct     NUMERIC(5,2)
  risk_score       NUMERIC(5,2)
  risk_level       VARCHAR(20)  CHECK IN (BAJO,MEDIO,ALTO,CRITICO)
  alertas          TEXT
  recomendaciones  TEXT
  llm_provider     VARCHAR(50)
  analyzed_at      TIMESTAMP    DEFAULT pg_systimestamp()

Indexes:
  idx_risk_results_score  btree(risk_score DESC)
  idx_risk_results_level  btree(risk_level)
  idx_risk_results_vendor btree(vendor_name)
```

## Risk Data (Top 3)

| Contract | Vendor | Score | Level | Exposure |
|----------|--------|-------|-------|----------|
| AYCO-2026-0149 | Constructora y Desarrolladora del Golfo | 9.2 | CRITICO | $12.5M |
| AYCO-2026-0147 | Outsourcing del Sureste | 8.7 | ALTO | $3.85M |
| AYCO-2026-0165 | Energía Solar del Golfo | 7.3 | ALTO | $11.2M |

**Distribution:** 1 CRITICO · 10 ALTO · 3 MEDIO · 6 BAJO · Average: 5.1

## Dify RAG Configuration

```
App: AYCO Chat (chat mode)
Model: DeepSeek v4 Flash via Huawei MaaS
Temperature: 0.3
Context window: 128K tokens

Datasets:
  ayco-contracts-kb     21 docs  semantic_search, top_k=3
  AYCO - Preguntas Frecuentes  9 docs   semantic_search, top_k=3

Retrieval: high_quality mode, no reranking
Streaming: SSE via nginx reverse proxy
  nginx proxy_buffering off, proxy_read_timeout 300s
```

## LLM Inference Pipeline (FunctionGraph)

```python
# llm_inference.py — Contract → Risk Score via MaaS DeepSeek
MAAS_ENDPOINT = "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions"
MAAS_MODEL = "deepseek-v4-flash"

def handler(event, context):
    contract = event.get("contract_data", event)
    prompt = build_prompt(contract)

    # 1. Call MaaS DeepSeek v4 Flash
    response = call_maas(prompt)

    # 2. Parse JSON (with repair for truncated/invalid)
    risk_report = parse_or_repair(response["content"])

    # 3. Trace to Langfuse (full input/output/metadata)
    trace_langfuse(contract, prompt, risk_report, response)

    return risk_report  # Persisted to DWS risk_results
```

**Fallback:** If MaaS fails, falls back to DeepSeek API direct (`api.deepseek.com`).
**Observability:** Every LLM call traced to Langfuse Cloud with input, output, model, latency, tokens.

## Live Queries (Copy-Paste Ready)

### DWS — Risk KPIs
```sql
SELECT
  COUNT(DISTINCT vendor_name) AS proveedores,
  COUNT(*) AS contratos,
  ROUND(SUM(monto_total)/1000000, 1) AS exposicion_mxn,
  ROUND(AVG(risk_score), 1) AS riesgo_promedio
FROM public.risk_results;
-- Result: 16 | 20 | 133.1 | 5.1
```

### DWS — Top 5 Risky Contracts
```sql
SELECT contract_number, vendor_name, risk_score, risk_level,
       ROUND(monto_total/1000000, 1) AS monto_mxn
FROM public.risk_results
ORDER BY risk_score DESC LIMIT 5;
```

### DWS — Schema Inspection
```sql
\d public.risk_results
-- Shows: 12 columns, PK, CHECK constraint, 4 btree indexes, pg_systimestamp()
```

### DWS — Data Quality
```sql
SELECT
  COUNT(*) FILTER (WHERE risk_score IS NULL) AS nulos,
  COUNT(*) FILTER (WHERE risk_score BETWEEN 0 AND 10) AS en_rango,
  COUNT(*) FILTER (WHERE risk_score < 0 OR risk_score > 10) AS fuera_rango
FROM public.risk_results;
-- Result: 0 | 20 | 0
```

### DWS — 3-Layer Governance
```sql
-- ODS: raw data
SELECT vendor_id, name, state, risk_score FROM ods.vendors LIMIT 5;
-- DW: star schema
SELECT name, state, risk_score FROM dw.dim_vendor WHERE risk_level = 'CRITICO';
-- DM: analytics views
SELECT * FROM dm.vendor_risk_summary ORDER BY avg_risk DESC LIMIT 5;
```

### Dify API — Chat (Blocking)
```bash
curl -s -X POST http://149.232.129.39/api/dify/chat-messages \
  -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"¿Cuál es el contrato con mayor riesgo?","user":"demo","response_mode":"blocking","inputs":{}}'
```

### Dify API — Chat (Streaming SSE)
```bash
curl -N -X POST http://149.232.129.39/api/dify/chat-messages \
  -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
  -H "Content-Type: application/json" \
  -d '{"query":"Compara los 3 contratos más riesgosos","user":"demo","response_mode":"streaming","inputs":{}}'
```

## Cost Breakdown

| Resource | Daily Cost (USD) |
|----------|-----------------|
| ECS ayco-dify (4 vCPU, 8GB) | ~$12 |
| ECS ayco-web (2 vCPU, 4GB) | ~$6 |
| DWS GaussDB Standard | ~$10 |
| OBS (3 buckets, <1GB) | ~$0.03 |
| FunctionGraph (3 functions) | ~$2 |
| DLI Spark (serverless) | ~$1 |
| **Total** | **~$31/day** |

MaaS DeepSeek: ~$0.40/1M input tokens. Average per contract: ~450 tokens.

## Key Technical Decisions

1. **GaussDB over vanilla PostgreSQL:** Columnar storage, MPP, compression for analytical workloads. PostgreSQL wire protocol compatible.
2. **MaaS over direct DeepSeek API:** Intra-region latency (<50ms vs ~200ms), data residency México, simplified IAM.
3. **FunctionGraph over ECS for pipeline:** Zero idle cost, auto-scaling, event-driven (OBS trigger), no server management.
4. **DLI Spark serverless over permanent cluster:** Pay-per-job, no cluster administration, same Spark SQL syntax.
5. **Weaviate over pgvector:** Purpose-built vector DB, HNSW indexing, horizontal scaling, Dify native integration.
6. **Langfuse over custom observability:** Open-source, no vendor lock-in, REST ingestion (30 lines of Python), full trace view.

## URLs

| Resource | URL |
|----------|-----|
| Frontend | http://149.232.129.39/ |
| Dify Admin | http://101.44.185.139/admin |
| Streamlit Dashboard | http://101.44.185.139:8501 |
| Langfuse | https://us.cloud.langfuse.com → ayco-demo |
| Terraform Repo | github.com/Borre/ayco-huawei-cloud |
| DWS Endpoint | 46.250.161.25:8000 (GaussDB) |
| MaaS Endpoint | api-ap-southeast-1.modelarts-maas.com |
| DeepSeek Fallback | api.deepseek.com |

---

*Huawei Cloud LATAM — May 8, 2026*
*Document version: v3.0 — Technical Depth*
