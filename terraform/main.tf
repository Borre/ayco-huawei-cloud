# AYCO Huawei Cloud — Terraform Root
# Region: la-north-2 (Mexico City 2)

terraform {
  required_version = ">= 1.5"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "= 1.91.0"
    }
  }
}

provider "huaweicloud" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
  # domain_id = var.domain_id  # Optional: inferred from AK/SK
}

# ─── Module: Foundation (VPC, SG, OBS, KMS, IAM) ─────────
module "foundation" {
  source = "./modules/foundation"

  project_id   = var.project_id
  keypair_name = var.keypair_name
  presenter_ip = var.presenter_ip
}

# ─── Module: Compute (ECS: Dify + Web + Dashboard) ────────
module "compute" {
  source = "./modules/compute"

  vpc_id            = module.foundation.vpc_id
  subnet_id         = module.foundation.subnet_id
  security_group_id = module.foundation.security_group_id
  keypair_name      = var.keypair_name
  project_id        = var.project_id

  # DWS connectivity for Streamlit dashboard
  dws_endpoint       = module.data_platform.dws_private_ip
  dws_port           = 8000
  dws_database       = var.dws_database
  dws_admin_password = var.dws_admin_password

  # Dify + Streamlit on same ECS
  dify_flavor = "s6.xlarge.2"
  web_flavor  = "s6.large.2"
}

# ─── Module: Data Platform (DLI, DWS, DataArts) ─────
module "data_platform" {
  source = "./modules/data-platform"

  vpc_id                = module.foundation.vpc_id
  subnet_id             = module.foundation.subnet_id
  security_group_id     = module.foundation.security_group_id
  project_id            = var.project_id
  dws_admin_password    = var.dws_admin_password
  dws_database          = var.dws_database
  dataarts_enabled      = var.dataarts_enabled
  obs_contracts_text    = "ayco-contracts-text"
  obs_contracts_results = "ayco-contracts-results"
}

# ─── Module: AI/OCR (FunctionGraph + OCR) ────────────────
module "ai_ocr" {
  source = "./modules/ai-ocr"

  project_id       = var.project_id
  vpc_id           = module.foundation.vpc_id
  subnet_id        = module.foundation.subnet_id
  maas_api_key     = var.maas_api_key
  deepseek_api_key = var.deepseek_api_key
  dify_api_url     = "http://${module.compute.dify_public_ip}/v1"

  obs_contracts_raw     = "ayco-contracts-raw"
  obs_contracts_text    = "ayco-contracts-text"
  obs_contracts_results = "ayco-contracts-results"

  langfuse_public_key = var.langfuse_public_key
  langfuse_secret_key = var.langfuse_secret_key
  langfuse_host       = var.langfuse_host

  access_key = var.access_key
  secret_key = var.secret_key
}
