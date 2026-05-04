     1|"""ayco-parse-contract: Parse OCR text into structured contract data.
     2|
     3|Trigger: DMS message on topic ayco-contract-parsed
     4|Output:  Structured JSON saved to OBS, forwarded to LLM inference
     5|"""
     6|
     7|import json
     8|import os
     9|import re
    10|
    11|
    12|def handler(event, context):
    13|    """FunctionGraph entry point."""
    14|    # Parse DMS message
    15|    messages = event.get("messages", [])
    16|    if not messages:
    17|        # Direct invocation
    18|        messages = [event]
    19|
    20|    results = []
    21|    for msg in messages:
    22|        try:
    23|            source_key = msg.get("source_key", "unknown")
    24|            text_content = msg.get("text_content", "")
    25|
    26|            # If text_content not provided, read from OBS
    27|            if not text_content:
    28|                text_key = msg.get("text_key", "")
    29|                text_content = read_from_obs(
    30|                    os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
    31|                    text_key,
    32|                    context,
    33|                )
    34|
    35|            # Parse contract fields
    36|            parsed = parse_contract_text(text_content, source_key)
    37|
    38|            # Save parsed result to OBS
    39|            result_key = source_key.replace(".pdf", "_parsed.json")
    40|            upload_json_to_obs(
    41|                os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
    42|                result_key,
    43|                parsed,
    44|                context,
    45|            )
    46|
    47|            # Forward to LLM inference
    48|            invoke_llm(parsed, context)
    49|
    50|            results.append({"key": source_key, "status": "ok", "fields_found": len(parsed)})
    51|        except Exception as e:
    52|            results.append({"key": source_key, "status": "error", "error": str(e)})
    53|
    54|    return {"statusCode": 200, "body": json.dumps(results)}
    55|
    56|
    57|def parse_contract_text(text, source_key):
    58|    """Extract structured fields from contract text."""
    59|    parsed = {
    60|        "source_key": source_key,
    61|        "contract_number": extract_field(r"(?:CONTRATO\s+N[UÚ]MERO|N[uú]mero\s+de\s+Contrato)[:\s]+([A-Z0-9\-]+)", text),
    62|        "contratante": extract_field(r"CONTRATANTE[:\s]+([^\n]+)", text),
    63|        "contratista": extract_field(r"CONTRATISTA[:\s]+([^\n]+)", text),
    64|        "monto_total": extract_field(r"MONTO\s+TOTAL[:\s]+\$?([\d,]+\.\d+)", text),
    65|        "moneda": "MXN",
    66|        "vigencia_inicio": extract_field(r"(?:VIGENCIA|del)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
    67|        "vigencia_fin": extract_field(r"(?:al|hasta)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
    68|        "penalizacion_anticipada": extract_field(r"[Tt]erminaci[oó]n\s+anticipada[:\s]+(\d+%)", text),
    69|        "penalizacion_retraso": extract_field(r"retraso[:\s]+\$?([\d,]+\.?\d*\s*MXN)", text),
    70|        "garantia": extract_field(r"[Gg]arant[ií]a[:\s]+([^\n]+)", text),
    71|        "jurisdiccion": extract_field(r"[Jj]urisdicci[oó]n[:\s]+([^\n]+)", text),
    72|        "confidencialidad": extract_field(r"[Cc]onfidencialidad[:\s]+([^\n]+)", text),
    73|        "text_length": len(text),
    74|    }
    75|    return parsed
    76|
    77|
    78|def extract_field(pattern, text):
    79|    """Regex extract a single field."""
    80|    match = re.search(pattern, text)
    81|    return match.group(1).strip() if match else None
    82|
    83|
    84|def read_from_obs(bucket, key, context):
    85|    """Read text from OBS."""
    86|    try:
    87|        from obs import ObsClient
    88|        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
    89|        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
    90|        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    91|        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    92|        resp = client.getObject(bucket, key)
    93|        data = resp.body.buffer.read().decode("utf-8")
    94|        client.close()
    95|        return data
    96|    except ImportError:
    97|        return ""
    98|
    99|
   100|def upload_json_to_obs(bucket, key, data, context):
   101|    """Upload JSON to OBS."""
   102|    try:
   103|        from obs import ObsClient
   104|        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
   105|        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
   106|        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
   107|        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
   108|        client.putContent(bucket, key, json.dumps(data, ensure_ascii=False, indent=2))
   109|        client.close()
   110|    except ImportError:
   111|        pass
   112|
   113|
   114|def invoke_llm(parsed_data, context):
   115|    """Forward parsed data to LLM inference function."""
   116|    # In production: invoke via FunctionGraph SDK
   117|    # For demo: log
   118|    print(f"[LLM] Would invoke ayco-llm-inference with contract {parsed_data.get('contract_number')}")
   119|