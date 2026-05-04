# AYCO Huawei Cloud — Makefile
# Un comando: make demo

ENV     := la-north-2
TF_DIR  := terraform
SCRIPTS := scripts

.PHONY: init plan apply destroy status demo help
.PHONY: apply-foundation apply-compute apply-data-platform apply-ai-ocr

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
deploy: init apply-foundation apply-compute apply-data-platform apply-ai-ocr post-provision
	@echo "=== AYCO Infraestructura desplegada ==="

# ─── Demo-ready (one command) ────────────────────────
demo: deploy
	@echo "=== Generando datos sintéticos México ==="
	python3 $(SCRIPTS)/generate-test-data.py
	@echo "=== Seed DWS schema ==="
	@if command -v psql &>/dev/null && [ -n "$${DWS_ENDPOINT:-}" ]; then \
	  PGPASSWORD="$${DWS_ADMIN_PASSWORD}" psql -h "$${DWS_ENDPOINT}" -U ayco_admin -d ayco -f $(SCRIPTS)/seed-dws.sql; \
	else \
	  echo "  (DWS seed — set DWS_ENDPOINT + DWS_ADMIN_PASSWORD to run manually)"; \
	fi
	@echo "=== Indexando Knowledge Base en Dify ==="
	python3 $(SCRIPTS)/index-knowledge-base.py 2>/dev/null || echo "  (KB index — ejecutar manualmente si falla)"
	@echo "=== Health check ==="
	bash $(SCRIPTS)/health-check.sh
	@echo ""
	@echo "=== AYCO DEMO READY ==="
	@echo "    Dify: http://$$(cd $(TF_DIR) && terraform output -raw dify_public_ip)"

# ─── Status ───────────────────────────────────────────
status:
	@echo "=== AYCO Status ==="
	@echo ""
	cd $(TF_DIR) && terraform output
	@echo ""
	bash $(SCRIPTS)/health-check.sh

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
	@echo ""
	@echo "  Fases individuales:"
	@echo "    make apply-foundation"
	@echo "    make apply-compute"
	@echo "    make apply-data-platform"
	@echo "    make apply-ai-ocr"
