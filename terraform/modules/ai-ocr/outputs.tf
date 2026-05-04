output "ocr_trigger_urn" {
  description = "OCR trigger function URN"
  value       = huaweicloud_fgs_function.ocr_trigger.urn
}

output "parse_contract_urn" {
  description = "Parse contract function URN"
  value       = huaweicloud_fgs_function.parse_contract.urn
}

output "llm_inference_urn" {
  description = "LLM inference function URN"
  value       = huaweicloud_fgs_function.llm_inference.urn
}
