"use client"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import type { FraudFlag } from "@/types"

interface FraudFlagsListProps {
  flags: FraudFlag[]
}

export default function FraudFlagsList({ flags }: FraudFlagsListProps) {
  if (flags.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-text-secondary">No fraud flags detected</p>
        <p className="text-xs text-text-muted mt-1">All documents passed verification checks</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {flags.map((flag, i) => (
        <div key={i} className="flex items-start gap-3 rounded-lg border border-border bg-card px-4 py-3">
          <div className={cn(
            "mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0",
            flag.severity === "critical" ? "bg-error" :
            flag.severity === "high" ? "bg-warning" :
            flag.severity === "medium" ? "bg-warning/60" : "bg-text-muted"
          )} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-sm font-medium text-text">{flag.type}</span>
              <Badge variant={flag.severity === "critical" ? "error" : flag.severity === "high" ? "warning" : "secondary"}>
                {flag.severity}
              </Badge>
            </div>
            <p className="text-sm text-text-secondary">{flag.description}</p>
            {flag.field && (
              <p className="text-xs text-text-muted mt-0.5 font-mono">{flag.field}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
