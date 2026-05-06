resource "huaweicloud_fgs_function" "ocr_trigger" {
  name = "ayco-ocr-trigger"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
  app         = "default"
  handler     = "index.handler"
  runtime     = "Python3.10"
  code_type   = "inline"
  func_code   = filebase64("${path.module}/functions/ocr_trigger.py")
  memory_size = 256
  timeout     = 30
  description = "Triggers OCR on contract PDF upload to OBS"

  user_data = jsonencode({
    OCR_ENDPOINT      = "ocr.ap-southeast-1.myhuaweicloud.com"
    OBS_ENDPOINT      = "obs.la-north-2.myhuaweicloud.com"
    OBS_BUCKET        = var.obs_contracts_raw
    OBS_TEXT_BUCKET   = var.obs_contracts_text
    HUAWEI_PROJECT_ID = var.project_id
  })
}

resource "huaweicloud_fgs_function" "parse_contract" {
  name = "ayco-parse-contract"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
  app         = "default"
  handler     = "index.handler"
  runtime     = "Python3.10"
  code_type   = "inline"
  func_code   = filebase64("${path.module}/functions/parse_contract.py")
  memory_size = 512
  timeout     = 60
  description = "Parses OCR text into structured contract data"

  user_data = jsonencode({
    OBS_ENDPOINT       = "obs.la-north-2.myhuaweicloud.com"
    OBS_TEXT_BUCKET    = var.obs_contracts_text
    OBS_RESULTS_BUCKET = var.obs_contracts_results
  })
}

resource "huaweicloud_fgs_function" "llm_inference" {
  name = "ayco-llm-inference"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
  app         = "default"
  handler     = "index.handler"
  runtime     = "Python3.10"
  code_type   = "inline"
  func_code   = filebase64("${path.module}/functions/llm_inference.py")
  memory_size = 1024
  timeout     = 120
  description = "DeepSeek inference for contract risk analysis"

  user_data = jsonencode({ for k, v in {
    MAAS_API_KEY        = var.maas_api_key
    MAAS_ENDPOINT       = var.maas_endpoint
    MAAS_MODEL          = var.maas_model
    DEEPSEEK_API_KEY    = var.deepseek_api_key
    DIFY_API_URL        = var.dify_api_url
    OBS_RESULTS_BUCKET  = var.obs_contracts_results
    LANGFUSE_PUBLIC_KEY = var.langfuse_public_key
    LANGFUSE_SECRET_KEY = var.langfuse_secret_key
    LANGFUSE_HOST       = var.langfuse_host
  } : k => v if v != "" })
}

# ─── Trigger: OBS upload → OCR pipeline ──────────────────────
resource "huaweicloud_fgs_trigger" "obs_upload" {
  function_urn = huaweicloud_fgs_function.ocr_trigger.urn
  type         = "OBS"
  obs {
    bucket_name             = var.obs_contracts_raw
    event_notification_name = "ayco-ocr-trigger-notification"
    events                  = ["ObjectCreated"]
    suffix                  = ".pdf"
  }

  lifecycle {
    ignore_changes = [
      obs[0].event_notification_name,  # API returns auto-generated UUID, not user-provided name
    ]
  }
}
