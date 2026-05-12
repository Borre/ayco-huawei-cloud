#!/usr/bin/env python3
"""List FunctionGraph executions via REST API."""
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

print("=" * 70)
print("FUNCTIONGRAPH EXECUTIONS (REST API)")
print("=" * 70)

def build_aksk_auth(method, uri, body, ak, sk):
    """Huawei SDK4 signature."""
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
    
    auth = f"{algorithm} Credential={ak}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    return auth, datetime_header

# List executions
uri = f"/v2/{PROJECT_ID}/functiongraph/functions/{FUNCTION_NAME}/execution-record"
url = f"https://functiongraph.la-north-2.myhuaweicloud.com{uri}"
body = '{"max_records": 10}'

auth, datetime_header = build_aksk_auth("GET", uri, "", AK, SK)

req = Request(url)
req.add_header("Content-Type", "application/json")
req.add_header("X-Sdk-Date", datetime_header)
req.add_header("Authorization", auth)

try:
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        print(f"✅ SUCCESS: {resp.status}")
        print()
        
        executions = data.get("items", [])
        print(f"Found {len(executions)} executions:\n")
        
        for exec_item in executions[:10]:
            print(f"📋 Execution:")
            print(f"   Request ID: {exec_item.get('request_id', 'N/A')}")
            print(f"   Started: {exec_item.get('started_at', 'N/A')}")
            print(f"   Status: {exec_item.get('status', 'N/A')}")
            print(f"   Duration: {exec_item.get('exec_time', 'N/A')}ms")
            if exec_item.get('error_message'):
                print(f"   ❌ ERROR: {exec_item['error_message']}")
            if exec_item.get('log_location'):
                print(f"   📄 Logs: {exec_item['log_location']}")
            print()
            
except HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.reason}")
    print(f"Body: {e.read().decode()[:500]}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
