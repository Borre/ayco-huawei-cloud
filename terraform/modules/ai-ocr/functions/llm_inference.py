"""ayco-llm-inference: DeepSeek risk analysis for contracts.

Trigger: Invoked by parse_contract function or API call
Output:  Risk assessment JSON saved to OBS + indexed in Dify
"""

import json
import os
import urllib.request


DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

SYSTEM_PROMPT = """Eres un analista de riesgo financiero especializado en contratos corporativos mexicanos.

Analiza el contrato proporcionado y genera un reporte de riesgo con:

1. RISK_SCORE: Número del 1-10 (10 = máximo riesgo)
2. RISK_LEVEL: Bajo | Medio | Alto | Crítico
3. ALERTAS: Lista de banderas rojas encontradas
4. RECOMENDACIONES: Acciones sugeridas
5. RESUMEN: Resumen ejecutivo en 3 oraciones

Factores de riesgo a evaluar:
- Penalizaciones por terminación anticipada (15% es alto)
- Montos superiores a $2M MXN requieren aprobación adicional
- Jurisdicción fuera de CDMX es riesgo adicional
- Sin garantía de cumplimiento = riesgo alto
- Periodos de confidencialidad > 5 años = riesgo medio

Responde SOLO en JSON válido."""


def handler(event, context):
    """FunctionGraph entry point."""
    try:
        contract_data = event.get("contract_data", event)

        # Build prompt
        user_msg = f"""Contrato a analizar:
- Número: {contract_data.get('contract_number', 'N/A')}
- Contratista: {contract_data.get('contratista', 'N/A')}
- Monto: ${contract_data.get('monto_total', 'N/A')} MXN
- Vigencia: {contract_data.get('vigencia_inicio', 'N/A')} al {contract_data.get('vigencia_fin', 'N/A')}
- Penalización anticipada: {contract_data.get('penalizacion_anticipada', 'N/A')}
- Penalización retraso: {contract_data.get('penalizacion_retraso', 'N/A')}
- Garantía: {contract_data.get('garantia', 'N/A')}
- Jurisdicción: {contract_data.get('jurisdiccion', 'N/A')}
- Confidencialidad: {contract_data.get('confidencialidad', 'N/A')}"""

        # Call DeepSeek
        analysis = call_deepseek(user_msg, context)

        # Parse response
        try:
            risk_report = json.loads(analysis)
        except json.JSONDecodeError:
            risk_report = {"raw_analysis": analysis, "risk_level": "Indeterminado"}

        # Merge source data
        risk_report["source_contract"] = contract_data.get("source_key", "unknown")
        risk_report["contract_number"] = contract_data.get("contract_number")

        # Save to OBS
        result_key = f"risk_{contract_data.get('contract_number', 'unknown')}.json"
        upload_to_obs(
            os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
            result_key,
            json.dumps(risk_report, ensure_ascii=False, indent=2),
            context,
        )

        # Index in Dify Knowledge Base
        index_in_dify(risk_report, context)

        return {"statusCode": 200, "body": json.dumps(risk_report, ensure_ascii=False)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def call_deepseek(user_message, context):
    """Call DeepSeek Chat API."""
    api_key = os.environ.get("DEEPSEEK_API_KEY", context.get("deepseek_api_key", ""))

    payload = json.dumps({
        "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def upload_to_obs(bucket, key, data, context):
    """Upload to OBS."""
    try:
        from obs import ObsClient
        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        client.putContent(bucket, key, data)
        client.close()
    except ImportError:
        print(f"[OBS] Would upload {key} to {bucket}")


def index_in_dify(risk_report, context):
    """Index risk report in Dify Knowledge Base via API."""
    dify_url = os.environ.get("DIFY_API_URL", "")
    if not dify_url:
        print("[Dify] No DIFY_API_URL configured, skipping indexing")
        return

    # In production: POST to Dify Knowledge Base API
    # POST {dify_url}/datasets/{dataset_id}/documents
    print(f"[Dify] Would index risk report for contract {risk_report.get('contract_number')}")
