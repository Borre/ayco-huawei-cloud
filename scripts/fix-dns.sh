#!/bin/bash
# scripts/fix-dns.sh — Arregla DNS en todos los ECS
# Huawei Cloud Ubuntu images: systemd-resolved roto, cloud-init falla sin esto

set -euo pipefail

TF_DIR="$(dirname "$0")/../terraform"
ECS_IPS=$(terraform -chdir="$TF_DIR" output -json ecs_ips 2>/dev/null | jq -r '.[]' || echo "")

if [ -z "$ECS_IPS" ]; then
  echo "No ECS IPs found in terraform output. Skipping."
  exit 0
fi

for ip in $ECS_IPS; do
  echo "=== Fixing DNS on $ip ==="
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@"$ip" "
    echo 'nameserver 8.8.8.8' > /etc/resolv.conf
    echo 'nameserver 1.1.1.1' >> /etc/resolv.conf
    if nslookup google.com > /dev/null 2>&1; then
      echo '  OK DNS working'
    else
      echo '  FAIL DNS still broken' >&2
    fi
  " 2>/dev/null || echo "  (unreachable — may not be provisioned yet)"
done
