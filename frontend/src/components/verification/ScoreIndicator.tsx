"use client"

import { cn } from "@/lib/utils"

interface ScoreIndicatorProps {
  score: number
  label: string
  className?: string
}

export default function ScoreIndicator({ score, label, className }: ScoreIndicatorProps) {
  const circumference = 2 * Math.PI * 42
  const offset = circumference - (score / 100) * circumference

  return (
    <div className={cn("flex flex-col items-center gap-3", className)}>
      <div className="relative w-24 h-24">
        <svg width="96" height="96" className="transform -rotate-90">
          <circle cx="48" cy="48" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
          <circle
            cx="48"
            cy="48"
            r="42"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="text-white transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-semibold text-text">{score}</span>
        </div>
      </div>
      <span className="text-xs text-text-muted">{label}</span>
    </div>
  )
}
