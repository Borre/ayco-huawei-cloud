terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "= 1.91.0"
    }
  }
}

variable "dws_database" {
  description = "DWS database name (created manually or via seed script)"
  type        = string
  default     = "ayco_db"
}

variable "dataarts_enabled" {
  description = "Enable DataArts Studio (set false to skip for faster deploys)"
  type        = bool
  default     = true
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

