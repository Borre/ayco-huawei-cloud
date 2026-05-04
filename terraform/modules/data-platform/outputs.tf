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

output "mrs_cluster_id" {
  description = "MRS cluster ID"
  value       = huaweicloud_mapreduce_cluster.ayco.id
}

output "mrs_master_ip" {
  description = "MRS master node IP"
  value       = huaweicloud_mapreduce_cluster.ayco.master_node_ip
}

output "kafka_connect_address" {
  description = "Kafka connect address"
  value       = huaweicloud_dms_kafka_instance.ayco.connect_address
}

output "dataarts_id" {
  description = "DataArts workspace ID"
  value       = huaweicloud_dataarts_studio_instance.ayco.id
}
