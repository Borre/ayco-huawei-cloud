resource "huaweicloud_vpc_eip" "dws" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "ayco-dws-eip-bw"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }
  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
    role        = "dws-public-ip"
  }
}

resource "huaweicloud_dws_cluster" "ayco" {
  name              = "ayco-dws"
  node_type         = "dwsx3.4U16G.4DPU"
  number_of_node    = var.dws_node_count
  number_of_cn      = 2
  version           = "9.1.0.223"
  user_name         = "ayco_admin"
  user_pwd          = var.dws_admin_password
  vpc_id            = var.vpc_id
  network_id        = var.subnet_id
  security_group_id = var.security_group_id
  availability_zone = "la-north-2a"

  public_ip {
    public_bind_type = "bind_existing"
    eip_id           = huaweicloud_vpc_eip.dws.id
  }

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
    role        = "data-warehouse"
  }
}
