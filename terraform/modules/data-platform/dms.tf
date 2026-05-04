resource "huaweicloud_dms_kafka_instance" "ayco" {
  name              = "ayco-kafka"
  flavor_id         = var.kafka_flavor
  engine_version    = "3.x"
  storage_spec_code = "dms.physical.storage.high.v2"
  storage_space     = 100
  broker_num        = 1
  vpc_id            = var.vpc_id
  network_id        = var.subnet_id
  security_group_id = var.security_group_id
  availability_zones = ["la-north-2a"]

  access_user = "admin"
  password    = var.dws_admin_password

  tags = {
    project = "ayco"
    role    = "message-queue"
  }
}
