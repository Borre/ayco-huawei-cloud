# ─── DLI Queue (serverless compute) ────────────────────────────────
# NOTE: Commented out — queue capacity sold out in la-north-2.
# Use the "default" DLI queue for Spark SQL jobs instead.
# resource "huaweicloud_dli_queue" "ayco" {
#   name       = "ayco_queue"
#   queue_type = "sql"
#   platform   = "x86_64"
#   cu_count   = 16
#
#   tags = {
#     project     = "ayco"
#     environment = "demo"
#     managed_by  = "terraform"
#   }
# }

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

# ─── DLI Tables ───────────────────────────────────────────────────
# Tables created manually via DLI SQL API (Terraform provider has
# "data_location is illegal" bug with huaweicloud_dli_table).
# Queue: "default" (serverless) since dedicated queue sold out in la-north-2.
#
# IMPORTANT: OBS data must be in json/ subdirectory (not root) to avoid
# DLI reading non-JSON files (CSV, Python scripts) as JSON.
#
# Created 2026-05-05 via Huawei Cloud SDK (DliClient.create_sql_job):
#
#   -- risk_results: LLM analysis output (20 records)
#   CREATE TABLE risk_results (
#     contract_number STRING, vendor_name STRING, monto_total DOUBLE,
#     plazo_dias INT, penalizacion_pct DOUBLE, garantia_pct DOUBLE,
#     risk_score INT, risk_level STRING,
#     alertas ARRAY<STRING>, recomendaciones ARRAY<STRING>,
#     resumen STRING, llm_provider STRING, analyzed_at STRING
#   ) USING json OPTIONS (path 'obs://ayco-contracts-results/json/');
#
#   -- contracts_raw: original contract text as JSON (23 records)
#   CREATE TABLE contracts_raw (
#     file_name STRING, contract_id STRING, content STRING, char_count INT
#   ) USING json OPTIONS (path 'obs://ayco-contracts-text/json/');
#
# Demo queries:
#   SELECT risk_level, COUNT(*), ROUND(AVG(risk_score),1)
#   FROM risk_results WHERE risk_level IS NOT NULL
#   GROUP BY risk_level ORDER BY AVG(risk_score) DESC;
#
#   SELECT contract_number, vendor_name, risk_score, risk_level
#   FROM risk_results WHERE risk_level IS NOT NULL
#   ORDER BY risk_score DESC LIMIT 5;

# ─── DLI Spark Job: disabled (provider crash on v1.91.0) ──────────
# resource "huaweicloud_dli_spark_job" "risk_aggregation" {
#   name       = "ayco-risk-aggregation"
#   queue_name = "default"
#   app_name   = "obs://${var.obs_contracts_results}/spark/risk_aggregation.py"
#   app_parameters = "--database ${huaweicloud_dli_database.ayco.name} --output obs://${var.obs_contracts_results}/aggregated/"
#   driver_cores    = 1
#   driver_memory   = "1g"
#   executor_cores  = 1
#   executor_memory = "1g"
#   executors       = 1
# }

# Upload Spark script to OBS (for future use)
resource "huaweicloud_obs_bucket_object" "spark_script" {
  bucket = var.obs_contracts_results
  key    = "spark/risk_aggregation.py"
  source = "${path.root}/../scripts/spark-risk-aggregation.py"
}
