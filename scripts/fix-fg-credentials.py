#!/usr/bin/env python3
"""Update FunctionGraph functions with OBS credentials from ayco-api service env.

Reads HUAWEI_ACCESS_KEY, HUAWEI_SECRET_KEY, and other env vars from the
running ayco-api systemd service, then updates user_data for the 3 pipeline
functions: ocr-trigger, parse-contract, llm-inference.

Usage:
  python3 scripts/fix-fg-credentials.py [--dry-run]

Requires: huaweicloudsdkcore, huaweicloudsdkfunctiongraph
"""
import json
import os
import sys
import subprocess

FUNCTIONS = [
    "ayco-ocr-trigger",
    "ayco-parse-contract",
    "ayco-llm-inference",
]

OBS_VARS = {
    "OBS_ENDPOINT": "obs.la-north-2.myhuaweicloud.com",
    "OBS_TEXT_BUCKET": "ayco-contracts-text",
    "OBS_RESULTS_BUCKET": "ayco-contracts-results",
}

REGION = "la-north-2"


def get_service_env():
    """Read env vars from the running ayco-api service process."""
    # Find the PID of the main python process
    result = subprocess.run(
        ["systemctl", "show", "ayco-api", "--property=MainPID", "--value"],
        capture_output=True, text=True
    )
    pid = result.stdout.strip()
    if pid == "0" or not pid:
        print("ERROR: ayco-api service not running")
        sys.exit(1)

    env_path = f"/proc/{pid}/environ"
    if not os.path.exists(env_path):
        print(f"ERROR: Cannot read {env_path}")
        sys.exit(1)

    env = {}
    with open(env_path, "rb") as f:
        raw = f.read()
    for item in raw.split(b"\x00"):
        if b"=" in item:
            k, v = item.split(b"=", 1)
            env[k.decode()] = v.decode()
    return env


def main():
    dry_run = "--dry-run" in sys.argv

    env = get_service_env()

    ak = env.get("HUAWEI_ACCESS_KEY", "")
    sk = env.get("HUAWEI_SECRET_KEY", "")
    project_id = env.get("FGS_PROJECT_ID", env.get("HUAWEI_PROJECT_ID", ""))

    if not ak or not sk:
        print("ERROR: HUAWEI_ACCESS_KEY or HUAWEI_SECRET_KEY not in service env")
        sys.exit(1)

    print(f"AK prefix: {ak[:8]}...")
    print(f"Project: {project_id[:12]}...")
    print(f"Functions: {', '.join(FUNCTIONS)}")

    if dry_run:
        print("DRY RUN — no changes made")
        return

    from huaweicloudsdkcore.auth.credentials import BasicCredentials
    from huaweicloudsdkfunctiongraph.v2.region.functiongraph_region import FunctionGraphRegion
    from huaweicloudsdkfunctiongraph.v2 import FunctionGraphClient
    from huaweicloudsdkfunctiongraph.v2.model.show_function_config_request import ShowFunctionConfigRequest
    from huaweicloudsdkfunctiongraph.v2.model.update_function_config_request import UpdateFunctionConfigRequest
    from huaweicloudsdkfunctiongraph.v2.model.update_function_config_request_body import UpdateFunctionConfigRequestBody

    creds = BasicCredentials(ak, sk, project_id)
    client = (
        FunctionGraphClient.new_builder()
        .with_region(FunctionGraphRegion.value_of(REGION))
        .with_credentials(creds)
        .build()
    )

    # Build env vars for user_data
    fg_env = {
        "HUAWEI_ACCESS_KEY": ak,
        "HUAWEI_SECRET_KEY": sk,
        "HUAWEI_PROJECT_ID": project_id,
        "HUAWEI_REGION": REGION,
        **OBS_VARS,
    }
    # Preserve additional vars from service env if present
    for key in ["MAAS_API_KEY", "OCR_ENDPOINT", "LANGFUSE_PUBLIC_KEY",
                 "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"]:
        if key in env:
            fg_env[key] = env[key]

    user_data_str = json.dumps(fg_env)

    for func_name in FUNCTIONS:
        urn = f"urn:fss:{REGION}:{project_id}:function:default:{func_name}"
        try:
            # Read current config to preserve handler
            show_req = ShowFunctionConfigRequest()
            show_req.function_urn = urn
            current = client.show_function_config(show_req)
            handler = current.handler
            print(f"  {func_name}: handler={handler}")

            # Update with preserved handler + new user_data
            body = UpdateFunctionConfigRequestBody()
            body.handler = handler
            body.user_data = user_data_str

            update_req = UpdateFunctionConfigRequest()
            update_req.function_urn = urn
            update_req.body = body

            client.update_function_config(update_req)
            print(f"  ✓ {func_name}: updated")
        except Exception as e:
            print(f"  ✗ {func_name}: {type(e).__name__}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
