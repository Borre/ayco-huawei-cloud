# ─── DataArts Architecture: Project Directory ────────────────────────────
resource "huaweicloud_dataarts_architecture_directory" "ayco" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  name         = "AYCO_Contract_Risk"
  type         = "STANDARD_ELEMENT"
  description  = "Directorio raíz del proyecto AYCO — análisis de riesgo contractual"
}

# ─── DataArts Catalog: Metadata Collection & Lineage ─────────────────────
resource "huaweicloud_dataarts_catalog_metadata_task" "contract_risk" {
  count            = var.dataarts_enabled ? 1 : 0
  workspace_id     = local.dataarts_workspace_id
  name             = "ayco-contract-metadata-collection"
  description      = "Metadata collection from DWS risk_results — enables data lineage visualization"
  data_source_type = "DWS"
  dir_id           = huaweicloud_dataarts_architecture_directory.ayco[0].id

  task_config = jsonencode({
    connection_id = huaweicloud_dataarts_studio_data_connection.dws[0].id
    db_type       = "DWS"
    database_name = var.dws_database
    table_configs = [
      {
        table_name = "risk_results"
        table_type = "TABLE"
      }
    ]
  })

  schedule_config {
    schedule_type = "ONCE"
  }
}

# Run the metadata task immediately to populate lineage
resource "huaweicloud_dataarts_catalog_metadata_task_action" "run_collection" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  task_id      = huaweicloud_dataarts_catalog_metadata_task.contract_risk[0].id
  action       = "RUN"
}

# ─── DataArts Architecture: Subject Area ──────────────────────────────────
resource "huaweicloud_dataarts_architecture_subject" "contract_risk" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  name         = "Gestión de Riesgo Contractual"
  code         = "AYCO_CONTRACT_RISK"
  level        = 1
  owner        = "ayco_admin"
  department   = "Riesgos"
  description  = "Subject area para análisis de riesgo de contratos de proveedores — AYCO Grupo Salinas"
}

# ─── DataArts Architecture: Data Model ────────────────────────────────────
resource "huaweicloud_dataarts_architecture_model" "contract_risk_dws" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  name         = "AYCO Contract Risk Model"
  type         = "THIRD_NF"
  physical     = true
  description  = "Modelo físico 3NF para resultados de análisis de riesgo contractual en DWS"
}

# ─── DataArts Architecture: Table Model (maps to risk_results) ────────────
resource "huaweicloud_dataarts_architecture_table_model" "risk_results" {
  count               = var.dataarts_enabled ? 1 : 0
  workspace_id        = local.dataarts_workspace_id
  model_id            = huaweicloud_dataarts_architecture_model.contract_risk_dws[0].id
  subject_id          = huaweicloud_dataarts_architecture_subject.contract_risk[0].id
  table_name          = "risk_results"
  physical_table_name = "public.risk_results"
  dw_type             = "DWS"
  description         = "Resultados de análisis de riesgo contractual con scoring LLM — DWS"

  # Key columns that demonstrate data governance
  attributes {
    name      = "contract_number"
    name_en   = "contract_number"
    data_type = "VARCHAR"
  }
  attributes {
    name      = "vendor_name"
    name_en   = "vendor_name"
    data_type = "VARCHAR"
  }
  attributes {
    name      = "monto_total"
    name_en   = "monto_total"
    data_type = "DECIMAL"
  }
  attributes {
    name      = "risk_score"
    name_en   = "risk_score"
    data_type = "DECIMAL"
  }
  attributes {
    name      = "risk_level"
    name_en   = "risk_level"
    data_type = "VARCHAR"
  }
}

# ─── DataArts Security: Data Secrecy Level ────────────────────────────────
resource "huaweicloud_dataarts_security_data_secrecy_level" "contract_sensitive" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  name         = "Contract_Financial_Sensitive"
  description  = "Datos financieros sensibles de contratos — montos, penalizaciones, proveedores"
}

# ─── DataArts Security: Data Recognition Rule ─────────────────────────────
resource "huaweicloud_dataarts_security_data_recognition_rule" "financial_amounts" {
  count              = var.dataarts_enabled ? 1 : 0
  workspace_id       = local.dataarts_workspace_id
  name               = "Detect_Financial_Amounts"
  rule_type          = "REGEX"
  method             = "REGEX"
  secrecy_level_id   = huaweicloud_dataarts_security_data_secrecy_level.contract_sensitive[0].id
  description        = "Detecta montos financieros, penalizaciones y garantías en columnas de contratos"
  enable             = true
  content_expression = "^\\$?[\\d,]+(\\.[\\d]{2})?(\\s*(MXN|USD|EUR))?$"
}

# ─── DataArts Security: Dynamic Masking Policy ────────────────────────────
resource "huaweicloud_dataarts_security_dynamic_masking_policy" "vendor_masking" {
  count           = var.dataarts_enabled ? 1 : 0
  workspace_id    = local.dataarts_workspace_id
  name            = "Mask_Vendor_Names"
  datasource_type = "DWS"
  cluster_id      = huaweicloud_dws_cluster.ayco.id
  cluster_name    = huaweicloud_dws_cluster.ayco.name
  conn_id         = huaweicloud_dataarts_studio_data_connection.dws[0].id
  conn_name       = huaweicloud_dataarts_studio_data_connection.dws[0].name
  database_name   = var.dws_database
  table_name      = "risk_results"

  # Mask vendor_name column — shows first char + *** + last char
  policy_list {
    column_name = "vendor_name"
    column_type = "VARCHAR"
  }
  # Mask monto_total for unauthorized API consumers
  policy_list {
    column_name = "monto_total"
    column_type = "DECIMAL"
  }
}
