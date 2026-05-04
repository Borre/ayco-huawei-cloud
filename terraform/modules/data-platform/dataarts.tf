resource "huaweicloud_dataarts_studio_instance" "ayco" {
  name                  = "ayco-dataarts"
  version               = "dayu.nb.professional"
  availability_zone     = "la-north-2a"
  vpc_id                = var.vpc_id
  subnet_id             = var.subnet_id
  security_group_id     = var.security_group_id
  period_unit           = "month"
  period                = 1
  enterprise_project_id = var.project_id
}
