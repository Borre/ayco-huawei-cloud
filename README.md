# AYCO × Huawei Cloud — Demo Infrastructure

Infrastructure-as-code for the AYCO (Grupo Salinas) Huawei Cloud workshop demo.

## Quick Start

```bash
# 1. Clone and configure
cd /home/eduardo/dev/ayco-huawei-cloud
cp .env.example .env
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit .env and terraform.tfvars with real credentials

# 2. One command to deploy everything
make demo

# 3. Verify
make status
```

## Architecture

- **Region:** la-north-2 (Mexico City 2)
- **Demo Duration:** 45 minutes (3 demos + PPT + Q&A)
- **Stack:** Huawei Cloud (VPC, ECS, DLI, DWS, DataArts, DMS, FunctionGraph, OBS, CFW) + DeepSeek + Dify

## What `make demo` does

1. `terraform init` + `terraform apply` (4 modules: foundation, compute, data-platform, ai-ocr)
2. `fix-dns.sh` — Fix DNS on all ECS instances
3. `setup-dify.sh` — Deploy Dify via docker-compose
4. `generate-test-data.py` — Generate 2,300 vendors + 500 customers + 5,000 transactions with CNBV anomalies
5. `seed-dws.sql` — Create DWS schema + materialized views + sample queries
6. `index-knowledge-base.py` — Index contract analysis results in Dify KB
7. `health-check.sh` — Smoke test all endpoints

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make init` | Initialize Terraform |
| `make plan` | Preview changes |
| `make apply` | Apply all modules |
| `make deploy` | Full deploy + DNS fix + Dify |
| `make demo` | Deploy + test data + health check |
| `make destroy` | Destroy everything |
| `make status` | Health check |
| `make apply-foundation` | Apply foundation only |
| `make apply-compute` | Apply compute only |
| `make apply-data-platform` | Apply data platform only |
| `make apply-ai-ocr` | Apply AI/OCR only |

## Demo Flow (45 min)

| Time | Segment | Key Action |
|------|---------|------------|
| 0-5 min | PPT (3 slides) | Problem → Solution → Value |
| 5-15 min | Demo 1: Risk Scoring | DLI Spark SQL + DWS dashboard |
| 15-22 min | Demo 2: Data Platform | DataArts + OBS pipeline |
| 22-35 min | Demo 3: Contract AI + Dify | OCR → DeepSeek → Dify chatbot |
| 35-40 min | ROI + Success Case | Business impact |
| 40-45 min | Q&A | — |

## Directory Structure

```
├── Makefile                          # Orchestration
├── terraform/
│   ├── main.tf                       # Provider + module calls
│   ├── variables.tf                  # Root variables
│   ├── outputs.tf                    # Root outputs
│   └── modules/
│       ├── foundation/               # VPC, SG, OBS, KMS, IAM
│       ├── compute/                  # ECS (Dify, Web), EIPs
│       ├── data-platform/            # DLI, DWS, DataArts, DMS
│       └── ai-ocr/                   # FunctionGraph, OCR
├── scripts/
│   ├── fix-dns.sh                    # DNS fix for ECS
│   ├── setup-dify.sh                 # Dify docker-compose deploy
│   ├── generate-test-data.py         # Synthetic Mexico data
│   ├── seed-dws.sql                  # DWS schema + queries
│   ├── index-knowledge-base.py       # Dify KB indexing
│   ├── health-check.sh               # Smoke test
│   ├── backup-record-demos.sh        # Screen recording Plan B
│   └── destroy-all.sh                # Full cleanup
├── data/                             # Generated CSVs + JSON (gitignored)
└── backups/                          # Demo recordings (gitignored)
```

## Credentials

Use 1Password CLI for production secrets:
```bash
export HUAWEI_ACCESS_KEY=$(op read "op://Huawei/AK-SK/username")
export HUAWEI_SECRET_KEY=$(op read "op://Huawei/AK-SK/password")
```

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
Check security group allows port 5432 from your IP.

---
**Workshop:** May 8, 2026 — Huawei Cloud × Salinas
