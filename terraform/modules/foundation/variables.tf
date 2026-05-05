terraform {
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "= 1.91.0"
    }
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "172.16.0.0/16"
}

variable "subnet_cidr" {
  description = "Subnet CIDR block"
  type        = string
  default     = "172.16.1.0/24"
}

variable "subnet_gateway" {
  description = "Subnet gateway IP"
  type        = string
  default     = "172.16.1.1"
}

variable "presenter_ip" {
  description = "Presenter IP for SSH access (CIDR notation, e.g. 189.203.100.50/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "keypair_name" {
  description = "SSH keypair name for ECS access"
  type        = string
}

variable "project_id" {
  description = "Huawei Cloud project ID"
  type        = string
}
