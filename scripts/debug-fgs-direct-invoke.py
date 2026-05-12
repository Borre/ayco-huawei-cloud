#!/usr/bin/env python3
"""Direct FunctionGraph invoke with debug payload."""
import os
import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkfunctiongraph.v2.region.functiongraph_region import FunctionGraphRegion
from huaweicloudsdkfunctiongraph.v2 import FunctionGraphClient
from huaweicloudsdkfunctiongraph.v2.model.invoke_function_request import InvokeFunctionRequest

AK = os.environ.get("HUAWEI_ACCESS_KEY", "")  # ¡SEGURIDAD! Forzar desde env var — sin fallback
SK = os.environ.get("HUAWEI_SECRET_KEY")
PROJECT_ID = "fbb6435c497c41bda90a0cc5240573e0"
FUNCTION_NAME = "ayco-ocr-trigger"

print("=" * 70)
print("DIRECT FUNCTION INVOKE (DEBUG MODE)")
print("=" * 70)

creds = BasicCredentials(ak=AK, sk=SK)
client = FunctionGraphClient.new_builder().with_credentials(creds).with_region(FunctionGraphRegion.value_of("la-north-2")).build()

# Test event with debug flag
event = {
    "_debug": True,
    "Records": [{
        "s3": {
            "bucket": {"name": "ayco-contracts-raw"},
            "object": {"key": "test-debug.pdf"}
        }
    }]
}

req = InvokeFunctionRequest()
req.function_urn = f"urn:fss:la-north-2:{PROJECT_ID}:function:default:{FUNCTION_NAME}:latest"
req.body = {"action": "invoke", "payload": json.dumps(event)}

print(f"Invoking {FUNCTION_NAME} with debug payload...")
print(f"Event: {json.dumps(event)}")
print()

try:
    resp = client.invoke_function(req)
    print(f"✅ Invocation successful!")
    print(f"   Status Code: {getattr(resp, 'status_code', 'N/A')}")
    print(f"   Request ID: {getattr(resp, 'x_request_id', 'N/A')}")
    
    # Try to get response body
    if hasattr(resp, 'body') and resp.body:
        print(f"   Response: {resp.body[:500]}")
    elif hasattr(resp, 'result') and resp.result:
        print(f"   Result: {resp.result[:500]}")
        
except Exception as e:
    print(f"❌ Invocation failed: {e}")
    import traceback
    traceback.print_exc()
