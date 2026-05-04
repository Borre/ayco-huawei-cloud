#!/bin/bash
# scripts/setup-dify.sh — Deploy Dify en ECS vía docker-compose

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

# Configurar DeepSeek como LLM default
cat >> .env << 'ENVVARS'
# DeepSeek API (AYCO demo)
DEEPSEEK_API_KEY=__DEEPSEEK_API_KEY_PLACEHOLDER__
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
ENVVARS

docker compose up -d

echo "=== Dify running on http://$(curl -s ifconfig.me) ==="
DEPLOY

# Reemplazar placeholder con API key real
ssh -o StrictHostKeyChecking=no root@"$DIFY_IP" \
  "sed -i 's|__DEEPSEEK_API_KEY_PLACEHOLDER__|${DEEPSEEK_API_KEY:-sk-placeholder}|' /opt/dify/docker/.env"

echo "=== Dify deploy complete ==="
echo "    Web: http://$DIFY_IP"
echo "    API: http://$DIFY_IP/v1"
