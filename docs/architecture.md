# AYCO — Architecture & Data Flows

> **Interactive Diagram:** [Main Architecture](ayco-main-architecture.html) · [Pipeline Detail](ayco-pipeline-detail.html)
> Open in browser: `xdg-open diagrams/ayco-main-architecture.html`

## System Architecture

![Main Architecture](../diagrams/ayco-main-architecture.png)

*Full interactive version: `xdg-open diagrams/ayco-main-architecture.html`*

## Demo 1: Risk Scoring Flow

![Pipeline Detail](../diagrams/ayco-pipeline-detail.png)

*Full interactive version: `xdg-open diagrams/ayco-pipeline-detail.html`*

**Key metrics shown in Demo 1:**
- Risk score per contract (0-100) — 20 seed contracts (3 canonical + 17 synthetic)
- Risk level classification (BAJO/MEDIO/ALTO/CRITICO)
- Alerts and recommendations from LLM
- Aggregated risk by vendor, by level
- Total exposure: ~$133M MXN across 20 contracts

## Demo 2: Data Governance Flow (DataArts)

| Component | Purpose | Status |
|-----------|---------|--------|
| **DataArts Catalog** | Lineage tracking (OBS→FG→DLI→DWS→API) | Demo |
| **Architecture** | Subject areas + Data model + Table definitions | Demo |
| **Security** | Field classification + dynamic masking | Demo |
| **Factory** | ETL pipeline scheduling | Demo |
| **DataService** | REST API: `GET /risk-results`, `GET /contracts/{id}` | Demo |

## Demo 3: Contract AI + Dify Chatbot

| Step | Flow | Service |
|------|------|---------|
| 1 | User opens Dify UI | Browser → ECS |
| 2 | Ask: "¿Contratos alto riesgo?" | Dify Chatbot |
| 3 | Search knowledge base | Dify KB + Vector |
| 4 | Context + prompt | Dify → FunctionGraph |
| 5 | LLM call | MaaS DeepSeek v4 Flash |
| 6 | Response + risk report | Dify → User |
| 7 | Upload new PDF | OBS → FunctionGraph → OCR → MaaS |

## Resource Map

| Resource | Flavor/Size | Purpose | Always-on? |
|----------|-------------|---------|------------|
| ECS Dify | s6.xlarge.2 (4vCPU/8GB) | AI chatbot + Streamlit dashboard | Yes (demo) |
| ECS Web | s6.large.2 (2vCPU/4GB) | Landing page | Yes (demo) |
| DWS Cluster | dwsx3.4U16G.4DPU ×3 | Data warehouse | Yes |
| DLI Queue | default (serverless) | Spark SQL | Pay-per-query |
| DataArts Studio | professional | ETL + Catalog + Architecture + Security + API | Yes (monthly) |
| CDM Cluster | cdm.large | DataArts Agent for batch movement | Yes (demo) |
| FunctionGraph ×3 | serverless | OCR, parse, LLM | Pay-per-invocation |
| OBS ×3 | standard | contracts-raw, contracts-text, contracts-results | Pay-per-GB |
| KMS | standard | Encryption AES-256 | Pay-per-key |
| Streamlit Dashboard | on ECS Dify (port 8501) | Risk visualization (Plotly) | Yes (demo) |
| Langfuse Cloud | free tier | LLM observability | Free |

## Security Architecture

| Layer | Control | Detail |
|-------|---------|--------|
| Network | VPC Isolation | 172.16.0.0/16, private subnets |
| Access | Security Groups | Admin (SSH), HTTP (80/443), DWS (8000) |
| Identity | IAM RBAC | Group + Role with least privilege |
| Encryption | KMS AES-256 | OBS server-side, DWS at rest |
| Secrets | 1Password → .env | Never committed to git |
| Compliance | CNBV controls | AML, KYC, audit trail |

*Full architecture details: [`docs/network-security.md`](network-security.md)*
