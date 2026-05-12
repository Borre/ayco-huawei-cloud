#!/usr/bin/env python3
"""Process contracts: extract text → MaaS risk analysis → DWS + OBS results."""

import json
import subprocess
import os
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

MaaS_API_KEY = "zj4l91iQ1C1GZdnboNC4A4IAZRdbxAfWlh_aOdQSZX4lSt2EFBY31zhSgAl77hJbXeVSWkmxV8Wjqm6G_40R0w"
MaaS_ENDPOINT = "https://api.modelarts-maas.com/v2"
DWS_PASSWORD = "AycoD3mo2026!"

CONTRACTS = [
    ("contrato-01-alto-riesgo", "/tmp/contrato-01.pdf"),
    ("contrato-02-bajo-riesgo", "/tmp/contrato-02.pdf"),
    ("contrato-03-critico", "/tmp/contrato-03.pdf"),
]


def extract_text(pdf_path):
    """Extract text from PDF using pdftotext."""
    result = subprocess.run(
        ["pdftotext", pdf_path, "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def analyze_contract(text):
    """Send contract text to MaaS for risk analysis."""
    prompt = f"""Eres un analista de riesgo contractual para una institución financiera mexicana. Analiza el siguiente contrato y devuelve SOLO un JSON válido con esta estructura exacta:

{{
  "contract_number": "extrae del contrato",
  "contratista": "nombre del contratista",
  "estado": "Código de estado de México (ej. CDMX, JAL, NLE, QRO, PUE, GTO, SON, CHIH, BC, TAMPS)",
  "monto_total": 1234567.89,
  "plazo_dias": 365,
  "penalizacion_pct": 5.0,
  "garantia_pct": 10.0,
  "risk_score": 8.5,
  "risk_level": "ALTO",
  "alertas": ["alerta1", "alerta2"],
  "recomendaciones": ["rec1", "rec2"],
  "resumen": "Resumen ejecutivo del contrato en 3-4 oraciones."
}}

risk_level debe ser uno de: BAJO, MEDIO, ALTO, CRITICO.
Si no encuentras el estado explícitamente, intenta inferirlo de la dirección o jurisdicción, o usa CDMX por defecto.

Contrato:
{text[:8000]}
"""

    body = json.dumps({
        "model": "deepseek-v3.2",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        f"{MaaS_ENDPOINT}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MaaS_API_KEY}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())

    content = data["choices"][0]["message"]["content"]
    # Extract JSON from response
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(content[start:end])
    raise ValueError(f"No JSON found in response: {content[:500]}")


def load_to_dws(analysis):
    """Insert risk analysis into DWS."""
    alertas = "|".join(analysis.get("alertas", []))
    recs = "|".join(analysis.get("recomendaciones", []))
    state = analysis.get("estado", "CDMX")

    sql = f"""INSERT INTO risk_results (
        contract_number, vendor_name, state, monto_total, plazo_dias,
        penalizacion_pct, garantia_pct, risk_score, risk_level,
        alertas, recomendaciones, resumen, llm_provider
    ) VALUES (
        '{analysis['contract_number']}',
        '{analysis['contratista']}',
        '{state}',
        {analysis['monto_total']},
        {analysis.get('plazo_dias', 365)},
        {analysis.get('penalizacion_pct', 0)},
        {analysis.get('garantia_pct', 0)},
        {analysis['risk_score']},
        '{analysis['risk_level']}',
        '{alertas}',
        '{recs}',
        '{analysis['resumen']}',
        'MaaS/DeepSeek-v3.2'
    ) ON CONFLICT (contract_number) DO UPDATE SET
        vendor_name = EXCLUDED.vendor_name,
        state = EXCLUDED.state,
        monto_total = EXCLUDED.monto_total,
        risk_score = EXCLUDED.risk_score,
        risk_level = EXCLUDED.risk_level,
        alertas = EXCLUDED.alertas,
        recomendaciones = EXCLUDED.recomendaciones,
        resumen = EXCLUDED.resumen,
        analyzed_at = CURRENT_TIMESTAMP;
"""
    dws_host = os.environ.get("DWS_HOST", "localhost")
    dws_port = os.environ.get("DWS_PORT", "8000")
    cmd = f"PGPASSWORD='{DWS_PASSWORD}' psql -h {dws_host} -p {dws_port} -U ayco_admin -d ayco_db -c \"{sql}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()


def save_results(analysis):
    """Save to local risk_results directory."""
    out_dir = Path(__file__).parent / "data" / "risk_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save individual JSON
    out_file = out_dir / f"risk_{analysis['contract_number']}.json"
    out_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))

    # Append to CSV
    csv_file = out_dir / "risk_results.csv"
    import csv
    fieldnames = [
        "contract_number", "contratista", "estado", "monto_total", "plazo_dias",
        "penalizacion_pct", "garantia_pct", "risk_score", "risk_level",
        "alertas", "recomendaciones", "resumen"
    ]

    file_exists = csv_file.exists()
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = {
            "contract_number": analysis["contract_number"],
            "contratista": analysis["contratista"],
            "estado": analysis.get("estado", "CDMX"),
            "monto_total": analysis["monto_total"],
            "plazo_dias": analysis.get("plazo_dias", 365),
            "penalizacion_pct": analysis.get("penalizacion_pct", 0),
            "garantia_pct": analysis.get("garantia_pct", 0),
            "risk_score": analysis["risk_score"],
            "risk_level": analysis["risk_level"],
            "alertas": "|".join(analysis.get("alertas", [])),
            "recomendaciones": "|".join(analysis.get("recomendaciones", [])),
            "resumen": analysis.get("resumen", ""),
        }
        writer.writerow(row)


def main():
    print("=== Contract Risk Analysis Pipeline ===")
    for name, pdf_path in CONTRACTS:
        print(f"\n--- Processing {name} ---")

        # Extract text
        text = extract_text(pdf_path)
        print(f"  Extracted {len(text)} chars")

        # Analyze with MaaS
        print("  Calling MaaS DeepSeek...")
        try:
            analysis = analyze_contract(text)
            print(f"  Risk: {analysis['risk_level']} (score: {analysis['risk_score']})")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        # Save results
        save_results(analysis)
        print("  Saved to risk_results/")

        # Load to DWS
        result = load_to_dws(analysis)
        print(f"  DWS: {result}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
