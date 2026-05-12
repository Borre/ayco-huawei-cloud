#!/usr/bin/env python3
"""List FunctionGraph executions via correct REST API."""
import os
import json
import hmac
import hashlib
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote

AK = os.environ.get("HUAWEI_ACCESS_KEY", "")  # ¡SEGURIDAD! Forzar desde env var — sin fallback
SK = os.environ.get("HUAWEI_SECRET_KEY")
PROJECT_ID = "fbb6435c497c41bda90a0cc5240573e0"
FUNCTION_NAME = "ayco-ocr-trigger"

print(f"Testing with AK={AK[:10]}... SK={SK[:10] if SK else 'NONE'}...")
print()

def build_aksk_auth(method, uri, body, ak, sk):
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y%m%d")
    datetime_header = now.strftime("%Y%m%dT%H%M%SZ")
    
    body_hash = hashlib.sha256(body.encode()).hexdigest() if body else hashlib.sha256(b"").hexdigest()
    canonical_uri = quote(uri, safe="/")
    canonical_headers = f"host:functiongraph.la-north-2.myhuaweicloud.com\nx-sdk-date:{datetime_header}\n"
    signed_headers = "host;x-sdk-date"
    
    canonical_request = f"{method}\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{body_hash}"
    credential_scope = f"{date}/la-north-2/functiongraph/sdk4_request"
    algorithm = "SDK4-HMAC-SHA256"
    string_to_sign = f"{algorithm}\n{datetime_header}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    
    k_date = hmac.new(f"SDK4{sk}".encode(), date.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, "la-north-2".encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, "functiongraph".encode(), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, "sdk4_request".encode(), hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()
    
    return f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}", datetime_header

# Try different endpoint patterns
endpoints = [
    f"/v2/{PROJECT_ID}/fgs/functions/{FUNCTION_NAME}/execution-record",
    f"/v2/{PROJECT_ID}/functions/{FUNCTION_NAME}/execution-record",
    f"/v2/{PROJECT_ID}/fgs/functions/{FUNCTION_NAME}/invocations",
]

for i, endpoint in enumerate(endpoints, 1):
    print(f"{i}. Trying: {endpoint}")
    url = f"https://functiongraph.la-north-2.myhuaweicloud.com{endpoint}"
    
    # For listing, we need GET with query params
    uri_with_params = f"{endpoint}?limit=10"
    auth, datetime_header = build_aksk_auth("GET", uri_with_params, "", AK, SK)
    
    req = Request(url + "?limit=10")
    req.add_header("X-Sdk-Date", datetime_header)
    req.add_header("Authorization", auth)
    
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            print(f"   ✅ SUCCESS ({resp.status})")
            executions = data.get("items", data.get("executions", []))
            print(f"   Found {len(executions)} executions")
            if executions:
                exec_0 = executions[0]
                print(f"   Latest: status={exec_0.get('status')}, started={exec_0.get('started_at')}")
                if exec_0.get('error_message'):
                    print(f"   Error: {exec_0['error_message']}")
            break
    except HTTPError as e:
        error_body = e.read().decode()[:200]
        print(f"   ❌ HTTP {e.code}: {error_body}")
    except Exception as e:
        print(f"   ❌ {e}")
    print()
