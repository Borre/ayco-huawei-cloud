resource "huaweicloud_identity_group" "ayco_team" {
  name        = "ayco-team"
  description = "AYCO demo team"
}

resource "huaweicloud_identity_role" "ayco_policy" {
  name        = "ayco-demo-policy"
  description = "Minimal access for AYCO demo: OBS, DWS, DLI, DataArts, FunctionGraph, OCR, MaaS"
  type        = "AX"

  # NOTE: Resource = "*" is scoped to var.project_id via the group role assignment below.
  # For production: split into per-service policies with explicit resource ARNs.
  policy = jsonencode({
    Version = "1.1"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "obs:*", "dws:*", "dli:*", "dataarts:*", "functiongraph:*",
          "ocr:*", "modelarts:*",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "huaweicloud_identity_group_role_assignment" "ayco" {
  group_id   = huaweicloud_identity_group.ayco_team.id
  role_id    = huaweicloud_identity_role.ayco_policy.id
  project_id = var.project_id
}
