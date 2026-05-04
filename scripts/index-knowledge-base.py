#!/usr/bin/env python3
"""scripts/index-knowledge-base.py — Index contract analysis results into Dify Knowledge Base.

Requires:
  - Dify running (http://DIFY_IP)
  - DIFY_API_KEY env var (from Dify console > API Keys)
  - Contract results in OBS bucket ayco-contracts-results

Usage:
  python3 scripts/index-knowledge-base.py
"""

import json
import os
import sys
import urllib.request
import csv
from pathlib import Path

# Load env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DIFY_BASE = os.environ.get("DIFY_BASE_URL", "")
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "")
DATASET_NAME = "ayco-contracts-kb"

if not DIFY_BASE or not DIFY_API_KEY:
    print("ERROR: DIFY_BASE_URL and DIFY_API_KEY must be set")
    print("  Set in .env or export as environment variables")
    sys.exit(1)


def dify_request(method, path, data=None):
    """Make authenticated request to Dify API."""
    url = f"{DIFY_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def get_or_create_dataset(name):
    """Get existing dataset or create new one."""
    datasets = dify_request("GET", "/datasets")
    for ds in datasets.get("data", []):
        if ds["name"] == name:
            print(f"  Found existing dataset: {ds['id']}")
            return ds["id"]

    # Create new
    result = dify_request("POST", "/datasets", {
        "name": name,
        "permission": "all_team_members",
        "indexing_technique": "high_quality",
    })
    print(f"  Created dataset: {result['id']}")
    return result["id"]


def main():
    print("=== Indexing Knowledge Base in Dify ===")

    # 1. Get/create dataset
    dataset_id = get_or_create_dataset(DATASET_NAME)

    # 2. Read contract results from local data dir
    results_dir = Path(__file__).parent.parent / "data"
    contracts = []

    risk_csv = results_dir / "risk_results" / "risk_results.csv"
    if risk_csv.exists():
        with risk_csv.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                contracts.append({
                    "contract_number": row["contract_number"],
                    "contratista": row["vendor_name"],
                    "monto_total": row["monto_total"],
                    "risk_score": row["risk_score"],
                    "risk_level": row["risk_level"],
                    "alertas": split_list(row.get("alertas", "")),
                    "recomendaciones": split_list(row.get("recomendaciones", "")),
                    "resumen": row.get("resumen", ""),
                })

    # Also index any live LLM reports written by FunctionGraph or downloaded locally.
    for f in results_dir.glob("risk_*.json"):
        try:
            contracts.append(json.loads(f.read_text()))
        except Exception as e:
            print(f"  Warning: Could not read {f}: {e}")

    if not contracts:
        print("ERROR: No canonical risk results found.")
        print("  Run: python3 scripts/generate-contract-data.py")
        sys.exit(1)

    # 3. Create documents in Dify
    for contract in contracts:
        text = f"""Contrato: {contract.get('contract_number', 'N/A')}
Contratista: {contract.get('contratista', 'N/A')}
Monto: ${contract.get('monto_total', 'N/A')} MXN
Nivel de Riesgo: {contract.get('risk_level', 'N/A')} (Score: {contract.get('risk_score', 'N/A')}/10)

Alertas:
{format_list(contract.get('alertas', [])) or '- Ninguna'}

Recomendaciones:
{format_list(contract.get('recomendaciones', [])) or '- Ninguna'}

Resumen: {contract.get('resumen', 'N/A')}
"""
        try:
            result = dify_request("POST", f"/datasets/{dataset_id}/documents", {
                "name": f"contract_{contract.get('contract_number', 'unknown')}",
                "text": text,
                "indexing_technique": "high_quality",
                "process_rule": {"mode": "automatic"},
            })
            print(f"  Indexed: {contract.get('contract_number')} -> {result.get('document', {}).get('id', 'ok')}")
        except Exception as e:
            print(f"  Error indexing {contract.get('contract_number')}: {e}")

    print(f"\n=== Done: {len(contracts)} contracts indexed in dataset {dataset_id} ===")


def split_list(value):
    return [item.strip() for item in value.split("|") if item.strip()]


def format_list(value):
    if isinstance(value, str):
        value = split_list(value) or [value]
    return "\n".join(f"- {item}" for item in value if item)


if __name__ == "__main__":
    main()
