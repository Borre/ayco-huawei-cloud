# IAM group for demo team (AK/SK already has admin access)
resource "huaweicloud_identity_group" "ayco_team" {
  name        = "ayco-team"
  description = "AYCO demo team"
}
