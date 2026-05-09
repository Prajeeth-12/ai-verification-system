"use client"

import { useState, useCallback, useRef } from "react"
import { Upload, FileText, X, Loader2, AlertCircle } from "lucide-react"
import { cn, formatFileSize } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"
import { uploadDocument } from "@/lib/api"
import type { UploadedFile, FileStatus } from "@/types"

interface UploadZoneProps {
  onUploadComplete?: (files: UploadedFile[]) => void
  className?: string
}

export default function UploadZone({ onUploadComplete, className }: UploadZoneProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const addFiles = useCallback((fileList: FileList | File[]) => {
    const newFiles: UploadedFile[] = Array.from(fileList)
      .filter((f) => /\.(pdf|png|jpe?g)$/i.test(f.name))
      .map((file) => ({
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        type: file.type,
        status: "selected" as FileStatus,
        progress: 0,
        file,
      }))
    if (newFiles.length) setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const removeFile = (id: string) => setFiles((prev) => prev.filter((f) => f.id !== id))
  const clearFiles = () => setFiles([])

  const uploadFiles = useCallback(async () => {
    if (!files.length || isUploading) return
    setIsUploading(true)

    for (const file of files) {
      if (file.status === "uploaded") continue
      setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, status: "uploading" } : f)))
      try {
        await uploadDocument(file.file, (progress) =>
          setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, progress } : f)))
        )
        setFiles((prev) => prev.map((f) => (f.id === file.id ? { ...f, status: "uploaded", progress: 100 } : f)))
      } catch (err) {
        setFiles((prev) =>
          prev.map((f) => (f.id === file.id ? { ...f, status: "error", error: err instanceof Error ? err.message : "Upload failed" } : f))
        )
      }
    }

    setIsUploading(false)
    onUploadComplete?.(files.filter((f) => f.status === "uploaded"))
  }, [files, isUploading, onUploadComplete])

  const hasUploadedFiles = files.some((f) => f.status === "uploaded")

  return (
    <div className={cn("space-y-3", className)}>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setIsDragOver(false); addFiles(e.dataTransfer.files) }}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "rounded-lg border border-dashed transition-colors cursor-pointer",
          isDragOver ? "border-white/40 bg-white/5" : "border-border hover:border-white/30"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg"
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <div className="flex items-center gap-4 px-5 py-4">
          <div className="p-2 rounded-md bg-card border border-border">
            <Upload className="w-4 h-4 text-text-muted" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text">
              {isDragOver ? "Drop files to upload" : "Upload documents"}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              PDF, PNG, or JPG — drag files here or click to browse
            </p>
          </div>
          <span className="text-xs text-text-muted whitespace-nowrap">PDF · PNG · JPG</span>
        </div>
      </div>

      {files.length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="flex items-center justify-between px-4 h-9 border-b border-border">
            <p className="text-xs text-text-muted">{files.length} file{files.length > 1 ? "s" : ""}</p>
            <button onClick={clearFiles} className="text-xs text-text-muted hover:text-text transition-colors">
              Clear
            </button>
          </div>

          <div className="divide-y divide-border">
            {files.map((file) => (
              <div key={file.id} className="flex items-center gap-3 px-4 py-2.5 group hover:bg-card-hover transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-text-muted flex-shrink-0" />
                    <span className="text-sm text-text truncate">{file.name}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-text-muted">{formatFileSize(file.size)}</span>
                    {file.status === "uploading" && (
                      <span className="text-xs text-accent">{file.progress}%</span>
                    )}
                    {file.status === "error" && file.error && (
                      <span className="text-xs text-error">{file.error}</span>
                    )}
                    {file.status === "uploaded" && (
                      <span className="text-xs text-success">Uploaded</span>
                    )}
                  </div>
                  {file.status === "uploading" && <Progress value={file.progress} className="mt-1.5" />}
                </div>
                {file.status !== "uploading" && (
                  <button onClick={() => removeFile(file.id)} className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-border text-text-muted hover:text-text transition-all">
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
                {file.status === "uploading" && <Loader2 className="w-4 h-4 text-text-muted animate-spin" />}
              </div>
            ))}
          </div>

          {!hasUploadedFiles && (
            <div className="px-4 py-3 border-t border-border">
              <button
                onClick={uploadFiles}
                disabled={isUploading}
                className="w-full h-9 rounded-md bg-white text-black text-sm font-medium hover:bg-white/90 disabled:opacity-40 transition-colors"
              >
                {isUploading ? "Uploading..." : "Upload"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
