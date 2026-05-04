# Cloud Firewall — IPS strict mode for demo
# NOTE: CFW requires a specific VPC attachment. 
# If CFW is not available in la-north-2, comment this out and rely on SG rules only.

# resource "huaweicloud_cfw_instance" "ayco" {
#   name                = "ayco-cfw"
#   flavor              = "cfw.standard"
#   pay_type            = "postPaid"
#   vpc_id              = huaweicloud_vpc.main.id
#   subnet_id           = huaweicloud_vpc_subnet.main.id
#   attach_vpc_ids      = [huaweicloud_vpc.main.id]
#   enterprise_project_id = var.project_id
# }
