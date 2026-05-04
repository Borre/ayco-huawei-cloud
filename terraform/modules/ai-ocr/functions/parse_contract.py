"""ayco-parse-contract: parse OCR text into structured contract data.

Input: direct FunctionGraph invocation with text_content or text_key.
Output: parsed JSON saved to OBS and a payload for ayco-llm-inference.
"""

import json
import os
import re


def handler(event, context):
    messages = _get_messages(event)
    results = []

    for msg in messages:
        try:
            source_key = msg.get("source_key", "unknown")
            text_content = msg.get("text_content") or read_from_obs(
                os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
                msg.get("text_key", ""),
                context,
            )
            parsed = parse_contract_text(text_content, source_key)
            result_key = source_key.replace(".pdf", "_parsed.json")

            upload_json_to_obs(
                os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
                result_key,
                parsed,
                context,
            )

            results.append(
                {
                    "key": source_key,
                    "status": "ok",
                    "fields_found": sum(1 for value in parsed.values() if value),
                    "next_function": "ayco-llm-inference",
                    "llm_payload": {"contract_data": parsed},
                }
            )
        except Exception as exc:
            results.append({"key": msg.get("source_key", "unknown"), "status": "error", "error": str(exc)})

    return {"statusCode": 200, "body": json.dumps(results, ensure_ascii=False)}


def _get_messages(event):
    if isinstance(event, str):
        event = json.loads(event)
    if event.get("messages"):
        return event["messages"]
    return [event]


def parse_contract_text(text, source_key):
    return {
        "source_key": source_key,
        "contract_number": extract_field(
            r"(?:CONTRATO\s+N[UÚ]MERO|N[uú]mero\s+de\s+Contrato)[:\s]+([A-Z0-9\-]+)",
            text,
        ),
        "contratante": extract_party("CONTRATANTE", text),
        "contratista": extract_party("CONTRATISTA", text),
        "monto_total": extract_field(r"MONTO\s+TOTAL[:\s]+\$?([\d,]+\.\d+)", text)
        or extract_field(r"monto total .*?\$?([\d,]+\.\d+)\s*MXN", text, re.IGNORECASE | re.DOTALL),
        "moneda": "MXN",
        "vigencia_inicio": extract_field(r"(?:VIGENCIA|del)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
        "vigencia_fin": extract_field(r"(?:al|hasta)\s+(\d+\s+de\s+\w+\s+de\s+\d{4})", text),
        "penalizacion_anticipada": extract_field(r"[Tt]erminaci[oó]n\s+anticipada[:\s]+(\d+%)", text)
        or extract_field(r"penalizaci[oó]n equivalente al\s+(\d+%)", text, re.IGNORECASE),
        "penalizacion_retraso": extract_field(r"retraso[:\s]+\$?([\d,]+\.?\d*\s*MXN)", text, re.IGNORECASE),
        "garantia": extract_field(r"[Gg]arant[ií]a[:\s]+([^\n]+)", text),
        "jurisdiccion": extract_field(r"[Jj]urisdicci[oó]n[:\s]+([^\n]+)", text),
        "confidencialidad": extract_field(r"[Cc]onfidencialidad[:\s]+([^\n]+)", text),
        "text_length": len(text),
    }


def extract_party(label, text):
    return extract_field(rf"{label}:\s*\n?([^\n]+)", text)


def extract_field(pattern, text, flags=0):
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def read_from_obs(bucket, key, context):
    try:
        from obs import ObsClient
    except ImportError as exc:
        raise RuntimeError("OBS SDK is not available in FunctionGraph runtime") from exc

    ak, sk = _credentials(context)
    endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    try:
        resp = client.getObject(bucket, key)
        return resp.body.buffer.read().decode("utf-8")
    finally:
        client.close()


def upload_json_to_obs(bucket, key, data, context):
    try:
        from obs import ObsClient
    except ImportError as exc:
        raise RuntimeError("OBS SDK is not available in FunctionGraph runtime") from exc

    ak, sk = _credentials(context)
    endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    try:
        client.putContent(bucket, key, json.dumps(data, ensure_ascii=False, indent=2))
    finally:
        client.close()


def _credentials(context):
    return (
        _context_get(context, "access_key") or os.environ.get("HUAWEI_ACCESS_KEY", ""),
        _context_get(context, "secret_key") or os.environ.get("HUAWEI_SECRET_KEY", ""),
    )


def _context_get(context, key):
    if isinstance(context, dict):
        return context.get(key)
    return getattr(context, key, "")
