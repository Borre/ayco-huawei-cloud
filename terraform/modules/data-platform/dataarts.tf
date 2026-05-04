# ─── DataArts Studio Instance ──────────────────────────────────────
resource "huaweicloud_dataarts_studio_instance" "ayco" {
  count                 = var.dataarts_enabled ? 1 : 0
  name                  = "ayco-dataarts"
  version               = "dayu.nb.professional"
  availability_zone     = "la-north-2a"
  vpc_id                = var.vpc_id
  subnet_id             = var.subnet_id
  security_group_id     = var.security_group_id
  period_unit           = "month"
  period                = 1
  enterprise_project_id = var.project_id

  lifecycle {
    ignore_changes = [period_unit, period, auto_renew]
  }
}

# ─── Resolve Workspace ID from Instance ────────────────────────────
data "huaweicloud_dataarts_studio_workspaces" "ayco" {
  count       = var.dataarts_enabled ? 1 : 0
  instance_id = huaweicloud_dataarts_studio_instance.ayco[0].id
}

locals {
  dataarts_workspace_id = var.dataarts_enabled ? data.huaweicloud_dataarts_studio_workspaces.ayco[0].workspaces[0].id : ""
}

# ─── Data Connections ─────────────────────────────────────────────
resource "huaweicloud_dataarts_studio_data_connection" "dli" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  type         = "DLI"
  name         = "ayco-dli-conn"
  env_type     = 0

  config = jsonencode({
    "cdm_property_enable" = "false"
  })
}

resource "huaweicloud_dataarts_studio_data_connection" "dws" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  type         = "DWS"
  name         = "ayco-dws-conn"
  env_type     = 0
  agent_id     = huaweicloud_cdm_cluster.ayco[0].id

  config = jsonencode({
    "db_port"     = tostring(huaweicloud_dws_cluster.ayco.port)
    "db_name"     = var.dws_database
    "username"    = "ayco_admin"
    "password"    = var.dws_admin_password
    "instance_ip" = "auto"
  })
}



# ─── Factory Scripts ──────────────────────────────────────────────
resource "huaweicloud_dataarts_factory_script" "dli_parse_contracts" {
  count           = var.dataarts_enabled ? 1 : 0
  workspace_id    = local.dataarts_workspace_id
  name            = "ayco-parse-contracts"
  type            = "DLISQL"
  connection_name = huaweicloud_dataarts_studio_data_connection.dli[0].name
  database        = huaweicloud_dli_database.ayco.name
  queue_name      = "default"
  description     = "Parse raw contract text from OBS into structured records"
  directory       = "/ayco/etl"

  content = <<-SQL
    -- Parse contract text files from OBS into structured records
    INSERT OVERWRITE TABLE ${huaweicloud_dli_database.ayco.name}.${huaweicloud_dli_table.contracts.name}
    SELECT
      regexp_extract(content, 'CONTRATO[:\\s]+(\\S+)', 1)       AS contract_number,
      regexp_extract(content, 'PROVEEDOR[:\\s]+([^\\n]+)', 1)   AS vendor_name,
      regexp_extract(content, 'MONTO[:\\s]+\\$?([\\d,.]+)', 1)  AS monto_total,
      regexp_extract(content, 'PLAZO[:\\s]+(\\d+)', 1)          AS plazo_dias,
      regexp_extract(content, 'PENALIZACI[OÓ]N[:\\s]+(\\d+)%', 1) AS penalizacion_pct,
      regexp_extract(content, 'GARANT[ÍI]A[:\\s]+(\\d+)%', 1)  AS garantia_pct,
      content,
      current_timestamp()                                       AS ingestion_time
    FROM (
      SELECT content FROM obs_source_table
      WHERE file_name LIKE '%.txt'
    )
  SQL
}

resource "huaweicloud_dataarts_factory_script" "dws_load_results" {
  count           = var.dataarts_enabled ? 1 : 0
  workspace_id    = local.dataarts_workspace_id
  name            = "ayco-load-risk-results"
  type            = "DWSSQL"
  connection_name = huaweicloud_dataarts_studio_data_connection.dws[0].name
  database        = var.dws_database
  description     = "Load AI risk analysis results from DLI into DWS"
  directory       = "/ayco/etl"

  content = <<-SQL
    INSERT INTO risk_results
      (contract_number, vendor_name, monto_total, risk_score, risk_level,
       alertas, recomendaciones, resumen, analyzed_at)
    SELECT
      contract_number, vendor_name, monto_total, risk_score, risk_level,
      alertas, recomendaciones, resumen, current_timestamp
    FROM dli_external_contracts
    WHERE analyzed_at > COALESCE(
      (SELECT MAX(analyzed_at) FROM risk_results), '1970-01-01'
    )
    ON CONFLICT (contract_number) DO UPDATE SET
      risk_score      = EXCLUDED.risk_score,
      risk_level      = EXCLUDED.risk_level,
      alertas         = EXCLUDED.alertas,
      recomendaciones = EXCLUDED.recomendaciones,
      resumen         = EXCLUDED.resumen,
      analyzed_at     = EXCLUDED.analyzed_at
  SQL
}

resource "huaweicloud_dataarts_factory_script" "dws_quality_check" {
  count           = var.dataarts_enabled ? 1 : 0
  workspace_id    = local.dataarts_workspace_id
  name            = "ayco-data-quality-check"
  type            = "DWSSQL"
  connection_name = huaweicloud_dataarts_studio_data_connection.dws[0].name
  database        = var.dws_database
  description     = "Validate data quality on loaded contract results"
  directory       = "/ayco/quality"

  content = <<-SQL
    SELECT
      COUNT(*)                                          AS total_records,
      COUNT(CASE WHEN risk_score IS NULL THEN 1 END)   AS missing_risk_score,
      COUNT(CASE WHEN risk_level NOT IN ('BAJO','MEDIO','ALTO','CRITICO') THEN 1 END) AS invalid_risk_level,
      COUNT(CASE WHEN monto_total <= 0 THEN 1 END)     AS invalid_amounts,
      MIN(analyzed_at)                                  AS earliest_analysis,
      MAX(analyzed_at)                                  AS latest_analysis
    FROM risk_results
  SQL
}

# ─── Factory Job: Contract ETL Pipeline ────────────────────────────
resource "huaweicloud_dataarts_factory_job" "contract_etl" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  name         = "contract-risk-etl-pipeline"
  process_type = "BATCH"
  log_path     = "obs://${var.obs_contracts_results}/dataarts-logs/"
  directory    = "/ayco/etl"

  basic_config {
    priority         = 1
    owner            = "ayco_admin"
    instance_timeout = 120
  }

  # Node 1: Parse contracts from OBS via DLI SQL
  nodes {
    name               = "parse_contracts"
    type               = "DLISQL"
    fail_policy        = "END"
    retry_times        = 1
    retry_interval     = 5
    max_execution_time = 30

    location {
      x = 100
      y = 100
    }

    properties {
      name  = "scriptName"
      value = huaweicloud_dataarts_factory_script.dli_parse_contracts[0].name
    }
    properties {
      name  = "connectionName"
      value = huaweicloud_dataarts_studio_data_connection.dli[0].name
    }
    properties {
      name  = "queueName"
      value = "default"
    }
  }

  # Node 2: Load results into DWS
  nodes {
    name               = "load_to_dws"
    type               = "DWSSQL"
    pre_node_name      = ["parse_contracts"]
    fail_policy        = "END"
    retry_times        = 1
    retry_interval     = 5
    max_execution_time = 30

    location {
      x = 100
      y = 300
    }

    conditions {
      pre_node_name = "parse_contracts"
      expression    = "parse_contracts.status == 'SUCCESS'"
    }

    properties {
      name  = "scriptName"
      value = huaweicloud_dataarts_factory_script.dws_load_results[0].name
    }
    properties {
      name  = "connectionName"
      value = huaweicloud_dataarts_studio_data_connection.dws[0].name
    }
    properties {
      name  = "database"
      value = var.dws_database
    }
  }

  # Node 3: Data quality check
  nodes {
    name               = "quality_check"
    type               = "DWSSQL"
    pre_node_name      = ["load_to_dws"]
    fail_policy        = "CONTINUE"
    retry_times        = 0
    max_execution_time = 15

    location {
      x = 100
      y = 500
    }

    conditions {
      pre_node_name = "load_to_dws"
      expression    = "load_to_dws.status == 'SUCCESS'"
    }

    properties {
      name  = "scriptName"
      value = huaweicloud_dataarts_factory_script.dws_quality_check[0].name
    }
    properties {
      name  = "connectionName"
      value = huaweicloud_dataarts_studio_data_connection.dws[0].name
    }
    properties {
      name  = "database"
      value = var.dws_database
    }
  }

  # Schedule: daily at 2 AM CST
  schedule {
    type = "CRON"
    cron {
      start_time = "2026-05-05T02:00:00-06"
      expression = "0 0 2 * * *"
    }
  }
}

# ─── DataService: REST API on top of DWS ──────────────────────────
resource "huaweicloud_dataarts_dataservice_catalog" "contracts" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  dlm_type     = "SHARED"
  name         = "Contract Risk APIs"
  description  = "REST APIs para consultar resultados de analisis de riesgo contractual"
}

resource "huaweicloud_dataarts_dataservice_api" "risk_query" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  dlm_type     = "SHARED"
  type         = "API_SPECIFIC_TYPE_CONFIGURATION"
  catalog_id   = huaweicloud_dataarts_dataservice_catalog.contracts[0].id
  name         = "GetRiskResults"
  description  = "Consulta resultados de analisis de riesgo desde DWS"
  auth_type    = "NONE"
  manager      = "ayco_admin"
  path         = "/api/v1/risk-results"
  protocol     = "PROTOCOL_TYPE_HTTP"
  request_type = "REQUEST_TYPE_GET"
  visibility   = "WORKSPACE"

  request_params {
    name          = "risk_level"
    position      = "REQUEST_PARAMETER_POSITION_QUERY"
    type          = "REQUEST_PARAMETER_TYPE_STRING"
    description   = "Filtrar por nivel: BAJO, MEDIO, ALTO, CRITICO"
    necessary     = false
    default_value = "ALTO"
  }
  request_params {
    name        = "contract_number"
    position    = "REQUEST_PARAMETER_POSITION_QUERY"
    type        = "REQUEST_PARAMETER_TYPE_STRING"
    description = "Filtrar por numero de contrato"
    necessary   = false
  }
  request_params {
    name          = "limit"
    position      = "REQUEST_PARAMETER_POSITION_QUERY"
    type          = "REQUEST_PARAMETER_TYPE_NUMBER"
    description   = "Maximo de resultados"
    necessary     = false
    default_value = "50"
  }

  datasource_config {
    type            = "DWS"
    connection_name = huaweicloud_dataarts_studio_data_connection.dws[0].name
    database        = var.dws_database
    datatable       = "risk_results"
    access_mode     = "SQL"

    sql = <<-SQL
      SELECT contract_number, vendor_name, monto_total,
             risk_score, risk_level, alertas, recomendaciones,
             resumen, llm_provider, analyzed_at
      FROM risk_results
      WHERE 1=1
    SQL

    backend_params {
      name      = "contract_number"
      mapping   = "contract_number"
      condition = "CONDITION_TYPE_EQ"
    }
    backend_params {
      name      = "risk_level"
      mapping   = "risk_level"
      condition = "CONDITION_TYPE_EQ"
    }
    backend_params {
      name      = "limit"
      mapping   = "limit"
      condition = "CONDITION_TYPE_LIMIT"
    }

    response_params {
      name  = "contract_number"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "contract_number"
    }
    response_params {
      name  = "vendor_name"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "vendor_name"
    }
    response_params {
      name  = "monto_total"
      type  = "REQUEST_PARAMETER_TYPE_NUMBER"
      field = "monto_total"
    }
    response_params {
      name  = "risk_score"
      type  = "REQUEST_PARAMETER_TYPE_NUMBER"
      field = "risk_score"
    }
    response_params {
      name  = "risk_level"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "risk_level"
    }
    response_params {
      name  = "alertas"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "alertas"
    }
    response_params {
      name  = "recomendaciones"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "recomendaciones"
    }
    response_params {
      name  = "resumen"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "resumen"
    }

    order_params {
      name     = "risk_score"
      field    = "risk_score"
      optional = true
      sort     = "DESC"
      order    = 1
    }
  }
}

resource "huaweicloud_dataarts_dataservice_api" "contract_detail" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  dlm_type     = "SHARED"
  type         = "API_SPECIFIC_TYPE_CONFIGURATION"
  catalog_id   = huaweicloud_dataarts_dataservice_catalog.contracts[0].id
  name         = "GetContractDetail"
  description  = "Detalle completo de un contrato y su analisis de riesgo"
  auth_type    = "NONE"
  manager      = "ayco_admin"
  path         = "/api/v1/contracts/{contract_number}"
  protocol     = "PROTOCOL_TYPE_HTTP"
  request_type = "REQUEST_TYPE_GET"
  visibility   = "WORKSPACE"

  request_params {
    name        = "contract_number"
    position    = "REQUEST_PARAMETER_POSITION_PATH"
    type        = "REQUEST_PARAMETER_TYPE_STRING"
    description = "Numero de contrato"
    necessary   = true
  }

  datasource_config {
    type            = "DWS"
    connection_name = huaweicloud_dataarts_studio_data_connection.dws[0].name
    database        = var.dws_database
    datatable       = "risk_results"
    access_mode     = "SQL"

    sql = <<-SQL
      SELECT contract_number, vendor_name, monto_total, plazo_dias,
             penalizacion_pct, garantia_pct,
             risk_score, risk_level, alertas, recomendaciones,
             resumen, llm_provider, analyzed_at
      FROM risk_results
      WHERE 1=1
    SQL

    backend_params {
      name      = "contract_number"
      mapping   = "contract_number"
      condition = "CONDITION_TYPE_EQ"
    }

    response_params {
      name  = "contract_number"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "contract_number"
    }
    response_params {
      name  = "vendor_name"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "vendor_name"
    }
    response_params {
      name  = "monto_total"
      type  = "REQUEST_PARAMETER_TYPE_NUMBER"
      field = "monto_total"
    }
    response_params {
      name  = "risk_score"
      type  = "REQUEST_PARAMETER_TYPE_NUMBER"
      field = "risk_score"
    }
    response_params {
      name  = "risk_level"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "risk_level"
    }
    response_params {
      name  = "alertas"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "alertas"
    }
    response_params {
      name  = "recomendaciones"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "recomendaciones"
    }
    response_params {
      name  = "resumen"
      type  = "REQUEST_PARAMETER_TYPE_STRING"
      field = "resumen"
    }
  }
}

# ─── DataService App (API client credentials) ─────────────────────
resource "huaweicloud_dataarts_dataservice_app" "ayco" {
  count        = var.dataarts_enabled ? 1 : 0
  workspace_id = local.dataarts_workspace_id
  dlm_type     = "SHARED"
  app_type     = "APP"
  name         = "ayco-api-client"
  description  = "App client para APIs de riesgo contractual"
}
