#!/bin/bash
# deploy.sh — Build and deploy AYCO frontend to ECS
# Usage: ./deploy.sh [user@host] [ssh-key]
# Defaults: root@149.232.129.39, ~/.ssh/ayco-demo

set -euo pipefail

HOST="${1:-root@149.232.129.39}"
SSH_KEY="${2:-$HOME/.ssh/ayco-demo}"
REMOTE_DIR="/var/www/ayco"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

SSH="ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no"
SCP="scp -i ${SSH_KEY} -o StrictHostKeyChecking=no"

echo "=== AYCO Frontend Deploy ==="
echo "Target: ${HOST}:${REMOTE_DIR}"
echo "Key:    ${SSH_KEY}"
echo ""

# 1. Build
echo "[1/4] Building frontend..."
cd "$SCRIPT_DIR"
npm run build 2>&1 | tail -3

# 2. Upload
echo ""
echo "[2/4] Uploading dist/ to ${HOST}..."
${SSH} "$HOST" "mkdir -p ${REMOTE_DIR}"
${SCP} -r dist/* "${HOST}:${REMOTE_DIR}/"

# 3. Nginx config
echo ""
echo "[3/4] Updating nginx config..."
${SCP} nginx.conf "${HOST}:/etc/nginx/conf.d/ayco.conf"
${SSH} "$HOST" "nginx -t 2>&1 && nginx -s reload"

# 4. Verify
echo ""
echo "[4/4] Verifying deployment..."
HTTP_CODE=$(${SSH} "$HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "=== Deploy exitoso ==="
    echo "Frontend: http://149.232.129.39/"
    echo "Dashboard: http://149.232.129.39/dashboard/"
    echo "API proxy: http://149.232.129.39/api/dify/chat-messages"
else
    echo "WARNING: HTTP status ${HTTP_CODE} — revisa nginx logs en el ECS"
fi
