#!/bin/bash
# scripts/health-check.sh — Smoke test pre-demo
# Verifies all components are accessible before running demos.

set -euo pipefail

TF_DIR="$(dirname "$0")/../terraform"
PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check() {
  local name="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
  if echo "$code" | grep -qE "^($expected)"; then
    echo -e "  ${GREEN}✓${NC} $name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} $name (got $code, expected $expected)"
    FAIL=$((FAIL + 1))
  fi
}

warn_check() {
  local name="$1" msg="$2"
  echo -e "  ${YELLOW}⚠${NC} $name: $msg"
  WARN=$((WARN + 1))
}

echo "=== AYCO Health Check $(date) ==="
echo ""

# ─── Load env ──────────────────────────────────────────────────
if [ -f "$(dirname "$0")/../.env" ]; then
    set -a; source "$(dirname "$0")/../.env"; set +a
fi

# ─── Terraform outputs ────────────────────────────────────────
echo -e "${CYAN}Terraform Outputs:${NC}"
DIFY_IP=$(terraform -chdir="$TF_DIR" output -raw dify_public_ip 2>/dev/null || echo "")
WEB_IP=$(terraform -chdir="$TF_DIR" output -raw web_public_ip 2>/dev/null || echo "")
DWS_ENDPOINT=$(terraform -chdir="$TF_DIR" output -raw dws_endpoint 2>/dev/null || echo "")

[ -n "$DIFY_IP" ] && echo -e "  Dify IP:       ${GREEN}$DIFY_IP${NC}" || warn_check "Dify IP" "not found in terraform outputs"
[ -n "$WEB_IP" ] && echo -e "  Web IP:        ${GREEN}$WEB_IP${NC}" || warn_check "Web IP" "not found"
[ -n "$DWS_ENDPOINT" ] && echo -e "  DWS Endpoint:  ${GREEN}$DWS_ENDPOINT${NC}" || warn_check "DWS Endpoint" "not found"
[ -n "$DATARTS_WS" ] && echo -e "  DataArts WS:   ${GREEN}$DATARTS_WS${NC}" || warn_check "DataArts" "not found"
echo ""

# ─── Demo 1: Compute (Dify + Web) ────────────────────────────
echo -e "${CYAN}Demo 1 — Compute:${NC}"
if [ -n "$DIFY_IP" ]; then
  check "Dify Web UI" "http://$DIFY_IP" "200|302"
  check "Dify API" "http://$DIFY_IP/v1" "200|401|404"
else
  warn_check "Dify" "IP not available"
fi
if [ -n "$WEB_IP" ]; then
  check "Web Server" "http://$WEB_IP" "200|302"
fi
echo ""

# ─── Demo 1: Data Platform (DWS) ─────────────────────────────
echo -e "${CYAN}Demo 1 — Data Platform:${NC}"
if [ -n "$DWS_ENDPOINT" ]; then
  check "DWS Endpoint" "https://$DWS_ENDPOINT" "200|302|400"
fi
  if host "$KAFKA_HOST" &>/dev/null || nslookup "$KAFKA_HOST" &>/dev/null 2>&1; then
    PASS=$((PASS + 1))
  else
  fi
fi
echo ""

# ─── Demo 2: DataArts ─────────────────────────────────────────
echo -e "${CYAN}Demo 2 — DataArts:${NC}"
if [ -n "$DATARTS_WS" ]; then
  echo -e "  ${GREEN}✓${NC} DataArts workspace exists (ID: ${DATARTS_WS:0:8}...)"
  PASS=$((PASS + 1))

  # Check if DataService APIs are accessible
  if [ -n "${DATARTS_API_HOST:-}" ]; then
    check "DataService API" "http://${DATARTS_API_HOST}/api/v1/risk-results" "200|401|403"
  else
    warn_check "DataService API" "DATARTS_API_HOST not set (get from console)"
  fi
else
  warn_check "DataArts" "workspace not found"
fi
echo ""

# ─── Demo 3: LLM APIs ────────────────────────────────────────
echo -e "${CYAN}Demo 3 — LLM APIs:${NC}"
if [ -n "${MAAS_API_KEY:-}" ]; then
  if curl -sf -H "Authorization: Bearer *** \
     "https://api-ap-southeast-1.modelarts-maas.com/v2/models" 2>/dev/null | grep -q "model"; then
    echo -e "  ${GREEN}✓${NC} MaaS DeepSeek API"
    PASS=$((PASS + 1))
  else
    warn_check "MaaS API" "key set but endpoint not responding"
  fi
else
  warn_check "MaaS API" "MAAS_API_KEY not set"
fi

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  if curl -sf -H "Authorization: Bearer *** \
     "https://api.deepseek.com/v1/models" 2>/dev/null | grep -q "deepseek"; then
    echo -e "  ${GREEN}✓${NC} DeepSeek API (fallback)"
    PASS=$((PASS + 1))
  else
    warn_check "DeepSeek API" "key set but endpoint not responding"
  fi
else
  warn_check "DeepSeek API" "DEEPSEEK_API_KEY not set"
fi
echo ""

# ─── Demo Data ─────────────────────────────────────────────────
echo -e "${CYAN}Demo Data:${NC}"
if [ -d "$(dirname "$0")/../data/contracts" ]; then
  pdf_count=$(ls "$(dirname "$0")/../data/contracts/"*.pdf 2>/dev/null | wc -l)
  if [ "$pdf_count" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Contract PDFs: $pdf_count files"
    PASS=$((PASS + 1))
  else
    warn_check "Contract PDFs" "no PDFs in data/contracts/"
  fi
fi

if [ -f "$(dirname "$0")/../data/risk_results/risk_results.csv" ]; then
  row_count=$(tail -n +2 "$(dirname "$0")/../data/risk_results/risk_results.csv" | wc -l)
  echo -e "  ${GREEN}✓${NC} Risk results: $row_count rows"
  PASS=$((PASS + 1))
else
  warn_check "Risk results" "run: python3 scripts/generate-contract-data.py"
fi
echo ""

# ─── Summary ───────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results: ${GREEN}$PASS passed${NC}, ${YELLOW}$WARN warnings${NC}, ${RED}$FAIL failed${NC}"
if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo -e "${GREEN}=== ALL HEALTHY — Ready for demo ===${NC}"
elif [ "$FAIL" -eq 0 ]; then
  echo -e "${YELLOW}=== MOSTLY HEALTHY — Check warnings ===${NC}"
else
  echo -e "${RED}=== ISSUES DETECTED — Fix before demo ===${NC}"
fi