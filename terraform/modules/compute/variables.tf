terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "= 1.91.0"
    }
  }
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

variable "keypair_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "dws_endpoint" {
  description = "DWS private endpoint for dashboard connectivity"
  type        = string
  default     = ""
}

variable "dws_port" {
  description = "DWS port"
  type        = number
  default     = 8000
}

variable "dws_database" {
  description = "DWS database name"
  type        = string
  default     = "ayco_db"
}

variable "dws_admin_password" {
  description = "DWS admin password for dashboard connectivity"
  type        = string
  sensitive   = true
  default     = ""
}

variable "dify_flavor" {
  description = "ECS flavor for Dify server"
  type        = string
  default     = "s6.xlarge.2" # 4 vCPU, 8GB
}

variable "web_flavor" {
  description = "ECS flavor for web/demo server"
  type        = string
  default     = "s6.large.2" # 2 vCPU, 4GB
}
