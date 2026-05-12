#!/usr/bin/env python3
"""Test FunctionGraph invoke with AK/SK signing."""
import hmac
import hashlib
import json
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError
import os

# Config
AK = os.environ.get("HUAWEI_ACCESS_KEY", "")  # ¡SEGURIDAD! Forzar desde env var — sin fallback
SK = os.environ.get("HUAWEI_SECRET_KEY", "")  # ¡SEGURIDAD! Forzar desde env var — sin fallback
FGS_PROJECT_ID = "fbb6435c497c41bda90a0cc5240573e0"
FGS_FUNCTION_NAME = "ayco-ocr-trigger"
FGS_PUBLIC_URL = "https://functiongraph.la-north-2.myhuaweicloud.com"

def build_auth_header(method, uri, body, ak, sk):
    """Build Huawei Cloud AK/SK authentication header."""
    now = datetime.utcnow()
    date = now.strftime("%Y%m%d")
    datetime_header = now.strftime("%Y%m%dT%H%M%SZ")
    
    body_hash = hashlib.sha256(body.encode()).hexdigest()
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
    
    authorization = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return authorization, datetime_header, canonical_request, string_to_sign, signature

# Test payload
event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "ayco-contracts-raw"},
            "object": {"key": "test-contract.pdf"}
        }
    }]
}

uri = f"/v2/{FGS_PROJECT_ID}/fgs/functions/{FGS_FUNCTION_NAME}/invocations"
invoke_url = f"{FGS_PUBLIC_URL}{uri}"
body = json.dumps({"action": "invoke", "payload": json.dumps(event)})

print("=" * 60)
print("FUNCTIONGRAPH INVOKE TEST")
print("=" * 60)
print(f"AK: {AK}")
print(f"SK: {SK[:20]}...")
print(f"URL: {invoke_url}")
print(f"Body: {body[:100]}...")
print()

auth_header, datetime_header, canonical_request, string_to_sign, signature = build_auth_header(
    "POST", uri, body, AK, SK
)

print("Canonical Request:")
print(canonical_request)
print()
print("String to Sign:")
print(string_to_sign)
print()
print(f"Signature: {signature}")
print()
print("Authorization Header (first 200 chars):")
print(f"{auth_header[:200]}...")
print()

req = Request(invoke_url)
req.add_header("Content-Type", "application/json")
req.add_header("X-Sdk-Date", datetime_header)
req.add_header("Authorization", auth_header)

try:
    with urlopen(req, data=body.encode(), timeout=15) as resp:
        result = json.loads(resp.read().decode())
        print(f"✅ SUCCESS: {result}")
except HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.reason}")
    print(f"Headers: {dict(e.headers)}")
    print(f"Body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"❌ ERROR: {e}")
