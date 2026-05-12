#!/usr/bin/env bash
# Deploy AYCO API Backend (FastAPI) to web ECS
# Usage: bash scripts/deploy-api.sh
# Fresh install: set HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY, DWS_PASSWORD env vars
set -euo pipefail

WEB_IP="${WEB_IP:?FATAL: WEB_IP no definida — usa terraform output web_eip}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/ayco-demo}"
API_DIR="/opt/ayco-api"
VENV_DIR="$API_DIR/venv"
SERVICE_NAME="ayco-api"

echo "=== Deploying AYCO API to $WEB_IP ==="

# 1. Ensure directory and venv exist (idempotent)
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@$WEB_IP "bash -s" <<'SETUP'
set -euo pipefail
API_DIR="/opt/ayco-api"
VENV_DIR="$API_DIR/venv"

mkdir -p "$API_DIR"

# Install system deps if missing
if ! command -v python3 &>/dev/null; then
    apt-get update -qq && apt-get install -y -qq python3 python3-venv python3-pip > /dev/null
fi

# Create venv if not exists
if [ ! -f "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Install Python deps
"$VENV_DIR/bin/pip" install -q fastapi uvicorn psycopg2-binary esdk-obs-python httpx

echo "✓ Environment ready"
SETUP

# 2. Deploy main.py
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "$(dirname "$0")/../ayco-api/main.py" \
    "root@$WEB_IP:$API_DIR/main.py"

# 3. Create/update systemd unit if not exists
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@$WEB_IP "bash -s" <<'UNIT'
set -euo pipefail
UNIT_FILE="/etc/systemd/system/ayco-api.service"

if [ ! -f "$UNIT_FILE" ]; then
    # Check required env vars
    if [ -z "${HUAWEI_ACCESS_KEY:-}" ] || [ -z "${HUAWEI_SECRET_KEY:-}" ] || [ -z "${DWS_PASSWORD:-}" ]; then
        echo "⚠️  Fresh install: HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY, and DWS_PASSWORD env vars required"
        echo "   Set them and re-run, or create $UNIT_FILE manually"
        exit 1
    fi

    cat > "$UNIT_FILE" <<EOF
[Unit]
Description=AYCO API Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ayco-api
Environment=PATH=/opt/ayco-api/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=HUAWEI_ACCESS_KEY=$HUAWEI_ACCESS_KEY
Environment=HUAWEI_SECRET_KEY=$HUAWEI_SECRET_KEY
Environment=DWS_HOST=${DWS_HOST:?FATAL: DWS_HOST no definida}
Environment=DWS_PORT=8000
Environment=DWS_DB=ayco_db
Environment=DWS_USER=ayco_admin
Environment=DWS_PASSWORD=$DWS_PASSWORD
Environment=OBS_ENDPOINT=obs.la-north-2.myhuaweicloud.com
Environment=OBS_RAW_BUCKET=ayco-contracts-raw
Environment=OBS_RESULTS_BUCKET=ayco-contracts-results
ExecStart=/opt/ayco-api/venv/bin/python /opt/ayco-api/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    echo "✓ Systemd unit created"
else
    echo "✓ Systemd unit exists (not overwriting)"
fi
UNIT

# 4. Restart service
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@$WEB_IP \
    "fuser -k 8001/tcp 2>/dev/null; sleep 1; systemctl restart $SERVICE_NAME; sleep 2"

# 5. Verify
echo -n "Health check: "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://$WEB_IP/api/health" 2>/dev/null || echo "FAIL")
if [ "$HEALTH" = "200" ]; then
    echo "✅ HTTP 200"
    curl -s "http://$WEB_IP/api/health"
else
    echo "❌ HTTP $HEALTH — check journalctl -u $SERVICE_NAME on ECS"
fi
