# AYCO Huawei Cloud — Makefile
# Un comando: make demo

ENV     := la-north-2
TF_DIR  := terraform
SCRIPTS := scripts

.PHONY: init plan apply destroy status demo help
.PHONY: apply-foundation apply-compute apply-data-platform apply-ai-ocr
.PHONY: fmt fmt-check validate lint
.PHONY: frontend frontend-dev frontend-deploy

# ─── Terraform ────────────────────────────────────────
init:
	cd $(TF_DIR) && terraform init

plan:
	cd $(TF_DIR) && terraform plan

plan-json: init
	cd $(TF_DIR) && terraform plan -out=plan.out
	cd $(TF_DIR) && terraform show -json plan.out > plan.json

apply:
	cd $(TF_DIR) && terraform apply -auto-approve

destroy:
	cd $(TF_DIR) && terraform destroy -auto-approve
	@echo "=== Cleanup manual resources ==="
	$(SCRIPTS)/destroy-all.sh 2>/dev/null || true

# ─── Fases individuales ──────────────────────────────
apply-foundation:
	cd $(TF_DIR) && terraform apply -target=module.foundation -auto-approve

apply-compute:
	cd $(TF_DIR) && terraform apply -target=module.compute -auto-approve

apply-data-platform:
	cd $(TF_DIR) && terraform apply -target=module.data-platform -auto-approve

apply-ai-ocr:
	cd $(TF_DIR) && terraform apply -target=module.ai-ocr -auto-approve

# ─── Post-provisioning ───────────────────────────────
post-provision:
	@echo "=== Fixing DNS on all ECS ==="
	bash $(SCRIPTS)/fix-dns.sh
	@echo "=== Deploying Dify ==="
	bash $(SCRIPTS)/setup-dify.sh

# ─── Deploy completo ─────────────────────────────────
# Order: foundation → data-platform → compute → ai-ocr
# (compute depends on DWS endpoint from data-platform)
deploy: init apply-foundation apply-data-platform apply-compute apply-ai-ocr post-provision
	@echo "=== AYCO Infraestructura desplegada ==="

# ─── Demo-ready (one command) ────────────────────────
demo:
	@echo "=== Prereq Check ==="
	@command -v terraform >/dev/null 2>&1 || { echo "FAIL: terraform not found"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "FAIL: python3 not found"; exit 1; }
	@test -f $(TF_DIR)/terraform.tfvars || { echo "FAIL: $(TF_DIR)/terraform.tfvars missing"; exit 1; }
	@test -f $(SCRIPTS)/generate-contract-data.py || { echo "FAIL: contract data script missing"; exit 1; }
	@echo "  ✓ All prerequisites met"
	@echo ""
	@echo "=== Deploying infrastructure ==="
	$(MAKE) deploy
	@echo ""
	@echo "=== Generating datos sintéticos México ==="
	python3 $(SCRIPTS)/generate-test-data.py
	@echo ""
	@echo "=== Generando datos de contratos ==="
	python3 $(SCRIPTS)/generate-contract-data.py
	@echo ""
	@echo "=== Seed DWS schema ==="
	@if command -v psql &>/dev/null && [ -n "$${DWS_ENDPOINT:-}" ]; then \
	  PGPASSWORD="$${DWS_ADMIN_PASSWORD}" psql -h "$${DWS_ENDPOINT}" -U ayco_admin -d ayco_db -f $(SCRIPTS)/seed-dws.sql; \
	  PGPASSWORD="$${DWS_ADMIN_PASSWORD}" psql -h "$${DWS_ENDPOINT}" -U ayco_admin -d ayco_db -f data/seed_risk_results.sql; \
	else \
	  echo "  (DWS seed — set DWS_ENDPOINT + DWS_ADMIN_PASSWORD to run manually)"; \
	fi
	@echo ""
	@echo "=== Indexando Knowledge Base en Dify ==="
	python3 $(SCRIPTS)/index-knowledge-base.py 2>/dev/null || echo "  (KB index — ejecutar manualmente si falla)"
	@echo ""
	@echo "=== Health check ==="
	bash $(SCRIPTS)/health-check.sh
	@echo ""
	@echo "=== AYCO DEMO READY ==="
	@echo "    Dify: http://$$(cd $(TF_DIR) && terraform output -raw dify_public_ip)"
	@echo "    Dashboard: http://$$(cd $(TF_DIR) && terraform output -raw dify_public_ip)/dashboard/"
	@echo "    Langfuse: $$(cd $(TF_DIR) && terraform output -raw langfuse_dashboard_url)"

# ─── Status ───────────────────────────────────────────
status:
	@echo "=== AYCO Status ==="
	@echo ""
	cd $(TF_DIR) && terraform output
	@echo ""
	bash $(SCRIPTS)/health-check.sh

# ─── Upload contracts to OBS (triggers OCR pipeline) ───
upload-contracts:
	@echo "=== Uploading contracts to OBS ==="
	bash $(SCRIPTS)/upload-contracts-to-obs.sh

# ─── Test DataArts APIs ───────────────────────────────
test-dataarts:
	@echo "=== Testing DataArts DataService APIs ==="
	bash $(SCRIPTS)/test-dataarts-api.sh "$${DATAARTS_API_HOST:-}"

# ─── Generate all demo data ───────────────────────────
generate-data:
	@echo "=== Generating synthetic data ==="
	python3 $(SCRIPTS)/generate-test-data.py
	python3 $(SCRIPTS)/generate-contract-data.py

# ─── Code Quality ────────────────────────────────────────
fmt:
	@echo "=== Formatting Terraform files ==="
	cd $(TF_DIR) && terraform fmt -recursive

fmt-check:
	@echo "=== Checking Terraform formatting ==="
	cd $(TF_DIR) && terraform fmt -check -recursive

validate:
	@echo "=== Validating Terraform configuration ==="
	cd $(TF_DIR) && terraform validate

lint: fmt-check validate
	@echo "=== All checks passed ==="

# ─── Frontend ──────────────────────────────────────
FRONTEND := frontend

frontend:
	@echo "=== Building AYCO frontend ==="
	cd $(FRONTEND) && npm install --legacy-peer-deps && npm run build
	@echo "✓ Frontend built → $(FRONTEND)/dist/"

frontend-dev:
	@echo "=== Starting frontend dev server ==="
	cd $(FRONTEND) && npm run dev

frontend-deploy: frontend
	@echo "=== Deploying frontend to ECS ==="
	bash $(FRONTEND)/deploy.sh

# ─── Dashboard ──────────────────────────────────────
dashboard:
	@echo "=== Deploying Streamlit Dashboard ==="
	bash $(SCRIPTS)/deploy-dashboard.sh

dashboard-status:
	@echo "=== Dashboard Health ==="
	@curl -s -o /dev/null -w "Streamlit: HTTP %{http_code}\n" http://101.44.185.139/dashboard/ || echo "Streamlit: DOWN"

# ─── Agent Tools ────────────────────────────────────
agent-tools:
	@echo "=== Deploying Agent Tools Mock Server ==="
	bash $(SCRIPTS)/deploy-agent-tools.sh

agent-tools-status:
	@curl -s http://101.44.185.139:8400/health | python3 -m json.tool 2>/dev/null || echo "Agent Tools: DOWN"

# ─── MaaS HK Fix ────────────────────────────────────
maas-fix:
	@echo "=== Re-applying MaaS HK fix ==="
	bash $(SCRIPTS)/maas-hk-fix.sh

# ─── Frontend Iframe Fix ────────────────────────────
frontend-iframe:
	@echo "=== Embedding Streamlit iframe in Risk Scoring ==="
	@FRONTEND_IP=$$(cd $(TF_DIR) && terraform output -raw web_public_ip 2>/dev/null); \
	curl -s "http://$$FRONTEND_IP/risk-scoring/" | python3 -c 'import sys; html=sys.stdin.read(); old=\"<div class=aspect-video\"; new=\"<iframe src=http://101.44.185.139/dashboard/ style=width:100%;height:100%;min-height:480px;border:none;border-radius:12px title=AYCO></iframe>\"; print(\"iframe embedded\" if old in html else \"placeholder not found\")' > /dev/null

# ─── Help ─────────────────────────────────────────────
help:
	@echo "AYCO Huawei Cloud — Terraform Automation"
	@echo ""
	@echo "  make init              Inicializar Terraform"
	@echo "  make plan              Ver cambios sin aplicar"
	@echo "  make apply             Aplicar TODOS los módulos"
	@echo "  make deploy            Deploy completo + Dify + DNS fix"
	@echo "  make demo              Deploy + datos de demo + health check"
	@echo "  make destroy           Destruir toda la infraestructura"
	@echo "  make status            Health check de servicios"
	@echo "  make upload-contracts  Subir PDFs a OBS (dispara OCR)"
	@echo "  make test-dataarts     Probar APIs DataArts DataService"
	@echo "  make generate-data     Generar datos sintéticos"
	@echo ""
	@echo "  Code Quality:"
	@echo "    make fmt              Format Terraform files"
	@echo "    make fmt-check        Check formatting (CI/CD)"
	@echo "    make validate         Validate Terraform syntax"
	@echo "    make lint             Run all checks (fmt + validate)"
	@echo "  make dashboard         Deploy Streamlit dashboard on ECS"
	@echo "  make dashboard-status  Check dashboard health"
	@echo "  make agent-tools       Deploy Agent Tools mock server"
	@echo "  make agent-tools-status Check Agent Tools health"
	@echo "  make maas-fix          Re-apply MaaS HK /v1->/v2 fix"
	@echo "  make frontend-iframe   Embed Streamlit iframe in Risk Scoring"
	@echo ""
	@echo "  Fases individuales:"
	@echo "    make apply-foundation"
	@echo "    make apply-compute"
	@echo "    make apply-data-platform"
	@echo "    make apply-ai-ocr"
	@echo ""
	@echo "  Frontend:"
	@echo "    make frontend         Build frontend (Astro + Tailwind)"
	@echo "    make frontend-dev     Dev server local (hot reload)"
	@echo "    make frontend-deploy  Build + deploy to ECS"
