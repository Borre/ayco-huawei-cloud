resource "huaweicloud_dws_cluster" "ayco" {
  name              = "ayco-dws"
  node_type         = var.dws_node_type
  number_of_node    = var.dws_node_count
  number_of_cn      = 2
  version           = "9.1.0.200"
  user_name         = "ayco_admin"
  user_pwd          = var.dws_admin_password
  vpc_id            = var.vpc_id
  network_id        = var.subnet_id
  security_group_id = var.security_group_id
  availability_zone = "la-north-2a"

  public_ip {
    public_bind_type = "auto_assign"
  }

  tags = {
    project = "ayco"
    role    = "data-warehouse"
  }
}
