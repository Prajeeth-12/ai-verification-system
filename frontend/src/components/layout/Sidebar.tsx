"use client"

import { cn } from "@/lib/utils"
import { LayoutDashboard, FileSearch, History, Settings, ChevronLeft } from "lucide-react"
import { useState } from "react"

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/", active: true },
  { icon: FileSearch, label: "Verify", href: "/verify", active: false },
  { icon: History, label: "History", href: "/history", active: false },
  { icon: Settings, label: "Settings", href: "/settings", active: false },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r border-border bg-bg flex flex-col transition-all duration-200",
        collapsed ? "w-[52px]" : "w-[200px]"
      )}
    >
      {/* Brand */}
      <div className="flex items-center justify-between px-3 h-12 border-b border-border">
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="w-6 h-6 rounded-[5px] bg-text flex items-center justify-center flex-shrink-0">
            <span className="text-bg text-[11px] font-bold tracking-tight">AV</span>
          </div>
          {!collapsed && (
            <span className="text-[13px] font-semibold text-text truncate">AI-Verify</span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded hover:bg-surface text-text-muted hover:text-text-secondary transition-colors flex-shrink-0 hidden lg:flex"
        >
          <ChevronLeft className={cn("w-3.5 h-3.5 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-1.5 space-y-0.5">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={cn(
              "flex items-center gap-2.5 w-full px-2.5 h-8 rounded-md text-[13px] transition-colors",
              item.active
                ? "bg-surface text-text font-medium"
                : "text-text-muted hover:text-text-secondary hover:bg-surface/50"
            )}
          >
            <item.icon className="w-[15px] h-[15px] flex-shrink-0" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Bottom */}
      {!collapsed && (
        <div className="p-2 border-t border-border">
          <div className="rounded-md bg-surface px-2.5 py-2">
            <p className="text-[10px] text-text-muted uppercase tracking-wider font-medium">Usage</p>
            <div className="flex items-baseline gap-1 mt-0.5">
              <span className="text-sm font-semibold text-text tabular-nums">1,240</span>
              <span className="text-[10px] text-text-muted">credits</span>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
