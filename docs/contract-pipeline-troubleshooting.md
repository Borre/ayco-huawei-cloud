# Contract AI Pipeline — Troubleshooting Guide

**Last updated:** 2026-05-08

## Architecture Overview

```
Frontend (contract-ai.astro)
  → POST /api/upload (FastAPI on :8001)
    → OBS upload (ayco-contracts-raw)
    → FunctionGraph OCR (ayco-ocr-trigger)
    → FunctionGraph Parse (ayco-parse-contract)
    → FunctionGraph LLM Inference (ayco-llm-inference)
    → OBS results (ayco-contracts-results)
    → DWS insert (risk_results table)
  → GET /api/status/{job_id}
    → Returns status + result JSON
```

## Common Failures

### 1. Upload returns 500

**Symptom:** `POST /api/upload` returns HTTP 500.

**Check:**
```bash
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 \
  'journalctl -u ayco-api --since "5 minutes ago" --no-pager | grep -i error'
```

**Common causes:**
- OBS connection failure (missing credentials in env)
- FunctionGraph invoke fails (no `HUAWEI_ACCESS_KEY`/`SECRET_KEY` in FunctionGraph `user_data`)
- DWS connection refused (cluster down or IP changed)

### 2. Status returns timeout / PENDIENTE

**Symptom:** Upload succeeds but status keeps returning `status: "pending"` or `status: "timeout"`.

**Check:**
```bash
# Check if pipeline ran at all
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 \
  'journalctl -u ayco-api --since "10 minutes ago" --no-pager | grep Pipeline'

# Check FunctionGraph executions
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 \
  'python3 scripts/debug-fgs-executions.py'
```

**Common causes:**
- FunctionGraph OCR function lacks OBS credentials → can't read uploaded PDF
- FunctionGraph parse function lacks OBS credentials → can't read OCR output
- LLM function fails → risk_level becomes invalid → DWS check constraint rejects

### 3. FunctionGraph OBS AccessDenied (403)

**Symptom:** OCR function logs show `AccessDenied` when reading from `ayco-contracts-raw`.

**Fix:** Update FunctionGraph function `user_data` with OBS credentials:
```bash
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 \
  'python3 scripts/fix-fg-credentials.py'
```

**Verify:**
```bash
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 \
  'python3 scripts/test-fgs-invoke.py'
```

### 4. DWS check constraint violation

**Symptom:** `[Pipeline] ... ERROR: new row for relation "risk_results" violates check constraint "risk_results_risk_level_check"`

**Cause:** LLM returns a risk_level not in `{BAJO, MEDIO, ALTO, CRITICO, PENDIENTE}`.

**Fix:** The backend validates risk_level before inserting. If invalid, defaults to `PENDIENTE`. If LLM is completely unavailable, synthetic fallback generates a heuristic score.

### 5. LLM unavailable (synthetic fallback)

**Symptom:** Pipeline completes but `llm_provider` shows `"synthetic-fallback"` instead of the actual model.

**Check:**
```bash
# Test MaaS directly
curl -s https://maas.huaweicloud.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MAAS_API_KEY" \
  -d '{"model":"deepseek-v4-pro","messages":[{"role":"user","content":"test"}]}'
```

**Known issues:**
- DeepSeek v4 Flash returns 404 from Huawei Cloud IPs (region-blocked)
- MaaS endpoint returns 400 if API key is invalid or expired
- Synthetic fallback is heuristic-based, not AI-generated

### 6. OBS `obs.close()` crash

**Symptom:** `RuntimeError: cannot release un-acquired lock` or thread safety errors.

**Cause:** `obs.close()` was called in a threaded FastAPI context. The OBS client is a singleton shared between request threads.

**Fix:** Never call `obs.close()`. The client reuses connections. This was patched in `main.py`.

## FunctionGraph Environment Variables

All three functions require these in `user_data`:

| Variable | Source |
|---|---|
| `HUAWEI_ACCESS_KEY` | Huawei Cloud IAM |
| `HUAWEI_SECRET_KEY` | Huawei Cloud IAM |
| `OBS_ENDPOINT` | `obs.la-north-2.myhuaweicloud.com` |
| `OBS_TEXT_BUCKET` | `ayco-contracts-text` |
| `OBS_RESULTS_BUCKET` | `ayco-contracts-results` |
| `HUAWEI_PROJECT_ID` | `0c2b5d2ff6802f4b2f37c00d43d0ce79` |
| `HUAWEI_REGION` | `la-north-2` |
| `MAAS_API_KEY` | For LLM inference |
| `OCR_ENDPOINT` | OCR API endpoint |
| `LANGFUSE_*` | Tracing (optional) |

Update via console or SDK:
```bash
python3 scripts/fix-fg-credentials.py
```

## Debug Scripts

| Script | Purpose |
|---|---|
| `scripts/debug-fgs-endpoints.py` | List all FunctionGraph functions + status |
| `scripts/debug-fgs-executions.py` | List recent FG executions + errors |
| `scripts/debug-fgs-logs.py` | Fetch logs from a specific FG function |
| `scripts/debug-fgs-direct-invoke.py` | Direct FG invoke with debug payload |
| `scripts/test-fgs-invoke.py` | End-to-end pipeline test (upload → FG → DWS) |
| `scripts/fix-fg-credentials.py` | Update FG functions with OBS credentials |

## Service Management

```bash
# Status
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl status ayco-api'

# Restart
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'systemctl restart ayco-api'

# Logs (live)
ssh -i ~/.ssh/ayco-demo root@149.232.129.39 'journalctl -u ayco-api -f'

# Health check
curl -s http://149.232.129.39:8001/api/health
```

## Key Files

- `/opt/ayco-api/main.py` — FastAPI backend (source in `ayco-api/main.py`)
- `/etc/systemd/system/ayco-api.service` — systemd unit
- `terraform/modules/ai-ocr/functions/` — FunctionGraph source code
- `scripts/seed-dws.sql` — DWS schema (risk_results table)
