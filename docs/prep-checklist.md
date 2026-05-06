# AYCO × Huawei Cloud — Demo Prep Checklist (v3: Technical Depth)

**Workshop:** May 8, 2026
**Region:** la-north-2 (Mexico City 2)
**Duration:** 45 min (3 demos + FinOps + Q&A)
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
  - [ ] Verify `public.risk_results` has 20 rows
  - [ ] Verify 4 schemas exist: ods, dw, dm, public
  - [ ] Verify 4 indexes on risk_results: pkey, score, level, vendor_name
  - [ ] Verify CHECK constraint on risk_level
  ```bash
  PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h 46.250.161.25 -p 8000 -U ayco_admin -d ayco_db -c "
    SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('ods','dw','dm','public') ORDER BY schemaname;
    SELECT COUNT(*) FROM public.risk_results;
    \d public.risk_results
  "
  ```

- [ ] FunctionGraph functions verified
  - [ ] `ocr_trigger` deployed and enabled
  - [ ] `parse_contract` deployed and enabled
  - [ ] `llm_inference` deployed and enabled
  - [ ] Test trigger with a sample OBS upload event
  - [ ] Verify Langfuse traces appear after test

- [ ] Dify knowledge bases configured
  - [ ] AYCO - Preguntas Frecuentes (FAQ): 9 docs indexed
  - [ ] ayco-contracts-kb: 21 docs indexed (including risk context PDF)
  - [ ] Both datasets connected to AYCO Chat app
  - [ ] Retrieval config: semantic_search, top_k=3, no reranking
  - [ ] Model: DeepSeek v4 Flash via MaaS, temperature 0.3

- [ ] Langfuse verified
  - [ ] Project `ayco-demo` exists in Langfuse Cloud
  - [ ] Traces visible from LLM test calls
  - [ ] Verify trace metadata includes model, provider, latency, tokens

- [ ] DeepSeek/MaaS API keys verified
  - [ ] MaaS: `curl -H "Authorization: Bearer $MAAS_API_KEY" https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions`
  - [ ] DeepSeek direct: `curl -H "Authorization: Bearer $DEEPS...KEY" https://api.deepseek.com/v1/models`

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
  - [ ] DWS SQL Editor: execute live query, results match frontend
  - [ ] DWS `\d public.risk_results` shows schema + indexes
  - [ ] EXPLAIN query uses index (not sequential scan)
- [ ] **Demo 2 dry run (Data Governance):**
  - [ ] Frontend `/data-governance/` loads — pipeline diagram, ETL steps
  - [ ] DWS 3-capas query: ods.vendors, dw.dim_vendor, dm.*
  - [ ] Quality queries: 100% completitud, 0 fuera rango, 0 duplicados
  - [ ] DLI Spark query functional (or acknowledge capacity issue)
  - [ ] Langfuse traces visible — click into trace detail
- [ ] **Demo 3 dry run (Contract AI):**
  - [ ] Frontend `/contract-ai/` loads — uploader + chatbot
  - [ ] Chatbot responds to "¿Cuál es el contrato con mayor riesgo?"
  - [ ] Response matches DWS data: AYCO-2026-0149, 9.2, Constructora
  - [ ] Streaming SSE works — characters appear progressively
  - [ ] Contract cards show correct data: 9.2, 8.7, 2.3
- [ ] **Health check:**
  - [ ] `bash scripts/health-check.sh` — 0 failures
  - [ ] Frontend all 4 pages return 200
  - [ ] Dify API returns 200 (both direct and via proxy)
  - [ ] Streamlit dashboard returns ok
  - [ ] DWS connection successful
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
  - [ ] DWS query: `SELECT COUNT(DISTINCT vendor_name), COUNT(*), ROUND(SUM(monto_total)/1000000,1), ROUND(AVG(risk_score),1) FROM public.risk_results;`
  - [ ] DWS query: `SELECT contract_number, vendor_name, risk_score, risk_level FROM public.risk_results ORDER BY risk_score DESC LIMIT 5;`
  - [ ] DWS command: `\d public.risk_results`
  - [ ] Quality query: `SELECT COUNT(*) FILTER (WHERE risk_score IS NULL) FROM public.risk_results;`
- [ ] Pre-type the first Dify chat query in the frontend chatbot: "¿Cuál es el contrato con mayor riesgo?"

---

## Tab Checklist (11 Tabs)

Open and pin in this exact order before the workshop:

| # | Tab | URL | Verification |
|---|-----|-----|-------------|
| 1 | Frontend Landing | `http://149.232.129.39/` | Hero loads, KPIs visible, 3 cards render |
| 2 | Frontend Risk Scoring | `http://149.232.129.39/risk-scoring/` | Gauge animates, tabla visible |
| 3 | Frontend Data Governance | `http://149.232.129.39/data-governance/` | Pipeline diagram, ETL steps |
| 4 | Frontend Contract AI | `http://149.232.129.39/contract-ai/` | Uploader + chatbot visible |
| 5 | Dify Admin | `http://101.44.185.139/admin` | Logged in, AYCO Chat config open |
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
# Check dataset connection
ssh -i ~/.ssh/ayco-demo root@101.44.185.139 \
  "docker exec docker-db_postgres-1 psql -U postgres -d dify \
   -c \"SELECT a.name, d.name FROM apps a JOIN app_dataset_joins aj ON a.id=aj.app_id JOIN datasets d ON aj.dataset_id=d.id WHERE a.name='AYCO Chat';\""

# If missing, connect via DB:
# INSERT INTO app_dataset_joins (id, app_id, dataset_id, created_at)
# VALUES (gen_random_uuid(), '<app_id>', '<dataset_id>', now());

# Then restart:
docker compose restart api worker
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
| Dify Admin | `http://101.44.185.139/admin` |
| Dify API (direct) | `http://101.44.185.139/v1/` |
| Dify API (via proxy) | `http://149.232.129.39/api/dify/` |
| Streamlit Dashboard | `http://101.44.185.139:8501` |
| Langfuse | `https://us.cloud.langfuse.com` → ayco-demo |
| Dify API Key | `app-Y8MxfRygyUWOAfyTlo1MQSJx` |
| DWS Endpoint | `46.250.161.25:8000` |
| Terraform Repo | `github.com/Borre/ayco-huawei-cloud` |

### Emergency Contacts

- **Huawei Cloud support:** Open ticket via console
- **1Password:** Secrets vault: `op://Huawei/AK-SK`
- **SSH config:** `~/.ssh/config` should have entries for both ECS

---

**File:** `docs/prep-checklist.md`
**Version:** v3.0 — Technical Depth
**Last updated:** May 6, 2026
