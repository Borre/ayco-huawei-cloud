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


OCR_ENDPOINT = os.environ.get("OCR_ENDPOINT", "ocr.la-north-2.myhuaweicloud.com")
OCR_PATH = "/v2/{project_id}/ocr/general-text"


def handler(event, context):
    # Debug mode: return credentials and env info
    if isinstance(event, str):
        try:
            ev = json.loads(event)
        except:
            ev = {}
    else:
        ev = event
    if ev.get("_debug") or (isinstance(ev, dict) and ev.get("body") and isinstance(ev["body"], str) and "_debug" in ev["body"]):
        try:
            ak, sk = _credentials(context)
            return {"statusCode": 200, "body": json.dumps({
                "debug": True,
                "ak_prefix": ak[:8] + "..." if ak else "(empty)",
                "sk_prefix": sk[:8] + "..." if sk else "(empty)",
                "has_ak": bool(ak),
                "has_sk": bool(sk),
                "obs_endpoint": os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com"),
                "obs_text_bucket": os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
                "env_keys": [k for k in os.environ.keys() if "ACCESS" in k or "SECRET" in k or "KEY" in k],
                "context_type": str(type(context)),
            })}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"debug_error": str(e)})}

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
            import traceback
            tb = traceback.format_exc()
            results.append({"key": key, "status": "error", "error": str(exc), "traceback": tb[-500:]})

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
    # OBS sends lowercase "records" in some versions, uppercase "Records" in others
    if event.get("records") or event.get("Records"):
        return event.get("records") or event.get("Records")
    if event.get("bucket") and event.get("key"):
        return [{"obs": {"bucket": {"name": event["bucket"]}, "object": {"key": event["key"]}}}]
    if "Records" in event and isinstance(event["Records"], list):
        return event["Records"]
    return []


def download_from_obs(bucket, key, context):
    """Download object from OBS. v2 — loadStreamInMemory + multi-format body handling."""
    try:
        from obs import ObsClient
    except ImportError as exc:
        raise RuntimeError("OBS SDK is not available in FunctionGraph runtime") from exc

    ak, sk = _credentials(context)
    endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    try:
        resp = client.getObject(bucket, key, loadStreamInMemory=True)
        body = getattr(resp, "body", None)
        body_type = str(type(body))
        if isinstance(body, bytes):
            if len(body) == 0:
                raise RuntimeError(f"Empty body from OBS (0 bytes)")
            print(f"[OBS] Downloaded {len(body)} bytes from {bucket}/{key}")
            return body
        if body is not None and hasattr(body, "buffer") and body.buffer is not None:
            buf = body.buffer
            if isinstance(buf, bytes):
                return buf
            data = buf.read()
            if data:
                return data
        if body is not None and hasattr(body, "read") and callable(body.read):
            return body.read()
        raise RuntimeError(f"Cannot read body. type={body_type}, len={len(body) if hasattr(body, '__len__') else '?'}")
    finally:
        client.close()


def call_ocr_api(pdf_data, key, context):
    ak, sk = _credentials(context)
    project_id = _context_get(context, "project_id") or os.environ.get("HUAWEI_PROJECT_ID", "")

    if not ak or not sk or not project_id:
        print("[OCR] Missing credentials, falling back to pdftotext")
        return fallback_pdftotext(pdf_data, key)

    # Log what we're doing
    ocr_endpoint = OCR_ENDPOINT
    print(f"[OCR] Calling {ocr_endpoint} (project={project_id[:8]}...) for {key} ({len(pdf_data)} bytes)")

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
            print(f"[OCR] Page {page} failed: {type(exc).__name__}: {exc}")
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
            raw_response = resp.read()
            resp_text = raw_response.decode("utf-8")
            data = json.loads(resp_text)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OCR API HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}") from exc

    # Debug: log response structure
    if page_number == 1:
        keys = list(data.keys()) if isinstance(data, dict) else str(type(data))
        print(f"[OCR debug] Response keys: {keys}")
        if "result" in data:
            rkeys = list(data["result"].keys()) if isinstance(data["result"], dict) else str(type(data["result"]))
            print(f"[OCR debug] result keys: {rkeys}")

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
    # Derive region from endpoint (e.g., ocr.la-north-2.myhuaweicloud.com -> la-north-2)
    region = os.environ.get("HUAWEI_REGION")
    if not region:
        endpoint_parts = OCR_ENDPOINT.split(".")
        if len(endpoint_parts) > 1:
            region = endpoint_parts[1]
        else:
            region = "la-north-2" # Default to project region
    
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
    """Extract text from PDF bytes without external dependencies."""
    # Try PyPDF2 first if available
    try:
        import io
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(pdf_data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            print(f"[PyPDF2] Extracted {len(text)} chars from {key}")
            return text
    except ImportError:
        pass
    except Exception as exc:
        print(f"[PyPDF2] Failed: {exc}")

    # Fallback: try PyPDF2 then raw extraction with zlib decompression
    try:
        import io, re, zlib
        raw = pdf_data
        texts = []
        # Method 1: Try zlib decompress for FlateDecode streams
        for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.DOTALL):
            try:
                decompressed = zlib.decompress(match.group(1))
                decoded = decompressed.decode("latin-1", errors="ignore")
                # Extract text between BT and ET
                for bt_block in re.findall(r"BT(.*?)ET", decoded, re.DOTALL):
                    for tm in re.findall(r"\(([^)]*)\)", bt_block):
                        if tm.strip() and len(tm) > 1:
                            texts.append(tm)
            except Exception:
                pass
        # Method 2: Plain text in PDF (uncompressed)
        if not texts:
            decoded = raw.decode("latin-1", errors="ignore")
            for bt_block in re.findall(r"BT(.*?)ET", decoded, re.DOTALL):
                for tm in re.findall(r"\(([^)]*)\)", bt_block):
                    if tm.strip() and len(tm) > 1:
                        texts.append(tm)
        if texts:
            text = "\n".join(texts)
            print(f"[Raw PDF+zlib] Extracted {len(text)} chars from {key}")
            return text
    except Exception as exc:
        print(f"[Raw PDF] Failed: {exc}")

    raise RuntimeError(f"Cannot extract text from PDF ({len(pdf_data)} bytes). Install pdftotext or PyPDF2.")


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
    """Get AK/SK — prefers env vars (work for API invocations), falls back to agency temp creds."""
    env_ak = os.environ.get("HUAWEI_ACCESS_KEY", "")
    env_sk = os.environ.get("HUAWEI_SECRET_KEY", "")
    if env_ak and env_sk:
        return (env_ak, env_sk)
    try:
        ak = context.getSecurityAccessKey()
        sk = context.getSecuritySecretKey()
        if ak and sk:
            return (ak, sk)
    except (AttributeError, Exception):
        pass
    return ("", "")


def _context_get(context, key):
    if isinstance(context, dict):
        return context.get(key)
    return getattr(context, key, "")
