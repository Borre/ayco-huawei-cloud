# AYCO Demo — Operations Runbook
**May 8, 2026** · Huawei Cloud × Grupo Salinas Workshop

---

## Pre-Demo Checklist (T-30 min)

```
# 1. SSH access
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 'hostname'  # → ayco-dify
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'hostname'   # → ayco-web

# 2. Dify health
curl -s http://101.44.185.139/console/api/version?current_version=1.0.0 | jq .version  # → "1.13.3"

# 3. DWS data
PGPASSWORD=AycoD3mo2026! psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "SELECT count(*) FROM risk_results;"  # → 20

# 4. Frontend pages (all must return 200)
for p in "" /risk-scoring/ /data-governance/ /contract-ai/; do
  echo "$p: $(curl -s -o /dev/null -w '%{http_code}' http://149.232.129.39$p)"
done

# 5. Streamlit dashboard
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501  # → 200

# 6. Agent tools mock
curl -s http://101.44.185.139:8400/aplicar_plan_pago  # → JSON response

# 7. OBS contract pipeline
# Check that OCR function processed uploads. Look for results in OBS or DWS.
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

### Emergency
- **DWS down:** Frontend shows static data (hardcoded in HTML). Demo still works but say "datos precargados del último refresh."
- **Streamlit iframe blank:** Dify ECS: `systemctl restart streamlit-dashboard` (5s). If still down, skip to table.
- **Frontend 404:** Web ECS: `systemctl restart nginx`

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
- API key if direct: `Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx`

**3b. AYCO Cobranza Agent:** http://101.44.185.139/chat/7e0472b6-249f-47bb-a2c1-cf298b7287f7
- "Quiero aplicar un plan de pagos fijos, debo $45,000"
- "Consulta mi historial en buró de crédito"
- API key: `Bearer app-ZrM7Pal6G2b89drd1zLVssvM`

**3c. AYCO Doc Analyzer (OCR):** http://101.44.185.139/chat/b7e99855-1fc9-4374-82c8-9a47693205d7
- Upload `contrato-01-alto-riesgo.pdf` from `data/contracts/`
- Shows extracted fields + risk assessment
- API key: `Bearer app-mGyFcdX7vT3CZDDsvttCX6iF`

### Emergency
- **Dify 502:** `ssh ayco-dify 'cd /opt/ayco/dify/docker && docker compose restart api worker web'` (30s)
- **Agent no responde:** Restart api+worker containers. Verificar DeepSeek API key.
- **Workflow OCR falla:** Verificar OCR proxy: `curl http://localhost:8300/health`
- **MaaS HK fallback:** Ya está configurado DeepSeek directo como fallback. Si MaaS aparece como opción, IGNORAR — da error 81009.

---

## Emergency Procedures

### Restart Dify
```bash
ssh root@101.44.185.139
cd /opt/ayco/dify/docker
docker compose restart api worker web
# Wait 10s
curl -s http://localhost/console/api/version?current_version=1.0.0
```

### Restart Streamlit Dashboard
```bash
ssh root@101.44.185.139 'systemctl restart streamlit-dashboard'
curl -s -o /dev/null -w '%{http_code}' http://101.44.185.139:8501
```

### Restart Agent Tools Mock
```bash
ssh root@101.44.185.139 'systemctl restart ayco-tools'
curl -s http://101.44.185.139:8400/health
```

### Re-apply MaaS HK Fix (if plugin_daemon restarted)
```bash
ssh root@101.44.185.139
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

### If Everything is Broken
1. Check all containers: `ssh ayco-dify 'docker ps'` → 11 containers
2. Check DWS: `psql` query above
3. Check FunctionGraph: Huawei Console → FunctionGraph → ayco-ocr-trigger
4. Restart everything: `docker compose restart` + `systemctl restart streamlit-dashboard ayco-tools`

---

## Quick Reference

| Resource | URL/Command |
|---|---|
| Dify UI | http://101.44.185.139 |
| Dify Login | eduardo@ayco-demo.com / ver 1Password |
| Frontend | http://149.232.129.39 |
| Dashboard | http://101.44.185.139:8501 |
| DWS | 46.250.161.25:8000 (ayco_admin / ver 1Password) |
| Dify API Chat | Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx |
| Dify API Agent | Bearer app-ZrM7Pal6G2b89drd1zLVssvM |
| Dify API Workflow | Bearer app-mGyFcdX7vT3CZDDsvttCX6iF |
| SSH Dify | ssh -i ~/.ssh/ayco-demo root@101.44.185.139 |
| SSH Web | ssh -i ~/.ssh/ayco-demo root@149.232.129.39 |
