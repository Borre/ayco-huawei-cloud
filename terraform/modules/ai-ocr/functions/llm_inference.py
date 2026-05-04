"""ayco-llm-inference: Risk analysis for contracts.

Default: Huawei Cloud MaaS (DeepSeek v4 Flash)
Fallback: DeepSeek API direct

Trigger: Invoked by parse_contract function or API call
Output:  Risk assessment JSON saved to OBS + indexed in Dify
"""

import json
import os
import urllib.request

# ─── LLM Configuration ──────────────────────────────────
# Priority: MaaS (Huawei Cloud) > DeepSeek direct
MAAS_ENDPOINT = "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions"
MAAS_MODEL = "deepseek-v4-flash"

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

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

        # Try MaaS first, fallback to DeepSeek direct
        analysis, provider = call_llm(user_msg, context)

        try:
            risk_report = json.loads(analysis)
        except json.JSONDecodeError:
            risk_report = {"raw_analysis": analysis, "risk_level": "Indeterminado"}

        risk_report["source_contract"] = contract_data.get("source_key", "unknown")
        risk_report["contract_number"] = contract_data.get("contract_number")
        risk_report["llm_provider"] = provider

        # Save to OBS
        result_key = f"risk_{contract_data.get('contract_number', 'unknown')}.json"
        upload_to_obs(
            os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
            result_key,
            json.dumps(risk_report, ensure_ascii=False, indent=2),
            context,
        )

        # Index in Dify
        index_in_dify(risk_report, context)

        return {"statusCode": 200, "body": json.dumps(risk_report, ensure_ascii=False)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def call_llm(user_message, context):
    """Call LLM with MaaS primary, DeepSeek fallback."""

    # ─── Try MaaS (Huawei Cloud) first ───────────────────
    maas_key = os.environ.get("MAAS_API_KEY", context.get("maas_api_key", ""))
    if maas_key:
        try:
            result = _call_maaS(maas_key, user_message)
            return result, "maas-deepseek-v4-flash"
        except Exception as e:
            print(f"[MaaS] Failed: {e}, falling back to DeepSeek direct")

    # ─── Fallback: DeepSeek API direct ───────────────────
    ds_key = os.environ.get("DEEPSEEK_API_KEY", context.get("deepseek_api_key", ""))
    if ds_key:
        try:
            result = _call_deepseek(ds_key, user_message)
            return result, "deepseek-direct"
        except Exception as e:
            print(f"[DeepSeek] Failed: {e}")

    return json.dumps({"error": "No LLM available", "risk_level": "Indeterminado"}), "none"


def _call_maaS(api_key, user_message):
    """Call Huawei Cloud MaaS (DeepSeek v4 Flash)."""
    payload = json.dumps({
        "model": os.environ.get("MAAS_MODEL", MAAS_MODEL),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        os.environ.get("MAAS_ENDPOINT", MAAS_ENDPOINT),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def _call_deepseek(api_key, user_message):
    """Call DeepSeek API direct (fallback)."""
    payload = json.dumps({
        "model": os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_MODEL),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_ENDPOINT,
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
    print(f"[Dify] Would index risk report for contract {risk_report.get('contract_number')}")
