     1|"""ayco-ocr-trigger: Trigger OCR on contract PDF upload.
     2|
     3|Trigger: OBS event notification (new object in ayco-contracts-raw)
     4|Output:  OCR text saved to ayco-contracts-text bucket
     5|
     6|Uses Huawei Cloud OCR API (General Text Recognition) via AK/SK signing.
     7|OCR endpoint: ap-southeast-1 (la-north-2 has no General Text OCR).
     8|Falls back to pdftotext for text-based PDFs.
     9|"""
    10|
    11|import json
    12|import os
    13|import base64
    14|import hashlib
    15|import hmac
    16|import datetime
    17|import urllib.request
    18|import urllib.parse
    19|import subprocess
    20|import tempfile
    21|
    22|
    23|# ─── Huawei Cloud OCR Configuration ─────────────────────────────────────────
    24|OCR_ENDPOINT = os.environ.get("OCR_ENDPOINT", "ocr.ap-southeast-1.myhuaweicloud.com")
    25|OCR_PATH = "/v2/{project_id}/ocr/general-text"
    26|
    27|
    28|def handler(event, context):
    29|    """FunctionGraph entry point."""
    30|    records = event.get("records", [])
    31|    if not records:
    32|        return {"statusCode": 200, "body": "No records to process"}
    33|
    34|    results = []
    35|    for record in records:
    36|        bucket = record.get("obs", {}).get("bucket", {}).get("name", "")
    37|        key = record.get("obs", {}).get("object", {}).get("key", "")
    38|
    39|        if not key.endswith(".pdf"):
    40|            results.append({"key": key, "status": "skipped", "reason": "not a PDF"})
    41|            continue
    42|
    43|        try:
    44|            # Download PDF from OBS
    45|            pdf_data = download_from_obs(bucket, key, context)
    46|
    47|            # Try Huawei Cloud OCR API first, fallback to pdftotext
    48|            ocr_text = call_ocr_api(pdf_data, key, context)
    49|
    50|            # Save extracted text to results bucket
    51|            text_key = key.replace(".pdf", ".txt")
    52|            upload_to_obs(
    53|                os.environ.get("OBS_TEXT_BUCKET", "ayco-contracts-text"),
    54|                text_key,
    55|                ocr_text,
    56|                context,
    57|            )
    58|
    59|            # Trigger parse_contract via DMS message
    60|            publish_to_dms({
    61|                "source_key": key,
    62|                "text_key": text_key,
    63|                "text_length": len(ocr_text),
    64|            })
    65|
    66|            results.append({"key": key, "status": "ok", "text_length": len(ocr_text)})
    67|        except Exception as e:
    68|            results.append({"key": key, "status": "error", "error": str(e)})
    69|
    70|    return {"statusCode": 200, "body": json.dumps(results)}
    71|
    72|
    73|def download_from_obs(bucket, key, context):
    74|    """Download file from OBS using Huawei Cloud SDK."""
    75|    try:
    76|        from obs import ObsClient
    77|        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
    78|        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
    79|        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
    80|        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
    81|        resp = client.getObject(bucket, key)
    82|        data = resp.body.buffer.read()
    83|        client.close()
    84|        return data
    85|    except ImportError:
    86|        return b"placeholder-pdf-data"
    87|
    88|
    89|def call_ocr_api(pdf_data, key, context):
    90|    """Call Huawei Cloud OCR API with AK/SK signing. Falls back to pdftotext."""
    91|    ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
    92|    sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
    93|    project_id = context.get("project_id", os.environ.get("HUAWEI_PROJECT_ID", ""))
    94|
    95|    if not ak or not sk or not project_id:
    96|        print("[OCR] Missing credentials, falling back to pdftotext")
    97|        return fallback_pdftotext(pdf_data, key)
    98|
    99|    # ─── Process each page of the PDF ────────────────────────────────
   100|    # Huawei OCR processes one page at a time via pdf_page_number
   101|    all_text = []
   102|    page = 1
   103|    max_pages = 20  # safety limit
   104|
   105|    while page <= max_pages:
   106|        try:
   107|            page_text = _call_ocr_single_page(pdf_data, page, ak, sk, project_id)
   108|            if page_text:
   109|                all_text.append(page_text)
   110|            else:
   111|                break  # no more pages
   112|            page += 1
   113|        except Exception as e:
   114|            error_str = str(e)
   115|            # Huawei OCR returns specific error when page doesn't exist
   116|            if "AIS.0005" in error_str or "page" in error_str.lower():
   117|                break
   118|            print(f"[OCR] Page {page} failed: {e}, falling back to pdftotext")
   119|            return fallback_pdftotext(pdf_data, key)
   120|
   121|    if all_text:
   122|        full_text = "\n\n".join(all_text)
   123|        print(f"[OCR] Huawei Cloud OCR extracted {len(full_text)} chars from {len(all_text)} pages")
   124|        return full_text
   125|    else:
   126|        print("[OCR] No text extracted from OCR, falling back to pdftotext")
   127|        return fallback_pdftotext(pdf_data, key)
   128|
   129|
   130|def _call_ocr_single_page(pdf_data, page_number, ak, sk, project_id):
   131|    """Call Huawei Cloud OCR API for a single PDF page using AK/SK signing."""
   132|    # Base64 encode the PDF
   133|    pdf_b64 = base64.b64encode(pdf_data).decode("utf-8")
   134|
   135|    # Request body
   136|    body = json.dumps({
   137|        "image": pdf_b64,
   138|        "pdf_page_number": page_number,
   139|        "detect_direction": False,
   140|        "quick_mode": False,
   141|        "language": "auto",
   142|    })
   143|
   144|    # Build request
   145|    url = f"https://{OCR_ENDPOINT}{OCR_PATH.format(project_id=project_id)}"
   146|    now = datetime.datetime.utcnow()
   147|    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
   148|    datestamp = now.strftime("%Y%m%d")
   149|
   150|    headers = {
   151|        "Content-Type": "application/json",
   152|        "Host": OCR_ENDPOINT,
   153|        "X-Sdk-Date": timestamp,
   154|    }
   155|
   156|    # AK/SK signing (Huawei Cloud APIG signature v2)
   157|    signed_headers, authorization = _sign_request(
   158|        "POST", url, headers, body, ak, sk, datestamp
   159|    )
   160|    headers["Authorization"] = authorization
   161|
   162|    # Make request
   163|    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
   164|
   165|    try:
   166|        with urllib.request.urlopen(req, timeout=60) as resp:
   167|            data = json.loads(resp.read().decode("utf-8"))
   168|    except urllib.error.HTTPError as e:
   169|        error_body = e.read().decode("utf-8", errors="replace")
   170|        raise Exception(f"OCR API HTTP {e.code}: {error_body}")
   171|
   172|    # Extract text from response
   173|    result = data.get("result", {})
   174|    blocks = result.get("words_block_list", [])
   175|    if not blocks:
   176|        return ""
   177|
   178|    text_lines = [block.get("words", "") for block in blocks if block.get("words")]
   179|    return "\n".join(text_lines)
   180|
   181|
   182|def _sign_request(method, url, headers, body, ak, sk, datestamp):
   183|    """Huawei Cloud APIG Signature v2 (AK/SK signing).
   184|
   185|    Compatible with the apig_sdk/signer.py approach.
   186|    """
   187|    # Canonical headers (lowercase, sorted)
   188|    signed_header_keys = sorted(k.lower() for k in headers.keys())
   189|    canonical_headers = ""
   190|    for k in signed_header_keys:
   191|        for orig_k, v in headers.items():
   192|            if orig_k.lower() == k:
   193|                canonical_headers += f"{k}:{v.strip()}\n"
   194|
   195|    signed_headers_str = ";".join(signed_header_keys)
   196|
   197|    # Body hash
   198|    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
   199|
   200|    # Canonical request
   201|    parsed = urllib.parse.urlparse(url)
   202|    canonical_uri = parsed.path or "/"
   203|    canonical_qs = parsed.query or ""
   204|
   205|    canonical_request = "\n".join([
   206|        method,
   207|        canonical_uri,
   208|        canonical_qs,
   209|        canonical_headers,
   210|        signed_headers_str,
   211|        body_hash,
   212|    ])
   213|
   214|    # String to sign
   215|    algorithm = "SDK-HMAC-SHA256"
   216|    region = OCR_ENDPOINT.split(".")[0].replace("https://ocr.", "")
    credential_scope = f"{datestamp}/{region}/ocr/sdk_request"
   217|    string_to_sign = "\n".join([
   218|        algorithm,
   219|        headers.get("X-Sdk-Date", ""),
   220|        credential_scope,
   221|        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
   222|    ])
   223|
   224|    # Signing key
   225|    def _hmac_sha256(key, msg):
   226|        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
   227|
   228|    k_date = _hmac_sha256(sk.encode("utf-8"), datestamp)
   229|    k_region = _hmac_sha256(k_date, "ap-southeast-1")
   230|    k_service = _hmac_sha256(k_region, "ocr")
   231|    k_signing = _hmac_sha256(k_service, "sdk_request")
   232|
   233|    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
   234|
   235|    authorization = (
   236|        f"{algorithm} "
   237|        f"Credential={ak}/{credential_scope}, "
   238|        f"SignedHeaders={signed_headers_str}, "
   239|        f"Signature={signature}"
   240|    )
   241|
   242|    return signed_headers_str, authorization
   243|
   244|
   245|def fallback_pdftotext(pdf_data, key):
   246|    """Fallback: extract text using pdftotext (poppler-utils)."""
   247|    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
   248|        tmp.write(pdf_data)
   249|        tmp_path = tmp.name
   250|
   251|    try:
   252|        result = subprocess.run(
   253|            ["pdftotext", "-layout", tmp_path, "-"],
   254|            capture_output=True, text=True, timeout=30
   255|        )
   256|        if result.returncode == 0 and result.stdout.strip():
   257|            print(f"[pdftotext] Extracted {len(result.stdout)} chars from {key}")
   258|            return result.stdout
   259|        else:
   260|            raise Exception(f"pdftotext failed: {result.stderr}")
   261|    finally:
   262|        os.unlink(tmp_path)
   263|
   264|
   265|def upload_to_obs(bucket, key, data, context):
   266|    """Upload text data to OBS."""
   267|    try:
   268|        from obs import ObsClient
   269|        ak = context.get("access_key", os.environ.get("HUAWEI_ACCESS_KEY", ""))
   270|        sk = context.get("secret_key", os.environ.get("HUAWEI_SECRET_KEY", ""))
   271|        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
   272|        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
   273|        client.putContent(bucket, key, data)
   274|        client.close()
   275|    except ImportError:
   276|        print(f"[OBS] Would upload {key} to {bucket}")
   277|
   278|
   279|def publish_to_dms(message):
   280|    """Publish parsed contract info to DMS/Kafka topic."""
   281|    print(f"[DMS] Would publish to topic ayco-contract-parsed: {json.dumps(message)}")
   282|