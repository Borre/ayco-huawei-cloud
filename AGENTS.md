# AGENTS.md — Huawei Cloud AI

## What This Is

Infrastructure-as-code demo for an Huawei Cloud workshop. Deploys a full contract risk analysis pipeline: OCR → LLM scoring → Spark aggregation → Data Warehouse → Streamlit dashboard + Dify chatbot. Designed for a 45-minute live demo.

**Region:** `la-north-2` (Mexico City 2). **Language:** All UI, data, and docs are in Spanish.

## Commands

```bash
make demo              # Full deploy + data generation + health check (one command)
make deploy            # Terraform deploy only (foundation → data-platform → compute → ai-ocr)
make plan              # Preview Terraform changes
make status            # Health check all services
make destroy           # Terraform destroy + manual cleanup

# Phased deployment (order matters — compute depends on data-platform DWS output)
make apply-foundation
make apply-data-platform
make apply-compute
make apply-ai-ocr

# Code quality
make lint              # fmt-check + validate
make fmt               # terraform fmt -recursive

# Data & testing
make generate-data     # Generate synthetic vendors/customers/transactions + contracts
make upload-contracts  # Upload PDFs to OBS (triggers FunctionGraph OCR pipeline)
make test-dataarts     # Test DataArts DataService REST APIs

# Frontend
make frontend          # Build Astro static site → frontend/dist/
make frontend-dev      # Dev server with hot reload
make frontend-deploy   # Build + SCP to web ECS

# Backend API
make deploy-api        # Deploy FastAPI backend → web ECS
make api-status        # Health check API backend

# Dashboard

# Direct Terraform (from repo root)
cd terraform && terraform init
cd terraform && terraform output -raw dify_public_ip
```

## Architecture & Data Flow

```
data/contracts/*.pdf
  → OBS (ayco-contracts-raw) ← upload-contracts-to-obs.sh
  → FunctionGraph OCR (extracts text)
  → OBS (ayco-contracts-text)
  → FunctionGraph Parse (structure data)
  → FunctionGraph LLM Inference (MaaS DeepSeek → risk score)
  → OBS (ayco-contracts-results)
  → DWS (risk_results table)
  → Streamlit Dashboard (port 8501)

Separate path:
  generate-test-data.py → CSV/JSON → seed-dws.sql → DWS (ods/dw/dm schemas)
  spark-risk-aggregation.py → DLI Spark → OBS (aggregated results)
  DataArts Factory → ETL pipeline (parse → load → quality check) → REST API
```

## Terraform Module Dependency Order

**Foundation → Data Platform → Compute → AI/OCR**

- `compute` needs `dws_private_ip` from `data_platform`
- `ai_ocr` needs OBS bucket names from `foundation` + `dify_public_ip` from `compute`
- Destroy in reverse order

The root module (`terraform/main.tf`) wires outputs between modules. Each module lives in `terraform/modules/<name>/` with its own `variables.tf`.

## Gotchas & Non-Obvious Behavior

### Terraform

- **Provider pinned to `= 1.91.0`** (exact). Defined per-module, not centrally. Upgrading the provider version may break resources.
- **Foundation reuses an existing VPC** (`vpc-default-flexus`) via data lookup — doesn't create one. If that VPC is deleted outside Terraform, everything breaks.
- **DLI module (`dli.tf`) is mostly commented out** — provider `v1.91.0` crashes on DLI table/job resources and queue capacity is sold out in `la-north-2`. Only the DLI database and OBS upload are active. DLI tables must be created manually via the console SQL editor.
- **ECS image ID is hardcoded** (`67c29d17-33bd-43f0-a17b-ed2015798bb8`) — Ubuntu 22.04 for `la-north-2`. Region-specific; won't work in other regions.
- **DWS password is passed through ECS user-data** (base64-encoded but not encrypted — visible in console).
- **DataArts DataService APIs have `auth_type = "NONE"`** — completely unauthenticated. Demo only.
- **`dataarts_enabled` defaults to `true`** — deploying the data-platform module will attempt to create DataArts resources (expensive, long provisioning time). Set to `false` for faster iteration.
- **The `dli_external_contracts` foreign table** referenced in `dataarts.tf` ETL scripts is **never defined** in Terraform or seed SQL — must be created manually.
- **FunctionGraph code is inlined** (`code_type = "inline"` with `filebase64()`) — any Python change creates noisy Terraform plan diffs on base64 blobs.
- **OCR API endpoint is cross-region**: resources in `la-north-2` call OCR in `ap-southeast-1`.
- **`terraform.tfvars` is gitignored** — must be created from `terraform.tfvars.example` before any deploy.

### Scripts

- **`fix-dns.sh` overwrites `/etc/resolv.conf`** on ECS with Google/Cloudflare DNS. Huawei Cloud Ubuntu images have broken `systemd-resolved`. This may break internal service resolution (OBS, DWS endpoints). Changes are lost on reboot.
- **`setup-dify.sh` requires SSH key at `~/.ssh/ayco-demo`** — hardcoded path, not configurable.
- **`generate-test-data.py` has no `if __name__` guard** — executes on import.
- **`generate-contract-data.py` generates `TRUNCATE TABLE risk_results`** — will delete all existing data when the seed SQL runs.
- **`process-contracts.py` has hardcoded API keys and DWS IP** — not suitable for production.
- **`seed-dws.sql` references schemas `ods`, `dw`, `dm`** that are never created by the script. `CREATE SCHEMA IF NOT EXISTS` is missing; must run manually.
- **`spark-risk-aggregation.py` only runs on DLI** — `pyspark` imports fail locally.

### DWS (GaussDB Data Warehouse)

- **No foreign keys** — DWS/GaussDB limitation.
- **No SERIAL/auto-increment** — keys must be managed externally.
- **No materialized views** — uses regular views (re-execute on every query).
- **Risk level comparison uses `MAX(risk_level)`** in views — this is alphabetical, not severity-weighted (`"MEDIO" > "CRITICO"` alphabetically).

### Dashboard (Streamlit)

- **Risk level case mismatch**: `generate-contract-data.py` produces Title Case (`"Bajo"`, `"Alto"`) but `risk_dashboard.py` expects UPPERCASE (`"BAJO"`, `"ALTO"`). Color mapping will fail silently.
- **DWS connection defaults to hardcoded `10.1.1.10`** if `DWS_ENDPOINT` env var is unset.
- **Auto-refresh uses `time.sleep(10)` + `st.rerun()`** — blocks the server thread; doesn't scale with concurrent users.

### Frontend

- **Astro 5 with `output: 'static'`** — pure SSG, no SSR, no JS framework (vanilla `<script>` tags only).
- **Tailwind CSS v3** (not v4) — uses `@astrojs/tailwind` integration.
- **Custom Tailwind colors**: `gs-navy`, `gs-blue`, `gs-gold` (Huawei Cloud brand), `risk-low/medium/high/critical`.
- **Dify API key is client-side** via `import.meta.env.PUBLIC_DIFY_API_KEY` — exposed in built JS. Must be set in `frontend/.env` before build.
- **COBRANZA_KEY was removed from Authorization header** — The ChatWidget previously used `cobranzaMode ? COBRANZA_KEY : DIFY_KEY` on the Authorization header. Since the COBRANZA key (`app-ZrM7Pal6G2b89drd1zLVssvM`) is also a Dify Chat app key (not an Agent key), both modes now use `DIFY_KEY` exclusively. If you re-add a separate cobranza key, test that the Authorization header still works for both modes.
- **Deep Analysis AI button uses event delegation** — The `openChatWithQuery` function in `risk-scoring.astro` dispatches a submit event on `#chat-form`, NOT a raw fetch call. This ensures the Authorization header from ChatWidget is included. If you replace this function, maintain the form-submit pattern.
- **`deploy.sh` hardcodes ECS IP `149.232.129.39`** — should be from Terraform output.
- **Streamlit Dashboard servido vía nginx proxy** — puerto 8501 bloqueado en redes corporativas. Acceso: `/dashboard/` en el Web ECS (149.232.129.39) → proxy_pass a `localhost:8501`.
- **Dify Chat API Proxy** — endpoint `/api/chat?query=...` en el FastAPI del ECS web (149.232.129.39:8001). Llama Dify `/v1/chat-messages` con API key `app-Y8MxfRygyUWOAfyTlo1MQSJx`.
- **Risk score threshold logic is duplicated** across `RiskGauge.astro`, `ContractUploader.astro`, and page files.
- **`stagger-children` CSS only handles 4 children** — 5th+ child won't animate.
- **ContractUploader connects to real `/api/upload`** — POSTs PDF, polls `/api/status/{job_id}` for 30s. Real OCR pipeline.

## Credentials & Secrets

- **1Password CLI** for production secrets: `scripts/setup-secrets.sh` reads from vault "Huawei".
- Required env vars in `.env` (gitignored): `HUAWEI_ACCESS_KEY`, `HUAWEI_SECRET_KEY`, `MAAS_API_KEY`, `DEEPSEEK_API_KEY`, `DWS_ADMIN_PASSWORD`.
- Terraform vars in `terraform/terraform.tfvars` (gitignored): same keys + `presenter_ip`.
- `setup-dify.sh` supports `op://` URIs — if `MAAS_API_KEY` starts with `op://`, it resolves via `op read`.

## Project Conventions

- **Terraform tagging**: `{ project = "ayco", environment = "demo", managed_by = "terraform" }` on all resources.
- **Module structure**: each module has its own `variables.tf` with provider pinning. Outputs via `outputs.tf`.
- **Python scripts**: use `random.seed(42)` for reproducible demo data. First 3 contracts are canonical (match real PDFs), rest are synthetic.
- **Shell scripts**: `set -euo pipefail` where present. Colored output with pass/warn/fail counters.
- **Spanish-language data**: RFC codes, Mexican addresses, CNBV anomaly patterns. LLM prompts are in Spanish.
- **Three-layer DWS schema**: ODS (raw) → DW (star schema) → DM (analytical views).

## Key Files Quick Reference

| File | Purpose |
|------|---------|
| `Makefile` | All orchestration commands |
| `terraform/main.tf` | Root module wiring (provider + 4 module calls) |
| `terraform/variables.tf` | Root-level variables (region, credentials, flags) |
| `terraform/modules/foundation/main.tf` | VPC, subnet, security groups, OBS, KMS, IAM |
| `terraform/modules/compute/main.tf` | ECS instances (dify + web) with user-data |
| `terraform/modules/data-platform/dws.tf` | DWS (GaussDB) cluster |
| `terraform/modules/data-platform/dli.tf` | DLI database (mostly commented out) |
| `terraform/modules/data-platform/dataarts.tf` | DataArts Studio (ETL + REST API) |
| `terraform/modules/ai-ocr/functiongraph.tf` | 3 serverless functions (OCR → parse → LLM) |
| `scripts/seed-dws.sql` | DWS schema (ods/dw/dm + risk_results) |
| `scripts/generate-test-data.py` | 2,300 vendors + 500 customers + 5,000 transactions |
| `scripts/generate-contract-data.py` | 20 contract risk results + seed SQL |
| `scripts/setup-dify.sh` | Deploy Dify + Streamlit dashboard to ECS |
| `dashboards/risk_dashboard.py` | Streamlit contract risk dashboard |
| `frontend/src/pages/index.astro` | Landing page (Astro SSG) |
| `docs/demo-script.md` | Step-by-step demo guide |
| `docs/prep-checklist.md` | Workshop preparation checklist |
