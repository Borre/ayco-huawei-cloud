# AYCO Documentation Verification Report

Generated: 2026-05-04
Project: `/Users/eduardo/dev/ayco-huawei-cloud`

## Current Status

- Terraform validates with the Huawei Cloud provider after `terraform init -backend=false`.
- Shell syntax checks pass for the demo helper scripts.
- Python compilation passes for FunctionGraph code, generators, and the Streamlit dashboard.
- Demo contract IDs are aligned across PDFs, generated DWS seed data, backports, and `docs/demo-script.md`:
  - `AYCO-2026-0147` — high risk — $3.85M MXN — score 8.7/10
  - `AYCO-2026-0148` — low risk — $450K MXN — score 2.3/10
  - `AYCO-2026-0149` — critical — $12.5M MXN — score 9.2/10

## Reality Checks Applied

- Cloud Firewall is not presented as active. The Terraform resource remains commented out and the docs describe security groups as the active control.
- DMS/Kafka is not presented as active. FunctionGraph functions now return explicit payloads for the next step unless a workflow/orchestration layer is added later.
- SSH and demo admin ports are controlled by `presenter_ip`; VPC-internal TCP traffic remains allowed for ECS-to-DWS access.
- Streamlit deployment is no longer only aspirational: `scripts/setup-dify.sh` copies `dashboards/risk_dashboard.py` to the Dify ECS and restarts the dashboard service.
- Missing screenshot fallbacks were removed from the script; backports now use committed text/JSON artifacts.
- Dify knowledge-base indexing now reads `data/risk_results/risk_results.csv`; it no longer generates unrelated fallback contracts.
- DWS contract governance output now uses `dm.contract_vendor_risk_summary`, a materialized view based on `risk_results`.
- `docs/slides-arquitectura.pptx`, `docs/slides-arquitectura.pdf`, and `docs/architecture-diagram.html` were checked against the current implementation: legacy MRS/DMS/Kafka claims are absent, Cloud Firewall/WAF are not listed as active controls, and unsupported latency/availability claims were removed.
- The resource map no longer contains a blank event-streaming row or an unverified CDM vCPU/memory claim.

## Remaining Operator Checks

- Confirm `presenter_ip` is set to the presenter public IP before deployment.
- Confirm DataArts masking behavior in the console/debugger before claiming active role-based masking live.
- Confirm FunctionGraph-to-FunctionGraph orchestration if the demo should show a fully automatic chain instead of explicit invocations.
- If the PDF needs to preserve the original PowerPoint styling exactly, regenerate it from PowerPoint/LibreOffice after opening the corrected PPTX. The tracked PDF content is accurate but intentionally simplified because no Office/Pandoc renderer is installed in this workspace.
