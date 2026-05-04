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

variable "dws_node_type" {
  description = "DWS node flavor"
  type        = string
  default     = "dws2.m6.xlarge.8"
}

variable "mrs_version" {
  description = "MRS cluster version"
  type        = string
  default     = "MRS 3.1.0-LTS.5"
}

variable "kafka_flavor" {
  description = "DMS Kafka flavor"
  type        = string
  default     = "kafka.2u4g.cluster"
}
