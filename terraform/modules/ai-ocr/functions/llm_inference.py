"""ayco-llm-inference: Risk analysis for contracts.

Default: Huawei Cloud MaaS (DeepSeek v4 Flash)
Fallback: DeepSeek API direct
Observability: Langfuse tracing (REST API, no SDK deps)

Trigger: Invoked by parse_contract function or API call
Output:  Risk assessment JSON saved to OBS + indexed in Dify
"""

import json
import os
import time
import uuid
import urllib.request

# ─── LLM Configuration ──────────────────────────────────
MAAS_ENDPOINT = "https://api-ap-southeast-1.modelarts-maas.com/v2/chat/completions"
MAAS_MODEL = "deepseek-v4-pro"

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

SYSTEM_PROMPT = """Eres un analista de riesgo financiero especializado en contratos corporativos mexicanos.

Analiza el contrato proporcionado y genera un reporte de riesgo con:

1. RISK_SCORE: Número del 1-10 (10 = máximo riesgo)
2. RISK_LEVEL: Bajo | Medio | Alto | Crítico
3. ALERTAS: Lista de banderas rojas encontradas
4. RECOMENDACIONES: Acciones sugeridas
5. RESUMEN: Resumen ejecutivo en 3 oraciones

Factores de riesgo a evaluar:
- Penalizaciones por terminación anticipada (15% es alto)
- Montos superiores a $2M MXN requieren aprobación adicional
- Jurisdicción fuera de CDMX es riesgo adicional
- Sin garantía de cumplimiento = riesgo alto
- Periodos de confidencialidad > 5 años = riesgo medio

Responde SOLO en JSON válido."""


def handler(event, context):
    """FunctionGraph entry point. Handles message arrays from parse chain."""
    try:
        messages = event.get("messages", [])
        if messages:
            contract_data = messages[0].get("contract_data", messages[0])
        else:
            contract_data = event.get("contract_data", event)

        user_msg = f"""Contrato a analizar:
- Número: {contract_data.get('contract_number', 'N/A')}
- Contratista: {contract_data.get('contratista', 'N/A')}
- Monto: ${contract_data.get('monto_total', 'N/A')} MXN
- Vigencia: {contract_data.get('vigencia_inicio', 'N/A')} al {contract_data.get('vigencia_fin', 'N/A')}
- Penalización anticipada: {contract_data.get('penalizacion_anticipada', 'N/A')}
- Penalización retraso: {contract_data.get('penalizacion_retraso', 'N/A')}
- Garantía: {contract_data.get('garantia', 'N/A')}
- Jurisdicción: {contract_data.get('jurisdiccion', 'N/A')}
- Confidencialidad: {contract_data.get('confidencialidad', 'N/A')}"""

        # Try MaaS first, fallback to DeepSeek direct
        analysis, provider, usage = call_llm(user_msg, context)

        try:
            risk_report = json.loads(analysis)
        except json.JSONDecodeError:
            # Try to repair truncated/malformed JSON from LLM
            risk_report = _repair_json(analysis)
            if risk_report is None:
                risk_report = {
                    "raw_analysis": analysis[:200],
                    "risk_level": "Indeterminado",
                    "risk_score": 0,
                    "alertas": ["LLM response truncated or invalid"],
                    "parse_error": True,
                }

        risk_report["source_contract"] = contract_data.get("source_key", "unknown")
        risk_report["contract_number"] = contract_data.get("contract_number")
        risk_report["llm_provider"] = provider
        risk_report["usage"] = usage

        # Save to OBS
        result_key = f"risk_{contract_data.get('contract_number', 'unknown')}.json"
        upload_to_obs(
            os.environ.get("OBS_RESULTS_BUCKET", "ayco-contracts-results"),
            result_key,
            json.dumps(risk_report, ensure_ascii=False, indent=2),
            context,
        )

        # Index in Dify
        index_in_dify(risk_report, context)

        return {"statusCode": 200, "body": json.dumps(risk_report, ensure_ascii=False)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def call_llm(user_message, context):
    """Call LLM with MaaS primary, DeepSeek fallback. Traces via Langfuse."""

    # ─── Try MaaS (Huawei Cloud) first ───────────────────
    maas_key = os.environ.get("MAAS_API_KEY", _context_get(context, "maas_api_key", ""))
    if maas_key:
        try:
            t0 = time.time()
            result = _call_maaS(maas_key, user_message)
            latency_ms = int((time.time() - t0) * 1000)
            provider = "maas-deepseek-v4-pro"
            usage = trace_llm_call(
                provider=provider,
                model=os.environ.get("MAAS_MODEL", MAAS_MODEL),
                user_message=user_message,
                response=result,
                latency_ms=latency_ms,
                contract_number=user_message.split("Número: ")[1].split("\n")[0] if "Número: " in user_message else "unknown",
            )
            return result, provider, usage
        except Exception as e:
            print(f"[MaaS] Failed: {e}, falling back to DeepSeek direct")

    # ─── Fallback: DeepSeek API direct ───────────────────
    ds_key = os.environ.get("DEEPSEEK_API_KEY", _context_get(context, "deepseek_api_key", ""))
    if ds_key:
        try:
            t0 = time.time()
            result = _call_deepseek(ds_key, user_message)
            latency_ms = int((time.time() - t0) * 1000)
            provider = "deepseek-direct"
            usage = trace_llm_call(
                provider=provider,
                model=os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_MODEL),
                user_message=user_message,
                response=result,
                latency_ms=latency_ms,
                contract_number=user_message.split("Número: ")[1].split("\n")[0] if "Número: " in user_message else "unknown",
            )
            return result, provider, usage
        except Exception as e:
            print(f"[DeepSeek] Failed: {e}")

    return json.dumps({"error": "No LLM available", "risk_level": "Indeterminado"}), "none", {}


def trace_llm_call(provider, model, user_message, response, latency_ms, contract_number):
    """Send trace to Langfuse via REST API (no SDK needed — FunctionGraph compatible)."""
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "https://us.cloud.langfuse.com")

    if not public_key or not secret_key:
        print("[Langfuse] Keys not configured — skipping trace")
        return {}

    trace_id = str(uuid.uuid4())
    generation_id = str(uuid.uuid4())
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    # Estimate token count (rough: ~4 chars per token)
    prompt_tokens = len(SYSTEM_PROMPT) // 4 + len(user_message) // 4
    completion_tokens = len(response) // 4
    usage_info = {
        "promptTokens": prompt_tokens,
        "completionTokens": completion_tokens,
        "totalTokens": prompt_tokens + completion_tokens,
    }

    batch = {
        "batch": [
            {
                "id": trace_id,
                "type": "trace-create",
                "timestamp": timestamp,
                "body": {
                    "id": trace_id,
                    "name": "contract-risk-analysis",
                    "metadata": {
                        "provider": provider,
                        "model": model,
                        "contract": contract_number,
                        "latency_ms": latency_ms,
                    },
                },
            },
            {
                "id": generation_id,
                "type": "generation-create",
                "timestamp": timestamp,
                "body": {
                    "id": generation_id,
                    "traceId": trace_id,
                    "name": f"{provider}-{model}",
                    "model": model,
                    "startTime": timestamp,
                    "endTime": timestamp,
                    "input": user_message[:500],  # Truncate for cost/security
                    "output": response[:500],
                    "usage": usage_info,
                    "metadata": {
                        "environment": "ayco-demo",
                        "region": "la-north-2",
                        "latency_ms": latency_ms,
                    },
                },
            },
        ]
    }

    try:
        import base64

        auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        payload = json.dumps(batch).encode("utf-8")
        req = urllib.request.Request(
            f"{host}/api/public/ingestion",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {auth}",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                print(f"[Langfuse] ✓ Trace {trace_id} sent ({latency_ms}ms)")
                return usage_info
            else:
                print(f"[Langfuse] ⚠ Ingestion returned {resp.status}")
    except Exception as e:
        print(f"[Langfuse] ⚠ Trace failed (non-blocking): {e}")

    return usage_info


def _call_maaS(api_key, user_message):
    """Call Huawei Cloud MaaS (DeepSeek v4 Flash)."""
    payload = json.dumps({
        "model": os.environ.get("MAAS_MODEL", MAAS_MODEL),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        os.environ.get("MAAS_ENDPOINT", MAAS_ENDPOINT),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def _call_deepseek(api_key, user_message):
    """Call DeepSeek API direct (fallback)."""
    payload = json.dumps({
        "model": os.environ.get("DEEPSEEK_MODEL", DEEPSEEK_MODEL),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def upload_to_obs(bucket, key, data, context):
    """Upload to OBS."""
    try:
        from obs import ObsClient
        ak, sk = _credentials(context)
        endpoint = os.environ.get("OBS_ENDPOINT", "obs.la-north-2.myhuaweicloud.com")
        client = ObsClient(access_key_id=ak, secret_access_key=sk, server=f"https://{endpoint}")
        client.putContent(bucket, key, data)
        client.close()
    except ImportError:
        print(f"[OBS] Would upload {key} to {bucket}")


def index_in_dify(risk_report, context):
    """Index risk report in Dify Knowledge Base via API."""
    dify_url = os.environ.get("DIFY_API_URL", "")
    if not dify_url:
        print("[Dify] No DIFY_API_URL configured, skipping indexing")
        return
    print(f"[Dify] Would index risk report for contract {risk_report.get('contract_number')}")


def _context_get(context, key, default=""):
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default)


def _credentials(context):
    """Get AK/SK — prefers temporary credentials via IAM agency, falls back to env vars."""
    try:
        ak = context.getSecurityAccessKey()
        sk = context.getSecuritySecretKey()
        if ak and sk:
            return (ak, sk)
    except (AttributeError, Exception):
        pass
    return (
        os.environ.get("HUAWEI_ACCESS_KEY", ""),
        os.environ.get("HUAWEI_SECRET_KEY", ""),
    )


def _repair_json(text: str) -> dict | None:
    """Attempt to extract valid JSON from truncated or malformed LLM output.

    Strategies (cheap, no dependencies):
    1. Find first '{' and last '}', try parsing the slice
    2. Close unclosed braces/brackets/quotes
    3. Strip trailing commas before '}' or ']'
    4. Wrap bare values in a minimal dict
    """
    # Strategy 1: extract the outermost JSON blob
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last <= first:
        return None
    candidate = text[first : last + 1]

    # Strategy 3: remove trailing commas (common LLM truncation issue)
    candidate = _remove_trailing_commas(candidate)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Strategy 2: close unclosed structures
    repaired = _close_unclosed(candidate)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Last resort: try each nested block individually
    try:
        # Maybe the LLM returned markdown-wrapped JSON
        import re
        code_blocks = re.findall(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
        for block in code_blocks:
            block = _remove_trailing_commas(block.strip())
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue
    except Exception:
        pass

    return None


def _remove_trailing_commas(s: str) -> str:
    """Remove trailing commas before } or ] in a JSON string."""
    import re
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s


def _close_unclosed(s: str) -> str:
    """Close any unclosed braces, brackets, or quotes."""
    in_string = False
    escape_next = False
    brace_count = 0
    bracket_count = 0
    for ch in s:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
        if not in_string:
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
            elif ch == "[":
                bracket_count += 1
            elif ch == "]":
                bracket_count -= 1

    result = s
    # Close unclosed strings
    if in_string:
        result += '"'
    # Close unclosed brackets then braces
    result += "]" * max(0, bracket_count)
    result += "}" * max(0, brace_count)
    return result
