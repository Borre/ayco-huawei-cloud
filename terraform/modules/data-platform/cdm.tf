# ─── CDM Cluster (required for DataArts DWS connection) ─────────────
resource "huaweicloud_cdm_cluster" "ayco" {
  count             = var.dataarts_enabled ? 1 : 0
  name              = "ayco-cdm"
  availability_zone = "la-north-2a"
  flavor_id         = "cdm.large"
  vpc_id            = var.vpc_id
  subnet_id         = var.subnet_id
  security_group_id = var.security_group_id

  is_auto_off = false # Keep running for demo
}
