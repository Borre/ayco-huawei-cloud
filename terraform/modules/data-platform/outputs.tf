output "dws_endpoint" {
  description = "DWS cluster endpoint"
  value       = huaweicloud_dws_cluster.ayco.public_ip[0].public_bind_type != "" ? (
    length(huaweicloud_dws_cluster.ayco.public_ip) > 0 ?
    "${huaweicloud_dws_cluster.ayco.public_ip[0].eip_id}" : ""
  ) : ""
}

output "dws_private_ip" {
  description = "DWS private IP"
  value       = huaweicloud_dws_cluster.ayco.public_ip
}

output "dli_database_name" {
  description = "DLI database name"
  value       = huaweicloud_dli_database.ayco.name
}

output "dli_database_id" {
  description = "DLI database ID"
  value       = huaweicloud_dli_database.ayco.id
}

output "kafka_connect_address" {
  description = "Kafka connect address"
  value       = huaweicloud_dms_kafka_instance.ayco.connect_address
}

output "dataarts_id" {
  description = "DataArts workspace ID"
  value       = huaweicloud_dataarts_studio_instance.ayco.id
}
