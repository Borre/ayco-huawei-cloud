#!/usr/bin/env python3
"""scripts/generate-test-data.py — Datos sintéticos México para AYCO demo.
Genera vendors, customers y transacciones con anomalías CNBV."""

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)  # Reproducible

MEX_STATES = ["CDMX", "JAL", "NLE", "QRO", "PUE", "GTO", "SON", "CHIH", "BC", "TAMPS"]
CNBV_FLAGGED = ["Tijuana", "Ciudad Juárez", "Nuevo Laredo", "Tapachula", "Reynosa"]
SECTORS = ["Tecnología", "Construcción", "Servicios Financieros", "Manufactura", "Retail", "Energía", "Salud"]
RISK_LEVELS = ["Bajo", "Medio", "Alto", "Crítico"]
KYC_LEVELS = ["Nivel1", "Nivel2", "Nivel3"]
ANOMALY_TYPES = ["normal", "structuring", "cross_border", "unusual_time", "large_amount"]

# ─── Vendors (2,300) ──────────────────────────────
print("Generating vendors...")
vendors = []
for i in range(1, 2301):
    risk = random.choices(RISK_LEVELS, weights=[45, 30, 18, 7])[0]
    city = random.choice(CNBV_FLAGGED) if random.random() < 0.1 else "CDMX"
    vendors.append({
        "vendor_id": f"V-{i:04d}",
        "name": f"Proveedor {i}",
        "sector": random.choice(SECTORS),
        "state": random.choice(MEX_STATES),
        "city": city,
        "risk_level": risk,
        "risk_score": round(random.uniform(1, 10), 1),
        "annual_revenue_mxn": round(random.uniform(1e6, 500e6), 2),
        "debt_ratio": round(random.uniform(0.1, 0.9), 2),
        "contract_count": random.randint(1, 15),
        "employee_count": random.randint(5, 2000),
    })

with open(DATA_DIR / "vendors.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=vendors[0].keys())
    w.writeheader()
    w.writerows(vendors)

# ─── Customers (500) ───────────────────────────────
print("Generating customers...")
customers = []
for i in range(1, 501):
    kyc = random.choices(KYC_LEVELS, weights=[55, 30, 15])[0]
    customers.append({
        "customer_id": f"C-{i:04d}",
        "name": f"Cliente {i}",
        "kyc_level": kyc,
        "monthly_limit_mxn": {"Nivel1": 7500, "Nivel2": 30000, "Nivel3": 999999}[kyc],
        "risk_score": round(random.uniform(1, 10), 1),
        "state": random.choice(MEX_STATES),
        "city": random.choice(CNBV_FLAGGED) if random.random() < 0.08 else "CDMX",
        "account_age_days": random.randint(30, 1825),
    })

with open(DATA_DIR / "customers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=customers[0].keys())
    w.writeheader()
    w.writerows(customers)

# ─── Transactions (5,000) ──────────────────────────
print("Generating transactions with CNBV anomalies...")
transactions = []
for i in range(1, 5001):
    anomaly = random.choices(ANOMALY_TYPES, weights=[70, 10, 6, 6, 8])[0]

    if anomaly == "structuring":
        amount = random.choice([14800, 14850, 14900, 14950, 14990])
        hour = random.randint(8, 18)
    elif anomaly == "large_amount":
        amount = round(random.uniform(50000, 250000), 2)
        hour = random.randint(8, 18)
    elif anomaly == "cross_border":
        amount = round(random.uniform(5000, 80000), 2)
        hour = random.randint(8, 18)
    elif anomaly == "unusual_time":
        amount = round(random.uniform(10000, 60000), 2)
        hour = random.choice([1, 2, 3, 4])
    else:
        amount = round(random.uniform(100, 45000), 2)
        hour = random.randint(6, 22)

    ts = datetime(2026, 4, random.randint(1, 30), hour, random.randint(0, 59))

    transactions.append({
        "tx_id": f"TX-{i:06d}",
        "vendor_id": f"V-{random.randint(1, 2300):04d}",
        "customer_id": f"C-{random.randint(1, 500):04d}",
        "amount_mxn": amount,
        "anomaly_type": anomaly,
        "timestamp": ts.isoformat(),
        "city_from": random.choice(CNBV_FLAGGED) if anomaly == "cross_border" else "CDMX",
        "city_to": "CDMX" if anomaly == "cross_border" else random.choice(["CDMX", "Guadalajara", "Monterrey"]),
    })

with open(DATA_DIR / "transactions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=transactions[0].keys())
    w.writeheader()
    w.writerows(transactions)

# ─── Summary ───────────────────────────────────────
anomaly_counts = {}
for t in transactions:
    anomaly_counts[t["anomaly_type"]] = anomaly_counts.get(t["anomaly_type"], 0) + 1

print(f"\n{'='*50}")
print(f"  {len(vendors):,} vendors (risk: {sum(1 for v in vendors if v['risk_level'] in ('Alto','Crítico')):,} Alto/Crítico)")
print(f"  {len(customers):,} customers")
print(f"  {len(transactions):,} transactions")
print(f"  Anomalies: {', '.join(f'{k}={v}' for k, v in sorted(anomaly_counts.items()) if k != 'normal')}")
print(f"{'='*50}")
print(f"Data written to {DATA_DIR}")
