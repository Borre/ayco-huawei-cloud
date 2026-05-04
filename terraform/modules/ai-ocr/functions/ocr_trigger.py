"""ayco-ocr-trigger: extract text from uploaded contract PDFs.

Trigger: OBS event notification on ayco-contracts-raw.
Output: extracted text saved to ayco-contracts-text and a parse payload returned.
"""

import base64
import datetime
import hashlib
import hmac
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request


OCR_ENDPOINT = os.environ.get("OCR_ENDPOINT", "ocr.ap-southeast-1.myhuaweicloud.com")
OCR_PATH = "/v2/{project_id}/ocr/general-text"


def handler(event, context):
    records = _get_records(event)
    if not records:
        return {"statusCode": 200, "body": json.dumps({"message": "No records to process"})}

    results = []
    for record in records:
        bucket = record.get("obs", {}).get("bucket", {}).get("name") or event.get("bucket", "")
        key = record.get("obs", {}).get("object", {}).get("key") or event.get("key", "")

        if not key.endswith(".pdf"):
            results.append({"key": key, "status": "skipped", "reason": "not a PDF"})
            continue

        try:
            pdf_data = download_from_obs(bucket, key, context)
            ocr_text = call_ocr_api(pdf_data, key, context)
            text_key = key.replace(".pdf", ".txt")

            upload_to_obs(
                os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
                text_key,
                ocr_text,
                context,
            )

            parse_payload = {
                "source_key": key,
                "text_key": text_key,
                "text_content": ocr_text,
                "text_length": len(ocr_text),
            }
            results.append(
                {
                    "key": key,
                    "status": "ok",
                    "text_length": len(ocr_text),
                    "next_function": "ayco-parse-contract",
                    "parse_payload": parse_payload,
                }
            )
        except Exception as exc:
            results.append({"key": key, "status": "error", "error": str(exc)})

    return {"statusCode": 200, "body": json.dumps(results, ensure_ascii=False)}


def _get_records(event):
    if isinstance(event, str):
        event = json.loads(event)
    if "body" in event and isinstance(event["body"], str):
        try:
            body = json.loads(event["body"])
            event.update(body)
        except json.JSONDecodeError:
            pass
    if event.get("records"):
        return event["records"]
    if event.get("bucket") and event.get("key"):
        return [{"obs": {"bucket": {"name": event["bucket"]}, "object": {"key": event["key"]}}}]
    return []


def download_from_obs(bucket, key, context):
    try:
        from obs import ObsClient
    except ImportError as exc:
        raise RuntimeError("OBS SDK is not available in FunctionGraph runtime") from exc

    ak, sk = _credentials(context)
    endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    try:
        resp = client.getObject(bucket, key)
        return resp.body.buffer.read()
    finally:
        client.close()


def call_ocr_api(pdf_data, key, context):
    ak, sk = _credentials(context)
    project_id = _context_get(context, "project_id") or os.environ.get("HUAWEI_PROJECT_ID", "")

    if not ak or not sk or not project_id:
        print("[OCR] Missing credentials, falling back to pdftotext")
        return fallback_pdftotext(pdf_data, key)

    all_text = []
    for page in range(1, 21):
        try:
            page_text = _call_ocr_single_page(pdf_data, page, ak, sk, project_id)
            if not page_text:
                break
            all_text.append(page_text)
        except Exception as exc:
            error = str(exc)
            if "AIS.0005" in error or "page" in error.lower():
                break
            print(f"[OCR] Page {page} failed: {exc}; falling back to pdftotext")
            return fallback_pdftotext(pdf_data, key)

    if all_text:
        full_text = "\n\n".join(all_text)
        print(f"[OCR] Huawei Cloud OCR extracted {len(full_text)} chars from {len(all_text)} pages")
        return full_text

    print("[OCR] No OCR text extracted; falling back to pdftotext")
    return fallback_pdftotext(pdf_data, key)


def _call_ocr_single_page(pdf_data, page_number, ak, sk, project_id):
    body = json.dumps(
        {
            "image": base64.b64encode(pdf_data).decode("utf-8"),
            "pdf_page_number": page_number,
            "detect_direction": False,
            "quick_mode": False,
            "language": "auto",
        }
    )
    url = f"https://{OCR_ENDPOINT}{OCR_PATH.format(project_id=project_id)}"
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    headers = {
        "Content-Type": "application/json",
        "Host": OCR_ENDPOINT,
        "X-Sdk-Date": timestamp,
    }
    headers["Authorization"] = _sign_request("POST", url, headers, body, ak, sk, datestamp)

    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OCR API HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}") from exc

    blocks = data.get("result", {}).get("words_block_list", [])
    return "\n".join(block.get("words", "") for block in blocks if block.get("words"))


def _sign_request(method, url, headers, body, ak, sk, datestamp):
    signed_header_keys = sorted(k.lower() for k in headers)
    canonical_headers = ""
    for key in signed_header_keys:
        value = next(v for k, v in headers.items() if k.lower() == key)
        canonical_headers += f"{key}:{value.strip()}\n"

    signed_headers = ";".join(signed_header_keys)
    parsed = urllib.parse.urlparse(url)
    canonical_request = "\n".join(
        [
            method,
            parsed.path or "/",
            parsed.query or "",
            canonical_headers,
            signed_headers,
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
        ]
    )

    algorithm = "SDK-HMAC-SHA256"
    region = OCR_ENDPOINT.split(".")[1] if OCR_ENDPOINT.startswith("ocr.") else "ap-southeast-1"
    credential_scope = f"{datestamp}/{region}/ocr/sdk_request"
    string_to_sign = "\n".join(
        [
            algorithm,
            headers["X-Sdk-Date"],
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    def hmac_sha256(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    signing_key = hmac_sha256(
        hmac_sha256(hmac_sha256(sk.encode("utf-8"), datestamp), region),
        "ocr",
    )
    signing_key = hmac_sha256(signing_key, "sdk_request")
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return (
        f"{algorithm} Credential={ak}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )


def fallback_pdftotext(pdf_data, key):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_data)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", tmp_path, "-"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"[pdftotext] Extracted {len(result.stdout)} chars from {key}")
            return result.stdout
        raise RuntimeError(f"pdftotext failed: {result.stderr}")
    finally:
        os.unlink(tmp_path)


def upload_to_obs(bucket, key, data, context):
    try:
        from obs import ObsClient
    except ImportError as exc:
        raise RuntimeError("OBS SDK is not available in FunctionGraph runtime") from exc

    ak, sk = _credentials(context)
    endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    try:
        client.putContent(bucket, key, data)
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
