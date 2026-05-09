"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { FraudFlag } from "@/types"

interface VerificationChartsProps {
  overallScore: number
  semanticScore?: number
  fraudFlags: FraudFlag[]
  matchedClaims?: number
  unverifiedClaims?: number
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-border bg-card px-3 py-2 text-xs shadow-lg">
        <p className="text-text-muted mb-1">{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={i} className="text-text font-medium">{entry.name}: {entry.value}</p>
        ))}
      </div>
    )
  }
  return null
}

export default function VerificationCharts({ fraudFlags }: VerificationChartsProps) {
  const counts = { Low: 0, Medium: 0, High: 0, Critical: 0 }
  fraudFlags.forEach((f) => {
    const key = f.severity.charAt(0).toUpperCase() + f.severity.slice(1) as keyof typeof counts
    if (key in counts) counts[key]++
  })
  const severity = Object.entries(counts).map(([severity, count]) => ({ severity, count }))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Fraud Flags by Severity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={severity.length > 0 ? severity : [{ severity: "None", count: 0 }]}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="severity" tick={{ fill: "#555", fontSize: 11 }} axisLine={{ stroke: "rgba(255,255,255,0.06)" }} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: "#555", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#f5f5f5" radius={[3, 3, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
