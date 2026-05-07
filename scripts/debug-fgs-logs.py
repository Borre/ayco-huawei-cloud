#!/usr/bin/env python3
"""Debug FunctionGraph executions and logs."""
import os
import json
from datetime import datetime, timedelta

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkfunctiongraph.v2.region.functiongraph_region import FunctionGraphRegion
from huaweicloudsdkfunctiongraph.v2 import FunctionGraphClient
from huaweicloudsdkfunctiongraph.v2.model.list_function_executions_request import ListFunctionExecutionsRequest

# Config
AK = os.environ.get("HUAWEI_ACCESS_KEY", "4DXDDBDYHYP5FLEHREH2")
SK = os.environ.get("HUAWEI_SECRET_KEY")
FGS_FUNCTION_NAME = "ayco-ocr-trigger"

print("=" * 70)
print("FUNCTIONGRAPH EXECUTION LOGS")
print("=" * 70)
print(f"AK: {AK}")
print(f"SK: {SK[:20] if SK else 'NOT SET'}...")
print()

creds = BasicCredentials(ak=AK, sk=SK)
client = FunctionGraphClient.new_builder().with_credentials(creds).with_region(FunctionGraphRegion.value_of("la-north-2")).build()

req = ListFunctionExecutionsRequest()
req.function_urn = f"urn:fss:la-north-2:fbb6435c497c41bda90a0cc5240573e0:function:default:{FGS_FUNCTION_NAME}:latest"
req.limit = 10

try:
    resp = client.list_function_executions(req)
    print(f"✅ Found {len(resp.executions or [])} recent executions:\n")
    
    for exec_item in (resp.executions or [])[:10]:
        started = exec_item.started_at
        if started:
            # Parse the timestamp
            try:
                if '.' in started:
                    started_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    started_str = started_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                else:
                    started_str = started
            except:
                started_str = started
        else:
            started_str = 'N/A'
            
        print(f"📋 Execution:")
        print(f"   Request ID: {exec_item.request_id}")
        print(f"   Started: {started_str}")
        print(f"   Status: {exec_item.status}")
        print(f"   Duration: {exec_item.exec_time}ms")
        print(f"   Memory: {exec_item.memory_usage}MB / {exec_item.memory_limit}MB")
        if hasattr(exec_item, 'error_message') and exec_item.error_message:
            print(f"   ❌ ERROR: {exec_item.error_message}")
        print()
        
except Exception as e:
    print(f"❌ Error fetching executions: {e}")
    import traceback
    traceback.print_exc()
