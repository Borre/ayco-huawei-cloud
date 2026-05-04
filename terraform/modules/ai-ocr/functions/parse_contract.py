"""ayco-parse-contract: Parse OCR text into structured contract data.

Trigger: DMS message on topic ayco-contract-parsed
Output:  Structured JSON saved to OBS, forwarded to LLM inference
"""

import json
import os
import re


def handler(event, context):
    """FunctionGraph entry point."""
    # Parse DMS message
    messages = event.get("messages", [])
    if not messages:
        # Direct invocation
        messages = [event]

    results = []
    for msg in messages:
        try:
            source_key = msg.get("source_key", "unknown")
            text_content = msg.get("text_content", "")

            # If text_content not provided, read from OBS
            if not text_content:
                text_key = msg.get("text_key", "")
                text_content = read_from_obs(
                    os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
                    text_key,
                    context,
                )

            # Parse contract fields
            parsed = parse_contract_text(text_content, source_key)

            # Save parsed result to OBS
            result_key = source_key.replace(".pdf", "_parsed.json")
            upload_json_to_obs(
                os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
                result_key,
                parsed,
                context,
            )

            # Forward to LLM inference
            invoke_llm(parsed, context)

            results.append({"key": source_key, "status": "ok", "fields_found": len(parsed)})
        except Exception as e:
            results.append({"key": source_key, "status": "error", "error": str(e)})

    return {"statusCode": 200, "body": json.dumps(results)}


def parse_contract_text(text, source_key):
    """Extract structured fields from contract text."""
    parsed = {
        "source_key": source_key,
        "contract_number": extract_field(r"(?:CONTRATO\s+N[UÚ]MERO|N[uú]mero\s+de\s+Contrato)[:\s]+([A-Z0-9\-]+)", text),
        "contratante": extract_field(r"CONTRATANTE[:\s]+([^\n]+)", text),
        "contratista": extract_field(r"CONTRATISTA[:\s]+([^\n]+)", text),
        "monto_total": extract_field(r"MONTO\s+TOTAL[:\s]+\$?([\d,]+\.\d+)", text),
        "moneda": "MXN",
        "vigencia_inicio": extract_field(r"(?:VIGENCIA|del)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
        "vigencia_fin": extract_field(r"(?:al|hasta)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
        "penalizacion_anticipada": extract_field(r"[Tt]erminaci[oó]n\s+anticipada[:\s]+(\d+%)", text),
        "penalizacion_retraso": extract_field(r"retraso[:\s]+\$?([\d,]+\.?\d*\s*MXN)", text),
        "garantia": extract_field(r"[Gg]arant[ií]a[:\s]+([^\n]+)", text),
        "jurisdiccion": extract_field(r"[Jj]urisdicci[oó]n[:\s]+([^\n]+)", text),
        "confidencialidad": extract_field(r"[Cc]onfidencialidad[:\s]+([^\n]+)", text),
        "text_length": len(text),
    }
    return parsed


def extract_field(pattern, text):
    """Regex extract a single field."""
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def read_from_obs(bucket, key, context):
    """Read text from OBS."""
    try:
        from obs import ObsClient
        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        resp = client.getObject(bucket, key)
        data = resp.body.buffer.read().decode("utf-8")
        client.close()
        return data
    except ImportError:
        return ""


def upload_json_to_obs(bucket, key, data, context):
    """Upload JSON to OBS."""
    try:
        from obs import ObsClient
        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        client.putContent(bucket, key, json.dumps(data, ensure_ascii=False, indent=2))
        client.close()
    except ImportError:
        pass


def invoke_llm(parsed_data, context):
    """Forward parsed data to LLM inference function."""
    # In production: invoke via FunctionGraph SDK
    # For demo: log
    print(f"[LLM] Would invoke ayco-llm-inference with contract {parsed_data.get('contract_number')}")
