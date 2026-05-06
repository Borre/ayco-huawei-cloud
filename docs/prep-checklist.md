# AYCO × Huawei Cloud — Demo Prep Checklist (v3.2: Contracts + Dify + MPP)

**Workshop:** May 8, 2026
**Region:** la-north-2 (Mexico City 2)
**Duration:** 50 min (3 demos + FinOps + Q&A)
**Audience:** Technical — Huawei Cloud LATAM Leadership
**Presenter:** Eduardo

---

## T-4 days (Monday, May 4)

- [ ] Huawei Cloud credits released — verify in console > My Resources > Quota
- [ ] `terraform.tfvars` populated with real values
  - [ ] `access_key` / `secret_key` (1Password: `op read "op://Huawei/AK-SK/username"`)
  - [ ] `dws_admin_password`
  - [ ] `maas_api_key` (MaaS DeepSeek v4 Flash)
  - [ ] `deepseek_api_key` (DeepSeek direct fallback)
  - [ ] `project_id = "fbb6435c497c41bda90a0cc5240573e0"`
  - [ ] `keypair_name = "hermes-agent"`
  - [ ] `region = "la-north-2"`
  - [ ] `langfuse_public_key` (from us.cloud.langfuse.com)
  - [ ] `langfuse_secret_key` (from us.cloud.langfuse.com)
- [ ] `.env` populated (MAAS_API_KEY, DEEPSEEK_API_KEY, DWS_ADMIN_PASSWORD, DWS_ENDPOINT, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
- [ ] `terraform init` passes
- [ ] `terraform plan` passes (no errors, expected ~20+ resources)

### Commands

```bash
cd /home/eduardo/dev/ayco-huawei-cloud
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with real values
terraform -chdir=terraform init
terraform -chdir=terraform plan
```

---

## T-3 days (Tuesday, May 5)

- [ ] `terraform apply` — full infrastructure deploy
  - [ ] foundation module (VPC 55d7ebd4, subnet 41121f0f, SGs, OBS buckets, KMS, IAM)
  - [ ] compute module (ECS ayco-dify 101.44.185.139, ayco-web 149.232.129.39, EIPs)
  - [ ] data-platform module (DWS 46.250.161.25:8000, DLI database)
  - [ ] ai-ocr module (FunctionGraph: ocr_trigger, parse_contract, llm_inference)
- [ ] DNS resolution works from both ECS instances
  - [ ] Run `scripts/fix-dns.sh`
  - [ ] Verify: `ssh root@101.44.185.139 nslookup google.com` succeeds
  - [ ] Verify: `ssh root@149.232.129.39 nslookup google.com` succeeds
- [ ] Dify deployed and accessible
  - [ ] Run `scripts/setup-dify.sh`
  - [ ] Verify: `curl -s -o /dev/null -w "%{http_code}" http://101.44.185.139/` returns 200
  - [ ] Dify containers all healthy (api, worker, web, db, redis, weaviate, nginx)
- [ ] Frontend deployed
  - [ ] Build: `cd frontend && npm run build && bash deploy.sh`
  - [ ] Verify: `curl -s -o /dev/null -w "%{http_code}" http://149.232.129.39/` returns 200
- [ ] Streamlit dashboard deployed
  - [ ] Copy `risk_dashboard_live.py` to ECS as `/opt/dashboards/risk_dashboard.py`
  - [ ] Create `.env` with DWS credentials on ECS
  - [ ] Verify: `curl -s http://101.44.185.139:8501/_stcore/health` returns ok

### Commands

```bash
make apply
bash scripts/fix-dns.sh
bash scripts/setup-dify.sh
make frontend-deploy
```

---

## T-2 days (Wednesday, May 6)

- [ ] DWS seed data executed and verified
  - [ ] Run: `python3 scripts/generate-contract-data.py`
  - [ ] Verify 3-layer schema: `ods` (vendors 2300, customers 500, transactions 5000), `dw`, `dm` (4 vistas)
  - [ ] Verify `public.risk_results` has 20 rows (10 ALTO, 6 BAJO, 3 MEDIO, 1 CRÍTICO)
  - [ ] Verify EXPLAIN ANALYZE shows MPP parallelism (2 datanodes: dn_6001_6002 + dn_6005_6006)
  ```bash
  PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "
    SELECT 'vendors' as tbl, count(*) FROM ods.vendors
    UNION ALL SELECT 'customers', count(*) FROM ods.customers
    UNION ALL SELECT 'transactions', count(*) FROM ods.transactions
    UNION ALL SELECT 'risk_results', count(*) FROM public.risk_results;
  "
  # MPP verification
  PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "
    EXPLAIN ANALYZE SELECT v.name, c.contract_name, r.risk_score, r.risk_level
    FROM ods.vendors v
    JOIN ods.contracts c ON v.vendor_id = c.vendor_id
    JOIN public.risk_results r ON c.contract_id = r.contract_id
    WHERE r.risk_level = 'CRITICO';
  "
  ```

- [ ] 6 nuevos contratos PDF generados y listos para demo
  - [ ] `data/contracts/contrato-bajo-riesgo-consultoria.pdf` ($850K, BAJO, garantía 15%)
  - [ ] `data/contracts/contrato-medio-riesgo-mantenimiento.pdf` ($4.2M, MEDIO, garantía 5%)
  - [ ] `data/contracts/contrato-alto-riesgo-software.pdf` ($7.8M, ALTO, sin garantía)
  - [ ] `data/contracts/contrato-critico-datacenter.pdf` ($22.5M, CRÍTICO, sin garantía, empresa RFC 2024)
  - [ ] `data/contracts/contrato-alto-riesgo-outsourcing.pdf` ($9.6M, ALTO, jurisdicción Tapachula)
  - [ ] `data/contracts/contrato-medio-riesgo-suministros.pdf` ($5.8M, MEDIO, garantía solo 1er año)
  - [ ] Script generador: `scripts/generate-contracts-pdf.py` (fpdf2 + DejaVu Unicode)
  - [ ] Todos los campos extraíbles por regex (CONTRATO NÚMERO, monto, penalización, garantía)

- [ ] FunctionGraph functions verified
  - [ ] `ocr_trigger` deployed and enabled
  - [ ] `parse_contract` deployed and enabled
  - [ ] `llm_inference` deployed and enabled
  - [ ] Test trigger with a sample OBS upload event
  - [ ] Verify Langfuse traces appear after test (us.cloud.langfuse.com → ayco-demo)

- [ ] Dify verified (3 apps + 4 datasets)
  - [ ] Login: `http://101.44.185.139/console` — eduardo@ayco-demo.com / AYCOcloud2026!
  - [ ] AYCO Chat (chat mode): app-Y8MxfRygyUWOAfyTlo1MQSJx — conectado a 2 datasets
  - [ ] AYCO Cobranza (agent-chat mode): app-ZrM7Pal6G2b89drd1zLVssvM
  - [ ] AYCO Analyzer (workflow mode): app-mGyFcdX7vT3CZDDsvttCX6iF — published
  - [ ] Datasets: ayco-contracts-kb (21 docs), FAQ (9 docs), Planes de Pago (6 docs), Políticas Cobranza (6 docs)
  - [ ] MaaS HK plugin v0.0.4 installed and working
  - [ ] Chat test: "¿Qué niveles de riesgo maneja AYCO?" → debe responder con datos reales

- [ ] Langfuse verified
  - [ ] Project `ayco-demo` exists in Langfuse Cloud
  - [ ] 3+ traces visible showing model, latency, tokens
  - [ ] Traces include OCR → Parse → LLM Inference pipeline

- [ ] Terraform zero-diff verified
  - [ ] `terraform plan` returns "No changes. Your infrastructure matches the configuration."
  - [ ] lifecycle `ignore_changes = [event_notification_name]` applied to FunctionGraph

- [ ] DeepSeek/MaaS API keys verified
  - [ ] MaaS: `curl -H "Authorization: Bearer *** https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions`
  - [ ] DeepSeek direct: `curl -H "Authorization: Bearer *** https://api.deepseek.com/v1/models`

### Commands

```bash
# Seed DWS
python3 scripts/generate-contract-data.py
PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -f scripts/seed-dws.sql

# Verify Dify datasets
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "docker exec docker-db_postgres-1 psql -U postgres -d dify \
   -c \"SELECT d.name, COUNT(*) FROM datasets d LEFT JOIN documents dd ON d.id=dd.dataset_id GROUP BY d.name;\""

# Test Langfuse connection
bash scripts/langfuse-setup.sh
```

---

## T-1 day (Thursday, May 7)

### Full Dry Run — All 3 Demos End-to-End

- [ ] **Pre-open all 11 browser tabs** (see Tab Checklist below)
- [ ] **Demo 1 dry run (Risk Scoring):**
  - [ ] Frontend `/risk-scoring/` loads — gauge, KPIs, tabla render
  - [ ] DWS SQL Editor: execute EXPLAIN ANALYZE LIVE — muestra MPP con 2 datanodes, ~8ms
  - [ ] DWS `\d public.risk_results` shows schema
  - [ ] Show risk distribution: SELECT risk_level, COUNT(*) FROM public.risk_results GROUP BY risk_level
  - [ ] MPP story: "3 datanodes, 8ms, los datos nunca salen de Huawei Cloud"
- [ ] **Demo 2 dry run (Data Governance):**
  - [ ] Frontend `/data-governance/` loads — pipeline diagram, ETL steps
  - [ ] DWS 3-capas query: JOIN ods.vendors → ods.transactions → dm.vendor_risk_summary
  - [ ] Quality queries: 100% completitud, 0 fuera rango, 0 duplicados
  - [ ] DLI Spark query functional (or acknowledge capacity issue)
  - [ ] Langfuse traces visible — click into trace detail showing OCR→Parse→LLM pipeline
- [ ] **Demo 3 dry run (Contract AI + Upload):**
  - [ ] Frontend `/contract-ai/` loads — uploader + chatbot
  - [ ] **Upload test:** Sube contrato-bajo-riesgo-consultoria.pdf ($850K) → verify pipeline en <30s
  - [ ] **Upload test:** Sube contrato-critico-datacenter.pdf ($22.5M) → verify score 9.0+
  - [ ] Chatbot test: "¿Cuál es el contrato con mayor riesgo?" → AYCO-2026-0163, 9.2
  - [ ] Chatbot test: "¿Qué anomalías tiene el contrato 0163?" → empresa RFC 2024, sin garantía
  - [ ] Streaming SSE works — characters appear progressively
  - [ ] Contract cards show correct data spanning 9 contratos (3 original + 6 nuevos)
- [ ] **FinOps dry run:**
  - [ ] CTS audit trail visible — muestra eventos DWS, FunctionGraph
  - [ ] Terraform `plan` zero-diff verificado
- [ ] **Health check:**
  - [ ] `bash scripts/health-check.sh` — 0 failures
  - [ ] Frontend all 4 pages return 200
  - [ ] Dify API returns 200 (both direct and via proxy)
  - [ ] Streamlit dashboard returns ok
  - [ ] DWS connection + EXPLAIN ANALYZE successful
- [ ] **Backup recordings:**
  - [ ] Run `bash scripts/backup-record-demos.sh`
  - [ ] Verify recordings save to `backups/` directory
  - [ ] Download recordings to local machine
- [ ] **API key warmup:**
  - [ ] Run 3 test queries against Dify API to warm up MaaS connection
  - [ ] First cold start can take 30-60s; subsequent < 5s

### Commands

```bash
make demo
bash scripts/health-check.sh
bash scripts/backup-record-demos.sh

# Warm up Dify/MaaS
for i in 1 2 3; do
  curl -s -X POST http://149.232.129.39/api/dify/chat-messages \
    -H "Authorization: Bearer app-Y8MxfRygyUWOAfyTlo1MQSJx" \
    -H "Content-Type: application/json" \
    -d '{"query":"¿Cuál es el contrato con mayor riesgo?","user":"warmup","response_mode":"blocking","inputs":{}}' > /dev/null
done
```

---

## Day of — Friday, May 8

### 2 Hours Before Workshop

- [ ] Health check morning of
  ```bash
  bash scripts/health-check.sh
  ```
- [ ] All 11 tabs open and verified (see Tab Checklist)
- [ ] DWS queries return data (run top-5 query)
- [ ] Dify chatbot responds to test query
- [ ] Screen sharing tested in actual meeting platform
  - [ ] Terminal text readable at presentation resolution
  - [ ] Huawei Console renders clearly (light theme, high contrast)
  - [ ] Code snippets in DWS SQL Editor are large enough (Ctrl+ if needed)
- [ ] Backup internet ready
  - [ ] Mobile hotspot tested and charged
  - [ ] Backup laptop with SSH access configured
  - [ ] Pre-recorded demo videos in `backups/`

### 30 Minutes Before Workshop

- [ ] Close all non-demo applications (Slack, email, notifications)
- [ ] DND mode on
- [ ] Terminal window open with SSH to both ECS (split pane)
- [ ] Clipboard loaded with:
  - [ ] EXPLAIN ANALYZE: `EXPLAIN ANALYZE SELECT v.name, c.contract_name, r.risk_score, r.risk_level FROM ods.vendors v JOIN ods.contracts c ON v.vendor_id = c.vendor_id JOIN public.risk_results r ON c.contract_id = r.contract_id WHERE r.risk_level = 'CRITICO';`
  - [ ] Risk distribution: `SELECT risk_level, COUNT(*) FROM public.risk_results GROUP BY risk_level ORDER BY COUNT(*) DESC;`
  - [ ] Top risk: `SELECT contract_number, vendor_name, risk_score, risk_level, monto_total, garantia_pct FROM public.risk_results ORDER BY risk_score DESC LIMIT 5;`
  - [ ] Quality check: `SELECT COUNT(*) FILTER (WHERE risk_score IS NULL) FROM public.risk_results;`
  - [ ] CTS query: Open `Huawei Console → CTS → Trace List` filtered by DWS events
  - [ ] Terraform: `cd terraform && terraform plan` — debe mostrar "No changes"

---

## Tab Checklist (11 Tabs)

Open and pin in this exact order before the workshop:

| # | Tab | URL | Verification |
|---|-----|-----|-------------|
| 1 | Frontend Landing | `http://149.232.129.39/` | Hero loads, KPIs visible, 3 cards render |
| 2 | Frontend Risk Scoring | `http://149.232.129.39/risk-scoring/` | Gauge animates, tabla visible |
| 3 | Frontend Data Governance | `http://149.232.129.39/data-governance/` | Pipeline diagram, ETL steps |
| 4 | Frontend Contract AI | `http://149.232.129.39/contract-ai/` | Uploader + chatbot visible |
| 5 | Dify Admin | `http://101.44.185.139/console` | Logged in (eduardo@ayco-demo.com), AYCO Chat config visible |
| 6 | Streamlit Dashboard | `http://101.44.185.139:8501` | KPIs visible, data matches DWS |
| 7 | Huawei Console > DWS > SQL Editor | Console | Cluster `ayco-dws` active, SQL Editor ready |
| 8 | Huawei Console > DLI > SQL Editor | Console | DLI database `ayco` visible |
| 9 | Huawei Console > FunctionGraph > llm-inference > Logs | Console | Function enabled, log stream open |
| 10 | Langfuse Cloud > ayco-demo > Traces | `https://us.cloud.langfuse.com` | Project loaded, traces visible |
| 11 | Huawei Console > CTS > Trace List | Console | CTS enabled, DWS events visible |

---

## Troubleshooting

### DNS not working on ECS

Huawei Cloud Ubuntu images have broken `systemd-resolved`. Fix:

```bash
bash scripts/fix-dns.sh
```

Or manually per instance:
```bash
ssh root@<ECS_IP>
echo 'nameserver 8.8.8.8' > /etc/resolv.conf
echo 'nameserver 1.1.1.1' >> /etc/resolv.conf
nslookup google.com   # should resolve
```

### Dify not starting or unreachable

```bash
ssh root@101.44.185.139
cd /opt/ayco/dify/docker
docker compose ps                    # check container status
docker compose logs api              # check API container logs
docker compose logs worker           # check worker logs
docker compose restart api worker    # restart if needed
```

Common fixes:
- **Containers restarting:** Check `.env` for correct MaaS API key
- **Port 80 in use:** `lsof -i :80` — kill conflicting process
- **Out of disk:** `df -h` — Dify needs ~20GB
- **Model not active:** In Dify Admin > Settings > Model Provider, DeepSeek must show "Active"

### DWS connection refused

- **Security group:** Verify SG allows port 8000 from your IP
- **DWS not ready:** Check status in Huawei Console
- **Test connection:**
  ```bash
  PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "SELECT 1;"
  ```

### DWS layered schema empty or missing

```bash
# Re-run seed
PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -f scripts/seed-dws.sql

# Verify
PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "
  SELECT schemaname, COUNT(*) as tables FROM pg_tables WHERE schemaname IN ('ods','dw','dm','public') GROUP BY schemaname;
"
```

### Dify chatbot not retrieving risk data

```bash
# Check datasets connected to AYCO Chat
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "docker exec docker-db_postgres-1 psql -U postgres -d dify \
   -c \"SELECT a.name, d.name FROM apps a JOIN app_dataset_joins aj ON a.id=aj.app_id JOIN datasets d ON aj.dataset_id=d.id WHERE a.name='AYCO Chat';\""

# If missing, connect via DB:
# INSERT INTO app_dataset_joins (id, app_id, dataset_id, created_at)
# VALUES (gen_random_uuid(), '<app_id>', '<dataset_id>', now());

# Then restart:
docker compose restart api worker
```

### Dify login lost / password reset

```bash
# Reset admin password via DB
ssh -i ~/.ssh/ayco-demo root@101.44.185.139
# Generate new hash using Dify's own function
CREDS=$(docker exec docker-api-1 python3 -c "
from libs.password import hash_password
import secrets, base64
new_pw = 'AYCOcloud2026!'
salt = secrets.token_bytes(16)
result = hash_password(new_pw, salt)
print(f'{base64.b64encode(salt).decode()}|{base64.b64encode(result).decode()}')
")
SALT=$(echo "$CREDS" | cut -d"|" -f1)
HASH=$(echo "$CREDS" | cut -d"|" -f2)
docker exec docker-db_postgres-1 psql -U postgres -d dify -c \
  "UPDATE accounts SET password = '$HASH', password_salt = '$SALT' WHERE email = 'eduardo@ayco-demo.com';"
# Login: eduardo@ayco-demo.com / AYCOcloud2026!
```

### Upload new contracts to OBS for demo

```bash
# Upload individual contracts
obsutil cp data/contracts/contrato-bajo-riesgo-consultoria.pdf obs://ayco-contracts-raw/
obsutil cp data/contracts/contrato-critico-datacenter.pdf obs://ayco-contracts-raw/

# Or batch upload all 6 new contracts
for pdf in data/contracts/contrato-{bajo,medio,alto,critico}*.pdf; do
  obsutil cp "$pdf" obs://ayco-contracts-raw/
done

# Verify pipeline processed them
obsutil ls obs://ayco-contracts-results/json/ | wc -l
# Should show 23+ after processing completes
```

### Langfuse not showing traces

- **API keys:** Verify LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in `.env`
- **Project:** Ensure `ayco-demo` exists in Langfuse Cloud
- **FunctionGraph:** Verify `langfuse-setup.sh` ran successfully
- **Test trace:** Send a manual test:
  ```bash
  curl -X POST https://us.cloud.langfuse.com/api/public/ingestion \
    -H "Authorization: Bearer $LANGFUSE_PUBLIC_KEY" \
    -H "Content-Type: application/json" \
    -d '{"batch":[{"id":"test-123","type":"trace-create","body":{"name":"healthcheck"}}]}'
  ```

### Frontend not loading or chatbot proxy failing

- **nginx down:**
  ```bash
  ssh root@149.232.129.39 "systemctl status nginx"
  ssh root@149.232.129.39 "systemctl restart nginx"
  ```
- **Dify proxy 502:** Dify ECS may be down
  ```bash
  ssh root@101.44.185.139 "cd /opt/ayco/dify/docker && docker compose ps"
  ```
- **Rebuild frontend:**
  ```bash
  cd /home/eduardo/dev/ayco-huawei-cloud/frontend
  npm run build && bash deploy.sh
  ```
- **nginx error logs:**
  ```bash
  ssh root@149.232.129.39 "tail -50 /var/log/nginx/error.log"
  ```

### Streamlit dashboard not showing data

- **DWS password missing:**
  ```bash
  ssh root@101.44.185.139 "cat /opt/dashboards/.env | grep DWS_PASS"
  ```
- **Restart with env:**
  ```bash
  ssh root@101.44.185.139 "kill -HUP \$(pgrep -f streamlit)"
  ```

### Live demo fails — use backup Plan

```bash
# Option 1: Pre-recorded videos
ls /home/eduardo/dev/ayco-huawei-cloud/backups/
# Play the .mp4 files corresponding to each demo

# Option 2: Direct to Dify API (skip frontend)
# Open http://101.44.185.139 and use Dify web UI directly

# Option 3: Terminal-only demo
# Execute all queries from Appendix A of demo-script.md via psql + curl
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make demo` | Full deploy + test data + health check |
| `make frontend-deploy` | Build + deploy branded frontend |
| `make status` | Run health check |
| `make destroy` | Tear down all resources |
| `bash scripts/health-check.sh` | Smoke test all endpoints |
| `bash scripts/fix-dns.sh` | Fix DNS on all ECS |
| `bash scripts/setup-dify.sh` | Deploy Dify on ECS |
| `bash scripts/backup-record-demos.sh` | Generate Plan B recordings |
| `bash scripts/langfuse-setup.sh` | Langfuse Cloud setup + verify |
| `PGPASSWORD=... psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db` | Connect to DWS |
| `ssh -i ~/.ssh/ayco-demo root@101.44.185.139` | SSH to Dify ECS |
| `ssh -i ~/.ssh/ayco-demo root@149.232.129.39` | SSH to Web ECS |

### URLs Quick Reference

| Recurso | URL |
|---------|-----|
| Frontend Landing | `http://149.232.129.39/` |
| Demo 1 — Risk Scoring | `http://149.232.129.39/risk-scoring/` |
| Demo 2 — Data Governance | `http://149.232.129.39/data-governance/` |
| Demo 3 — Contract AI | `http://149.232.129.39/contract-ai/` |
| Dify Console | `http://101.44.185.139/console` (eduardo@ayco-demo.com / AYCOcloud2026!) |
| Dify API (direct) | `http://101.44.185.139/v1/` |
| Dify API (via proxy) | `http://149.232.129.39/api/dify/` |
| Streamlit Dashboard | `http://101.44.185.139:8501` |
| Langfuse | `https://us.cloud.langfuse.com` → ayco-demo |
| Dify API Key (AYCO Chat) | `app-Y8MxfRygyUWOAfyTlo1MQSJx` |
| Dify API Key (AYCO Cobranza) | `app-ZrM7Pal6G2b89drd1zLVssvM` |
| DWS Endpoint | `46.250.161.25:8000` |
| Terraform Repo | `github.com/Borre/ayco-huawei-cloud` |

### Contract PDFs Quick Reference

| # | Contrato | Monto | Riesgo | Garantía | Penal | Flag |
|---|----------|-------|--------|----------|-------|------|
| 0147 | Consultoría TI | $3.85M | ALTO | 0% | 30% | Sin garantía |
| 0148 | Diseño web | $450K | BAJO | 50% depósito | 5% | — |
| 0149 | Obra pública datacenter | $12.5M | CRÍTICO | 0% | 40% | Arbitraje UNCITRAL |
| 0160 | Consultoría administrativa | $850K | BAJO | 15% fianza | 10% | — |
| 0161 | Mantenimiento flota | $4.2M | MEDIO | 5% carta crédito | 25% | Garantía baja |
| 0162 | Software empresarial | $7.8M | ALTO | 0% | 40% | Sector financiero |
| 0163 | Centro de datos Tier III | $22.5M | CRÍTICO | 0% | 50% | Empresa RFC 2024 |
| 0164 | Outsourcing bancario | $9.6M | ALTO | 0% | 35% | Jurisd. Tapachula |
| 0165 | Equipo médico | $5.8M | MEDIO | 10% (1er año) | 20% | Garantía parcial |

### Emergency Contacts

- **Huawei Cloud support:** Open ticket via console
- **1Password:** Secrets vault: `op://Huawei/AK-SK`
- **SSH config:** `~/.ssh/config` should have entries for both ECS

---

**File:** `docs/prep-checklist.md`
**Version:** v3.2 — Contracts + Dify + MPP
**Last updated:** May 7, 2026
