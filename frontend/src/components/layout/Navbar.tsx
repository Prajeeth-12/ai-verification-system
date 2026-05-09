"use client"

import { Search, Bell, User } from "lucide-react"

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 h-14 border-b border-border bg-bg/80 backdrop-blur-md flex items-center justify-between px-6">
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <Search className="w-4 h-4 text-text-muted" />
        <input
          type="text"
          placeholder="Search documents..."
          className="flex-1 bg-transparent text-sm text-text placeholder:text-text-muted outline-none"
        />
      </div>
      <div className="flex items-center gap-2">
        <button className="relative p-2 rounded-md hover:bg-card transition-colors text-text-muted hover:text-text">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-accent" />
        </button>
        <div className="flex items-center gap-2.5 ml-2 pl-3 border-l border-border">
          <div className="text-right">
            <p className="text-sm text-text">Prajeeth</p>
            <p className="text-xs text-text-muted">Admin</p>
          </div>
          <div className="w-8 h-8 rounded-md bg-card border border-border flex items-center justify-center">
            <User className="w-4 h-4 text-text-muted" />
          </div>
        </div>
      </div>
    </header>
  )
}
