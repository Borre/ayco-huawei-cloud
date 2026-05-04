output "vpc_id" {
  description = "VPC ID"
  value       = huaweicloud_vpc.main.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = huaweicloud_vpc_subnet.main.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = huaweicloud_networking_secgroup.main.id
}

output "obs_bucket_names" {
  description = "OBS bucket names"
  value       = [for b in huaweicloud_obs_bucket.buckets : b.bucket]
}

output "kms_key_id" {
  description = "KMS key ID"
  value       = huaweicloud_kms_key.ayco.id
}

output "iam_group_id" {
  description = "IAM group ID for AYCO team"
  value       = huaweicloud_identity_group.ayco_team.id
}
