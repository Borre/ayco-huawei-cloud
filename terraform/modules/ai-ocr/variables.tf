variable "project_id" {
  type = string
}

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

variable "deepseek_api_key" {
  description = "DeepSeek API key"
  type        = string
  sensitive   = true
}

variable "dify_api_url" {
  description = "Dify API base URL (http://DIFY_IP/v1)"
  type        = string
  default     = ""
}

variable "obs_contracts_raw" {
  description = "OBS bucket for raw contracts"
  type        = string
  default     = "ayco-contracts-raw"
}

variable "obs_contracts_text" {
  description = "OBS bucket for extracted text"
  type        = string
  default     = "ayco-contracts-text"
}

variable "obs_contracts_results" {
  description = "OBS bucket for AI results"
  type        = string
  default     = "ayco-contracts-results"
}
