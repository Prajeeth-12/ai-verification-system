"use client"

import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { VerificationResult } from "@/types"

interface StatRowProps {
  label: string
  value: string | number
  subtitle?: string
  className?: string
}

function StatRow({ label, value, subtitle, className }: StatRowProps) {
  return (
    <div className={cn("flex items-center justify-between px-4 py-3", className)}>
      <div>
        <p className="text-sm text-text-secondary">{label}</p>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
      <span className="text-sm font-semibold text-text">{value}</span>
    </div>
  )
}

interface StatsCardsGridProps {
  result: VerificationResult
}

export default function StatsCardsGrid({ result }: StatsCardsGridProps) {
  const stats = [
    {
      label: "Verification Score",
      value: `${result.overall_score}%`,
      subtitle: result.overall_score >= 80 ? "Passing threshold" : "Below threshold",
    },
    {
      label: "Semantic Score",
      value: result.semantic_score ? `${result.semantic_score}%` : "N/A",
      subtitle: result.semantic_score ? "Cross-document consistency" : undefined,
    },
    {
      label: "Risk Level",
      value: result.risk_level.charAt(0).toUpperCase() + result.risk_level.slice(1),
      subtitle: `${result.fraud_flags.length} flag${result.fraud_flags.length !== 1 ? "s" : ""} detected`,
    },
    {
      label: "Fraud Flags",
      value: result.fraud_flags.length,
      subtitle: result.fraud_flags.length === 0 ? "No issues" : "Requires review",
    },
    {
      label: "Matched Claims",
      value: result.matched_claims ?? 0,
      subtitle: "Successfully verified",
    },
    {
      label: "Unverified Claims",
      value: result.unverified_claims ?? 0,
      subtitle: "Manual review needed",
    },
  ]

  return (
    <Card>
      <div className="divide-y divide-border">
        {stats.map((stat) => (
          <StatRow key={stat.label} {...stat} />
        ))}
      </div>
    </Card>
  )
}
