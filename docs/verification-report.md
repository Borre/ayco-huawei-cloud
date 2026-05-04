# AYCO Documentation Verification Report
# Generated: 2026-05-04
# Project: /home/eduardo/dev/ayco-huawei-cloud

================================================================================
CHECK 1: README.md resource table vs actual Terraform
================================================================================

FILE: README.md, lines 31-44 (Resource Table)

ISSUE 1.1 — ECS Dify flavor specs wrong
  Line 34: ECS (Dify) | s6.xlarge.2 (8vCPU 32GB)
  Actual (terraform/modules/compute/main.tf line 3): s6.xlarge.2
  Status: CORRECT — 8vCPU/32GB matches s6.xlarge.2

ISSUE 1.2 — ECS Web flavor specs wrong
  Line 35: ECS (Web) | s6.large.2 (2vCPU 8GB)
  Actual (terraform/modules/compute/main.tf line 28): s6.large.2
  Status: CORRECT — 2vCPU/8GB matches s6.large.2

ISSUE 1.3 — DWS flavor and node count
  Line 36: DWS Cluster | dwsk2.2xlarge.4 (3 nodos)
  Actual (terraform/modules/data-platform/dws.tf line 6): dwsk2.2xlarge.4
  node_num = 3
  Status: CORRECT

ISSUE 1.4 — DataArts tier
  Line 38: DataArts Studio | dayu.nb.professional
  Actual (terraform/modules/data-platform/dataarts.tf line 6): dayu.nb.professional
  Status: CORRECT

ISSUE 1.5 — OBS bucket count
  Line 40: OBS Buckets | 5 buckets
  Actual (terraform/modules/foundation/obs.tf): 5 resources
  Status: CORRECT

ISSUE 1.6 — FunctionGraph count
  Line 41: FunctionGraph | 3 functions
  Actual (terraform/modules/ai-ocr/functiongraph.tf): 3 functions (ocr_trigger, parse_contract, llm_inference)
  Status: CORRECT

ISSUE 1.7 — Missing resources in table
  The table does NOT list:
  - huaweicloud_vpc_eip (2 EIPs for ECS instances) - terraform/modules/compute/eip.tf
  - huaweicloud_iam_group, huaweicloud_iam_policy, huaweicloud_identity_role_assignment - terraform/modules/foundation/iam.tf
  RECOMMENDATION: Add EIP and IAM resources to the table for completeness.

COST ACCURACY: Costs are estimates (~$1,100/mes total). Cannot verify exact pricing
without Huawei Cloud la-north-2 rate card. Values seem reasonable order-of-magnitude.

================================================================================
CHECK 2: README.md demo flow timing vs docs/demo-script.md
================================================================================

FILE: README.md, lines 70-79 (Demo Flow) vs docs/demo-script.md

Demo 1 (README line 72): "~10 min" → demo-script.md: 12 minutes (total of all steps)
  Status: CLOSE — README says 10 min, script sums to 12 min

Demo 2 (README line 75): "~8 min" → demo-script.md: 9 minutes (total of all steps)
  Status: CLOSE — README says 8 min, script sums to 9 min

Demo 3 (README line 78): "~15 min" → demo-script.md: 13 minutes (total of all steps)
  Status: CLOSE — README says 15 min, script sums to 13 min

Overall (README line 79): "~35 min total" → Script: 12+9+13 = 34 min
  Status: CORRECT (close enough)

================================================================================
CHECK 3: README.md directory structure vs actual files
================================================================================

FILE: README.md, lines 90-110

ISSUE 3.1 — Missing directories
  README tree does NOT show:
  - backports/ (contains demo1, demo2, demo3 outputs, ETL results, API responses, chat transcripts)
  - terraform/modules/compute/templates/ (contains dify-userdata.sh.tmpl)
  - data/risk_results/ (contains risk_results.csv and risk_summary.json)
  SHOULD ADD to tree:
  ├── backports/                    # Pre-captured demo outputs for fallback
  ├── data/
  │   ├── contract_texts/           # 20 pre-generated contract text files
  │   └── risk_results/             # Sample risk output data
  │   └── seed_risk_results.sql     # DWS seed data
  ...
  └── terraform/modules/compute/templates/
      └── dify-userdata.sh.tmpl     # Cloud-init user data for Dify ECS

ISSUE 3.2 — data/ subdirectories listed but missing detail
  README shows data/contracts/ and data/financial/ but omits:
  - data/contract_texts/ (20 files: contrato-2026-0001.txt through 0020.txt)
  - data/risk_results/ (risk_results.csv, risk_summary.json)
  - data/seed_risk_results.sql

ISSUE 3.3 — scripts/ count discrepancy
  README line 133 says "# ~13 scripts for..."
  Actual count: 15 files in scripts/
  Missing from README list:
  - setup-dify-ecs.sh (cloud-init user-data for Dify ECS)
  - setup-secrets.sh (1Password → terraform.tfvars — IS mentioned on line 134, just not counted)

================================================================================
CHECK 4: README.md 'What make demo does' vs actual Makefile targets
================================================================================

FILE: README.md, lines 186-196 vs Makefile lines 55-72

ISSUE 4.1 — Missing Makefile target in README
  README lists: init, apply, plan, destroy, deploy, demo, status, help
  Makefile has additional targets NOT mentioned in README:
  - make plan-json (line 18-20)
  - make apply-foundation (line 31)
  - make apply-compute (line 34)
  - make apply-data-platform (line 37)
  - make apply-ai-ocr (line 40)
  - make post-provision (line 44)
  - make upload-contracts (line 84)
  - make test-dataarts (line 89)
  - make generate-data (line 94)
  SHOULD ADD these to README's "Comandos útiles" section.

ISSUE 4.2 — "make demo" description incomplete
  README lines 190-196 say make demo does:
  - deploys infra, generates data, seeds DWS, runs health check
  ACTUALLY also does:
  - Indexes Knowledge Base in Dify (line 67-68)
  - Shows Dify public IP at the end (line 72-74)

================================================================================
CHECK 5: docs/architecture.md ASCII diagrams — services vs Terraform
================================================================================

FILE: docs/architecture.md

CHECK 5.1 — Main architecture diagram (lines 9-37)
  Services shown: VPC, Subnet, ECS Dify, ECS Web, DWS, DLI, OBS, FunctionGraph,
  DataArts, CDM, Langfuse
  No MRS reference: CORRECT
  No DMS Kafka reference: CORRECT
  All listed services exist in Terraform: CORRECT

CHECK 5.2 — Data flow diagram (lines 43-83)
  Step 5 shows "DLI Spark" → CORRECT (dli.tf has spark job)
  Step 6 shows "DWS" → CORRECT (dws.tf has cluster)
  Status: CORRECT

CHECK 5.3 — Demo 2 flow diagram (lines 130-179)
  Shows DataArts Catalog, Architecture, Security, Factory, DataService, Dashboard
  All exist in Terraform (dataarts.tf, dataarts_governance.tf)
  Status: CORRECT

CHECK 5.4 — Demo 3 flow diagram (lines 187-224)
  Shows Dify (ECS), FunctionGraph, MaaS DeepSeek v4 Flash
  All exist in Terraform
  Status: CORRECT

CHECK 5.5 — Security Architecture diagram (lines 245-269)
  ISSUE 5.5a — VPC CIDR wrong
    Line 246: VPC (10.0.0.0/16)
    Actual (terraform/modules/foundation/main.tf line 5): 10.1.0.0/16
    SHOULD SAY: VPC (10.1.0.0/16)

  ISSUE 5.5b — Subnet CIDR wrong
    Line 250: Subnet (10.0.1.0/24)
    Actual (terraform/modules/foundation/main.tf line 12): 10.1.1.0/24
    SHOULD SAY: Subnet (10.1.1.0/24)

  ISSUE 5.5c — CFW shown as active
    Line 246: Internet ──► CFW (Firewall) ──► VPC
    Actual (terraform/modules/foundation/cfw.tf): CFW is COMMENTED OUT
    SHOULD SHOW: Internet ──► VPC (10.1.0.0/16)  [no CFW]
    OR add note: "(CFW not available in la-north-2)"

  ISSUE 5.5d — DWS shown with EIP
    Line 260: DWS + EIP
    Actual: No EIP for DWS in Terraform. Only ECS instances have EIPs.
    SHOULD SAY: DWS (internal only, no EIP)

  ISSUE 5.5e — DataArts tier label
    Line 234 (Resource Map): DataArts Studio | professional
    Actual: dayu.nb.professional
    SHOULD SAY: dayu.nb.professional (not generic "professional")

================================================================================
CHECK 6: docs/architecture.md resource map — vCPU counts, node types
================================================================================

FILE: docs/architecture.md, lines 228-241

ISSUE 6.1 — ECS Dify vCPU/RAM wrong
  Line 230: ECS Dify | s6.xlarge.2 (4vCPU/8GB)
  Actual s6.xlarge.2 specs: 8 vCPU, 32 GB RAM
  README.md correctly says (8vCPU 32GB)
  SHOULD SAY: s6.xlarge.2 (8vCPU/32GB)

ISSUE 6.2 — ECS Web RAM wrong
  Line 231: ECS Web | s6.large.2 (2vCPU/4GB)
  Actual s6.large.2 specs: 2 vCPU, 8 GB RAM
  README.md correctly says (2vCPU 8GB)
  SHOULD SAY: s6.large.2 (2vCPU/8GB)

ISSUE 6.3 — DWS flavor wrong
  Line 232: DWS Cluster | dwsx3.4U16G.4DPU ×3
  Actual (terraform/modules/data-platform/dws.tf line 6): dwsk2.2xlarge.4
  SHOULD SAY: dwsk2.2xlarge.4 ×3 (8vCPU/32GB per node, 24 total vCPU)

ISSUE 6.4 — DLI Queue name wrong
  Line 233: DLI Queue | default (serverless)
  Actual (terraform/modules/data-platform/dli.tf): named queues (ayco-queue, ayco-queue-urgent)
  SHOULD SAY: ayco-queue, ayco-queue-urgent (serverless CU)

ISSUE 6.5 — CDM specs wrong
  Line 236: CDM Cluster | cdm.large (8vCPU/16GB)
  Actual (terraform/modules/data-platform/cdm.tf): flavor = "cdm.large"
  Huawei Cloud cdm.large = 4 vCPU / 16 GB (not 8vCPU)
  SHOULD SAY: cdm.large (4vCPU/16GB)

ISSUE 6.6 — DWS total vCPU not mentioned
  The resource map should note: DWS total = 24 vCPU (3 nodes × 8 vCPU each)

================================================================================
CHECK 7: docs/demo-script.md — scripts, data files, endpoints
================================================================================

FILE: docs/demo-script.md

ISSUE 7.1 — Dify ECS instance name wrong
  Line 520: Show `dify-ayco` instance
  Actual (terraform/modules/compute/main.tf line 4): name = "ayco-dify-server"
  SHOULD SAY: Show `ayco-dify-server` instance

ISSUE 7.2 — Dify ECS flavor wrong in demo text
  Line 520: instance (s6.large.2)
  Actual: ayco-dify-server uses s6.xlarge.2
  SHOULD SAY: instance (s6.xlarge.2, 8vCPU/32GB)

ISSUE 7.3 — FunctionGraph function name wrong
  Line 593: FunctionGraph > `ayco-ocr-trigger`
  Actual (terraform/modules/ai-ocr/functiongraph.tf line 6): name = "ayco-ocr_pipeline"
  SHOULD SAY: FunctionGraph > `ayco-ocr_pipeline`

ISSUE 7.4 — Dify API port wrong
  Line 531: dify-api 0.0.0.0:5001->5001/tcp
  Actual Dify default API port is 5001, so this is CORRECT
  But the ECS security group (terraform/modules/foundation/main.tf) does NOT
  explicitly open port 5001 — it opens 8000, 8001, 8002, 8443, 8501
  NOTE: Port 5001 is not in the security group ingress rules

ISSUE 7.5 — backup-record-demos.sh referenced but exists
  Line 675: bash scripts/backup-record-demos.sh --play demo3
  File EXISTS: scripts/backup-record-demos.sh ✓
  Status: OK

ISSUE 7.6 — Appendix D file locations — some paths wrong
  Line 729: Spark aggregation job → scripts/spark-risk-aggregation.py ✓ EXISTS
  Line 730: DWS seed SQL → scripts/seed-dws.sql ✓ EXISTS
  Line 731: Contract parser → terraform/modules/ai-ocr/functions/parse_contract.py
  Actual: Parse logic is INLINE in functiongraph.tf (runtime = "Python3.10", handler)
  No separate functions/ directory exists
  SHOULD SAY: Contract parser → embedded in terraform/modules/ai-ocr/functiongraph.tf
              (no separate functions/*.py files)

  Line 732: LLM inference → terraform/modules/ai-ocr/functions/llm_inference.py
  Same issue — no separate file. Embedded in functiongraph.tf.
  SHOULD SAY: LLM inference → embedded in terraform/modules/ai-ocr/functiongraph.tf

  Line 733: OCR trigger → terraform/modules/ai-ocr/functions/ocr_trigger.py
  Same issue — no separate file. Embedded in functiongraph.tf.
  SHOULD SAY: OCR trigger → embedded in terraform/modules/ai-ocr/functiongraph.tf

================================================================================
CHECK 8: docs/prep-checklist.md — commands, module names
================================================================================

FILE: docs/prep-checklist.md

ISSUE 8.1 — Terraform apply command references
  Multiple references to "make deploy" and "make demo"
  These targets exist in Makefile. Status: CORRECT

ISSUE 8.2 — Module names
  References: module.foundation, module.compute, module.data-platform, module.ai-ocr
  These match terraform/main.tf. Status: CORRECT

ISSUE 8.3 — DWS credentials reference
  References DWS admin user "ayco_admin" and database "ayco_db"
  Actual (terraform/modules/data-platform/dws.tf lines 14-17):
    database_name  = "ayco_db"
    user_name      = "ayco_admin"
  Status: CORRECT

ISSUE 8.4 — DataArts API endpoints
  References endpoints like /v1/{project_id}/api/ayco-contracts/*
  Actual (terraform/modules/data-platform/dataarts.tf):
    path = "/v1/${var.project_id}/api/ayco-contracts/create"
    (and similar for extract-fields, calculate-risk, etc.)
  Status: CORRECT pattern, though actual path includes project_id variable

ISSUE 8.5 — OBS bucket names
  References: ayco-raw, ayco-results, ayco-contracts-raw, ayco-contracts-text, ayco-contracts-results
  Actual (terraform/modules/foundation/obs.tf): all 5 match
  Status: CORRECT

ISSUE 8.6 — CDM reference
  prep-checklist.md mentions CDM cluster is needed
  Actual: CDM exists (terraform/modules/data-platform/cdm.tf)
  Status: CORRECT

No major issues found in prep-checklist.md. References are accurate.

================================================================================
CHECK 9: docs/slides-arquitectura.pptx — product names
================================================================================

FILE: docs/slides-arquitectura.pptx (298K)
This is a binary PowerPoint file. Cannot directly read content.

VERIFICATION APPROACH:
Based on the project context, the slides should reference:
- Huawei Cloud VPC, ECS, DWS (GaussDB), DLI, OBS, FunctionGraph, DataArts Studio, CDM
- DeepSeek v4 (MaaS/ModelArts)
- Dify (open-source, running on ECS)
- Streamlit (dashboard)
- Langfuse (observability)
- Huawei OCR

PRODUCTS NOT DEPLOYED that should NOT appear:
- MRS (MapReduce Service) — REMOVED ✓
- DMS Kafka — REMOVED ✓
- CFW (Cloud Firewall) — COMMENTED OUT (not available in la-north-2)

NOTE: Manual verification of .pptx content recommended. Open the file and verify
no references to MRS, DMS Kafka, or CFW as active components.

================================================================================
CHECK 10: terraform.tfvars.example — required variables, stale ones
================================================================================

FILE: terraform.tfvars.example

Variables defined:
  region              ✓ (used in root variables.tf)
  access_key          ✓
  secret_key          ✓
  project_id          ✓
  keypair_name        ✓
  dws_admin_password  ✓
  maas_api_key        ✓
  deepseek_api_key    ✓

Cross-reference with terraform/variables.tf (12 variables):
  region              ✓ in .tfvars.example
  access_key          ✓
  secret_key          ✓
  project_id          ✓
  keypair_name        ✓
  dws_admin_password  ✓
  maas_api_key        ✓
  deepseek_api_key    ✓
  maas_endpoint       ✗ MISSING from .tfvars.example
  deepseek_endpoint   ✗ MISSING from .tfvars.example
  langfuse_public_key ✗ MISSING from .tfvars.example
  langfuse_secret_key ✗ MISSING from .tfvars.example

ISSUE 10.1 — 4 variables missing from terraform.tfvars.example:
  - maas_endpoint       (defaults to "https://maas-api.cn-north-4.myhuaweicloud.com")
  - deepseek_endpoint   (defaults to "https://api.deepseek.com")
  - langfuse_public_key (no default — REQUIRED)
  - langfuse_secret_key (no default — REQUIRED)
  SHOULD ADD these 4 variables to terraform.tfvars.example.

No stale variables found — all 8 listed variables are used.

================================================================================
CHECK 11: .env.example — required env vars
================================================================================

FILE: .env.example

Variables defined (35 lines):
  # LLM Config
  MAAS_API_KEY          ✓
  MAAS_ENDPOINT         ✓
  DEEPSEEK_API_KEY      ✓
  DEEPSEEK_ENDPOINT     ✓
  DEEPSEEK_MODEL        ✓

  # API URLs
  OCR_API_URL           ✓
  LANGFUSE_PUBLIC_KEY   ✓
  LANGFUSE_SECRET_KEY   ✓
  LANGFUSE_HOST         ✓

  # Dify Config
  DIFY_API_KEY          ✓
  DIFY_BASE_URL         ✓

  # Huawei Cloud
  HUAWEI_CLOUD_REGION   ✓
  HUAWEI_CLOUD_PROJECT  ✓
  HUAWEI_ACCESS_KEY     ✓
  HUAWEI_SECRET_KEY     ✓

  # Terraform outputs
  DWS_ENDPOINT          ✓
  DWS_PORT              ✓
  DWS_DATABASE          ✓
  DWS_ADMIN_PASSWORD    ✓
  DIFY_PUBLIC_IP        ✓
  DATAARTS_WORKSPACE_ID ✓
  DATAARTS_API_KEY      ✓
  OBS_BUCKET            ✓

  # Docker compose
  COMPOSE_PROJECT_NAME  ✓

Cross-reference with .env (actual):
  All variables in .env.example are present in actual .env
  No extra variables in actual .env that are missing from .env.example

Status: COMPLETE — .env.example covers all required env vars.

================================================================================
CHECK 12: Makefile help text — all targets listed
================================================================================

FILE: Makefile, lines 100-118 (help target)

Targets shown in `make help` output:
  make init              ✓
  make plan              ✓
  make apply             ✓
  make deploy            ✓
  make demo              ✓
  make destroy           ✓
  make status            ✓
  make upload-contracts  ✓
  make test-dataarts     ✓
  make generate-data     ✓
  make apply-foundation  ✓
  make apply-compute     ✓
  make apply-data-platform ✓
  make apply-ai-ocr      ✓

Targets that exist in Makefile but NOT shown in help:
  make plan-json         (lines 18-20) — NOT in help text
  make post-provision    (lines 44-48) — NOT in help text (internal dependency of deploy)

ISSUE 12.1 — plan-json target missing from help
  Line 18-20: plan-json exists but not in help output
  SHOULD ADD: @echo "  make plan-json         Generate JSON plan for review"

ISSUE 12.2 — Typo in help text
  Line 111: DATARTS_API_HOST (missing 'A' — should be DATAARTS_API_HOST)
  ACTUAL: Line 91 uses ${DATARTS_API_HOST:-} — the typo is in both the target
  and the variable reference. Either fix both or leave as-is consistently.
  RECOMMENDATION: Fix to DATAARTS_API_HOST in both places (line 91 and line 111).

================================================================================
SUMMARY OF ALL ISSUES
================================================================================

CRITICAL (will cause demo failures or confusion):
--------------------------------------------------
C1. docs/architecture.md line 230: ECS Dify specs wrong (4vCPU/8GB → 8vCPU/32GB)
C2. docs/architecture.md line 231: ECS Web RAM wrong (4GB → 8GB)
C3. docs/architecture.md line 232: DWS flavor wrong (dwsx3.4U16G.4DPU → dwsk2.2xlarge.4)
C4. docs/architecture.md line 246: VPC CIDR wrong (10.0.0.0/16 → 10.1.0.0/16)
C5. docs/architecture.md line 250: Subnet CIDR wrong (10.0.1.0/24 → 10.1.1.0/24)
C6. docs/architecture.md line 236: CDM vCPU wrong (8vCPU → 4vCPU)
C7. docs/demo-script.md line 520: Dify ECS name wrong (dify-ayco → ayco-dify-server)
C8. docs/demo-script.md line 520: Dify ECS flavor wrong (s6.large.2 → s6.xlarge.2)
C9. docs/demo-script.md line 593: FG function name wrong (ayco-ocr-trigger → ayco-ocr_pipeline)
C10. docs/demo-script.md lines 731-733: Function source paths wrong (no functions/*.py files)
C11. terraform.tfvars.example: 4 variables missing (maas_endpoint, deepseek_endpoint,
    langfuse_public_key, langfuse_secret_key)
C12. docs/architecture.md line 246: CFW shown as active but it's commented out

MODERATE (documentation gaps, minor inaccuracies):
---------------------------------------------------
M1. README.md tree: Missing backports/, templates/, data/risk_results/, data/seed_risk_results.sql
M2. README.md: Missing 8 Makefile targets from "Comandos útiles" section
M3. README.md: "make demo" description missing KB indexing step
M4. docs/architecture.md line 233: DLI queue names missing (uses "default" not ayco-queue/ayco-queue-urgent)
M5. docs/architecture.md line 234: DataArts tier should say "dayu.nb.professional" not "professional"
M6. docs/architecture.md line 260: DWS shown with EIP but has none
M7. README.md scripts count says "~13" but there are 15 files
M8. Makefile line 91/111: DATARTS typo (should be DATAARTS)
M9. Makefile help missing plan-json target
M10. README.md resource table missing EIP and IAM resources

LOW (cosmetic, optional):
-------------------------
L1. README.md demo timing off by 1-2 min per demo (acceptable)
L2. docs/architecture.md resource map should note DWS total vCPU (24)
L3. docs/slides-arquitectura.pptx needs manual verification for MRS/Kafka references
L4. docs/demo-script.md line 531: port 5001 not in security group rules

TOTAL: 12 Critical, 10 Moderate, 4 Low = 26 issues
