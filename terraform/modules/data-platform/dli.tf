# ─── DLI Database (serverless Spark SQL) ───────────────────────────
resource "huaweicloud_dli_database" "ayco" {
  name = "ayco_contracts"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
  description = "AYCO contract risk analysis database (serverless Spark)"
}

# ─── DLI Table: parsed contracts (OBS-backed) ─────────────────────
resource "huaweicloud_dli_table" "contracts" {
  database_name = huaweicloud_dli_database.ayco.name
  name          = "contracts"
  description   = "Parsed contract data from OCR pipeline"
  data_location = "obs://${var.obs_contracts_text}/parsed/"
  data_format   = "json"

  columns {
    name = "contract_number"
    type = "string"
  }
  columns {
    name = "contratante"
    type = "string"
  }
  columns {
    name = "contratista"
    type = "string"
  }
  columns {
    name = "monto_total"
    type = "string"
  }
  columns {
    name = "moneda"
    type = "string"
  }
  columns {
    name = "vigencia_inicio"
    type = "string"
  }
  columns {
    name = "vigencia_fin"
    type = "string"
  }
  columns {
    name = "penalizacion_anticipada"
    type = "string"
  }
  columns {
    name = "penalizacion_retraso"
    type = "string"
  }
  columns {
    name = "garantia"
    type = "string"
  }
  columns {
    name = "jurisdiccion"
    type = "string"
  }
  columns {
    name = "confidencialidad"
    type = "string"
  }
  columns {
    name = "text_length"
    type = "int"
  }
}

# ─── DLI Table: risk analysis results (OBS-backed) ────────────────
resource "huaweicloud_dli_table" "risk_results" {
  database_name = huaweicloud_dli_database.ayco.name
  name          = "risk_results"
  description   = "LLM risk analysis results"
  data_location = "obs://${var.obs_contracts_results}/"
  data_format   = "json"

  columns {
    name = "contract_number"
    type = "string"
  }
  columns {
    name = "risk_score"
    type = "int"
  }
  columns {
    name = "risk_level"
    type = "string"
  }
  columns {
    name = "alertas"
    type = "string"
  }
  columns {
    name = "recomendaciones"
    type = "string"
  }
  columns {
    name = "resumen"
    type = "string"
  }
  columns {
    name = "llm_provider"
    type = "string"
  }
  columns {
    name = "vendor_name"
    type = "string"
  }
  columns {
    name = "monto_total"
    type = "double"
  }
  columns {
    name = "plazo_dias"
    type = "int"
  }
  columns {
    name = "penalizacion_pct"
    type = "double"
  }
  columns {
    name = "garantia_pct"
    type = "double"
  }
  columns {
    name = "source_contract"
    type = "string"
  }
}

# ─── DLI Spark Job: risk aggregation query ────────────────────────
resource "huaweicloud_dli_spark_job" "risk_aggregation" {
  name       = "ayco-risk-aggregation"
  queue_name = "default"
  app_name   = "obs://${var.obs_contracts_results}/spark/risk_aggregation.py"

  app_parameters = "--database ${huaweicloud_dli_database.ayco.name} --output obs://${var.obs_contracts_results}/aggregated/"

  driver_cores    = 1
  driver_memory   = "1g"
  executor_cores  = 1
  executor_memory = "1g"
  executors       = 1
}

# Upload Spark script to OBS (required by DLI Spark job)
resource "huaweicloud_obs_bucket_object" "spark_script" {
  bucket = var.obs_contracts_results
  key    = "spark/risk_aggregation.py"
  source = "${path.root}/../scripts/spark-risk-aggregation.py"
}
