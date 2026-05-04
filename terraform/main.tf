# AYCO Huawei Cloud — Terraform Root
# Region: la-north-2 (Mexico City 2)

terraform {
  required_version = ">= 1.5"
  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.72.0"
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
}

# ─── Module: Compute (ECS: Dify + Web) ───────────────────
module "compute" {
  source = "./modules/compute"

  vpc_id            = module.foundation.vpc_id
  subnet_id         = module.foundation.subnet_id
  security_group_id = module.foundation.security_group_id
  keypair_name      = var.keypair_name
  project_id        = var.project_id

  # MVP flavors (override defaults)
  dify_flavor = "s6.large.2"   # 2 vCPU, 4GB (was 4vCPU/8GB)
  web_flavor  = "s6.medium.2"  # 1 vCPU, 2GB (was 2vCPU/4GB)
}

# ─── Module: Data Platform (DLI, DWS, DataArts, DMS) ─────
module "data_platform" {
  source = "./modules/data-platform"

  vpc_id             = module.foundation.vpc_id
  subnet_id          = module.foundation.subnet_id
  security_group_id  = module.foundation.security_group_id
  project_id         = var.project_id
  dws_admin_password = var.dws_admin_password
  keypair_name       = var.keypair_name
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
}
