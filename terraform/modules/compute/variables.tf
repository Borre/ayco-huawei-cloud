terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.72.0"
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

variable "dify_flavor" {
  description = "ECS flavor for Dify server"
  type        = string
  default     = "s6.xlarge.2"  # 4 vCPU, 8GB
}

variable "web_flavor" {
  description = "ECS flavor for web/demo server"
  type        = string
  default     = "s6.large.2"  # 2 vCPU, 4GB
}
