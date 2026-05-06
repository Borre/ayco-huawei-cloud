#!/usr/bin/env bash
# Re-apply MaaS HK fix if plugin_daemon container restarts
# Usage: bash scripts/maas-hk-fix.sh
set -euo pipefail

ECS_IP="${1:-101.44.185.139}"
SSH_KEY="${SSH_KEY_PATH:-~/.ssh/ayco-demo}"

echo "=== Fixing MaaS HK plugin on $ECS_IP ==="

ssh -i "$SSH_KEY" root@$ECS_IP << 'EOF'
# Find plugin directory
PLUGIN_DIR=$(docker exec docker-plugin_daemon-1 find /app -maxdepth 3 -name 'dify-plugin-maas-hk-*' -type d 2>/dev/null | head -1)

if [ -z "$PLUGIN_DIR" ]; then
    echo "ERROR: MaaS HK plugin directory not found"
    exit 1
fi

echo "Plugin dir: $PLUGIN_DIR"
echo "Models before fix:"
docker exec docker-plugin_daemon-1 grep "url:" $PLUGIN_DIR/models/*.yaml | head -3

echo "Applying fix..."
# Fix 1: /v1 -> /v2
docker exec docker-plugin_daemon-1 sed -i 's|/v1/chat/completions|/v2/chat/completions|g' $PLUGIN_DIR/models/*.yaml

# Fix 2: lowercase model names -> capitalized
docker exec docker-plugin_daemon-1 sed -i 's|model: deepseek-v3|model: DeepSeek-V3|g' $PLUGIN_DIR/models/*.yaml
docker exec docker-plugin_daemon-1 sed -i 's|model: deepseek-r1|model: DeepSeek-R1|g' $PLUGIN_DIR/models/*.yaml
docker exec docker-plugin_daemon-1 sed -i 's|model: qwen3-32b|model: Qwen3-32B|g' $PLUGIN_DIR/models/*.yaml

echo "Models after fix:"
docker exec docker-plugin_daemon-1 grep "url:" $PLUGIN_DIR/models/*.yaml | head -3

echo "Restarting plugin_daemon..."
cd /opt/ayco/dify/docker && docker compose restart plugin_daemon

echo "Done. MaaS HK fix re-applied."
EOF
