# AYCO DEMO — End-to-End Status
**Date:** May 13, 2026
**Status:** FULLY OPERATIONAL (revived after DWS + frontend fixes)

---

## System Status

| Component | Status | Endpoint | Notes |
|-----------|--------|----------|-------|
| **Frontend (Astro)** | OK | http://149.232.129.39/ | 4 pages, auth fix applied |
| **API Backend** | OK | http://149.232.129.39/api/health | 8 endpoints, DWS connected |
| **Upload + OCR + Analysis** | OK | `POST /api/upload-and-process` | Full pipeline ~5-8s |
| **DWS (GaussDB)** | OK | 46.250.168.254:8000 | 24 records, recreated May 13 |
| **Dashboard (Streamlit)** | OK | http://149.232.129.39/dashboard/ | Nginx proxy → Streamlit :8501 |
| **Dify Chatbot** | OK | http://101.44.185.139 | 3 apps, 11 containers |
| **Agent Tools** | OK | localhost:8400 (via SSH) | 4 endpoints, puerto 8400 no expuesto |
| **Langfuse** | OK | /api/langfuse/metrics | Observability active |
| **OBS Storage** | OK | 3 buckets | Raw, Text, Results |

---

## Data in DWS

| Metric | Value | Notes |
|--------|-------|-------|
| risk_results records | 24 | 3 CRÍTICO, 11 ALTO, 5 MEDIO, 5 BAJO |
| Total Exposure | ~$175M MXN | Synthetic demo data |
| DWS version | 9.1.0.226 | Recreated May 13, 2026 |
| DWS nodes | 2 (dwsx3.4U16G.4DPU) | Reduced from 3 to save cost |

---

## Auth Fix Applied (Chat 401 / Deep Analysis AI)

**Problem:** The ChatWidget's `Authorization` header used `cobranzaMode ? COBRANZA_KEY : DIFY_KEY`. The COBRANZA key was either missing or caused a 401 when used by the wrong app type.

**Fix:** Removed the conditional. Both modes now use `DIFY_KEY` (`app-Y8MxfRygyUWOAfyTlo1MQSJx`).

**Deep Analysis AI button** — Changed from inline `onclick` to event delegation (`document.addEventListener`). The `openChatWithQuery` function now dispatches a `submit` event on `#chat-form`, ensuring the Authorization header from ChatWidget is included.

**Frontend rebuild:** `frontend/.env` needs `PUBLIC_DIFY_API_KEY`.

---

## Demo Script (45 min)

### 1. Intro (5 min)
- Architecture overview: OCR → LLM → DWS → Dashboard
- Business problem: Contract risk analysis at scale
- Solution: Automated pipeline with AI

### 2. Live Upload Demo (10 min)
```bash
curl -X POST http://149.232.129.39/api/upload-and-process \
  -F "file=@contrato.pdf"
```
- Show real-time processing
- Display risk analysis results

### 3. Dashboard Walkthrough (15 min)
- KPIs: Total contracts, exposure, risk distribution
- Drill-down: Filter by risk level
- Contract details: Alerts, recommendations

### 4. Chatbot Demo (10 min)
- "Analiza el contrato AYCO-2026-0147"
- "¿Cuáles son los proveedores con mayor riesgo?"
- "Quiero reestructurar mi deuda" (cobranza flow)

### 5. Q&A (5 min)

---

## Technical Fixes Applied (cumulative)

| # | Fix | Date |
|---|-----|------|
| 1 | FunctionGraph timeout 30s → 120s | May 7 |
| 2 | Direct pipeline `/api/upload-and-process` | May 7 |
| 3 | OCR SDK4 HMAC-SHA256 signing | May 7 |
| 4 | DWS rule-based risk fallback | May 7 |
| 5 | Chat auth: removed COBRANZA_KEY conditional | **May 13** |
| 6 | Deep Analysis AI: event delegation + form submit | **May 13** |
| 7 | DWS recreated (v9.1.0.226, 2 nodes) | **May 13** |
| 8 | DWS nodes reduced 3→2 for cost | **May 13** |
| 9 | Agent Tools levantado (systemd ayco-tools, 4 endpoints) | **May 13** |

---

## Verification Checklist

- [x] Frontend loads (<50ms)
- [x] API health returns 200
- [x] DWS reachable (24 records)
- [x] Dify chatbot responds
- [x] Deep Analysis AI → opens chat with query
- [x] Agent Tools mock responde (SSH localhost:8400)
- [x] Streamlit dashboard loads
- [x] Langfuse receives traces

---

**Demo Status:** READY TO PRESENT
