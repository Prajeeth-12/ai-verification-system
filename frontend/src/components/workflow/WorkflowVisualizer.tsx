"use client"

import { cn } from "@/lib/utils"
import { Check, Loader2, X } from "lucide-react"
import type { WorkflowNode } from "@/types"

interface WorkflowVisualizerProps {
  nodes: WorkflowNode[]
  className?: string
}

const stageLabels: Record<string, string> = {
  upload: "Upload",
  ocr: "OCR",
  parser: "Parse",
  verification: "Verify",
  semantic: "Semantic",
  report: "Report",
}

export default function WorkflowVisualizer({ nodes, className }: WorkflowVisualizerProps) {
  if (!nodes?.length) return null

  return (
    <div className={cn("flex items-center gap-0", className)}>
      {nodes.map((node, i) => {
        const isActive = node.status === "processing"
        const isDone = node.status === "success"
        const isFailed = node.status === "failed"
        const isLast = i === nodes.length - 1

        return (
          <div key={node.stage} className="flex items-center flex-1 min-w-0">
            <div className="flex items-center gap-2 min-w-0">
              <div className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 transition-colors",
                isDone && "bg-white",
                isActive && "bg-card border border-border",
                isFailed && "bg-error/20 border border-error/30",
                !isDone && !isActive && !isFailed && "bg-card border border-border"
              )}>
                {isDone && <Check className="w-3 h-3 text-black" />}
                {isActive && <Loader2 className="w-3 h-3 text-text animate-spin" />}
                {isFailed && <X className="w-3 h-3 text-error" />}
                {!isDone && !isActive && !isFailed && (
                  <div className="w-1.5 h-1.5 rounded-full bg-border" />
                )}
              </div>
              <span className={cn(
                "text-xs truncate",
                isDone && "text-text",
                isActive && "text-text",
                isFailed && "text-error",
                !isDone && !isActive && !isFailed && "text-text-muted"
              )}>
                {stageLabels[node.stage] || node.label}
              </span>
            </div>
            {!isLast && (
              <div className={cn(
                "flex-1 h-px mx-2",
                isDone ? "bg-white/30" : "bg-border"
              )} />
            )}
          </div>
        )
      })}
    </div>
  )
}
