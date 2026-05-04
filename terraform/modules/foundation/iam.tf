resource "huaweicloud_identity_group" "ayco_team" {
  name        = "ayco-team"
  description = "AYCO demo team"
}

resource "huaweicloud_identity_role" "ayco_policy" {
  name        = "ayco-demo-policy"
  description = "Minimal access for AYCO demo: OBS, DWS, MRS, FunctionGraph"
  type        = "AX"

  policy = jsonencode({
    Version = "1.1"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "obs:*", "dws:*", "mrs:*", "functiongraph:*",
          "dataarts:*", "dms:*", "ocr:*", "modelarts:*"
        ]
        Resource = "*"
      }
    ]
  })
}
