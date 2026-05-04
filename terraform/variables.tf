variable "region" {
  description = "Huawei Cloud region"
  type        = string
  default     = "la-north-2"
}

variable "access_key" {
  description = "Huawei Cloud AK"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Huawei Cloud SK"
  type        = string
  sensitive   = true
}

variable "domain_id" {
  description = "Huawei Cloud domain ID (optional, inferred from AK/SK)"
  type        = string
  default     = ""
}

variable "project_id" {
  description = "Huawei Cloud project ID"
  type        = string
  default     = "fbb6435c497c41bda90a0cc5240573e0"
}

variable "keypair_name" {
  description = "SSH keypair name"
  type        = string
  default     = "hermes-agent"
}

variable "dws_admin_password" {
  description = "DWS admin password"
  type        = string
  sensitive   = true
}

variable "maas_api_key" {
  description = "MaaS (ModelArts) API key — primary LLM provider"
  type        = string
  sensitive   = true
}

variable "deepseek_api_key" {
  description = "DeepSeek API key"
  type        = string
  sensitive   = true
}
