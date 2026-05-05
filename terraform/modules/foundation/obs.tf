locals {
  buckets = [
    { name = "ayco-contracts-raw", acl = "private", versioning = true },
    { name = "ayco-contracts-text", acl = "private", versioning = true },
    { name = "ayco-contracts-results", acl = "private", versioning = true },
  ]
}

resource "huaweicloud_obs_bucket" "buckets" {
  for_each = { for b in local.buckets : b.name => b }

  bucket        = each.value.name
  storage_class = "STANDARD"
  acl           = each.value.acl
  versioning    = each.value.versioning
  encryption    = true
  force_destroy = true

  lifecycle {
    prevent_destroy = false
  }
}
