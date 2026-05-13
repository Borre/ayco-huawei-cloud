# AYCO × Huawei Cloud — Demo Infrastructure

Infrastructure-as-code for the AYCO (Grupo Salinas) Huawei Cloud workshop demo.

## Quick Start

```bash
# 1. Clone and configure
cd /home/eduardo/dev/ayco-huawei-cloud
cp .env.example .env
cp terraform.tfvars.example terraform/terraform.tfvars
# Edit .env and terraform/terraform.tfvars with real credentials

# 2. One command to deploy everything
make demo

# 3. Verify
make status
```

## Current State (May 13, 2026)

Demo revived after original DWS cluster was deleted. 2 ECS instances survived (ayco-dify, ayco-web). DWS recreated via Terraform, frontend rebuilt with auth fixes.

| Resource | Public IP | Private IP | Status |
|----------|-----------|------------|--------|
| ECS Dify (ayco-dify) | 101.44.185.139 | 192.168.100.135 | Running (11 Docker containers) |
| ECS Web (ayco-web) | 149.232.129.39 | 192.168.100.123 | Running (Nginx + FastAPI) |
| DWS Cluster (ayco-dws) | 46.250.168.254:8000 | 192.168.100.157, 192.168.100.126 | Available (24 records) |
| Streamlit Dashboard | 101.44.185.139:8501 | — | Running |
| Agent Tools mock | localhost:8400 (via SSH) | — | Running (puerto no expuesto) |

**SSH access:** `ssh -i ~/.ssh/ayco-demo root@<IP>`

## Architecture

- **Region:** la-north-2 (Mexico City 2)
- **Demo Duration:** 45 minutes (3 demos + PPT + Q&A)
- **Stack:** Huawei Cloud (VPC, ECS, DLI, DWS, DataArts, FunctionGraph, OBS) + DeepSeek v4 Flash (MaaS) + Dify + Langfuse (LLM Observability)
- **Security note:** Cloud Firewall is documented as an optional future hardening step, but it is not provisioned in this demo because the Terraform resource is intentionally commented out.

### Resource Summary

| Resource | Flavor | Purpose | Billing |
|----------|--------|---------|---------|
| ECS Dify | s6.xlarge.2 (4vCPU/8GB) | AI chatbot | Pay-per-hour |
| ECS Web | s6.large.2 (2vCPU/4GB) | Landing page | Pay-per-hour |
| DWS Cluster | dwsx3.4U16G.4DPU ×3 | Data warehouse | Pay-per-hour |
| DLI Queue | default (serverless) | Spark SQL | Pay-per-CU |
| DataArts Studio | professional | ETL + Data API | Monthly |
| FunctionGraph ×3 | serverless | OCR, parse, LLM | Pay-per-invocation |
| OBS ×3 | standard | Storage | Pay-per-GB |
| Langfuse Cloud | free tier | LLM observability | Free |

## Demo Flow (45 min)

| Time | Segment | Key Action |
|------|---------|------------|
| 0-5 min | PPT (3 slides) | Problem → Solution → Value |
| 5-15 min | Demo 1: Risk Scoring | OCR → Parse → MaaS DeepSeek → DLI Spark → DWS |
| 15-25 min | Demo 2: Data Governance | DWS layered queries + DLI Spark + Langfuse traces |
| 25-38 min | Demo 3: Contract AI + Dify | Dify chatbot + live OCR processing |
| 38-41 min | ROI + Success Case | Business impact |
| 41-45 min | Q&A | — |

**✨ Wow Factor Highlights:**
- **Live Streamlit Dashboard:** Features a dynamic animated gauge for Average Risk, an interactive vendor exposure chart, and an auto-refresh toggle for real-time monitoring of the DWS data warehouse.
- **Real-time LLM Observability:** Instant traces in Langfuse without blocking the main workflow.
- **RAG Chatbot:** Conversational query interface via Dify querying knowledge extracted entirely by the automated OCR+MaaS pipeline.

**Full demo script:** [`docs/demo-script.md`](docs/demo-script.md)
**Architecture diagrams:** [`docs/architecture.md`](docs/architecture.md)
**Prep checklist:** [`docs/prep-checklist.md`](docs/prep-checklist.md)
**Network security:** [`docs/network-security.md`](docs/network-security.md) | [`docs/network-security-mermaid.md`](docs/network-security-mermaid.md)

## What `make demo` does

1. `terraform init` + `terraform apply` (4 modules: foundation, compute, data-platform, ai-ocr)
2. `fix-dns.sh` — Fix DNS on all ECS instances
3. `setup-dify.sh` — Deploy Dify via docker-compose
4. `generate-test-data.py` — Generate 2,300 vendors + 500 customers + 5,000 transactions with CNBV anomalies
5. `seed-dws.sql` — Create DWS schema (risk_results + analytics tables) + materialized views
6. `index-knowledge-base.py` — Index contract analysis results in Dify KB
7. `health-check.sh` — Smoke test all endpoints

## Makefile Targets

| Target | Description |
|--------|-------------|
| **Infrastructure** | |
| `make init` | Initialize Terraform |
| `make plan` | Preview changes |
| `make apply` | Apply all modules |
| `make deploy` | Full deploy + DNS fix + Dify |
| `make demo` | Deploy + test data + health check |
| `make destroy` | Destroy everything |
| `make status` | Health check |
| **Phased Deployment** | |
| `make apply-foundation` | Apply foundation only |
| `make apply-compute` | Apply compute only |
| `make apply-data-platform` | Apply data platform only |
| `make apply-ai-ocr` | Apply AI/OCR only |
| **Data & Testing** | |
| `make upload-contracts` | Upload PDFs to OBS (triggers OCR pipeline) |
| `make test-dataarts` | Test DataArts DataService REST APIs (if provisioned) |
| `make generate-data` | Generate all synthetic demo data |
| **Code Quality** | |
| `make fmt` | Format Terraform files |
| `make fmt-check` | Check formatting (for CI/CD) |
| `make validate` | Validate Terraform syntax |
| `make lint` | Run all checks (fmt + validate) |

## Demo Data

**3 contract PDFs** in `data/contracts/`:

| Contract | Contract No. | Profile | Risk | Amount | Key Signal |
|----------|--------------|---------|------|--------|------------|
| contrato-01-alto-riesgo.pdf | AYCO-2026-0147 | High risk | 8.7/10 | $3.85M MXN | 30% penalty, no guarantee |
| contrato-02-bajo-riesgo.pdf | AYCO-2026-0148 | Low risk | 2.3/10 | $450K MXN | 5% penalty, 20% bond |
| contrato-03-critico.pdf | AYCO-2026-0149 | Critical | 9.2/10 | $12.5M MXN | 40% penalty, UNCITRAL arbitration |

`make generate-data` expands these canonical examples into 20 demo contract records and 20 text files for DWS, OBS, and Dify indexing.

**Synthetic data** (generated by `generate-test-data.py`):
- 2,300 vendors across Mexico (32 states)
- 500 customers with KYC levels
- 5,000 transactions with CNBV anomaly patterns

## LLM Stack

| Provider | Model | Role | Endpoint | Observability |
|----------|-------|------|----------|---------------|
| Huawei MaaS (primary) | DeepSeek v4 Flash | Risk analysis | api-ap-southeast-1.modelarts-maas.com | Langfuse Cloud |
| DeepSeek (fallback) | deepseek-chat | Risk analysis | api.deepseek.com | Langfuse Cloud |

The OCR → Parse → LLM pipeline uses MaaS as default. If MaaS fails, falls back to DeepSeek direct API.

Every LLM call is traced automatically via Langfuse REST API (non-blocking, no SDK dependency):
- **Traces:** Contract risk analysis lifecycle (trace ID, latency, contract number)
- **Generations:** Model call details (input/output preview, estimated tokens, provider metadata)
- **Dashboard:** https://us.cloud.langfuse.com → project ayco-demo → free tier

## Directory Structure

```
├── Makefile                              # Orchestration
├── README.md                             # This file
├── .env.example                          # Environment template
├── terraform.tfvars.example              # Terraform variables template
├── docs/
│   ├── demo-script.md                    # Step-by-step demo guide (667 lines)
│   ├── prep-checklist.md                 # Workshop prep checklist (287 lines)
│   └── architecture.md                   # Architecture diagrams + flows
├── terraform/
│   ├── main.tf                           # Provider + module calls
│   ├── variables.tf                      # Root variables
│   ├── outputs.tf                        # Root outputs
│   └── modules/
│       ├── foundation/                   # VPC, SG, OBS, KMS, IAM
│       ├── compute/                      # ECS (Dify, Web), EIPs
│       ├── data-platform/                # DLI, DWS
│       └── ai-ocr/                       # FunctionGraph (OCR, parse, LLM)
├── scripts/
│   ├── setup-secrets.sh                  # 1Password → terraform.tfvars
│   ├── langfuse-setup.sh                 # Langfuse Cloud setup + verify
│   ├── fix-dns.sh                        # DNS fix for ECS
│   ├── setup-dify.sh                     # Dify docker-compose deploy
│   ├── generate-test-data.py             # Synthetic Mexico data
│   ├── seed-dws.sql                      # DWS schema + queries
│   ├── spark-risk-aggregation.py         # DLI Spark aggregation job
│   ├── index-knowledge-base.py           # Dify KB indexing
│   ├── health-check.sh                   # Smoke test
│   ├── backup-record-demos.sh            # Screen recording Plan B
│   └── destroy-all.sh                    # Full cleanup
├── data/
│   └── contracts/                        # 3 demo contract PDFs
├── dashboards/
│   ├── contract-risk.json                # Risk scoring dashboard
│   ├── vendor-exposure.json              # Vendor exposure dashboard
│   └── risk-overview.json                # Risk overview dashboard
└── backups/                              # Demo recordings (gitignored)
```

## Frontend Env Variables

The Astro frontend needs env vars at build time. Create `frontend/.env` (see `frontend/.env.example`):

```bash
cd frontend
cp .env.example .env
# Edit with your Dify API keys
npm install --legacy-peer-deps && npm run build
```

| Variable | Required | Description | Current Value |
|----------|----------|-------------|---------------|
| `PUBLIC_DIFY_API_KEY` | **Yes** | Dify app key (AYCO Chat) | `app-Y8MxfRygyUWOAfyTlo1MQSJx` |
| `PUBLIC_COBRANZA_API_KEY` | No | Dify cobranza agent key (currently unused) | `app-ZrM7Pal6G2b89drd1zLVssvM` |
| `PUBLIC_DASHBOARD_URL` | No | Streamlit dashboard URL | `http://101.44.185.139` |

## Credentials

Use 1Password CLI for production secrets:
```bash
# Setup (one time)
scripts/setup-secrets.sh
```

**Required secrets (in 1Password vault "Huawei"):**
- AK/SK HUAWEI CLOUD — Huawei Cloud access key
- MaaS API Key Master — MaaS DeepSeek v4 Flash key
- deepseek key — DeepSeek fallback API key

## Troubleshooting

**DNS not working on ECS:**
```bash
bash scripts/fix-dns.sh
```

**Dify not starting:**
```bash
ssh root@$(cd terraform && terraform output -raw dify_public_ip)
cd /opt/dify/docker && docker compose logs
```

**DWS connection refused:**
Check security group allows port from your IP. DWS takes 5-10 min to provision.

**Dify chat returns 401 Unauthorized:**
The frontend ChatWidget uses `Authorization: Bearer ${DIFY_KEY}`. If the COBRANZA_KEY was removed or the env var `PUBLIC_DIFY_API_KEY` is missing, replace `frontend/src/components/ChatWidget.astro` line 104.
```
# In frontend/.env — required before build
PUBLIC_DIFY_API_KEY=app-Y8MxfRygyUWOAfyTlo1MQSJx
```
Then rebuild + redeploy: `make frontend-deploy`

**Deep Analysis AI button doesn't open chat:**
The button uses event delegation (`document.addEventListener`). If you rewrote the `risk-scoring.astro` script, make sure the `openChatWithQuery` function dispatches a form submit event on `#chat-form` (not a raw fetch call), or the Authorization header won't be included.

**DWS version mismatch on recreate:**
If Terraform fails with `datastore version is illegal`, check the current version:
```bash
hcloud DWS ListNodeTypes --cli-region=la-north-2 | python3 -c "import sys,json; [print(v.get('detail',[])) for v in json.load(sys.stdin).get('node_types',[])]"
```
Then update `terraform/modules/data-platform/dws.tf` variable `version`.

**Health check fails:**
```bash
make status
# Check each component individually:
curl http://$(terraform -chdir=terraform output -raw dify_public_ip)/v1
```

**Full troubleshooting guide:** [`docs/prep-checklist.md#troubleshooting`](docs/prep-checklist.md)

---
**Workshop:** May 8, 2026 — Huawei Cloud × Salinas
