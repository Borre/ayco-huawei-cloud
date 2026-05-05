# ─── VPC (reusing existing default flexus VPC to avoid quota limit) ──────────
data "huaweicloud_vpc" "existing" {
  name = "vpc-default-flexus"
}

resource "huaweicloud_vpc_subnet" "main" {
  name       = "ayco-demo-subnet"
  cidr       = var.subnet_cidr
  gateway_ip = var.subnet_gateway
  vpc_id     = data.huaweicloud_vpc.existing.id

  # Huawei Cloud DNS + Google fallback
  primary_dns   = "100.125.1.250"
  secondary_dns = "8.8.8.8"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
}

# ─── Security Group ──────────────────────────────────────
resource "huaweicloud_networking_secgroup" "main" {
  name        = "ayco-demo-sg"
  description = "AYCO demo security group"

  tags = {
    project     = "ayco"
    environment = "demo"
    managed_by  = "terraform"
  }
}

# ─── SSH Access ────────────────────────────────────────────
# SSH access restricted to presenter's IP only
resource "huaweicloud_networking_secgroup_rule" "ssh" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 22
  port_range_max    = 22
  remote_ip_prefix  = var.presenter_ip
}

# ─── Web UI Public Access ───────────────────────────────────
# Public HTTPS for Dify web UI (demo requirement)
resource "huaweicloud_networking_secgroup_rule" "https" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
}

# Public HTTP for Dify web UI (demo requirement)
resource "huaweicloud_networking_secgroup_rule" "http" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}

# ─── Demo Service Ports (Presenter Only) ────────────────────
# Port 8000-8002: Dify API, web services
# Port 8443: Secure demo services
# Port 8501: Streamlit dashboard
# All restricted to presenter IP for security
resource "huaweicloud_networking_secgroup_rule" "demo_ports" {
  for_each = toset(["8000", "8001", "8002", "8443", "8501"])

  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = each.value
  port_range_max    = each.value
  remote_ip_prefix  = var.presenter_ip
}

# ─── Internal VPC Communication ─────────────────────────────
# Allow all TCP between instances within VPC (Dify <-> DWS <-> DLI)
resource "huaweicloud_networking_secgroup_rule" "internal_tcp" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 1
  port_range_max    = 65535
  remote_ip_prefix  = var.vpc_cidr
}

# ─── Egress Rules (Specific Instead of Allow-All) ───────────
# HTTPS: External API calls (Huawei Cloud SDK, DeepSeek, Langfuse)
resource "huaweicloud_networking_secgroup_rule" "egress_https" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
}

# HTTP: Package downloads, Docker images, yum/apt updates
resource "huaweicloud_networking_secgroup_rule" "egress_http" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 80
  port_range_max    = 80
  remote_ip_prefix  = "0.0.0.0/0"
}

# DNS: Domain name resolution (Huawei DNS 100.125.1.250, Google 8.8.8.8)
resource "huaweicloud_networking_secgroup_rule" "egress_dns" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "udp"
  port_range_min    = 53
  port_range_max    = 53
  remote_ip_prefix  = "0.0.0.0/0"
}

# DWS: Database connection (port 8000 default)
resource "huaweicloud_networking_secgroup_rule" "egress_dws" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 8000
  port_range_max    = 8000
  remote_ip_prefix  = "0.0.0.0/0"
}

# NTP: Time synchronization
resource "huaweicloud_networking_secgroup_rule" "egress_ntp" {
  security_group_id = huaweicloud_networking_secgroup.main.id
  direction         = "egress"
  ethertype         = "IPv4"
  protocol          = "udp"
  port_range_min    = 123
  port_range_max    = 123
  remote_ip_prefix  = "0.0.0.0/0"
}
