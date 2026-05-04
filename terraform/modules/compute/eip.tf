# ─── EIP for Dify ────────────────────────────────────────
resource "huaweicloud_vpc_eip" "dify" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "ayco-dify-eip"
    size        = 10
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_compute_eip_associate" "dify" {
  public_ip   = huaweicloud_vpc_eip.dify.address
  instance_id = huaweicloud_compute_instance.dify.id
}

# ─── EIP for Web ─────────────────────────────────────────
resource "huaweicloud_vpc_eip" "web" {
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "ayco-web-eip"
    size        = 5
    share_type  = "PER"
    charge_mode = "traffic"
  }
}

resource "huaweicloud_compute_eip_associate" "web" {
  public_ip   = huaweicloud_vpc_eip.web.address
  instance_id = huaweicloud_compute_instance.web.id
}
