export type RiskLevel = "low" | "medium" | "high" | "critical"
export type WorkflowStage = "upload" | "ocr" | "parser" | "verification" | "semantic" | "report"
export type WorkflowStatus = "pending" | "processing" | "success" | "failed"
export type FileStatus = "selected" | "uploading" | "uploaded" | "error"

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  status: FileStatus
  progress: number
  error?: string
  file: File
}

export interface WorkflowNode {
  stage: WorkflowStage
  label: string
  status: WorkflowStatus
  duration?: number
  error?: string
}

export interface VerificationResult {
  overall_score: number
  risk_level: RiskLevel
  fraud_flags: FraudFlag[]
  semantic_score?: number
  matched_claims?: number
  unverified_claims?: number
  document_summaries?: DocumentSummary[]
  report_url?: string
  report_filename?: string
  workflow?: WorkflowNode[]
}

export interface FraudFlag {
  type: string
  severity: "low" | "medium" | "high" | "critical"
  description: string
  field?: string
}

export interface DocumentSummary {
  document_type: string
  filename: string
  confidence: number
  key_fields: Record<string, string>
}

export interface UploadResponse {
  id?: string
  filename: string
  url?: string
  file_url?: string
  message: string
}

export interface ProcessCompleteResponse {
  overall_score?: number
  risk_level?: RiskLevel
  flags?: FraudFlag[] | string[]
  semantic_score?: number
  matched_claims?: number
  unverified_claims?: number
  report_url?: string
  report_filename?: string
  workflow?: WorkflowNode[]
  document_summaries?: DocumentSummary[]
  status?: string
}
