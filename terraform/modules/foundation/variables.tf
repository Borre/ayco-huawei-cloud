terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.72.0"
    }
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.1.0.0/16"
}

variable "subnet_cidr" {
  description = "Subnet CIDR block"
  type        = string
  default     = "10.1.1.0/24"
}

variable "subnet_gateway" {
  description = "Subnet gateway IP"
  type        = string
  default     = "10.1.1.1"
}

variable "keypair_name" {
  description = "SSH keypair name for ECS access"
  type        = string
}

variable "project_id" {
  description = "Huawei Cloud project ID"
  type        = string
}
