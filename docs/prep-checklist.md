# AYCO × Huawei Cloud — Demo Prep Checklist

**Workshop:** May 8, 2026
**Region:** la-north-2 (Mexico City 2)
**Duration:** 45 min (3 demos + PPT + Q&A)

---

## T-4 days (Monday, May 4)

- [ ] Huawei Cloud credits released — verify in Huawei Cloud console > My Resources > Quota
- [ ] `terraform.tfvars` populated with real values
  - [ ] `access_key` / `secret_key` (1Password: `op read "op://Huawei/AK-SK/username"`)
  - [ ] `dws_admin_password`
  - [ ] `maas_api_key` (MaaS DeepSeek)
  - [ ] `deepseek_api_key` (DeepSeek direct fallback)
  - [ ] `project_id = "fbb6435c497c41bda90a0cc5240573e0"`
  - [ ] `keypair_name = "hermes-agent"`
  - [ ] `region = "la-north-2"`
  - [ ] `langfuse_public_key` (from cloud.langfuse.com)
  - [ ] `langfuse_secret_key` (from cloud.langfuse.com)
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
  - [ ] foundation module (VPC, subnets, SGs, OBS buckets, KMS, IAM)
  - [ ] compute module (ECS for Dify, web server, EIPs)
  - [ ] data-platform module (DLI, DWS, DataArts)
  - [ ] ai-ocr module (FunctionGraph functions)
- [ ] DNS resolution works from all ECS instances
  - [ ] Run `scripts/fix-dns.sh`
  - [ ] Verify: `ssh root@<ECS_IP> nslookup google.com` succeeds
- [ ] Dify deployed and accessible
  - [ ] Run `scripts/setup-dify.sh`
  - [ ] Verify: `curl -s -o /dev/null -w "%{http_code}" http://<DIFY_IP>/` returns 200 or 302
  - [ ] Verify: `curl -s http://<DIFY_IP>/v1` responds

### Commands

```bash
make apply
bash scripts/fix-dns.sh
bash scripts/setup-dify.sh
```

---

## T-2 days (Wednesday, May 6)

- [ ] DWS seed script executed
  - [ ] Run: `PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -f scripts/seed-dws.sql`
  - [ ] Verify: `dm.vendor_risk_summary` materialized view has data
  - [ ] Verify: `risk_results` table exists with indexes
- [ ] Contract PDFs uploaded to OBS bucket
  - [ ] Upload sample contracts to the OBS bucket created by terraform (foundation module)
  - [ ] Verify files visible in Huawei Cloud console > OBS > bucket
- [ ] FunctionGraph functions deployed
  - [ ] Verify `parse_contract.py` deployed and enabled
  - [ ] Verify `ocr_trigger.py` deployed and enabled
  - [ ] Verify `llm_inference.py` deployed and enabled
  - [ ] Test trigger with a sample OBS upload event
- [ ] DataArts pipeline tested
  - [ ] Verify DataArts Factory workspace created
  - [ ] Run test job: DLI Spark SQL -> DWS ingestion
  - [ ] Verify data flows from ODS to DW to DM layers

### Commands

```bash
PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -f scripts/seed-dws.sql

# Verify DWS data
psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -c "SELECT COUNT(*) FROM ods.vendors;"
psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -c "SELECT * FROM dm.vendor_risk_summary;"

# Test DLI Spark SQL
bash scripts/spark-risk-aggregation.py
```

---

## T-1 day (Thursday, May 7)

- [ ] Full demo dry run — all 3 demos end-to-end
  - [ ] Demo 1 (Risk Scoring): DLI Spark SQL + DWS dashboard queries
    - Top vendors by risk level
    - Total exposure by risk level
    - CNBV anomaly summary
  - [ ] Demo 2 (Data Governance): DataArts ETL + DataService REST API + DWS analytics
  - [ ] Demo 3 (Contract AI + Dify): OCR -> DeepSeek -> Dify chatbot Q&A
- [ ] Health check passes — run `scripts/health-check.sh` (0 failures)
- [ ] Backup/recording setup
  - [ ] Run `scripts/backup-record-demos.sh` to generate Plan B videos
  - [ ] Verify ffmpeg and Xvfb installed (`sudo apt install ffmpeg xvfb`)
  - [ ] Verify recordings save to `backups/` directory
  - [ ] Download recordings to local machine as additional backup
- [ ] Dify knowledge base indexed
  - [ ] Run `scripts/index-knowledge-base.py`
  - [ ] Verify contract analysis results appear in Dify KB
  - [ ] Test chatbot can answer questions about contract clauses
- [ ] DataService API tested
  - [ ] Verify DataService REST endpoint returns risk data
  - [ ] Test from ECS: `curl http://<dataservice-api>/risk_results` returns JSON
  - [ ] Verify response includes `risk_score`, `risk_level`, `alertas` fields

### Commands

```bash
make demo          # Full deploy + test data + health check
bash scripts/health-check.sh
bash scripts/backup-record-demos.sh
python scripts/index-knowledge-base.py
```

---

## Day of — Friday, May 8

- [ ] Health check morning of (run at least 2 hours before workshop)
  ```bash
  bash scripts/health-check.sh
  ```
- [ ] Dify accessible — open browser, navigate to `http://<DIFY_IP>/`, log in
- [ ] DWS queries return data
  ```bash
  psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -c "SELECT * FROM dm.vendor_risk_summary;"
  psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -c "SELECT * FROM dm.anomaly_summary LIMIT 5;"
  ```
- [ ] Screen sharing tested
  - [ ] Test in the actual meeting platform (Teams/Zoom/etc.)
  - [ ] Verify terminal text is readable at presentation resolution
  - [ ] Verify browser tabs (Dify, Huawei Cloud console) render clearly
- [ ] Backup internet connection ready
  - [ ] Mobile hotspot tested and charged
  - [ ] Backup laptop with SSH access pre-configured
  - [ ] Pre-recorded demo videos available in `backups/` directory

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
ssh root@<DIFY_IP>
cd /opt/dify/docker
docker compose ps                    # check container status
docker compose logs api              # check API container logs
docker compose logs worker           # check worker logs
docker compose logs redis            # check Redis
docker compose logs postgres         # check PostgreSQL
```

Common fixes:
- **Containers restarting:** Check `.env` for correct LLM API key
- **Port 80 in use:** `lsof -i :80` — kill conflicting process or change port
- **Out of disk:** `df -h` — Dify needs ~20GB for images + data
- **API key invalid:** Verify MAAS_API_KEY or DEEPSEEK_API_KEY is current:
  ```bash
  curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models
  ```
- After changes, restart: `docker compose restart api worker`

### DWS connection refused

- **Security group:** Verify SG allows port 5432 from your IP. Check in Huawei Cloud > VPC > Security Groups.
- **DWS not ready:** DWS takes 15-30 min to provision after `terraform apply`. Check status in console.
- **Wrong endpoint:** Get current endpoint:
  ```bash
  cd terraform && terraform output -raw dws_endpoint
  ```
- **Test connection:**
  ```bash
  PGPASSWORD=$DWS_ADMIN_PASSWORD psql -h $DWS_ENDPOINT -U ayco_admin -d ayco_db -c "SELECT 1;"
  ```

### FunctionGraph function failing

- **Timeout:** Default may be too short for large PDFs. Increase in console: Configuration > Timeout to 300s.
- **Permissions:** Verify FunctionGraph has OBS read + MaaS invoke permissions via IAM agency.
- **Logs:** Check in Huawei Cloud > FunctionGraph > Function > Logs.
- **Test locally:**
  ```bash
  python terraform/modules/ai-ocr/functions/parse_contract.py  # run with sample PDF
  ```

### DataArts pipeline stuck or failing

- **DLI cluster:** Check DLI queue is active and has available slots.
- **IAM permissions:** DataArts needs DWS write + OBS read + DLI execute permissions.
- **Check job logs:** Huawei Cloud > DataArts Factory > Job > Click failed job > Logs.
- **Re-run job:** Delete and recreate the job if schema changed.

### Terraform apply fails

- **Quota exceeded:** Check Huawei Cloud console > My Resources > Quota. Common limits: ECS instances, EIPs.
- **AK/SK invalid:** Re-verify credentials:
  ```bash
  op read "op://Huawei/AK-SK/username"
  op read "op://Huawei/AK-SK/password"
  ```
- **Module dependency failure:** Apply in order:
  ```bash
  make apply-foundation
  make apply-compute
  make apply-data-platform
  make apply-ai-ocr
  ```
- **State lock:** If interrupted:
  ```bash
  terraform -chdir=terraform force-unlock <LOCK_ID>
  ```

### Demo 3 (Contract AI) — Dify not returning answers

- **KB not indexed:** Run `python scripts/index-knowledge-base.py`
- **LLM API key expired:** Check MAAS_API_KEY or DEEPSEEK_API_KEY in `.env`
- **Dify model config:** In Dify web UI: Settings > Model Provider > Verify DeepSeek is connected and shows "Active"
- **Slow responses:** First request may take 30-60s (cold start). Run a test query before the demo.

### Live demo fails — use backup Plan

```bash
# Option 1: Pre-recorded videos
ls /home/eduardo/dev/ayco-huawei-cloud/backups/
# Play the .mp4 files corresponding to each demo

# Option 2: Quick re-deploy (if cloud issue)
make demo   # Full redeploy takes ~20-30 min

# Option 3: Static screenshots
# Have screenshots of each demo step ready in presentations/
```

### Emergency contacts

- **Huawei Cloud support:** Open ticket via console for quota/infrastructure issues
- **1Password:** Secrets vault: `op://Huawei/AK-SK`
- **Local SSH config:** `~/.ssh/config` should have entries for all ECS instances

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make demo` | Full deploy + test data + health check |
| `bash scripts/langfuse-setup.sh` | Langfuse Cloud setup + verify |
| `make status` | Run health check |
| `make destroy` | Tear down all resources |
| `bash scripts/health-check.sh` | Smoke test endpoints |
| `bash scripts/fix-dns.sh` | Fix DNS on all ECS |
| `bash scripts/setup-dify.sh` | Deploy Dify on ECS |
| `bash scripts/backup-record-demos.sh` | Generate Plan B recordings |
| `make apply-foundation` | Deploy VPC, OBS, KMS, IAM only |
| `make apply-compute` | Deploy ECS + EIPs only |
| `make apply-data-platform` | Deploy DLI, DWS, DataArts only |
| `make apply-ai-ocr` | Deploy FunctionGraph functions only |
