#!/usr/bin/env python3
"""Local OCR pipeline: extract text from PDFs -> analyze with MaaS DeepSeek."""
import json
import os
import subprocess
import sys
from pathlib import Path

# Load env
env_file = Path(__file__).parent.parent / ".env"
env = {}
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')

MAAS_API_KEY = env.get("MAAS_API_KEY", "")
MAAS_ENDPOINT = env.get("MAAS_ENDPOINT", "https://maas-api.la-north-2.myhuaweicloud.com/v1")

CONTRACTS_DIR = Path(__file__).parent.parent / "data" / "contracts"
RESULTS_DIR = Path(__file__).parent.parent / "data" / "risk_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ANALYSIS_PROMPT = """Eres un analista de riesgo de contratos para una institución financiera mexicana.
Analiza el siguiente contrato y genera un reporte de riesgo.

Requisitos:
1. Extrae: contract_number, vendor_name (contratista), monto_total, plazo_dias, penalizacion_pct, garantia_pct
2. Calcula risk_score (1-10) basado en: monto alto, penalizaciones excesivas, plazos irregulares, garantías insuficientes
3. Clasifica risk_level: BAJO (1-3), MEDIO (4-6), ALTO (7-8), CRITICO (9-10)
4. Lista alertas concretas (máximo 5)
5. Lista recomendaciones accionables (máximo 5)
6. Escribe un resumen de 2-3 oraciones

Responde SOLO con JSON válido en este formato:
{
  "contract_number": "string",
  "vendor_name": "string",
  "monto_total": 0.0,
  "plazo_dias": 0,
  "penalizacion_pct": 0.0,
  "garantia_pct": 0.0,
  "risk_score": 0,
  "risk_level": "BAJO|MEDIO|ALTO|CRITICO",
  "alertas": ["alerta1", "alerta2"],
  "recomendaciones": ["rec1", "rec2"],
  "resumen": "texto"
}
"""

def extract_text(pdf_path):
    """Extract text from PDF using pdftotext."""
    result = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True)
    return result.stdout

def analyze_contract(text, contract_name):
    """Call MaaS API for risk analysis."""
    import urllib.request
    
    url = f"{MAAS_ENDPOINT}/chat/completions"
    headers = {
        "Authorization": f"Bearer {MAAS_API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "model": "DeepSeek-V3.2",
        "messages": [
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": f"Contrato {contract_name}:\n\n{text[:8000]}"}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return {"error": "No JSON found", "raw": content}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=== Local OCR + Risk Analysis Pipeline ===")
    
    pdfs = sorted(CONTRACTS_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} contracts")
    
    results = []
    for pdf in pdfs:
        print(f"\n--- Processing: {pdf.name} ---")
        
        # Step 1: Extract text
        text = extract_text(pdf)
        print(f"  Extracted {len(text)} chars")
        
        # Save text
        text_file = RESULTS_DIR / f"{pdf.stem}.txt"
        text_file.write_text(text)
        print(f"  Text saved to {text_file}")
        
        # Step 2: Analyze with MaaS
        print("  Analyzing with MaaS DeepSeek...")
        analysis = analyze_contract(text, pdf.name)
        
        if "error" in analysis:
            print(f"  ERROR: {analysis.get('error', 'unknown')}")
            continue
        
        # Save results
        result_file = RESULTS_DIR / f"risk_{pdf.stem}.json"
        result_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))
        print(f"  Risk: {analysis.get('risk_level', '?')} (score: {analysis.get('risk_score', '?')})")
        print(f"  Saved to {result_file}")
        
        results.append(analysis)
    
    # Step 3: Generate CSV summary
    if results:
        import csv
        csv_file = RESULTS_DIR / "risk_results.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "contract_number", "vendor_name", "monto_total", "plazo_dias",
                "penalizacion_pct", "garantia_pct", "risk_score", "risk_level",
                "alertas", "recomendaciones", "resumen"
            ])
            writer.writeheader()
            for r in results:
                row = {k: r.get(k, "") for k in writer.fieldnames}
                if isinstance(row.get("alertas"), list):
                    row["alertas"] = " | ".join(row["alertas"])
                if isinstance(row.get("recomendaciones"), list):
                    row["recomendaciones"] = " | ".join(row["recomendaciones"])
                writer.writerow(row)
        print(f"\nCSV summary saved to {csv_file}")
    
    print(f"\n=== Done: {len(results)} contracts analyzed ===")

if __name__ == "__main__":
    main()
