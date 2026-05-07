output "dws_endpoint" {
  description = "DWS cluster public connect string (host:port)"
  value       = length(huaweicloud_dws_cluster.ayco.public_endpoints) > 0 ? huaweicloud_dws_cluster.ayco.public_endpoints[0].public_connect_info : ""
}

output "dws_public_ip" {
  description = "DWS managed EIP address"
  value       = huaweicloud_vpc_eip.dws.address
}

output "dws_private_ip" {
  description = "DWS private IP"
  value       = length(huaweicloud_dws_cluster.ayco.private_ip) > 0 ? huaweicloud_dws_cluster.ayco.private_ip[0] : ""
}

output "dli_database_name" {
  description = "DLI database name"
  value       = huaweicloud_dli_database.ayco.name
}

output "dli_database_id" {
  description = "DLI database ID"
  value       = huaweicloud_dli_database.ayco.id
}

output "dataarts_id" {
  description = "DataArts studio instance ID"
  value       = var.dataarts_enabled ? huaweicloud_dataarts_studio_instance.ayco[0].id : null
}

output "dataarts_workspace_id" {
  description = "DataArts workspace ID"
  value       = local.dataarts_workspace_id
}

output "dataarts_api_app_key" {
  description = "DataService API app key"
  value       = var.dataarts_enabled ? huaweicloud_dataarts_dataservice_app.ayco[0].app_key : null
  sensitive   = true
}

output "dataarts_api_app_secret" {
  description = "DataService API app secret"
  value       = var.dataarts_enabled ? huaweicloud_dataarts_dataservice_app.ayco[0].app_secret : null
  sensitive   = true
}

output "dataarts_etl_job_name" {
  description = "DataArts Factory ETL job name"
  value       = var.dataarts_enabled ? huaweicloud_dataarts_factory_job.contract_etl[0].name : null
}
