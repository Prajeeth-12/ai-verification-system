"use client"

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import DashboardLayout from "@/components/layout/DashboardLayout"
import { cn } from "@/lib/utils"
import { formatFileSize } from "@/lib/utils"
import { handleApiError, processComplete, uploadDocument, getReportDownloadUrl } from "@/lib/api"
import type { UploadedFile, WorkflowNode, VerificationResult, ProcessCompleteResponse } from "@/types"
import {
  Upload, FileText, CheckCircle2, XCircle, Loader2,
  AlertTriangle, ArrowRight, Download, ExternalLink,
  Cpu, HardDrive, Database, Clock, BarChart3, Shield
} from "lucide-react"

/* ─── Pipeline Stage Indicator ──────────────────────────── */

type StageStatus = "pending" | "processing" | "success" | "failed"

function PipelineStage({ label, status, isLast }: { label: string; status: StageStatus; isLast: boolean }) {
  return (
    <div className="flex items-center gap-0">
      <div className="flex items-center gap-1.5">
        <div className={cn(
          "w-1.5 h-1.5 rounded-full transition-colors",
          status === "success" && "bg-success",
          status === "failed" && "bg-error",
          status === "processing" && "bg-text animate-pulse",
          status === "pending" && "bg-border-light"
        )} />
        <span className={cn(
          "text-[11px] font-medium transition-colors",
          status === "success" && "text-text-secondary",
          status === "failed" && "text-error",
          status === "processing" && "text-text",
          status === "pending" && "text-text-muted"
        )}>{label}</span>
      </div>
      {!isLast && <ArrowRight className="w-3 h-3 text-border-light mx-1.5" />}
    </div>
  )
}

function Pipeline({ nodes }: { nodes: WorkflowNode[] }) {
  return (
    <div className="flex items-center flex-wrap gap-y-1">
      {nodes.map((node, i) => (
        <PipelineStage key={node.stage} label={node.label} status={node.status} isLast={i === nodes.length - 1} />
      ))}
    </div>
  )
}

/* ─── Upload Drop Zone ──────────────────────────────────── */

function UploadZone({ onFilesSelected, isUploading }: { onFilesSelected: (files: File[]) => void; isUploading: boolean }) {
  const [isDragOver, setIsDragOver] = useState(false)

  return (
    <div
      className={cn(
        "border border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer",
        isDragOver ? "border-text-secondary bg-surface" : "border-border hover:border-border-light hover:bg-surface/50",
        isUploading && "pointer-events-none opacity-50"
      )}
      onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragOver(false)
        const files = Array.from(e.dataTransfer.files)
        if (files.length) onFilesSelected(files)
      }}
      onClick={() => {
        const input = document.createElement("input")
        input.type = "file"
        input.accept = ".pdf,.png,.jpg,.jpeg"
        input.multiple = true
        input.onchange = (e) => {
          const files = Array.from((e.target as HTMLInputElement).files || [])
          if (files.length) onFilesSelected(files)
        }
        input.click()
      }}
    >
      <Upload className="w-5 h-5 text-text-muted mx-auto mb-2" />
      <p className="text-sm text-text-secondary">Drop files here or click to browse</p>
      <p className="text-[11px] text-text-muted mt-1">PDF, PNG, JPG — max 10MB</p>
    </div>
  )
}

/* ─── Metric Card ───────────────────────────────────────── */

function Metric({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="space-y-1">
      <p className="text-[11px] text-text-muted uppercase tracking-wider font-medium">{label}</p>
      <p className="text-xl font-semibold text-text tabular-nums">{value}</p>
      {sub && <p className="text-[11px] text-text-muted">{sub}</p>}
    </div>
  )
}

/* ─── Initial State ─────────────────────────────────────── */

function initialWorkflow(): WorkflowNode[] {
  return [
    { stage: "upload", label: "Upload", status: "pending" },
    { stage: "ocr", label: "OCR", status: "pending" },
    { stage: "parser", label: "Parse", status: "pending" },
    { stage: "verification", label: "Verify", status: "pending" },
    { stage: "semantic", label: "Semantic", status: "pending" },
    { stage: "report", label: "Report", status: "pending" },
  ]
}

/* ─── Page ──────────────────────────────────────────────── */

export default function DashboardPage() {
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [workflowNodes, setWorkflowNodes] = useState<WorkflowNode[]>(initialWorkflow())
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])

  const updateNode = (stage: string, status: WorkflowNode["status"]) =>
    setWorkflowNodes((prev) =>
      prev.map((n) => (n.stage === stage ? { ...n, status } : n))
    )

  const handleFilesSelected = useCallback(async (files: File[]) => {
    setError(null)

    for (const file of files) {
      const entry: UploadedFile = {
        id: "",
        name: file.name,
        size: file.size,
        type: file.type,
        status: "uploading",
        progress: 0,
        file,
      }
      setUploadedFiles((prev) => [...prev, entry])

      try {
        const res = await uploadDocument(file, (progress) => {
          setUploadedFiles((prev) =>
            prev.map((f) => (f.name === file.name && f.status === "uploading" ? { ...f, progress } : f))
          )
        })
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.name === file.name && f.status === "uploading"
              ? { ...f, id: res.id || res.filename, name: res.filename, status: "uploaded", progress: 100 }
              : f
          )
        )
      } catch (err) {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.name === file.name && f.status === "uploading"
              ? { ...f, status: "error", error: handleApiError(err) }
              : f
          )
        )
      }
    }
  }, [])

  const startVerification = useCallback(async () => {
    const ready = uploadedFiles.filter((f) => f.status === "uploaded")
    if (!ready.length) return

    setIsProcessing(true)
    setError(null)
    setResult(null)
    setWorkflowNodes(initialWorkflow())

    updateNode("upload", "success")
    await new Promise((r) => setTimeout(r, 150))
    updateNode("ocr", "processing")
    await new Promise((r) => setTimeout(r, 300))
    updateNode("ocr", "success")
    updateNode("parser", "processing")
    await new Promise((r) => setTimeout(r, 300))
    updateNode("parser", "success")
    updateNode("verification", "processing")

    try {
      const first = ready[0]
      const apiResult: ProcessCompleteResponse = await processComplete(first.id, first.name)

      updateNode("verification", "success")
      updateNode("semantic", "success")
      updateNode("report", "success")

      // Normalize flags from backend (can be string[] or FraudFlag[])
      const normalizedFlags = (apiResult.flags || []).map((f: any) =>
        typeof f === "string"
          ? { type: "flag", severity: "medium" as const, description: f }
          : f
      )

      setResult({
        overall_score: apiResult.overall_score ?? 0,
        risk_level: apiResult.risk_level ?? "medium",
        fraud_flags: normalizedFlags,
        semantic_score: apiResult.semantic_score,
        matched_claims: apiResult.matched_claims,
        unverified_claims: apiResult.unverified_claims,
        document_summaries: apiResult.document_summaries,
        report_url: apiResult.report_url,
        report_filename: apiResult.report_filename,
        workflow: [
          { stage: "upload", label: "Upload", status: "success" },
          { stage: "ocr", label: "OCR", status: "success" },
          { stage: "parser", label: "Parse", status: "success" },
          { stage: "verification", label: "Verify", status: "success" },
          { stage: "semantic", label: "Semantic", status: "success" },
          { stage: "report", label: "Report", status: "success" },
        ],
      })
    } catch (err) {
      const msg = handleApiError(err)
      setError(msg)
      setWorkflowNodes((prev) =>
        prev.map((n) => (n.status === "processing" ? { ...n, status: "failed" } : n))
      )
    } finally {
      setIsProcessing(false)
    }
  }, [uploadedFiles])

  const hasReady = uploadedFiles.some((f) => f.status === "uploaded")

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-lg font-semibold text-text">Verification Dashboard</h1>
            <p className="text-[13px] text-text-muted mt-0.5">Upload documents and run the AI verification pipeline.</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-text-muted flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" })}
            </span>
          </div>
        </div>

        {/* Pipeline */}
        <div className="bg-surface border border-border rounded-lg px-4 py-2.5">
          <Pipeline nodes={workflowNodes} />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

          {/* ─── LEFT COLUMN ─── */}
          <div className="lg:col-span-8 space-y-5">

            {/* Upload */}
            {!result && (
              <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-[13px] font-medium text-text">Documents</h2>
                  {hasReady && !isProcessing && (
                    <button
                      onClick={startVerification}
                      className="h-7 px-3 bg-text text-bg text-[12px] font-medium rounded-md hover:bg-text/90 transition-colors flex items-center gap-1.5"
                    >
                      <Shield className="w-3 h-3" />
                      Run Verification
                    </button>
                  )}
                  {isProcessing && (
                    <div className="flex items-center gap-1.5 text-[12px] text-text-secondary">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      Processing...
                    </div>
                  )}
                </div>

                <UploadZone onFilesSelected={handleFilesSelected} isUploading={isProcessing} />

                {/* File List */}
                {uploadedFiles.length > 0 && (
                  <div className="space-y-1">
                    {uploadedFiles.map((file, i) => (
                      <div key={i} className="flex items-center justify-between py-2 px-2.5 rounded-md hover:bg-card transition-colors">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <FileText className="w-4 h-4 text-text-muted flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="text-[13px] text-text truncate">{file.name}</p>
                            <p className="text-[11px] text-text-muted">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5">
                          {file.status === "uploading" && (
                            <span className="text-[11px] text-text-muted tabular-nums">{file.progress}%</span>
                          )}
                          {file.status === "uploaded" && <CheckCircle2 className="w-3.5 h-3.5 text-success" />}
                          {file.status === "error" && <XCircle className="w-3.5 h-3.5 text-error" />}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="flex items-start gap-2.5 bg-error/5 border border-error/10 rounded-lg px-3.5 py-2.5">
                <AlertTriangle className="w-3.5 h-3.5 text-error mt-0.5 flex-shrink-0" />
                <p className="text-[13px] text-error/80">{error}</p>
              </div>
            )}

            {/* Results */}
            <AnimatePresence>
              {result && !isProcessing && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className="space-y-5"
                >
                  {/* Scores Row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="bg-surface border border-border rounded-lg p-3.5">
                      <Metric label="Overall" value={`${result.overall_score}%`} sub={result.risk_level.toUpperCase()} />
                    </div>
                    <div className="bg-surface border border-border rounded-lg p-3.5">
                      <Metric label="Semantic" value={`${result.semantic_score ?? "—"}%`} />
                    </div>
                    <div className="bg-surface border border-border rounded-lg p-3.5">
                      <Metric label="Claims" value={result.matched_claims ?? 0} sub="matched" />
                    </div>
                    <div className="bg-surface border border-border rounded-lg p-3.5">
                      <Metric label="Flags" value={result.fraud_flags.length} sub={result.fraud_flags.length === 0 ? "none" : "detected"} />
                    </div>
                  </div>

                  {/* Flags */}
                  {result.fraud_flags.length > 0 && (
                    <div className="bg-surface border border-border rounded-lg p-4 space-y-2.5">
                      <h3 className="text-[13px] font-medium text-text">Risk Flags</h3>
                      <div className="space-y-1">
                        {result.fraud_flags.map((flag, i) => (
                          <div key={i} className="flex items-start gap-2.5 py-2 px-2.5 rounded-md bg-card/50">
                            <AlertTriangle className={cn(
                              "w-3.5 h-3.5 mt-0.5 flex-shrink-0",
                              flag.severity === "critical" || flag.severity === "high" ? "text-error" : "text-warning"
                            )} />
                            <div className="min-w-0">
                              <p className="text-[13px] text-text">{flag.description}</p>
                              {flag.field && <p className="text-[11px] text-text-muted mt-0.5">{flag.field}</p>}
                            </div>
                            <span className={cn(
                              "text-[10px] font-medium uppercase tracking-wider flex-shrink-0 px-1.5 py-0.5 rounded",
                              flag.severity === "critical" && "bg-error/10 text-error",
                              flag.severity === "high" && "bg-error/10 text-error",
                              flag.severity === "medium" && "bg-warning/10 text-warning",
                              flag.severity === "low" && "bg-text-muted/10 text-text-muted"
                            )}>{flag.severity}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.fraud_flags.length === 0 && (
                    <div className="bg-surface border border-border rounded-lg px-4 py-3 flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
                      <p className="text-[13px] text-text-secondary">No fraud indicators detected.</p>
                    </div>
                  )}

                  {/* Documents */}
                  {result.document_summaries && result.document_summaries.length > 0 && (
                    <div className="bg-surface border border-border rounded-lg p-4 space-y-2.5">
                      <h3 className="text-[13px] font-medium text-text">Extracted Documents</h3>
                      <div className="space-y-1">
                        {result.document_summaries.map((doc: any, i: number) => (
                          <div key={i} className="bg-card/50 rounded-md p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <FileText className="w-3.5 h-3.5 text-text-muted" />
                                <span className="text-[13px] font-medium text-text truncate">
                                  {doc.filename || doc.metadata?.filename || "Document"}
                                </span>
                              </div>
                              <span className="text-[11px] text-text-muted font-mono">
                                {doc.document_type || doc.metadata?.document_type || "—"} · {Math.round((doc.confidence || doc.metadata?.classification_confidence || 0) * 100)}%
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                              {Object.entries(doc.key_fields || doc.data || {}).slice(0, 6).map(([k, v]) => (
                                <div key={k} className="flex justify-between text-[12px]">
                                  <span className="text-text-muted capitalize">{k.replace(/_/g, " ")}</span>
                                  <span className="text-text-secondary font-medium truncate ml-2">{String(v)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Report Download */}
                  {result.report_url && (
                    <div className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <BarChart3 className="w-4 h-4 text-text-muted" />
                        <div>
                          <p className="text-[13px] font-medium text-text">Verification Report</p>
                          <p className="text-[11px] text-text-muted">Full analysis PDF available</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={result.report_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="h-7 px-3 bg-card border border-border text-[12px] text-text-secondary font-medium rounded-md hover:bg-card-hover hover:text-text transition-colors flex items-center gap-1.5"
                        >
                          <ExternalLink className="w-3 h-3" />
                          View
                        </a>
                        {result.report_filename && (
                          <a
                            href={getReportDownloadUrl(result.report_filename)}
                            className="h-7 px-3 bg-text text-bg text-[12px] font-medium rounded-md hover:bg-text/90 transition-colors flex items-center gap-1.5"
                          >
                            <Download className="w-3 h-3" />
                            Download
                          </a>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Reset */}
                  <button
                    onClick={() => {
                      setResult(null)
                      setUploadedFiles([])
                      setWorkflowNodes(initialWorkflow())
                      setError(null)
                    }}
                    className="text-[12px] text-text-muted hover:text-text-secondary transition-colors"
                  >
                    ← New verification
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ─── RIGHT COLUMN ─── */}
          <div className="lg:col-span-4 space-y-5">

            {/* System Health */}
            <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-[11px] font-medium text-text-muted uppercase tracking-wider">System</h3>
              <div className="space-y-2">
                {[
                  { icon: Cpu, label: "OCR Engine", status: "online" },
                  { icon: HardDrive, label: "LLM Parser", status: "online" },
                  { icon: Database, label: "Vector DB", status: "idle" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-1">
                    <div className="flex items-center gap-2">
                      <item.icon className="w-3.5 h-3.5 text-text-muted" />
                      <span className="text-[13px] text-text-secondary">{item.label}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className={cn(
                        "w-1.5 h-1.5 rounded-full",
                        item.status === "online" && "bg-success",
                        item.status === "idle" && "bg-text-muted"
                      )} />
                      <span className="text-[11px] text-text-muted">{item.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Execution Log */}
            <div className="bg-surface border border-border rounded-lg p-4 space-y-3">
              <h3 className="text-[11px] font-medium text-text-muted uppercase tracking-wider">Pipeline</h3>
              <div className="space-y-1">
                {workflowNodes.map((node) => (
                  <div key={node.stage} className="flex items-center justify-between py-1.5">
                    <span className="text-[13px] text-text-secondary">{node.label}</span>
                    <span className={cn(
                      "text-[11px] font-mono font-medium",
                      node.status === "success" && "text-success",
                      node.status === "failed" && "text-error",
                      node.status === "processing" && "text-text",
                      node.status === "pending" && "text-text-muted"
                    )}>
                      {node.status === "success" ? "OK" : node.status === "failed" ? "FAIL" : node.status === "processing" ? "RUN" : "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Scores */}
            {result && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-surface border border-border rounded-lg p-4 space-y-4"
              >
                <h3 className="text-[11px] font-medium text-text-muted uppercase tracking-wider">Confidence</h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-[12px] text-text-secondary">Verification</span>
                      <span className="text-[12px] font-medium text-text tabular-nums">{result.overall_score}%</span>
                    </div>
                    <div className="h-1 bg-card rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-text rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${result.overall_score}%` }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                  {result.semantic_score !== undefined && (
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-[12px] text-text-secondary">Semantic</span>
                        <span className="text-[12px] font-medium text-text tabular-nums">{result.semantic_score}%</span>
                      </div>
                      <div className="h-1 bg-card rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-text-secondary rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${result.semantic_score}%` }}
                          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                <div className="pt-3 border-t border-border">
                  <div className="flex justify-between">
                    <span className="text-[12px] text-text-secondary">Risk Level</span>
                    <span className={cn(
                      "text-[11px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded",
                      result.risk_level === "low" && "bg-success/10 text-success",
                      result.risk_level === "medium" && "bg-warning/10 text-warning",
                      result.risk_level === "high" && "bg-error/10 text-error",
                      result.risk_level === "critical" && "bg-error/10 text-error"
                    )}>{result.risk_level}</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Empty State */}
            {!result && !isProcessing && (
              <div className="bg-surface border border-border rounded-lg p-5 text-center">
                <FileText className="w-5 h-5 text-text-muted mx-auto mb-2" />
                <p className="text-[13px] text-text-secondary">No results yet</p>
                <p className="text-[11px] text-text-muted mt-0.5">Upload documents to begin</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
