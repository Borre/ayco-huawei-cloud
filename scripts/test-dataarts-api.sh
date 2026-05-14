#!/usr/bin/env bash
# scripts/test-dataarts-api.sh — Test DataArts DataService REST APIs
# Calls the risk query and contract detail endpoints.
#
# Usage: bash scripts/test-dataarts-api.sh [DATAARTS_HOST]
# Requires: DataArts deployed and APIs published

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

# DataArts API host (from console or terraform output)
HOST="${1:-${DATAARTS_API_HOST:-}}"
if [ -z "$HOST" ]; then
    echo "Usage: $0 <DATAARTS_API_HOST>"
    echo ""
    echo "Get the host from Huawei Cloud console:"
    echo "  DataArts Studio → DataService → API Management → GetRiskResults → Debug"
    echo ""
    echo "Or set DATAARTS_API_HOST in .env"
    exit 1
fi

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[dataarts]${NC} $*"; }
info() { echo -e "${CYAN}[dataarts]${NC} $*"; }
warn() { echo -e "${YELLOW}[dataarts]${NC} $*"; }

BASE="http://${HOST}"

echo ""
log "Testing DataArts DataService APIs"
log "Host: ${HOST}"
echo ""

# ─── Test 1: Get all high-risk contracts ───────────────────────
log "Test 1: GET /api/v1/risk-results?risk_level=ALTO"
echo "────────────────────────────────────────────────"
RESPONSE=$(curl -s "${BASE}/api/v1/risk-results?risk_level=ALTO&limit=5" 2>/dev/null || echo '{"error":"connection failed"}')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ─── Test 2: Get critical contracts ────────────────────────────
log "Test 2: GET /api/v1/risk-results?risk_level=CRITICO"
echo "────────────────────────────────────────────────"
RESPONSE=$(curl -s "${BASE}/api/v1/risk-results?risk_level=CRITICO&limit=3" 2>/dev/null || echo '{"error":"connection failed"}')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ─── Test 3: Get specific contract detail ──────────────────────
log "Test 3: GET /api/v1/contracts/CT-2026-0001"
echo "────────────────────────────────────────────────"
RESPONSE=$(curl -s "${BASE}/api/v1/contracts/CT-2026-0001" 2>/dev/null || echo '{"error":"connection failed"}')
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# ─── Test 4: Get contract that doesn't exist ──────────────────
log "Test 4: GET /api/v1/contracts/NONEXISTENT (expect 404 or empty)"
echo "────────────────────────────────────────────────"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/v1/contracts/NONEXISTENT" 2>/dev/null || echo "000")
echo "HTTP Status: ${HTTP_CODE}"
echo ""

# ─── Summary ───────────────────────────────────────────────────
log "Tests complete."
echo ""
info "If tests fail:"
info "  1. Check DataArts APIs are published (DataArts Studio → DataService → API Management)"
info "  2. Check DWS has data: psql -c 'SELECT COUNT(*) FROM risk_results;'"
info "  3. Check DataArts data connections are active"
info "  4. Check security group allows traffic to DataArts endpoint"
