"""ayco-ocr-trigger: Trigger OCR on contract PDF upload.

Trigger: OBS event notification (new object in ayco-contracts-raw)
Output:  OCR text saved to ayco-contracts-text bucket

Uses Huawei Cloud OCR API (General Text Recognition) via AK/SK signing.
OCR endpoint: ap-southeast-1 (la-north-2 has no General Text OCR).
Falls back to pdftotext for text-based PDFs.
"""

import json
import os
import base64
import hashlib
import hmac
import datetime
import urllib.request
import urllib.parse
import subprocess
import tempfile


# ─── Huawei Cloud OCR Configuration ─────────────────────────────────────────
OCR_ENDPOINT = os.environ.get("OCR_ENDPOINT", "ocr.ap-southeast-1.myhuaweicloud.com")
OCR_PATH = "/v2/{project_id}/ocr/general-text"


def handler(event, context):
    """FunctionGraph entry point."""
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

            # Try Huawei Cloud OCR API first, fallback to pdftotext
            ocr_text = call_ocr_api(pdf_data, key, context)

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
        return b"placeholder-pdf-data"


def call_ocr_api(pdf_data, key, context):
    """Call Huawei Cloud OCR API with AK/SK signing. Falls back to pdftotext."""
    ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
    sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
    project_id = context.get("project_id", os.environ.get("HUAWEI_PROJECT_ID", ""))

    if not ak or not sk or not project_id:
        print("[OCR] Missing credentials, falling back to pdftotext")
        return fallback_pdftotext(pdf_data, key)

    # ─── Process each page of the PDF ────────────────────────────────
    # Huawei OCR processes one page at a time via pdf_page_number
    all_text = []
    page = 1
    max_pages = 20  # safety limit

    while page <= max_pages:
        try:
            page_text = _call_ocr_single_page(pdf_data, page, ak, sk, project_id)
            if page_text:
                all_text.append(page_text)
            else:
                break  # no more pages
            page += 1
        except Exception as e:
            error_str = str(e)
            # Huawei OCR returns specific error when page doesn't exist
            if "AIS.0005" in error_str or "page" in error_str.lower():
                break
            print(f"[OCR] Page {page} failed: {e}, falling back to pdftotext")
            return fallback_pdftotext(pdf_data, key)

    if all_text:
        full_text = "\n\n".join(all_text)
        print(f"[OCR] Huawei Cloud OCR extracted {len(full_text)} chars from {len(all_text)} pages")
        return full_text
    else:
        print("[OCR] No text extracted from OCR, falling back to pdftotext")
        return fallback_pdftotext(pdf_data, key)


def _call_ocr_single_page(pdf_data, page_number, ak, sk, project_id):
    """Call Huawei Cloud OCR API for a single PDF page using AK/SK signing."""
    # Base64 encode the PDF
    pdf_b64 = base64.b64encode(pdf_data).decode("utf-8")

    # Request body
    body = json.dumps({
        "image": pdf_b64,
        "pdf_page_number": page_number,
        "detect_direction": False,
        "quick_mode": False,
        "language": "auto",
    })

    # Build request
    url = f"https://{OCR_ENDPOINT}{OCR_PATH.format(project_id=project_id)}"
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")

    headers = {
        "Content-Type": "application/json",
        "Host": OCR_ENDPOINT,
        "X-Sdk-Date": timestamp,
    }

    # AK/SK signing (Huawei Cloud APIG signature v2)
    signed_headers, authorization = _sign_request(
        "POST", url, headers, body, ak, sk, datestamp
    )
    headers["Authorization"] = authorization

    # Make request
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise Exception(f"OCR API HTTP {e.code}: {error_body}")

    # Extract text from response
    result = data.get("result", {})
    blocks = result.get("words_block_list", [])
    if not blocks:
        return ""

    text_lines = [block.get("words", "") for block in blocks if block.get("words")]
    return "\n".join(text_lines)


def _sign_request(method, url, headers, body, ak, sk, datestamp):
    """Huawei Cloud APIG Signature v2 (AK/SK signing).

    Compatible with the apig_sdk/signer.py approach.
    """
    # Canonical headers (lowercase, sorted)
    signed_header_keys = sorted(k.lower() for k in headers.keys())
    canonical_headers = ""
    for k in signed_header_keys:
        for orig_k, v in headers.items():
            if orig_k.lower() == k:
                canonical_headers += f"{k}:{v.strip()}\n"

    signed_headers_str = ";".join(signed_header_keys)

    # Body hash
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    # Canonical request
    parsed = urllib.parse.urlparse(url)
    canonical_uri = parsed.path or "/"
    canonical_qs = parsed.query or ""

    canonical_request = "\n".join([
        method,
        canonical_uri,
        canonical_qs,
        canonical_headers,
        signed_headers_str,
        body_hash,
    ])

    # String to sign
    algorithm = "SDK-HMAC-SHA256"
    credential_scope = f"{datestamp}/ap-southeast-1/ocr/sdk_request"
    string_to_sign = "\n".join([
        algorithm,
        headers.get("X-Sdk-Date", ""),
        credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    # Signing key
    def _hmac_sha256(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = _hmac_sha256(sk.encode("utf-8"), datestamp)
    k_region = _hmac_sha256(k_date, "ap-southeast-1")
    k_service = _hmac_sha256(k_region, "ocr")
    k_signing = _hmac_sha256(k_service, "sdk_request")

    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} "
        f"Credential={ak}/{credential_scope}, "
        f"SignedHeaders={signed_headers_str}, "
        f"Signature={signature}"
    )

    return signed_headers_str, authorization


def fallback_pdftotext(pdf_data, key):
    """Fallback: extract text using pdftotext (poppler-utils)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_data)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", tmp_path, "-"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[pdftotext] Extracted {len(result.stdout)} chars from {key}")
            return result.stdout
        else:
            raise Exception(f"pdftotext failed: {result.stderr}")
    finally:
        os.unlink(tmp_path)


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
        print(f"[OBS] Would upload {key} to {bucket}")


def publish_to_dms(message):
    """Publish parsed contract info to DMS/Kafka topic."""
    print(f"[DMS] Would publish to topic ayco-contract-parsed: {json.dumps(message)}")
