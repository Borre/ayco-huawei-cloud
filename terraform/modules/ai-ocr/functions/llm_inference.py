     1|"""ayco-llm-inference: Risk analysis for contracts.
     2|
     3|Default: Huawei Cloud MaaS (DeepSeek v4 Flash)
     4|Fallback: DeepSeek API direct
     5|
     6|Trigger: Invoked by parse_contract function or API call
     7|Output:  Risk assessment JSON saved to OBS + indexed in Dify
     8|"""
     9|
    10|import json
    11|import os
    12|import urllib.request
    13|
    14|# ─── LLM Configuration ──────────────────────────────────
    15|# Priority: MaaS (Huawei Cloud) > DeepSeek direct
    16|MAAS_ENDPOINT = "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions"  # base URL + path
    17|MAAS_MODEL = "deepseek-v4-flash"
    18|
    19|DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    20|DEEPSEEK_MODEL = "deepseek-chat"
    21|
    22|SYSTEM_PROMPT = """Eres un analista de riesgo financiero especializado en contratos corporativos mexicanos.
    23|
    24|Analiza el contrato proporcionado y genera un reporte de riesgo con:
    25|
    26|1. RISK_SCORE: Número del 1-10 (10 = máximo riesgo)
    27|2. RISK_LEVEL: Bajo | Medio | Alto | Crítico
    28|3. ALERTAS: Lista de banderas rojas encontradas
    29|4. RECOMENDACIONES: Acciones sugeridas
    30|5. RESUMEN: Resumen ejecutivo en 3 oraciones
    31|
    32|Factores de riesgo a evaluar:
    33|- Penalizaciones por terminación anticipada (15% es alto)
    34|- Montos superiores a $2M MXN requieren aprobación adicional
    35|- Jurisdicción fuera de CDMX es riesgo adicional
    36|- Sin garantía de cumplimiento = riesgo alto
    37|- Periodos de confidencialidad > 5 años = riesgo medio
    38|
    39|Responde SOLO en JSON válido."""
    40|
    41|
    42|def handler(event, context):
    43|    """FunctionGraph entry point."""
    44|    try:
    45|        contract_data = event.get("contract_data", event)
    46|
    47|        user_msg = f"""Contrato a analizar:
    48|- Número: {contract_data.get('contract_number', 'N/A')}
    49|- Contratista: {contract_data.get('contratista', 'N/A')}
    50|- Monto: ${contract_data.get('monto_total', 'N/A')} MXN
    51|- Vigencia: {contract_data.get('vigencia_inicio', 'N/A')} al {contract_data.get('vigencia_fin', 'N/A')}
    52|- Penalización anticipada: {contract_data.get('penalizacion_anticipada', 'N/A')}
    53|- Penalización retraso: {contract_data.get('penalizacion_retraso', 'N/A')}
    54|- Garantía: {contract_data.get('garantia', 'N/A')}
    55|- Jurisdicción: {contract_data.get('jurisdiccion', 'N/A')}
    56|- Confidencialidad: {contract_data.get('confidencialidad', 'N/A')}"""
    57|
    58|        # Try MaaS first, fallback to DeepSeek direct
    59|        analysis, provider = call_llm(user_msg, context)
    60|
    61|        try:
    62|            risk_report = json.loads(analysis)
    63|        except json.JSONDecodeError:
    64|            risk_report = {"raw_analysis": analysis, "risk_level": "Indeterminado"}
    65|
    66|        risk_report["source_contract"] = contract_data.get("source_key", "unknown")
    67|        risk_report["contract_number"] = contract_data.get("contract_number")
    68|        risk_report["llm_provider"] = provider
    69|
    70|        # Save to OBS
    71|        result_key = f"risk_{contract_data.get('contract_number', 'unknown')}.json"
    72|        upload_to_obs(
    73|            os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
    74|            result_key,
    75|            json.dumps(risk_report, ensure_ascii=False, indent=2),
    76|            context,
    77|        )
    78|
    79|        # Index in Dify
    80|        index_in_dify(risk_report, context)
    81|
    82|        return {"statusCode": 200, "body": json.dumps(risk_report, ensure_ascii=False)}
    83|    except Exception as e:
    84|        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    85|
    86|
    87|def call_llm(user_message, context):
    88|    """Call LLM with MaaS primary, DeepSeek fallback."""
    89|
    90|    # ─── Try MaaS (Huawei Cloud) first ───────────────────
    91|    maas_key = os.environ.get("MAAS_API_KEY", context.get("maas_api_key", ""))
    92|    if maas_key:
    93|        try:
    94|            result = _call_maaS(maas_key, user_message)
    95|            return result, "maas-deepseek-v4-flash"
    96|        except Exception as e:
    97|            print(f"[MaaS] Failed: {e}, falling back to DeepSeek direct")
    98|
    99|    # ─── Fallback: DeepSeek API direct ───────────────────
   100|    ds_key = os.environ.get("DEEPSEEK_API_KEY", context.get("deepseek_api_key", ""))
   101|    if ds_key:
   102|        try:
   103|            result = _call_deepseek(ds_key, user_message)
   104|            return result, "deepseek-direct"
   105|        except Exception as e:
   106|            print(f"[DeepSeek] Failed: {e}")
   107|
   108|    return json.dumps({"error": "No LLM available", "risk_level": "Indeterminado"}), "none"
   109|
   110|
   111|def _call_maaS(api_key, user_message):
   112|    """Call Huawei Cloud MaaS (DeepSeek v4 Flash)."""
   113|    payload = json.dumps({
   114|        "model": os.environ.get("MAAS_MODEL", MAAS_MODEL),
   115|        "messages": [
   116|            {"role": "system", "content": SYSTEM_PROMPT},
   117|            {"role": "user", "content": user_message},
   118|        ],
   119|        "temperature": 0.1,
   120|        "max_tokens": 2000,
   121|    }).encode("utf-8")
   122|
   123|    req = urllib.request.Request(
   124|        os.environ.get("MAAS_ENDPOINT", MAAS_ENDPOINT),
   125|        data=payload,
   126|        headers={
   127|            "Content-Type": "application/json",
   128|            "Authorization": f"Bearer {api_key}",
   129|        },
   130|    )
   131|
   132|    with urllib.request.urlopen(req, timeout=60) as resp:
   133|        data = json.loads(resp.read().decode("utf-8"))
   134|        return data["choices"][0]["message"]["content"]
   135|
   136|
   137|def _call_deepseek(api_key, user_message):
   138|    """Call DeepSeek API direct (fallback)."""
   139|    payload = json.dumps({
   140|        "model": os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_MODEL),
   141|        "messages": [
   142|            {"role": "system", "content": SYSTEM_PROMPT},
   143|            {"role": "user", "content": user_message},
   144|        ],
   145|        "temperature": 0.1,
   146|        "max_tokens": 2000,
   147|    }).encode("utf-8")
   148|
   149|    req = urllib.request.Request(
   150|        DEEPSEEK_ENDPOINT,
   151|        data=payload,
   152|        headers={
   153|            "Content-Type": "application/json",
   154|            "Authorization": f"Bearer {api_key}",
   155|        },
   156|    )
   157|
   158|    with urllib.request.urlopen(req, timeout=60) as resp:
   159|        data = json.loads(resp.read().decode("utf-8"))
   160|        return data["choices"][0]["message"]["content"]
   161|
   162|
   163|def upload_to_obs(bucket, key, data, context):
   164|    """Upload to OBS."""
   165|    try:
   166|        from obs import ObsClient
   167|        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
   168|        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
   169|        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
   170|        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
   171|        client.putContent(bucket, key, data)
   172|        client.close()
   173|    except ImportError:
   174|        print(f"[OBS] Would upload {key} to {bucket}")
   175|
   176|
   177|def index_in_dify(risk_report, context):
   178|    """Index risk report in Dify Knowledge Base via API."""
   179|    dify_url = os.environ.get("DIFY_API_URL", "")
   180|    if not dify_url:
   181|        print("[Dify] No DIFY_API_URL configured, skipping indexing")
   182|        return
   183|    print(f"[Dify] Would index risk report for contract {risk_report.get('contract_number')}")
   184|