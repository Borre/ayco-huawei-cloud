output "dify_public_ip" {
  description = "Dify ECS public IP"
  value       = module.compute.dify_public_ip
}

output "dws_endpoint" {
  description = "DWS cluster endpoint"
  value       = module.data_platform.dws_endpoint
}

output "ecs_ips" {
  description = "All ECS public IPs"
  value       = module.compute.all_public_ips
}

output "obs_buckets" {
  description = "OBS bucket names"
  value       = module.foundation.obs_bucket_names
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.foundation.vpc_id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = module.foundation.subnet_id
}
