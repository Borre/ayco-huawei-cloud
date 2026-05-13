# AYCO Demo — Operations Runbook
**Updated: May 13, 2026** · Huawei Cloud × Grupo Salinas Workshop

---

## Infrastructure Map

| Resource | Public IP | Private IP | SSH |
|----------|-----------|------------|-----|
| **ayco-dify** (Dify + Dashboard + Agent Tools) | 101.44.185.139 | 192.168.100.135 | `ssh -i ~/.ssh/ayco-demo root@101.44.185.139` |
| **ayco-web** (Frontend + API) | 149.232.129.39 | 192.168.100.123 | `ssh -i ~/.ssh/ayco-demo root@149.232.129.39` |
| **ayco-dws** (GaussDB) | 46.250.168.254:8000 | 192.168.100.157 / 192.168.100.126 | — |

---

## Pre-Demo Checklist (T-30 min)

```bash
# 1. SSH access
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'hostname'  # → ayco-dify
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'hostname'   # → ayco-web

# 2. Dify health
curl -s http://101.44.185.139/console/api/version?current_version=1.0.0 | jq .version  # → "1.13.3"

# 3. Dify containers (all 11 must be Up)
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'docker ps --format "{{.Names}}\t{{.Status}}"'

# 4. DWS data
PGPASSWORD=AycoD3mo2026! psql -h 46.250.168.254 -p 8000 -U ayco_admin -d ayco_db -c "SELECT count(*) FROM risk_results;"  # → 24

# 5. Frontend pages (all must return 200/301)
for p in "" /risk-scoring/ /data-governance/ /contract-ai/; do
  echo "$p: $(curl -s -o /dev/null -w '%{http_code}' http://149.232.129.39$p)"
done

# 6. Streamlit dashboard
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501  # → 200

# 7. Agent tools mock
# NOTA: Puerto 8400 NO expuesto al público (SG bloquea). Verificar via SSH:
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'curl -s http://localhost:8400/health'
# → {"status":"ok","tools":["aplicar_plan_pago","consultar_buro","generar_carta"]}

# 8. API health
curl -s http://149.232.129.39/api/health  # → {"status": "ok", ...}

# 9. Dify Chat API (via API proxy)
curl -s http://149.232.129.39/api/dify/chat-messages \
  -X POST -H "Content-Type: application/json" \
  -d '{"inputs":{},"query":"Hola, prueba","response_mode":"blocking","user":"demo-workshop"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('answer','')[:80])"
```

---

## Demo 1: Risk Scoring
**URL:** http://149.232.129.39/risk-scoring/
**Duration:** 5-7 min

### Flow
1. Open URL → KPIs animate (2,347 providers, 5,128 transactions, 47 alerts, $2.1B exposure)
2. Scroll to Streamlit iframe → dashboard with vendor data
3. Risk gauge 5.8/10 → distribution by level
4. Top 5 providers table
5. Click **"Deep Analysis AI"** → opens chat with pre-filled query
6. Click **"Quiero reestructurar mi deuda"** → cobranza flow in chat

### Emergency
- **DWS down:** Frontend shows static data (hardcoded in HTML). Demo still works but say "datos precargados del último refresh."
- **Streamlit iframe blank:** Dify ECS: `systemctl restart streamlit-dashboard` (5s). If still down, skip to table.
- **Frontend 404:** `ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl restart nginx'`
- **Deep Analysis AI button no abre chat:** See "Auth Fix" section below. Rebuild frontend.
- **Chat 401 response:** See "Auth Fix" section below. Check `frontend/.env` has `PUBLIC_DIFY_API_KEY`.

---

## Demo 2: Data Governance
**URL:** http://149.232.129.39/data-governance/
**Duration:** 5 min

### Flow
1. Pipeline diagram: CNBV Data → DLI Spark → DWS → DataService API
2. ETL steps with timing estimates
3. API Explorer: live calls to `GET /risk-results`

### Plan B (DataArts not provisioned)
> "DataArts Studio agrega gobierno automatizado — catálogo de datos, linaje, reglas de calidad. Por restricciones de billing prePaid lo tenemos en un sandbox separado. Aquí les muestro cómo se ve en la consola."

Show screenshots from `docs/screenshots/dataarts/` (Catalog, Lineage, Quality Rules).

---

## Demo 3: Contract AI (Dify)
**URL:** http://101.44.185.139
**Frontend proxy:** http://149.232.129.39/contract-ai/

### Flow — 3 sub-demos
**3a. AYCO Chat (FAQ):** http://101.44.185.139/chat/253ad7c8-1cd7-44ea-a27d-9d67f031e5a1
- "¿Cómo solicito un crédito personal?"
- "¿Qué pasa si no pago a tiempo?"
- API key: `Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx`

**3b. AYCO Cobranza Agent:** http://101.44.185.139/chat/7e0472b6-249f-47bb-a2c1-cf298b7287f7
- "Quiero aplicar un plan de pagos fijos, debo $45,000"
- "Consulta mi historial en buró de crédito"
- API key: `Bearer app-ZrM7Pal6G2b89drd1zLVssvM`

**3c. AYCO Doc Analyzer (OCR):** http://101.44.185.139/chat/b7e99855-1fc9-4374-82c8-9a47693205d7
- Upload `contrato-01-alto-riesgo.pdf` from `data/contracts/`
- Shows extracted fields + risk assessment
- API key: `Bearer app-mGyFcdX7vT3CZDDsvttCX6iF`

### Emergency
- **Dify 502:** `ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'cd /opt/ayco/dify/docker && docker compose restart api worker web'` (30s)
- **Agent no responde:** Restart api+worker containers. Verificar DeepSeek API key.
- **Workflow OCR falla:** Verificar OCR proxy: `curl http://localhost:8300/health`
- **MaaS HK fallback:** DeepSeek directo configurado como fallback. Si MaaS aparece como opción en Dify, IGNORAR — da error 81009.

---

## Emergency Procedures

### Auth Fix (Chat 401 / Deep Analysis AI broken)

**Symptom:** Chat returns 401 Unauthorized, or clicking "Deep Analysis AI" opens chat but doesn't send the query.

**Root cause:** The ChatWidget's Authorization header previously checked `cobranzaMode ? COBRANZA_KEY : DIFY_KEY`. If the COBRANZA key is missing or invalid, the API call fails silently.

**Fix:**
```bash
# 1. Check frontend/.env exists with the right key
cat frontend/.env
# Must contain: PUBLIC_DIFY_API_KEY=app-Y8MxfRygyUWOAfyTlo1MQSJx

# 2. Rebuild and deploy
cd frontend && npm install --legacy-peer-deps && npm run build
cd .. && bash frontend/deploy.sh

# 3. Verify the fix was deployed
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'grep -c "chatForm.dispatchEvent" /var/www/ayco/risk-scoring/index.html'
# If returns 0 → old version; if returns 1+ → fix deployed
```

### Restart Dify
```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139
cd /opt/ayco/dify/docker
docker compose restart api worker web
# Wait 10s
curl -s http://localhost/console/api/version?current_version=1.0.0
```

### Restart Streamlit Dashboard
```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'systemctl restart streamlit-dashboard'
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501
```

### Restart Agent Tools Mock
```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'systemctl restart ayco-tools'
curl -s http://101.44.185.139:8400/health
```

### Restart API Backend
```bash
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl restart ayco-api'
curl -s http://localhost:8001/api/health
```

### Restart Nginx (Frontend)
```bash
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl restart nginx'
curl -s -o /dev/null -w '%{http_code}' http://149.232.129.39/
```

### Re-apply MaaS HK Fix (if plugin_daemon restarted)
```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139
docker exec docker-plugin_daemon-1 sed -i 's|/v1/chat/completions|/v2/chat/completions|g' \
  /app/dify-plugin-maas-hk-*/models/*.yaml
docker exec docker-plugin_daemon-1 sed -i 's|model: deepseek|model: DeepSeek|g' \
  /app/dify-plugin-maas-hk-*/models/*.yaml
docker compose -f /opt/ayco/dify/docker/docker-compose.yaml restart plugin_daemon
```

### Re-upload Contracts to OBS
```bash
cd /home/eduardo/dev/ayco-huawei-cloud
source .env
bash scripts/upload-contracts-to-obs.sh
```

### Recreate DWS (if deleted)
```bash
cd /home/eduardo/dev/ayco-huawei-cloud/terraform

# Check current DWS version
hcloud DWS ListNodeTypes --cli-region=la-north-2 | python3 -c \
  "import sys,json; [print(v['detail'][0].get('version','?')) for v in json.load(sys.stdin).get('node_types',[]) if v['detail']]" \
  | sort -u

# Update version in terraform/modules/data-platform/dws.tf if needed
terraform apply -target=module.data_platform.huaweicloud_dws_cluster.ayco -auto-approve
# Wait 15-20 min for cluster to provision

# Seed data once available
PGPASSWORD=AycoD3mo2026! psql -h $(terraform output -raw dws_public_ip) \
  -p 8000 -U ayco_admin -d ayco_db -f ../scripts/seed-dws.sql
```

### Rebuild Frontend (after changes)
```bash
cd /home/eduardo/dev/ayco-huawei-cloud/frontend

# Edit .env if needed
cat .env  # Must have PUBLIC_DIFY_API_KEY

npm install --legacy-peer-deps && npm run build
cd .. && bash frontend/deploy.sh
```

### If Everything is Broken
1. Check all containers: `ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'docker ps'` → 11 containers
2. Check DWS: `psql` query above
3. Check FunctionGraph: Huawei Console → FunctionGraph → ayco-ocr-trigger
4. Restart everything:
```bash
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'docker compose restart && systemctl restart streamlit-dashboard ayco-tools'
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl restart ayco-api nginx'
```

---

## Quick Reference

| Resource | URL/Command |
|---|---|
| Dify UI | http://101.44.185.139 |
| Dify Login | eduardo@ayco-demo.com / ver 1Password |
| Frontend | http://149.232.129.39 |
| Risk Scoring | http://149.232.129.39/risk-scoring/ |
| Dashboard | http://101.44.185.139:8501 |
| DWS | 46.250.168.254:8000 (ayco_admin / ver 1Password) |
| API Health | http://149.232.129.39/api/health |
| Agent Tools | http://101.44.185.139:8400/health |
| Dify API Chat | Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx |
| Dify API Agent | Bearer app-ZrM7Pal6G2b89drd1zLVssvM |
| Dify API Workflow | Bearer app-mGyFcdX7vT3CZDDsvttCX6iF |
| Langfuse | https://us.cloud.langfuse.com (proyecto ayco-demo) |
| SSH Dify | `ssh -i ~/.ssh/ayco-demo root@101.44.185.139` |
| SSH Web | `ssh -i ~/.ssh/ayco-demo root@149.232.129.39` |
| Repo | `/home/eduardo/dev/ayco-huawei-cloud` |
| .env (frontend) | `frontend/.env` → `PUBLIC_DIFY_API_KEY=app-Y8...` |
| Terraform | `terraform/` — DWS recreated May 13, 2026 |
