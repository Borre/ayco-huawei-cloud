#!/usr/bin/env bash
# Deploy Streamlit dashboard on Dify ECS
# Usage: bash scripts/deploy-dashboard.sh
set -euo pipefail

ECS_IP="101.44.185.139"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/ayco-demo}"
DASHBOARD_SRC="dashboards/risk_dashboard_demo.py"
DASHBOARD_DST="/opt/dashboards/risk_dashboard.py"
SERVICE_NAME="streamlit-dashboard"

echo "=== Deploying AYCO Dashboard to $ECS_IP ==="

# 1. Copy dashboard file
ssh -i "$SSH_KEY" root@$ECS_IP "mkdir -p /opt/dashboards"
scp -i "$SSH_KEY" "$(dirname "$0")/../$DASHBOARD_SRC" "root@$ECS_IP:$DASHBOARD_DST"

# 2. Install deps
ssh -i "$SSH_KEY" root@$ECS_IP "pip3 install streamlit plotly pandas 2>&1 | tail -3"

# 3. Create systemd service
ssh -i "$SSH_KEY" root@$ECS_IP "cat > /etc/systemd/system/$SERVICE_NAME.service << 'EOF'
[Unit]
Description=AYCO Risk Dashboard
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/opt/dashboards
ExecStart=/usr/local/bin/streamlit run risk_dashboard.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=on-failure
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF"

# 4. Enable and start
ssh -i "$SSH_KEY" root@$ECS_IP "systemctl daemon-reload && systemctl enable $SERVICE_NAME && systemctl restart $SERVICE_NAME"

# 5. Verify
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://$ECS_IP:8501")
if [ "$HTTP_CODE" = "200" ]; then
    echo "Dashboard UP: http://$ECS_IP:8501"
else
    echo "WARNING: Dashboard returned HTTP $HTTP_CODE"
    exit 1
fi
