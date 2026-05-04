output "dify_public_ip" {
  description = "Dify server public IP"
  value       = huaweicloud_vpc_eip.dify.address
}

output "web_public_ip" {
  description = "Web server public IP"
  value       = huaweicloud_vpc_eip.web.address
}

output "dify_id" {
  description = "Dify ECS instance ID"
  value       = huaweicloud_compute_instance.dify.id
}

output "web_id" {
  description = "Web ECS instance ID"
  value       = huaweicloud_compute_instance.web.id
}

output "all_public_ips" {
  description = "All ECS public IPs"
  value = [
    huaweicloud_vpc_eip.dify.address,
    huaweicloud_vpc_eip.web.address,
  ]
}
