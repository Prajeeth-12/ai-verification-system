"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, ExternalLink } from "lucide-react"
import { getReportDownloadUrl } from "@/lib/api"
import type { DocumentSummary } from "@/types"

interface ReportCardProps {
  reportUrl?: string
  reportFilename?: string
  documentSummaries?: DocumentSummary[]
  overallScore?: number
}

export default function ReportCard({ reportUrl, reportFilename, documentSummaries, overallScore }: ReportCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Report</CardTitle>
          {reportFilename && (
            <div className="flex gap-1.5">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => window.open(getReportDownloadUrl(reportFilename), "_blank")}
              >
                <ExternalLink className="w-3.5 h-3.5" />
                View
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  const a = document.createElement("a")
                  a.href = getReportDownloadUrl(reportFilename)
                  a.download = reportFilename
                  a.click()
                }}
              >
                <Download className="w-3.5 h-3.5" />
                Download
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {overallScore !== undefined && (
          <div className="flex items-center gap-3 rounded-lg bg-card border border-border px-3 py-2.5">
            <FileText className="w-4 h-4 text-text-muted" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text">PDF Report</p>
              <p className="text-xs text-text-muted">
                Score: {overallScore}% — {new Date().toLocaleDateString()}
              </p>
            </div>
          </div>
        )}

        {documentSummaries && documentSummaries.length > 0 && (
          <div>
            <p className="text-xs text-text-muted mb-2">Documents</p>
            <div className="space-y-1.5">
              {documentSummaries.map((doc, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg bg-card border border-border px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-text truncate">{doc.filename}</p>
                    <p className="text-xs text-text-muted capitalize">{doc.document_type}</p>
                  </div>
                  <Badge variant={doc.confidence >= 0.8 ? "success" : "warning"}>
                    {Math.round(doc.confidence * 100)}%
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
