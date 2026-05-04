terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.72.0"
    }
  }
}

variable "keypair_name" {
  description = "SSH keypair name for MRS cluster"
  type        = string
  default     = "hermes-agent"
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}

variable "project_id" {
  type = string
}

variable "dws_admin_password" {
  description = "DWS admin password"
  type        = string
  sensitive   = true
}

variable "dws_node_count" {
  description = "Number of DWS nodes"
  type        = number
  default     = 3
}

variable "kafka_flavor" {
  description = "DMS Kafka flavor"
  type        = string
  default     = "kafka.2u4g.single"
}

variable "obs_contracts_text" {
  description = "OBS bucket for extracted contract text"
  type        = string
  default     = "ayco-contracts-text"
}

variable "obs_contracts_results" {
  description = "OBS bucket for AI analysis results"
  type        = string
  default     = "ayco-contracts-results"
}
