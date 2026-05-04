# AYCO — Architecture & Data Flows

> **Diagrama interactivo:** [`docs/architecture.drawio`](architecture.drawio) — abrir en [app.diagrams.net](https://app.diagrams.net)

## System Architecture

```
                           ┌──────────────────────────────────────────────────────┐
                           │              Huawei Cloud la-north-2 (Mexico City 2)  │
                           │                                                      │
  ┌──────────┐             │  ┌──────────────────────────────────────────────┐    │
  │ Contract │  Upload     │  │  OBS Buckets (×5)                            │    │
  │ PDFs     │────────────►│  │  ┌────────────┐  ┌───────────────┐           │    │
  │ (3 demo) │  to OBS     │  │  │contracts-  │  │ contracts-    │           │    │
  └──────────┘             │  │  │raw (raw)   │  │ text (parsed) │           │    │
                           │  │  └─────┬──────┘  └───────▲───────┘           │    │
                           │  │        │                  │                   │    │
                           │  │  ┌─────┴──────┐  ┌───────┴───────┐           │    │
                           │  │  │ contracts- │  │ ayco-raw      │           │    │
                           │  │  │ results    │  │ (DLI source)  │           │    │
                           │  │  └─────▲──────┘  └───────▲───────┘           │    │
                           │  │        │                  │                   │    │
                           │  │  ┌─────┴──────┐                           │    │
                           │  │  │ ayco-      │                           │    │
                           │  │  │ results    │                           │    │
                           │  │  └────────────┘                           │    │
                           │  └────────┼─────────────────┼─────────────────┘    │
                           │           │                 │                      │
                           │           ▼                 │                      │
                           │  ┌──────────────────────────┴──────────────────┐   │
                           │  │       FunctionGraph (Serverless)             │   │
                           │  │  ┌─────────────┐ ┌────────────┐ ┌──────────┐│   │
                           │  │  │ocr_trigger  │→│parse_cont  │→│llm_infer ││   │
                           │  │  │(OCR API)    │ │ract(regex) │ │ence(MaaS)││   │
                           │  │  └─────────────┘ └────────────┘ └────┬─────┘│   │
                           │  │        │               │              │      │   │
                           │  │        ▼               ▼              │      │   │
                           │  │    Huawei OCR    Regex Parse          │      │   │
                           │  │    la-north-2    Structured Data      │      │   │
                           │  │                                       │      │   │
                           │  │                          LLM Trace ───┤      │   │
                           │  │                          (REST API)   │      │   │
                           │  └──────────────────────────────┼────────┘──────┘   │
                           │                                 │                  │
                           │                          ┌──────▼──────────┐       │
                           │                          │ Langfuse Cloud   │       │
                           │                          │ (Observability)  │       │
                           │                          │ traces·latency·  │       │
                           │                          │ tokens·cost·errs │       │
                           │                          └──────────────────┘       │
                           │           ▼               ▼              ▼         │
                           │  ┌──────────────────────────────────────────────┐   │
                           │  │              Data Platform                    │   │
                           │  │  ┌─────┐ ┌──────┐ ┌─────────┐ ┌──────┐      │   │
                           │  │  │ DLI │ │ DWS  │ │DataArts │ │ CDM  │      │   │
                           │  │  │Spark│ │(DW)  │ │(ETL+API)│ │Agent │      │   │
                           │  │  └──┬──┘ └──▲───┘ └────┬────┘ └──▲───┘      │   │
                           │  │     │       │          │         │          │   │
                           │  │     └───────┼──────────┘    ┌────┘          │   │
                           │  │             │               │               │   │
                           │  │             │  ┌────────────┘               │   │
                           │  │             │  │ DWS ← CDM Agent → DataArts │   │
                           │  └─────────────┼──┼────────────────────────────┘   │
                           │                 │  │                                │
                           │  ┌──────────────▼──┼────────────────────────────┐   │
                           │  │         Compute (ECS)                        │   │
                           │  │  ┌──────────────┐  ┌──────────────────────┐ │   │
                           │  │  │ Dify (AI)    │  │ Web Server           │ │   │
                           │  │  │ s6.large.2   │  │ s6.medium.2          │ │   │
                           │  │  │ Chatbot + KB │  │ Landing / Reports    │ │   │
                           │  │  └──────────────┘  └──────────────────────┘ │   │
                           │  └──────────────────────────────────────────────┘   │
                           │                                                      │
                           │  ┌──────────────────────────────────────────────┐   │
                           │  │  Foundation: VPC, SG, KMS, IAM, CFW, DMS     │   │
                           │  └──────────────────────────────────────────────┘   │
                           └──────────────────────────────────────────────────────┘
```

## Demo 1: Risk Scoring Flow

```
  Contract PDFs          FunctionGraph              MaaS DeepSeek         DLI Spark          DWS
  (OBS raw)              (Serverless)               v4 Flash              (Serverless)       (Analytics)
      │                       │                          │                     │                │
      │  1. OBS Event         │                          │                     │                │
      │  (new file)           │                          │                     │                │
      ├──────────────────────►│                          │                     │                │
      │                       │                          │                     │                │
      │                       │  2. OCR API call         │                     │                │
      │                       │  (per page)              │                     │                │
      │                       ├──────────────────────────►│                     │                │
      │                       │  3. Extracted text       │                     │                │
      │                       │◄──────────────────────────┤                     │                │
      │                       │                          │                     │                │
      │                       │  4. Regex parse          │                     │                │
      │                       │  (structured data)       │                     │                │
      │                       │──────┐                   │                     │                │
      │                       │      │                   │                     │                │
      │                       │◄─────┘                   │                     │                │
      │                       │                          │                     │                │
      │                       │  5. Risk analysis prompt │                     │                │
      │                       ├──────────────────────────►│                     │                │
      │                       │  6. Risk JSON response   │                     │                │
      │                       │◄──────────────────────────┤                     │                │
      │                       │                          │                     │                │
      │  7. Save results      │                          │                     │                │
      │◄──────────────────────┤                          │                     │                │
      │                       │                          │                     │                │
      │                       │                          │  8. Spark SQL       │                │
      │                       │                          │  (aggregate)        │                │
      │                       │                          │────────────────────►│                │
      │                       │                          │                     │                │
      │                       │                          │  9. Load results    │                │
      │                       │                          │                     ├───────────────►│
      │                       │                          │                     │                │
      │                       │                          │                     │  10. Dashboard │
      │                       │                          │                     │    queries     │
      │                       │                          │                     │◄───────────────┤
```

**Key metrics shown in Demo 1:**
- Risk score per contract (0-100)
- Risk level classification (BAJO/MEDIO/ALTO/CRITICO)
- Alerts and recommendations from LLM
- Aggregated risk by vendor, by level

## Demo 2: Data Governance Flow (DataArts)

```
  DataArts Catalog    Architecture     Security        Factory           DataService     Dashboard
  (Lineage)           (Model)          (Masking)       (ETL Pipeline)   (REST API)      (Streamlit)
      │                   │                │                │                 │                │
      │  1. Metadata      │                │                │                 │                │
      │  collection       │                │                │                 │                │
      │  DWS→Catalog      │                │                │                 │                │
      │──────┐            │                │                │                 │                │
      │      │            │                │                │                 │                │
      │◄─────┘            │                │                │                 │                │
      │                   │                │                │                 │                │
      │  2. Lineage graph │                │                │                 │                │
      │  OBS→FG→DLI→      │                │                │                 │                │
      │     DWS→API       │                │                │                 │                │
      │──────┐            │                │                │                 │                │
      │      │            │                │                │                 │                │
      │◄─────┘            │                │                │                 │                │
      │                   │                │                │                 │                │
      │                   │  3. Subject    │                │                 │                │
      │                   │  area + Model  │                │                 │                │
      │                   │  + Table def   │                │                 │                │
      │                   │──────┐         │                │                 │                │
      │                   │      │         │                │                 │                │
      │                   │◄─────┘         │                │                 │                │
      │                   │                │                │                 │                │
      │                   │                │  4. Classify   │                 │                │
      │                   │                │  sensitive     │                 │                │
      │                   │                │  fields +      │                 │                │
      │                   │                │  masking       │                 │                │
      │                   │                │──────┐         │                 │                │
      │                   │                │      │         │                 │                │
      │                   │                │◄─────┘         │                 │                │
      │                   │                │                │                 │                │
      │                   │                │                │  5. Run ETL     │                │
      │                   │                │                │  pipeline       │                │
      │                   │                │                │──────┐          │                │
      │                   │                │                │      │          │                │
      │                   │                │                │◄─────┘          │                │
      │                   │                │                │                 │                │
      │                   │                │                │  6. Publish API │                │
      │                   │                │                ├────────────────►│                │
      │                   │                │                │                 │                │
      │                   │                │                │                 │  7. Dashboard  │
      │                   │                │                │                 │  DWS→Plotly    │
      │                   │                │                │                 │◄───────────────┤
      │                   │                │                │                 │                │
      │                   │                │                │  8. LLM Trace   │                │
      │                   │                │                │  → Langfuse     │                │
      │                   │                │                │─────────────────┤                │
```

**DataService API endpoints:**
- `GET /api/v1/risk-results?risk_level=ALTO&limit=50`
- `GET /api/v1/contracts/{contract_number}`

## Demo 3: Contract AI + Dify Chatbot Flow

```
  User                   Dify (ECS)               FunctionGraph           MaaS DeepSeek
  (Browser)              (Chatbot)                (OCR + Parse + LLM)     v4 Flash
      │                       │                          │                     │
      │  1. Open Dify UI      │                          │                     │
      ├──────────────────────►│                          │                     │
      │                       │                          │                     │
      │  2. Ask question      │                          │                     │
      │  "Contratos alto      │                          │                     │
      │   riesgo?"            │                          │                     │
      ├──────────────────────►│                          │                     │
      │                       │                          │                     │
      │                       │  3. Search KB            │                     │
      │                       │──────┐                   │                     │
      │                       │      │                   │                     │
      │                       │◄─────┘                   │                     │
      │                       │                          │                     │
      │                       │  4. Context + prompt     │                     │
      │                       ├──────────────────────────►│                     │
      │                       │                          │  5. LLM call        │
      │                       │                          ├────────────────────►│
      │                       │                          │  6. Response        │
      │                       │                          │◄────────────────────┤
      │  7. Answer            │                          │                     │
      │◄──────────────────────┤                          │                     │
      │                       │                          │                     │
      │  8. Upload new        │                          │                     │
      │  contract PDF         │                          │                     │
      ├──────────────────────►│                          │                     │
      │                       │  9. OCR + parse          │                     │
      │                       ├──────────────────────────►│                     │
      │                       │                          │  10. Risk analysis  │
      │                       │                          ├────────────────────►│
      │                       │                          │  11. Result         │
      │                       │                          │◄────────────────────┤
      │  12. Risk report      │                          │                     │
      │◄──────────────────────┤                          │                     │
```

## Resource Map

| Resource | Flavor/Size | Purpose | Always-on? |
|----------|-------------|---------|------------|
| ECS Dify | s6.xlarge.2 (4vCPU/8GB) | AI chatbot + Streamlit dashboard | Yes (demo) |
| ECS Web | s6.large.2 (2vCPU/4GB) | Landing page | Yes (demo) |
| DWS Cluster | dwsx3.4U16G.4DPU ×3 | Data warehouse | Yes |
| DLI Queue | default (serverless) | Spark SQL | Pay-per-query |
| DataArts Studio | professional | ETL + Catalog + Architecture + Security + Data API | Yes (monthly) |
| DMS Kafka | kafka.2u4g.single | Event streaming | Yes |
| CDM Cluster | cdm.large (8vCPU/16GB) | DataArts Agent | Yes (demo) |
| FunctionGraph ×3 | serverless | OCR, parse, LLM | Pay-per-invocation |
| OBS ×5 | standard | Storage | Pay-per-GB |
| KMS | standard | Encryption | Pay-per-key |
| Streamlit Dashboard | on ECS Dify (port 8501) | Risk visualization (Plotly) | Yes (demo) |
| Langfuse Cloud | free tier | LLM observability (traces, latency, tokens, errors) | Free |

## Security Architecture

```
  Internet ──► CFW (Firewall) ──► VPC (10.0.0.0/16)
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              Subnet (10.0.1.0/24)    │                 │
                    │                 │                 │
              ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
              │ SG: SSH   │    │ SG: HTTP  │    │ SG: DWS   │
              │ 22 (IP)   │    │ 80,443    │    │ 8000      │
              │ 8000-8501 │    │ 8000-8501 │    │ (internal)│
              └───────────┘    └──────────┘    └───────────┘
                    │                 │                 │
              ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
              │ ECS Dify  │    │ ECS Web   │    │ DWS       │
              │ + EIP     │    │ + EIP     │    │ + EIP     │
              │ :80 Dify  │    │            │    │            │
              │ :8501 Str │    │            │    │            │
              └───────────┘    └───────────┘    └───────────┘

  Secrets: 1Password vault "Huawei" ──► setup-secrets.sh ──► terraform.tfvars
  API keys: MaaS + DeepSeek injected via FunctionGraph env vars (user_data)
  Langfuse: Public/Secret keys → FunctionGraph user_data → Langfuse Cloud (traces)
  Security: Langfuse keys are project-scoped ingestion-only; provider keys never leave FunctionGraph
```
