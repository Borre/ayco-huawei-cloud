# ─── Dify Server ECS ─────────────────────────────────────
resource "huaweicloud_compute_instance" "dify" {
  name               = "ayco-dify"
  flavor_id          = var.dify_flavor
  security_group_ids = [var.security_group_id]
  key_pair           = var.keypair_name

  system_disk_type = "GPSSD"
  system_disk_size = 80

  network {
    uuid = var.subnet_id
  }

  tags = {
    project = "ayco"
    role    = "dify"
  }
}

# ─── Web/Demo Server ECS ─────────────────────────────────
resource "huaweicloud_compute_instance" "web" {
  name               = "ayco-web"
  flavor_id          = var.web_flavor
  security_group_ids = [var.security_group_id]
  key_pair           = var.keypair_name

  system_disk_type = "GPSSD"
  system_disk_size = 40

  network {
    uuid = var.subnet_id
  }

  tags = {
    project = "ayco"
    role    = "web"
  }
}
