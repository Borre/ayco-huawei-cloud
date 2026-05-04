resource "huaweicloud_kms_key" "ayco" {
  key_alias    = "ayco-key"
  pending_days = 7
  is_enabled   = true

  key_algorithm = "AES_256"
  key_usage     = "ENCRYPT_DECRYPT"
}
