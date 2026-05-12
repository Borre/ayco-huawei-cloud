#!/bin/bash
# scripts/fix-dns.sh — Verifica resolución DNS en todos los ECS
# Ya NO sobreescribe resolv.conf con 8.8.8.8/1.1.1.1.
# El subnet ya tiene primary_dns=100.125.1.250 (Huawei Cloud DNS interno)
# que resuelve MaaS, OBS, DWS endpoints sin problemas.
# Si hay issues, revisar systemd-resolved en lugar de sobrescribir.

set -euo pipefail

TF_DIR="$(dirname "$0")/../terraform"
ECS_IPS=$(terraform -chdir="$TF_DIR" output -json ecs_ips 2>/dev/null | jq -r '.[]' || echo "")

if [ -z "$ECS_IPS" ]; then
  echo "No ECS IPs found in terraform output. Skipping."
  exit 0
fi

for ip in $ECS_IPS; do
  echo "=== Verificando DNS en $ip ==="
  ssh -i ~/.ssh/ayco-demo -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@"$ip" "
    echo '  resolv.conf actual:'
    cat /etc/resolv.conf
    echo ''
    if nslookup api-ap-southeast-1.modelarts-maas.com > /dev/null 2>&1; then
      echo '  OK MaaS endpoint resuelve'
    else
      echo '  FAIL: MaaS endpoint NO resuelve'
      echo '  Intentar: systemctl stop systemd-resolved && systemctl disable systemd-resolved'
      echo '  Luego verificar que subnet DNS en la VPC tenga 100.125.1.250 como primary'
    fi
  " 2>/dev/null || echo "  (unreachable — may not be provisioned yet)"
done
