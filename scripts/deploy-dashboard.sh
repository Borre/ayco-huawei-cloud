#!/usr/bin/env bash
# Deploy Streamlit dashboard on WEB ECS (ayco-web)
# Usage: bash scripts/deploy-dashboard.sh
set -euo pipefail

# ── Configuración (AYCO Web ECS) ──────────────────────────────────────────────
ECS_IP="149.232.129.39"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/ayco-demo}"
DASHBOARD_SRC="dashboards/risk_dashboard.py"
DASHBOARD_DST="/opt/ayco/dashboards/risk_dashboard.py"
SERVICE_NAME="ayco-dashboard"
ENV_FILE="/opt/ayco/.env"

echo "=== Deploying AYCO Dashboard to $ECS_IP ==="

# 1. Copy dashboard file
ssh -i "$SSH_KEY" root@$ECS_IP "mkdir -p /opt/ayco/dashboards"
scp -i "$SSH_KEY" "$(dirname "$0")/../$DASHBOARD_SRC" "root@$ECS_IP:$DASHBOARD_DST"

# 2. Ensure Python deps (streamlit ya instalado en el ECS)
ssh -i "$SSH_KEY" root@$ECS_IP "pip3 install --upgrade streamlit plotly pandas 2>&1 | tail -3" || true

# 3. Create/update systemd service (AYCO Web ECS uses ayco-dashboard)
ssh -i "$SSH_KEY" root@$ECS_IP "cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=AYCO Risk Dashboard (ChatBI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ayco/dashboards
EnvironmentFile=$ENV_FILE
ExecStart=/opt/ayco/venv/bin/python3 -m streamlit run risk_dashboard.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# 4. Reload systemd, enable and restart
ssh -i "$SSH_KEY" root@$ECS_IP "systemctl daemon-reload && systemctl enable $SERVICE_NAME && systemctl restart $SERVICE_NAME"

# 5. Wait and verify via nginx proxy (port 80 → /dashboard/)
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://$ECS_IP/dashboard/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "Dashboard UP: http://$ECS_IP/dashboard/"
else
    echo "WARNING: Dashboard returned HTTP $HTTP_CODE — check nginx/streamlit logs"
    exit 1
fi
