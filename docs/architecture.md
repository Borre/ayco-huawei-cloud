# AYCO — Architecture & Data Flows

## System Architecture

```
                           ┌─────────────────────────────────────────────────────┐
                           │              Huawei Cloud la-north-2                │
                           │                                                     │
  ┌──────────┐             │  ┌─────────────────────────────────────────────┐    │
  │ Contract │  Upload     │  │  OBS Buckets                                │    │
  │ PDFs     │────────────►│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ │    │
  │ (3 demo) │  to OBS     │  │  │ ayco-raw  │ │ayco-text  │ │ayco-results│ │    │
  └──────────┘             │  │  └─────┬─────┘ └─────▲─────┘ └─────▲─────┘ │    │
                           │  │        │             │             │        │    │
                           │  └────────┼─────────────┼─────────────┼────────┘    │
                           │           │             │             │             │
                           │           ▼             │             │             │
                           │  ┌──────────────────────┴─────────────┴──────────┐  │
                           │  │         FunctionGraph (Serverless)            │  │
                           │  │  ┌─────────────┐ ┌────────────┐ ┌──────────┐ │  │
                           │  │  │ocr_trigger  │→│parse_contract│→│llm_infere│ │  │
                           │  │  │(OCR API)    │ │(regex parse) │ │nce (MaaS)│ │  │
                           │  │  └─────────────┘ └────────────┘ └──────────┘ │  │
                           │  │        │               │              │       │  │
                           │  │        │    Huawei OCR  │   DeepSeek   │       │  │
                           │  │        │    API        │   v4 Flash   │       │  │
                           │  └────────┼───────────────┼──────────────┼───────┘  │
                           │           │               │              │          │
                           │           ▼               ▼              ▼          │
                           │  ┌──────────────────────────────────────────────┐   │
                           │  │              Data Platform                    │   │
                           │  │  ┌─────┐  ┌──────┐  ┌─────────┐  ┌───────┐  │   │
                           │  │  │ DLI │  │ DWS  │  │DataArts │  │DMS    │  │   │
                           │  │  │Spark│  │(DW)  │  │(ETL+API)│  │Kafka  │  │   │
                           │  │  └──┬──┘  └──▲───┘  └────┬────┘  └───────┘  │   │
                           │  │     │        │           │                    │   │
                           │  │     └────────┼───────────┘                    │   │
                           │  │              │                                │   │
                           │  └──────────────┼────────────────────────────────┘   │
                           │                 │                                   │
                           │  ┌──────────────▼────────────────────────────────┐   │
                           │  │         Compute (ECS)                         │   │
                           │  │  ┌──────────────┐  ┌──────────────────────┐  │   │
                           │  │  │ Dify (AI)    │  │ Web Server           │  │   │
                           │  │  │ s6.large.2   │  │ s6.medium.2          │  │   │
                           │  │  │ Chatbot + KB │  │ Landing / Reports    │  │   │
                           │  │  └──────────────┘  └──────────────────────┘  │   │
                           │  └──────────────────────────────────────────────┘   │
                           │                                                     │
                           │  ┌──────────────────────────────────────────────┐   │
                           │  │  Foundation: VPC, SG, KMS, IAM, CFW         │   │
                           │  └──────────────────────────────────────────────┘   │
                           └─────────────────────────────────────────────────────┘
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
  DataArts Studio                Data Connections           Factory Job              DataService
  (Workspace)                    (DLI, DWS, OBS)            (ETL Pipeline)           (REST API)
      │                              │                          │                        │
      │  1. Create workspace         │                          │                        │
      │──────┐                       │                          │                        │
      │      │                       │                          │                        │
      │◄─────┘                       │                          │                        │
      │                              │                          │                        │
      │  2. Register connections     │                          │                        │
      ├─────────────────────────────►│                          │                        │
      │                              │                          │                        │
      │  3. Create ETL scripts       │                          │                        │
      │──────┐                       │                          │                        │
      │      │                       │                          │                        │
      │◄─────┘                       │                          │                        │
      │                              │                          │                        │
      │  4. Deploy pipeline          │                          │                        │
      ├──────────────────────────────┼─────────────────────────►│                        │
      │                              │                          │                        │
      │                              │    ┌─────────────────┐   │                        │
      │                              │    │ Node 1: DLI SQL │   │                        │
      │                              │    │ (parse)         │   │                        │
      │                              │    └────────┬────────┘   │                        │
      │                              │             │ SUCCESS    │                        │
      │                              │    ┌────────▼────────┐   │                        │
      │                              │    │ Node 2: DWS SQL │   │                        │
      │                              │    │ (load)          │   │                        │
      │                              │    └────────┬────────┘   │                        │
      │                              │             │ SUCCESS    │                        │
      │                              │    ┌────────▼────────┐   │                        │
      │                              │    │ Node 3: DWS SQL │   │                        │
      │                              │    │ (quality check) │   │                        │
      │                              │    └─────────────────┘   │                        │
      │                              │                          │                        │
      │  5. Publish APIs             │                          │                        │
      ├──────────────────────────────┼──────────────────────────┼───────────────────────►│
      │                              │                          │                        │
      │                              │                          │  6. GET /api/v1/       │
      │                              │                          │     risk-results       │
      │                              │                          │◄───────────────────────┤
      │                              │                          │                        │
      │                              │                          │  7. JSON response      │
      │                              │                          ├───────────────────────►│
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
| ECS Dify | s6.large.2 (2vCPU/4GB) | AI chatbot frontend | Yes (demo) |
| ECS Web | s6.medium.2 (1vCPU/2GB) | Landing page | Yes (demo) |
| DWS Cluster | dwsx3.4U16G.4DPU ×3 | Data warehouse | Yes |
| DLI Queue | default (serverless) | Spark SQL | Pay-per-query |
| DataArts Studio | professional | ETL + Data API | Yes (monthly) |
| DMS Kafka | kafka.2u4g.single | Event streaming | Yes |
| FunctionGraph ×3 | serverless | OCR, parse, LLM | Pay-per-invocation |
| OBS ×5 | standard | Storage | Pay-per-GB |
| KMS | standard | Encryption | Pay-per-key |

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
              │ 22 (IP)   │    │ 80,443   │    │ 8000      │
              │ 8000-8443 │    │ 8000-8443│    │ (internal)│
              └───────────┘    └──────────┘    └───────────┘
                    │                 │                 │
              ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
              │ ECS Dify  │    │ ECS Web   │    │ DWS       │
              │ + EIP     │    │ + EIP     │    │ + EIP     │
              └───────────┘    └───────────┘    └───────────┘

  Secrets: 1Password vault "Huawei" ──► setup-secrets.sh ──► terraform.tfvars
  API keys: MaaS + DeepSeek injected via FunctionGraph env vars (user_data)
```
