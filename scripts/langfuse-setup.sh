#!/bin/bash
# ─── Langfuse Observability Setup for AYCO Demo ─────────
# Langfuse Cloud free tier — no infrastructure needed
# Reads keys from .env and verifies connectivity
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "══════════════════════════════════════════════════════"
echo "  Langfuse Observability Setup — AYCO Demo"
echo "══════════════════════════════════════════════════════"
echo ""

# ─── Load .env ─────────────────────────────────────────
if [ -f .env ]; then
    set -a; source .env; set +a
fi

# ─── Step 1: Check if keys exist ────────────────────────
echo "1/3  Checking Langfuse credentials..."
if [ -z "${LANGFUSE_PUBLIC_KEY:-}" ] || [ -z "${LANGFUSE_SECRET_KEY:-}" ]; then
    echo ""
    echo "  ✗ Langfuse keys not found in .env"
    echo ""
    echo "  Para obtener tus keys (gratis):"
    echo "    1. Ve a https://us.cloud.langfuse.com"
    echo "    2. Crea cuenta (Sign up with GitHub/Google)"
    echo "    3. Create Project → \"ayco-demo\""
    echo "    4. Project Settings → API Keys → Create API Key"
    echo "    5. Copia LANGFUSE_PUBLIC_KEY y LANGFUSE_SECRET_KEY"
    echo ""
    echo "  Después actualiza .env:"
    echo "    LANGFUSE_PUBLIC_KEY=pk-lf-..."
    echo "    LANGFUSE_SECRET_KEY=sk-lf-..."
    echo "    LANGFUSE_HOST=https://us.cloud.langfuse.com"
    echo ""
    exit 1
fi
echo "  ✓ Keys found"

# ─── Step 2: Verify connectivity ────────────────────────
echo "2/3  Testing Langfuse API connectivity..."
LANGFUSE_HOST="${LANGFUSE_HOST:-https://us.cloud.langfuse.com}"

HTTP_CODE=$(curl -s -o /tmp/langfuse-health.json -w "%{http_code}" \
    --max-time 10 \
    -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
    "${LANGFUSE_HOST}/api/public/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    STATUS=$(jq -r '.status' /tmp/langfuse-health.json 2>/dev/null || echo "unknown")
    VERSION=$(jq -r '.version' /tmp/langfuse-health.json 2>/dev/null || echo "unknown")
    echo "  ✓ Langfuse API reachable (HTTP ${HTTP_CODE}, status=${STATUS}, version=${VERSION})"
    rm -f /tmp/langfuse-health.json
else
    echo "  ✗ Langfuse API unreachable (HTTP ${HTTP_CODE})"
    echo "  Check LANGFUSE_HOST and network connectivity"
    exit 1
fi

# ─── Step 3: Publish config to Terraform ────────────────
echo "3/3  Publishing Langfuse config to Terraform..."
cat >> .env <<'TFLANGFUSE'

# ─── Langfuse Terraform vars ──────────────────────────
TF_VAR_langfuse_public_key=${LANGFUSE_PUBLIC_KEY}
TF_VAR_langfuse_secret_key=${LANGFUSE_SECRET_KEY}
TF_VAR_langfuse_host=${LANGFUSE_HOST}
TFLANGFUSE

# Validate Terraform still passes
echo "  Running terraform validate..."
if terraform -chdir=terraform validate > /dev/null 2>&1; then
    echo "  ✓ Terraform validation passed with Langfuse vars"
else
    echo "  ✗ Terraform validation failed — check tfvars"
    exit 1
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  Langfuse setup completo  ✓"
echo ""
echo "  Dashboard: ${LANGFUSE_HOST}"
echo "  Proyecto:  ayco-demo"
echo ""
echo "  Después de terraform apply, cada llamada LLM"
echo "  aparecerá como trace en el dashboard."
echo ""
echo "  Traces incluyen:"
echo "    • Latencia (ms)"
echo "    • Tokens estimados"
echo "    • Provider (maas vs deepseek-direct)"
echo "    • Contract number"
echo "    • Input/output truncados (500 chars, seguro)"
echo "══════════════════════════════════════════════════════"
