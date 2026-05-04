#!/bin/bash
# scripts/health-check.sh — Smoke test pre-demo

set -euo pipefail

TF_DIR="$(dirname "$0")/../terraform"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
  local name="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -sf -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
  if echo "$code" | grep -qE "^($expected)"; then
    echo -e "  ${GREEN}✓${NC} $name"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} $name (got $code, expected $expected) — $url"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== AYCO Health Check $(date) ==="
echo ""

# Terraform outputs
DIFY_IP=$(terraform -chdir="$TF_DIR" output -raw dify_public_ip 2>/dev/null || echo "")
DWS_ENDPOINT=$(terraform -chdir="$TF_DIR" output -raw dws_endpoint 2>/dev/null || echo "")

# Dify
if [ -n "$DIFY_IP" ]; then
  check "Dify Web UI"  "http://$DIFY_IP"            "200|302"
  check "Dify API"     "http://$DIFY_IP/v1"         "200|401|404"
fi

# DWS
if [ -n "$DWS_ENDPOINT" ]; then
  check "DWS Endpoint"  "https://$DWS_ENDPOINT"     "200|302|400"
fi

# DeepSeek API
if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  if curl -sf -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
     "https://api.deepseek.com/v1/models" 2>/dev/null | grep -q "deepseek"; then
    echo -e "  ${GREEN}✓${NC} DeepSeek API"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${NC} DeepSeek API"
    FAIL=$((FAIL + 1))
  fi
fi

echo ""
echo "Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
[ "$FAIL" -eq 0 ] && echo "=== ALL HEALTHY ===" || echo "=== ISSUES DETECTED ==="
