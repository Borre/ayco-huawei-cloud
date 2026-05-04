#!/usr/bin/env bash
# scripts/upload-contracts-to-obs.sh — Upload contract PDFs + texts to OBS buckets
# Triggers FunctionGraph OCR pipeline for each uploaded file.
#
# Usage: bash scripts/upload-contracts-to-obs.sh
# Requires: HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY in env or .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load env
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a; source "$PROJECT_DIR/.env"; set +a
fi

AK="${HUAWEI_ACCESS_KEY:?Set HUAWEI_ACCESS_KEY}"
SK="${HUAWEI_SECRET_KEY:?Set HUAWEI_SECRET_KEY}"
REGION="${HUAWEI_REGION:-la-north-2}"
RAW_BUCKET="${OBS_RAW_BUCKET:-ayco-contracts-raw}"
TEXT_BUCKET="${OBS_TEXT_BUCKET:-ayco-contracts-text}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[upload]${NC} $*"; }
warn() { echo -e "${YELLOW}[upload]${NC} $*"; }
err() { echo -e "${RED}[upload]${NC} $*" >&2; }

# Check if obsutil or hcloud is available
upload_file() {
    local file="$1"
    local bucket="$2"
    local key="$3"

    if command -v obsutil &>/dev/null; then
        obsutil cp "$file" "obs://${bucket}/${key}" -f 2>/dev/null
    elif command -v hcloud &>/dev/null; then
        # hcloud doesn't have direct OBS upload, fall back to curl
        warn "obsutil not found, using manual upload"
        return 1
    else
        err "Neither obsutil nor hcloud found. Install obsutil: https://support.huaweicloud.com/intl/en-us/obsutil/obsutil_01_0001.html"
        return 1
    fi
}

# ─── Upload contract PDFs to raw bucket (triggers OCR) ─────────
log "Uploading contract PDFs to obs://${RAW_BUCKET}/"
log "This will trigger FunctionGraph OCR pipeline for each file."

CONTRACTS_DIR="$PROJECT_DIR/data/contracts"
if [ ! -d "$CONTRACTS_DIR" ]; then
    err "No contracts directory found at $CONTRACTS_DIR"
    exit 1
fi

pdf_count=0
for pdf in "$CONTRACTS_DIR"/*.pdf; do
    [ -f "$pdf" ] || continue
    fname=$(basename "$pdf")
    log "  Uploading: ${fname} → obs://${RAW_BUCKET}/${fname}"
    if upload_file "$pdf" "$RAW_BUCKET" "$fname"; then
        ((pdf_count++))
    fi
done

# ─── Upload contract texts to text bucket ─────────────────────
log "Uploading contract texts to obs://${TEXT_BUCKET}/"

TEXTS_DIR="$PROJECT_DIR/data/contract_texts"
if [ -d "$TEXTS_DIR" ]; then
    txt_count=0
    for txt in "$TEXTS_DIR"/*.txt; do
        [ -f "$txt" ] || continue
        fname=$(basename "$txt")
        log "  Uploading: ${fname} → obs://${TEXT_BUCKET}/${fname}"
        if upload_file "$txt" "$TEXT_BUCKET" "$fname"; then
            ((txt_count++))
        fi
    done
else
    warn "No contract_texts directory. Run: python3 scripts/generate-contract-data.py"
    txt_count=0
fi

# ─── Summary ───────────────────────────────────────────────────
echo ""
log "Upload complete:"
log "  PDFs:  ${pdf_count} files → obs://${RAW_BUCKET}/"
log "  Texts: ${txt_count} files → obs://${TEXT_BUCKET}/"
echo ""
log "Next steps:"
log "  1. FunctionGraph ocr_trigger will process PDFs automatically"
log "  2. Check results: obsutil ls obs://ayco-contracts-results/"
log "  3. Seed DWS: psql -f data/seed_risk_results.sql"
