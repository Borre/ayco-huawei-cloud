#!/bin/bash
# ─── AYCO Dify + Streamlit ECS Startup Script ──────────────────
# Runs on first boot via cloud-init. Idempotent — safe to re-run.

set -euo pipefail
LOG="/var/log/ayco-setup.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== AYCO ECS Setup — $(date) ==="

# ─── System Updates ────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq python3-pip python3-venv nginx certbot python3-certbot-nginx 2>&1 | tail -5

# ─── Create ayco user ──────────────────────────────────────────
id -u ayco &>/dev/null || useradd -m -s /bin/bash ayco
mkdir -p /opt/ayco/dashboards /opt/ayco/dify /opt/ayco/scripts
chown -R ayco:ayco /opt/ayco

# ─── Python venv ───────────────────────────────────────────────
sudo -u ayco python3 -m venv /opt/ayco/venv
sudo -u ayco /opt/ayco/venv/bin/pip install --upgrade pip -q
sudo -u ayco /opt/ayco/venv/bin/pip install -q \
    streamlit psycopg2-binary pandas plotly \
    docker-compose 2>&1 | tail -3

# ─── Dify (if not already installed) ───────────────────────────
if [ ! -d /opt/ayco/dify/docker ]; then
    echo "Installing Dify..."
    sudo -u ayco git clone https://github.com/langgenius/dify.git /opt/ayco/dify 2>&1 | tail -3
    cd /opt/ayco/dify/docker
    cp .env.example .env
    # Update .env with Huawei Cloud specifics
    sed -i "s|^CONSOLE_WEB_URL=.*|CONSOLE_WEB_URL=http://\$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"public-ipv4\"])'):8000|" .env 2>/dev/null || true
    sudo -u ayco docker-compose up -d 2>&1 | tail -5
fi

# ─── Streamlit Dashboard (systemd service) ─────────────────────
cat > /etc/systemd/system/ayco-dashboard.service << 'SYSTEMD'
[Unit]
Description=AYCO Contract Risk Dashboard (Streamlit)
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
User=ayco
WorkingDirectory=/opt/ayco
Environment="DWS_ENDPOINT=${dws_endpoint}"
Environment="DWS_PORT=${dws_port}"
Environment="DWS_DATABASE=${dws_database}"
Environment="DWS_USER=ayco_admin"
Environment="DWS_PASSWORD=${dws_password}"
Environment="STREAMLIT_SERVER_PORT=8501"
Environment="STREAMLIT_SERVER_HEADLESS=true"
Environment="STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
ExecStart=/opt/ayco/venv/bin/streamlit run /opt/ayco/dashboards/risk_dashboard.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

# Copy dashboard code
cp /opt/ayco/dashboards/risk_dashboard.py /opt/ayco/dashboards/risk_dashboard.py 2>/dev/null || true

systemctl daemon-reload
systemctl enable ayco-dashboard
systemctl restart ayco-dashboard

# ─── Nginx reverse proxy (optional — for HTTPS) ────────────────
# Uncomment for production:
# cat > /etc/nginx/sites-available/ayco << 'NGINX'
# server {
#     listen 80;
#     server_name _;
#     location /dashboard { proxy_pass http://127.0.0.1:8501; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }
#     location /dify { proxy_pass http://127.0.0.1:8000; }
# }
# NGINX
# ln -sf /etc/nginx/sites-available/ayco /etc/nginx/sites-enabled/
# nginx -t && systemctl reload nginx

echo "=== AYCO ECS Setup Complete — $(date) ==="
echo "Dashboard: http://$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | python3 -c 'import json,sys; print(json.load(sys.stdin)["public-ipv4"])'):8501"
echo "Dify:      http://$(curl -s http://169.254.169.254/openstack/latest/meta_data.json | python3 -c 'import json,sys; print(json.load(sys.stdin)["public-ipv4"])'):8000"
