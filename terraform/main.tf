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
  domain_id  = var.domain_id
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
}

# ─── Module: Data Platform (MRS, DWS, DataArts, DMS) ────
module "data_platform" {
  source = "./modules/data-platform"

  vpc_id             = module.foundation.vpc_id
  subnet_id          = module.foundation.subnet_id
  security_group_id  = module.foundation.security_group_id
  project_id         = var.project_id
  dws_admin_password = var.dws_admin_password
  keypair_name       = var.keypair_name
}

# ─── Module: AI/OCR (FunctionGraph + OCR) ────────────────
module "ai_ocr" {
  source = "./modules/ai-ocr"

  project_id       = var.project_id
  vpc_id           = module.foundation.vpc_id
  subnet_id        = module.foundation.subnet_id
  deepseek_api_key = var.deepseek_api_key
  dify_api_url     = "http://${module.compute.dify_public_ip}/v1"
}
