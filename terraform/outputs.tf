output "dify_public_ip" {
  description = "Dify ECS public IP"
  value       = module.compute.dify_public_ip
}

output "web_public_ip" {
  description = "Web ECS public IP"
  value       = module.compute.web_public_ip
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

output "dataarts_workspace_id" {
  description = "DataArts workspace ID"
  value       = module.data_platform.dataarts_workspace_id
}

output "dataarts_api_app_key" {
  description = "DataService API app key"
  value       = module.data_platform.dataarts_api_app_key
  sensitive   = true
}

output "dashboard_url" {
  description = "Streamlit Contract Risk Dashboard URL"
  value       = "http://${module.compute.dify_public_ip}:8501"
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.foundation.vpc_id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = module.foundation.subnet_id
}
