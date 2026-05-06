# AYCO × Huawei Cloud — Project Context & Instructions

This project is an Infrastructure-as-Code (IaC) and Data/AI pipeline for the AYCO (Grupo Salinas) Huawei Cloud workshop. It automates the deployment of a contract risk analysis system using Huawei Cloud native services and advanced LLMs.

## Project Overview

- **Purpose:** Demonstrate a complete OCR → AI Analysis → Data Warehouse → Dashboard pipeline on Huawei Cloud.
- **Architecture:**
    - **Compute:** ECS (Dify, Streamlit, Astro Web), FunctionGraph (Serverless processing).
    - **Data:** OBS (Object Storage), DWS (Data Warehouse), DLI (Spark SQL), DataArts Studio.
    - **AI:** MaaS (DeepSeek v4 Flash via Huawei Cloud), Dify (RAG Chatbot), OCR.
    - **Observability:** Langfuse (LLM tracing).
- **Primary Tech Stack:** Terraform, Python, Astro, Streamlit, PostgreSQL (DWS), Bash, Makefile.

## Core Directories

- `terraform/`: Infrastructure modules (foundation, compute, data-platform, ai-ocr).
- `scripts/`: Python and Bash scripts for data generation, deployment, and pipeline logic.
- `frontend/`: Astro-based landing page.
- `dashboards/`: Streamlit dashboard for risk visualization.
- `docs/`: Extensive documentation (demo scripts, architecture, prep checklists).
- `data/`: Sample contract PDFs and synthetic data generation inputs.

## Building and Running

The project uses a `Makefile` for orchestration.

### Initial Setup
```bash
cp .env.example .env
cp terraform.tfvars.example terraform/terraform.tfvars
# Edit credentials in .env and terraform/terraform.tfvars
make init
```

### Full Deployment
```bash
make demo   # Deploys infra, generates data, and runs health checks
```

### Key Operational Commands
- `make status`: Checks health of all deployed services.
- `make upload-contracts`: Uploads demo PDFs to OBS, triggering the OCR pipeline.
- `make frontend`: Builds the Astro web interface.
- `make dashboard`: Deploys the Streamlit risk dashboard.
- `make destroy`: Tears down all infrastructure.

## Development Conventions

- **Infrastructure:** Use Terraform for all resource provisioning. Modules are separated by logical layer.
- **AI Pipeline:**
    - OCR triggers are handled by FunctionGraph.
    - LLM calls use MaaS (DeepSeek) with a fallback mechanism to the direct DeepSeek API.
    - Every LLM interaction must be traced via Langfuse.
- **Data Engineering:**
    - Synthetic data generation (Python) is used to populate DWS for the demo.
    - SQL schemas and views are managed in `scripts/seed-dws.sql`.
- **Frontend/Dashboard:**
    - The landing page is built with Astro + Tailwind CSS.
    - The real-time dashboard is built with Streamlit and connects directly to DWS.

## AI Pipeline Flow
1. **Upload:** PDF uploaded to OBS (`ayco-contracts-input`).
2. **OCR:** FunctionGraph triggered to extract raw text → Saved to OBS (`ayco-contracts-text`).
3. **Parse:** FunctionGraph extracts structured fields (Contract #, Amount, etc.) → Saved to OBS (`ayco-contracts-results`).
4. **Analyze:** MaaS/DeepSeek performs risk analysis → Structured JSON response.
5. **Load:** Results ingested into DWS (`risk_results` table) for visualization.
6. **Observe:** All LLM steps traced in Langfuse.

## Security Note
- Cloud Firewall (`cfw.tf`) is currently commented out in Terraform and should not be provisioned unless explicitly requested for hardening steps.
- Secrets are managed via `.env` and `terraform.tfvars`. Use `scripts/setup-secrets.sh` if 1Password CLI is available.
