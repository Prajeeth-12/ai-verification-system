"use client"

import { Search, Bell, User, Command } from "lucide-react"

export default function Topbar() {
  return (
    <header className="h-12 sticky top-0 z-30 flex items-center justify-between px-4 lg:px-6 bg-bg/80 backdrop-blur-md border-b border-border">
      {/* Search */}
      <div className="flex items-center flex-1">
        <div className="relative w-full max-w-[280px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full h-7 pl-8 pr-3 bg-surface border border-border rounded-md text-[13px] text-text placeholder:text-text-muted focus:outline-none focus:border-border-light transition-colors"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-0.5 px-1 py-[1px] border border-border rounded text-[10px] text-text-muted">
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        <button className="relative p-1.5 rounded-md hover:bg-surface text-text-muted hover:text-text-secondary transition-colors">
          <Bell className="w-3.5 h-3.5" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-success rounded-full" />
        </button>
        <div className="w-px h-4 bg-border mx-1 hidden sm:block" />
        <button className="flex items-center gap-2 p-1 rounded-md hover:bg-surface transition-colors">
          <div className="w-6 h-6 rounded-full bg-surface border border-border flex items-center justify-center">
            <User className="w-3 h-3 text-text-muted" />
          </div>
          <span className="text-[13px] text-text-secondary hidden sm:block">Admin</span>
        </button>
      </div>
    </header>
  )
}
