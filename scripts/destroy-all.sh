#!/bin/bash
# scripts/destroy-all.sh — Full cleanup: Terraform + manual resources
# Use with caution: deletes EVERYTHING

set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
PROJECT_DIR="$SCRIPT_DIR/.."
TF_DIR="$PROJECT_DIR/terraform"

echo "=== AYCO DESTROY ALL ==="
echo "    This will destroy all infrastructure in la-north-2"
echo ""
read -p "Type 'DESTROY' to confirm: " confirm
if [ "$confirm" != "DESTROY" ]; then
  echo "Aborted."
  exit 1
fi

# 1. Terraform destroy
echo "=== Terraform Destroy ==="
cd "$TF_DIR"
terraform destroy -auto-approve

# 2. Clean up local data
echo "=== Cleaning local data ==="
rm -rf "$PROJECT_DIR/data/"*.csv
rm -rf "$PROJECT_DIR/data/"*.json
rm -rf "$PROJECT_DIR/backups/"

# 3. Clean up Terraform state (optional)
read -p "Remove .terraform directory and state files? (y/N): " clean_tf
if [ "$clean_tf" = "y" ] || [ "$clean_tf" = "Y" ]; then
  rm -rf "$TF_DIR/.terraform"
  rm -f "$TF_DIR/terraform.tfstate" "$TF_DIR/terraform.tfstate.backup"
  rm -f "$TF_DIR/plan.out" "$TF_DIR/plan.json"
  echo "  Terraform state cleaned."
fi

echo ""
echo "=== DESTROY COMPLETE ==="
echo "    Verify in console: https://console.huaweicloud.com/la-north-2/"
