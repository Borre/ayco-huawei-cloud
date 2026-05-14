# Infrastructure Architecture — Current Deployed State
**Last updated:** May 5, 2026

## Overview
```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET                              │
│  Presenter Browser ─────────────────────────────────┐   │
│  IP: (variable, set via presenter_ip /32)           │   │
└──────────────────────────────────┬──────────────────┘   │
                                   │                        │
                    ┌──────────────┴──────────────┐        │
                    │   Huawei Cloud la-north-2    │        │
                    │   Project: fbb6435c...       │        │
                    └──────────────┬──────────────┘        │
                                   │                        │
     ┌─────────────────────────────┼─────────────────────┐ │
     │            VPC 10.0.0.0/16                        │ │
     │                                                    │ │
     │  ┌──────────────────────┐  ┌───────────────────┐  │ │
     │  │  ECS: ayco-dify       │  │  ECS: ayco-web     │  │ │
     │  │  101.44.185.139       │  │  149.232.129.39    │  │ │
     │  │                       │  │                    │  │ │
     │  │  Docker (11 containers)│  │  nginx             │  │ │
     │  │  ├─ api               │  │  ├─ / (Landing)     │  │ │
     │  │  ├─ web (Dify UI)     │  │  ├─ /risk-scoring/  │  │ │
     │  │  ├─ worker            │  │  ├─ /data-gov/      │  │ │
     │  │  ├─ db (postgres)     │  │  ├─ /contract-ai/   │  │ │
     │  │  ├─ redis             │  │  └─ proxy /api/dify │  │ │
     │  │  ├─ sandbox           │  │       → dify ECS    │  │ │
     │  │  ├─ weaviate           │  │                    │  │ │
     │  │  ├─ nginx (Dify)      │  │  Static Astro build│  │ │
     │  │  ├─ plugin_daemon     │  │  /var/www/ayco/    │  │ │
     │  │  ├─ ssrf_proxy        │  └───────────────────┘  │ │
     │  │  └─ web (Dify)        │                          │ │
     │  │                       │                          │ │
     │  │  Services:            │                          │ │
     │  │  ├─ Streamlit :8501   │                          │ │
     │  │  ├─ Agent Tools :8400 │                          │ │
     │  │  └─ OCR Proxy :8300   │                          │ │
     │  └──────────────────────┘                          │ │
     │                                                    │ │
     │  ┌──────────────────────┐                          │ │
     │  │  DWS Cluster          │                          │ │
     │  │  3 nodes              │                          │ │
     │  │  46.250.161.25:8000   │                          │ │
     │  │  DB: ayco_db          │                          │ │
     │  │  Table: risk_results  │                          │ │
     │  │  (20 rows)            │                          │ │
     │  └──────────────────────┘                          │ │
     │                                                    │ │
     │  ┌──────────────────────┐                          │ │
     │  │  OBS Buckets (3)      │                          │ │
     │  │  ├─ ayco-contracts-raw│                          │ │
     │  │  ├─ ayco-contracts-text│                         │ │
     │  │  └─ ayco-contracts-res│                          │ │
     │  └──────────────────────┘                          │ │
     │                                                    │ │
     │  ┌──────────────────────┐                          │ │
     │  │  FunctionGraph (3)    │                          │ │
     │  │  ├─ ocr_trigger       │                          │ │
     │  │  ├─ parse_contract    │                          │ │
     │  │  └─ llm_inference     │                          │ │
     │  │  Trigger: OBS upload  │                          │ │
     │  └──────────────────────┘                          │ │
     │                                                    │ │
     │  ┌──────────────────────┐                          │ │
     │  │  DLI                  │                          │ │
     │  │  Database: ayco       │                          │ │
     │  │  (Serverless)         │                          │ │
     │  └──────────────────────┘                          │ │
     │                                                    │ │
     │  ┌──────────────────────┐                          │ │
     │  │  DataArts Studio      │                          │ │
     │  │  ❌ NOT PROVISIONED    │                          │ │
     │  │  Reason: prePaid month│                          │ │
     │  │  Plan B: frontend page│                          │ │
     │  │  + Console screenshots│                          │ │
     │  └──────────────────────┘                          │ │
     └────────────────────────────────────────────────────┘ │
```

## Ports & Security
| Port | Service | Access | Security Group Rule |
|------|---------|--------|-------------------|
| 22 | SSH | presenter_ip/32 ONLY | huaweicloud_networking_secgroup_rule.ssh |
| 80 | HTTP (Dify UI + Frontend) | 0.0.0.0/0 | Public |
| 443 | HTTPS | 0.0.0.0/0 | Public |
| 8000-8002 | Demo ports | presenter_ip/32 | Restricted |
| 8443 | Secure demo | presenter_ip/32 | Restricted |
| 8501 | Streamlit dashboard | presenter_ip/32 | Restricted |
| 8300 | OCR Proxy | Internal only (Docker→host) | Not externally open |

**⚠️ presenter_ip default = 0.0.0.0/0 → SET IN terraform.tfvars**

## Dify Data Flow
```
User Query → Dify App → Dataset Search (Weaviate) → LLM (DeepSeek V4) → Response
                              ↑
                    17 docs / 3 datasets
```
Agent adds: ... → Tool Selection → Mock API :8400 → Response
Workflow adds: User Upload → OCR Proxy :8300 → Parse+Classify → LLM Extract → Response

## Contract Pipeline (OBS → FunctionGraph → DWS)
```
Contract PDF → OBS raw bucket → FunctionGraph ocr_trigger → OCR API
  → parse_contract (JSON) → llm_inference (risk score) → OBS results
  → DWS seed import → risk_results table (20 rows)
```
