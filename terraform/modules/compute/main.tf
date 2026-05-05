# ─── Dify Server ECS ─────────────────────────────────────
resource "huaweicloud_compute_instance" "dify" {
  name               = "ayco-dify"
  flavor_id          = var.dify_flavor
  image_id           = "67c29d17-33bd-43f0-a17b-ed2015798bb8" # Ubuntu 22.04 server 64bit
  security_group_ids = [var.security_group_id]
  key_pair           = var.keypair_name

  system_disk_type = "GPSSD"
  system_disk_size = 80

  network {
    uuid = var.subnet_id
  }

  user_data = base64encode(templatefile("${path.module}/templates/dify-userdata.sh.tmpl", {
    dws_endpoint = var.dws_endpoint
    dws_port     = var.dws_port
    dws_database = var.dws_database
    dws_password = var.dws_admin_password
  }))

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
    role        = "chatbot"
  }
}

# ─── Web/Demo Server ECS ─────────────────────────────────
resource "huaweicloud_compute_instance" "web" {
  name               = "ayco-web"
  flavor_id          = var.web_flavor
  image_id           = "67c29d17-33bd-43f0-a17b-ed2015798bb8" # Ubuntu 22.04 server 64bit
  security_group_ids = [var.security_group_id]
  key_pair           = var.keypair_name

  system_disk_type = "GPSSD"
  system_disk_size = 40

  network {
    uuid = var.subnet_id
  }

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
    role        = "web"
  }
}
