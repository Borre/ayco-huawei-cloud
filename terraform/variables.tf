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

variable "presenter_ip" {
  description = "Presenter IP for SSH (e.g. 189.203.100.50/32). Use 0.0.0.0/0 for open access."
  type        = string
  default     = "0.0.0.0/0"
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

variable "dws_database" {
  description = "DWS database name"
  type        = string
  default     = "ayco_db"
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

variable "langfuse_public_key" {
  description = "Langfuse public key for LLM observability"
  type        = string
  default     = ""
}

variable "langfuse_secret_key" {
  description = "Langfuse secret key for LLM observability"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langfuse_host" {
  description = "Langfuse host URL"
  type        = string
  default     = "https://us.cloud.langfuse.com"
}

variable "dataarts_enabled" {
  description = "Enable DataArts Studio resources"
  type        = bool
  default     = true
}
