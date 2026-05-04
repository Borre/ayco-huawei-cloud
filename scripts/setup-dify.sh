#!/bin/bash
# scripts/setup-dify.sh — Deploy Dify en ECS vía docker-compose
# LLM: MaaS DeepSeek v4 Flash (primary) + DeepSeek direct (fallback)

set -euo pipefail

TF_DIR="$(dirname "$0")/../terraform"
DIFY_IP=$(terraform -chdir="$TF_DIR" output -raw dify_public_ip 2>/dev/null || echo "")

if [ -z "$DIFY_IP" ]; then
  echo "No dify_public_ip in terraform output. Skipping."
  exit 0
fi

# Load env
if [ -f "$(dirname "$0")/../.env" ]; then
  set -a; source "$(dirname "$0")/../.env"; set +a
fi

# Resolve MaaS key
MAAS_KEY="${MAAS_API_KEY:-}"
if [[ "$MAAS_KEY" == op://* ]]; then
  MAAS_KEY=$(op read "$MAAS_KEY" 2>/dev/null || echo "")
fi

echo "=== Deploying Dify on $DIFY_IP ==="

ssh -o StrictHostKeyChecking=no root@"$DIFY_IP" << 'DEPLOY'
set -euo pipefail

# ─── DNS fix ────────────────────────────────────────
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# ─── Docker ──────────────────────────────────────────
if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

# ─── Dify clone ──────────────────────────────────────
cd /opt
if [ ! -d dify ]; then
  git clone https://github.com/langgenius/dify.git
fi

cd dify/docker
cp -n .env.example .env || true

# ─── Configure LLM provider ─────────────────────────
cat >> .env << 'ENVVARS'

# === AYCO Demo — LLM Configuration ===
# Primary: Huawei Cloud MaaS (DeepSeek v4 Flash)
DEEPSEEK_API_KEY=__MAAS_API_KEY_PLACEHOLDER__
DEEPSEEK_API_BASE=https://api-ap-southeast-1.modelarts-maas.com/openai/v1

# Note: Using OpenAI-compatible endpoint for Dify
# Model: deepseek-v4-flash
ENVVARS

docker compose up -d

echo "=== Dify running on http://$(curl -s ifconfig.me) ==="
DEPLOY

# Inject real MaaS API key
ssh -o StrictHostKeyChecking=no root@"$DIFY_IP" \
  "python3 -c 'import sys; f=sys.argv[1]; t=open(f).read().replace(\"__MAAS_API_KEY_PLACEHOLDER__\", sys.argv[2]); open(f, \"w\").write(t)' /opt/dify/docker/.env '${MAAS_KEY:-placeholder}'"

# Restart to pick up new env
ssh -o StrictHostKeyChecking=no root@"$DIFY_IP" \
  "cd /opt/dify/docker && docker compose restart api worker"

echo "=== Deploying Streamlit dashboard ==="
scp -o StrictHostKeyChecking=no "$(dirname "$0")/../dashboards/risk_dashboard.py" root@"$DIFY_IP":/tmp/risk_dashboard.py
ssh -o StrictHostKeyChecking=no root@"$DIFY_IP" << 'DASHBOARD'
set -euo pipefail
mkdir -p /opt/ayco/dashboards
cp /tmp/risk_dashboard.py /opt/ayco/dashboards/risk_dashboard.py
chown -R ayco:ayco /opt/ayco/dashboards || true

if [ -f /etc/systemd/system/ayco-dashboard.service ]; then
  systemctl daemon-reload
  systemctl enable ayco-dashboard
  systemctl restart ayco-dashboard || true
else
  echo "WARN: ayco-dashboard.service not found. The ECS user_data may not have completed."
fi
DASHBOARD

echo "=== Dify deploy complete ==="
echo "    Web:  http://$DIFY_IP"
echo "    API:  http://$DIFY_IP/v1"
echo "    Dashboard: http://$DIFY_IP:8501"
echo "    LLM:  MaaS DeepSeek v4 Flash (via Huawei Cloud)"
