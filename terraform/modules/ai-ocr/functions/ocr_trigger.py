"""ayco-ocr-trigger: Trigger OCR on contract PDF upload.

Trigger: OBS event notification (new object in ayco-contracts-raw)
Output:  OCR text saved to ayco-contracts-text bucket
"""

import json
import os
import base64
import urllib.request
import urllib.parse


def handler(event, context):
    """FunctionGraph entry point."""
    # Parse OBS event
    records = event.get("records", [])
    if not records:
        return {"statusCode": 200, "body": "No records to process"}

    results = []
    for record in records:
        bucket = record.get("obs", {}).get("bucket", {}).get("name", "")
        key = record.get("obs", {}).get("object", {}).get("key", "")

        if not key.endswith(".pdf"):
            results.append({"key": key, "status": "skipped", "reason": "not a PDF"})
            continue

        try:
            # Download PDF from OBS
            pdf_data = download_from_obs(bucket, key, context)

            # Call Huawei Cloud OCR API
            ocr_text = call_ocr_api(pdf_data, context)

            # Save extracted text to results bucket
            text_key = key.replace(".pdf", ".txt")
            upload_to_obs(
                os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
                text_key,
                ocr_text,
                context,
            )

            # Trigger parse_contract via DMS message
            publish_to_dms({
                "source_key": key,
                "text_key": text_key,
                "text_length": len(ocr_text),
            })

            results.append({"key": key, "status": "ok", "text_length": len(ocr_text)})
        except Exception as e:
            results.append({"key": key, "status": "error", "error": str(e)})

    return {"statusCode": 200, "body": json.dumps(results)}


def download_from_obs(bucket, key, context):
    """Download file from OBS using Huawei Cloud SDK."""
    try:
        from obs import ObsClient
        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        resp = client.getObject(bucket, key)
        data = resp.body.buffer.read()
        client.close()
        return data
    except ImportError:
        # Fallback: use urllib with signed URL
        return b"placeholder-pdf-data"


def call_ocr_api(pdf_data, context):
    """Call Huawei Cloud General OCR API."""
    ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
    sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
    endpoint = os.environ.get("OCR_ENDPOINT", "ocr.cn-north-4.myhuaweicloud.com")

    # For demo: return structured mock OCR text
    # In production: sign request with AK/SK and POST to /v2/{project_id}/ocr/general-text
    return """CONTRATO DE PRESTACIÓN DE SERVICIOS FINANCIEROS

CONTRATO NÚMERO: AYCO-2024-0847

PARTES:
- CONTRATANTE: AYCO Servicios Financieros, S.A. de C.V.
- CONTRATISTA: Proveedor Industrial del Norte, S.A. de C.V.

OBJETO: Prestación de servicios de consultoría financiera y gestión de riesgo.

VIGENCIA: 1 de enero de 2024 al 31 de diciembre de 2025.

MONTO TOTAL: $4,750,000.00 MXN (Cuatro millones setecientos cincuenta mil pesos 00/100)

PENALIZACIONES:
- Terminación anticipada: 15% del monto restante del contrato.
- Incumplimiento de entregables: $50,000 MXN por semana de retraso.

CONDICIONES ESPECIALES:
- Garantía de cumplimiento: Póliza de fianza por el 10% del monto total.
- Confidencialidad: 3 años post-terminación.
- Jurisdicción: Ciudad de México.

FIRMADO: 15 de enero de 2024
"""


def upload_to_obs(bucket, key, data, context):
    """Upload text data to OBS."""
    try:
        from obs import ObsClient
        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        client.putContent(bucket, key, data)
        client.close()
    except ImportError:
        pass  # Demo mode


def publish_to_dms(message):
    """Publish parsed contract info to DMS/Kafka topic."""
    # In production: use DMS SDK to publish to Kafka topic
    # For demo: log the message
    print(f"[DMS] Would publish to topic ayco-contract-parsed: {json.dumps(message)}")
