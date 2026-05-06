#!/usr/bin/env bash
# scripts/health-check.sh - Smoke test pre-demo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TF_DIR="$PROJECT_DIR/terraform"
PASS=0
FAIL=0
WARN=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check_http() {
  local name="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
  if echo "$code" | grep -qE "^(${expected})$"; then
    echo -e "  ${GREEN}✓${NC} $name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} $name (got $code, expected $expected)"
    FAIL=$((FAIL + 1))
  fi
}

check_tcp() {
  local name="$1" host="$2" port="$3"
  if command -v nc >/dev/null 2>&1 && nc -z -w 5 "$host" "$port" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} $name"
    PASS=$((PASS + 1))
  else
    warn_check "$name" "could not verify TCP ${host}:${port}"
  fi
}

warn_check() {
  local name="$1" msg="$2"
  echo -e "  ${YELLOW}⚠${NC} $name: $msg"
  WARN=$((WARN + 1))
}

tf_output() {
  local output
  local exit_code

  output=$(terraform -chdir="$TF_DIR" output -raw "$1" 2>&1)
  exit_code=$?

  if [ $exit_code -eq 0 ] && [ -n "$output" ]; then
    echo "$output"
  elif [ $exit_code -ne 0 ] && echo "$output" | grep -q "not found"; then
    echo ""
  else
    echo ""
  fi
}

load_env() {
  if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
  fi
}

echo "=== AYCO Health Check $(date) ==="
echo ""

load_env

echo -e "${CYAN}Terraform Outputs:${NC}"
DIFY_IP="$(tf_output dify_public_ip)"
WEB_IP="$(tf_output web_public_ip)"
DWS_ENDPOINT="$(tf_output dws_endpoint)"
DATAARTS_WS="${DATAARTS_WORKSPACE_ID:-$(tf_output dataarts_workspace_id)}"
DATAARTS_HOST="${DATAARTS_API_HOST:-}"

[ -n "$DIFY_IP" ] && echo -e "  Dify IP:       ${GREEN}$DIFY_IP${NC}" || warn_check "Dify IP" "not found in Terraform outputs"
[ -n "$WEB_IP" ] && echo -e "  Web IP:        ${GREEN}$WEB_IP${NC}" || warn_check "Web IP" "not found in Terraform outputs"
[ -n "$DWS_ENDPOINT" ] && echo -e "  DWS Endpoint:  ${GREEN}$DWS_ENDPOINT${NC}" || warn_check "DWS Endpoint" "not found in Terraform outputs"
[ -n "$DATAARTS_WS" ] && echo -e "  DataArts WS:   ${GREEN}${DATAARTS_WS:0:8}...${NC}" || warn_check "DataArts" "workspace not found"
echo ""

echo -e "${CYAN}Compute:${NC}"
if [ -n "$DIFY_IP" ]; then
  check_http "Dify Web UI" "http://$DIFY_IP" "200|302|307|308"
  check_http "Dify API" "http://$DIFY_IP/v1" "200|302|307|308|401|404"
  check_http "Streamlit Dashboard" "http://$DIFY_IP/dashboard/" "200|302"
else
  warn_check "Dify" "IP not available"
fi
if [ -n "$WEB_IP" ]; then
  check_http "Web Server" "http://$WEB_IP" "200|302"
fi
echo ""

echo -e "${CYAN}Data Platform:${NC}"
if [ -n "$DWS_ENDPOINT" ]; then
  dws_host="${DWS_ENDPOINT%%:*}"
  dws_port="${DWS_ENDPOINT##*:}"
  [ "$dws_port" = "$DWS_ENDPOINT" ] && dws_port="8000"
  check_tcp "DWS TCP Endpoint" "$dws_host" "$dws_port"
else
  warn_check "DWS" "endpoint not available"
fi
echo ""

echo -e "${CYAN}DataArts:${NC}"
if [ -n "$DATAARTS_WS" ]; then
  echo -e "  ${GREEN}✓${NC} DataArts workspace configured"
  PASS=$((PASS + 1))
  if [ -n "$DATAARTS_HOST" ]; then
    check_http "DataService API" "http://${DATAARTS_HOST}/api/v1/risk-results" "200|401|403"
  else
    warn_check "DataService API" "DATAARTS_API_HOST not set; verify from DataArts console"
  fi
else
  warn_check "DataArts" "workspace not found"
fi
echo ""

echo -e "${CYAN}LLM APIs:${NC}"
if [ -n "${MAAS_API_KEY:-}" ]; then
  # Measure MaaS endpoint latency (cross-region: la-north-2 → ap-southeast-1)
  t0=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))" 2>/dev/null || echo "0")
  if curl -sf -H "Authorization: Bearer *** " \
    "https://api-ap-southeast-1.modelarts-maas.com/v2/models" 2>/dev/null | grep -qi "model"; then
    t1=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))" 2>/dev/null || echo "0")
    if [ "$t0" != "0" ] && [ "$t1" != "0" ]; then
      latency_ms=$(( (t1 - t0) / 1000000 ))
      if [ "$latency_ms" -gt 500 ]; then
        warn_check "MaaS API" "cross-region latency ${latency_ms}ms (ap-southeast-1)"
      else
        echo -e "  ${GREEN}✓${NC} MaaS API (${latency_ms}ms)"
        PASS=$((PASS + 1))
      fi
    else
      echo -e "  ${GREEN}✓${NC} MaaS API"
      PASS=$((PASS + 1))
    fi
  else
    warn_check "MaaS API" "key set but endpoint did not confirm models"
  fi
else
  warn_check "MaaS API" "MAAS_API_KEY not set"
fi

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  if curl -sf -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
    "https://api.deepseek.com/v1/models" 2>/dev/null | grep -qi "deepseek"; then
    echo -e "  ${GREEN}✓${NC} DeepSeek API fallback"
    PASS=$((PASS + 1))
  else
    warn_check "DeepSeek API" "key set but endpoint did not confirm models"
  fi
else
  warn_check "DeepSeek API" "DEEPSEEK_API_KEY not set"
fi
echo ""

echo -e "${CYAN}Demo Data:${NC}"
pdf_count=$(find "$PROJECT_DIR/data/contracts" -maxdepth 1 -name '*.pdf' 2>/dev/null | wc -l | tr -d ' ')
if [ "$pdf_count" -gt 0 ]; then
  echo -e "  ${GREEN}✓${NC} Contract PDFs: $pdf_count files"
  PASS=$((PASS + 1))
else
  warn_check "Contract PDFs" "no PDFs in data/contracts"
fi

if [ -f "$PROJECT_DIR/data/risk_results/risk_results.csv" ]; then
  row_count=$(tail -n +2 "$PROJECT_DIR/data/risk_results/risk_results.csv" | wc -l | tr -d ' ')
  if [ "$row_count" -ge 20 ]; then
    echo -e "  ${GREEN}✓${NC} Risk results: $row_count rows (full demo set)"
  else
    warn_check "Risk results" "$row_count rows — run 'make generate-data' for full 20-contract set"
  fi
  PASS=$((PASS + 1))
else
  warn_check "Risk results" "run: python3 scripts/generate-contract-data.py"
fi

# ─── DWS Schema Validation (pre-demo) ───────────────────────────
echo ""
echo -e "${CYAN}DWS Schema:${NC}"
if [ -n "$DWS_ENDPOINT" ] && [ -n "${DWS_ADMIN_PASSWORD:-}" ]; then
  dws_host="${DWS_ENDPOINT%%:*}"
  dws_port="${DWS_ENDPOINT##*:}"
  [ "$dws_port" = "$DWS_ENDPOINT" ] && dws_port="8000"
  # Check if risk_results table exists and has data
  tbl_check=$(PGPASSWORD="$DWS_ADMIN_PASSWORD" psql -h "$dws_host" -p "$dws_port" -U ayco_admin -d ayco_db -t -c \
    "SELECT count(*) FROM risk_results LIMIT 1;" 2>/dev/null || echo "FAIL")
  if [ "$tbl_check" != "FAIL" ] && [ -n "$(echo "$tbl_check" | tr -d ' ')" ]; then
    echo -e "  ${GREEN}✓${NC} DWS risk_results table: $tbl_check rows"
    PASS=$((PASS + 1))
  else
    warn_check "DWS Schema" "risk_results table missing or empty — seed data not loaded"
  fi
  # Validate terraform config
  if cd "$TF_DIR" && terraform validate -no-color >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Terraform config valid"
    PASS=$((PASS + 1))
  else
    warn_check "Terraform" "validate failed — run 'make validate'"
  fi
else
  warn_check "DWS Schema" "DWS_ENDPOINT or DWS_ADMIN_PASSWORD not set (pre-deploy)"
fi
echo ""

echo "----------------------------------------"
echo -e "Results: ${GREEN}$PASS passed${NC}, ${YELLOW}$WARN warnings${NC}, ${RED}$FAIL failed${NC}"
if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo -e "${GREEN}=== ALL HEALTHY - Ready for demo ===${NC}"
elif [ "$FAIL" -eq 0 ]; then
  echo -e "${YELLOW}=== MOSTLY HEALTHY - Check warnings ===${NC}"
else
  echo -e "${RED}=== ISSUES DETECTED - Fix before demo ===${NC}"
fi

exit "$FAIL"
