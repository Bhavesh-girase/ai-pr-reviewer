import type { Project } from '@/types/project'
import { Terminal, HardDrive, Database, GitCommit, ShieldAlert, FileText } from 'lucide-react'

interface DeveloperPanelProps {
  project: Project
}

export default function DeveloperPanel({ project }: DeveloperPanelProps) {
  return (
    <div className="rounded-xl border border-amber-900/60 bg-amber-950/10 p-6 space-y-5 animate-fade-in shadow-lg">
      <div className="flex items-center justify-between border-b border-amber-900/40 pb-3">
        <div className="flex items-center gap-2">
          <Terminal className="h-4.5 w-4.5 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">Developer Diagnostics & Filesystem Info</h3>
        </div>
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase">
          Developer Mode ON
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <FileText className="h-3 w-3 text-amber-400" />
            <span>Project UUID</span>
          </span>
          <p className="text-amber-200 bg-zinc-950/80 p-2 rounded border border-zinc-800 text-[11px] truncate select-all">
            {project.id}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <GitCommit className="h-3 w-3 text-emerald-400" />
            <span>Full Commit SHA-1 Hash</span>
          </span>
          <p className="text-emerald-300 bg-zinc-950/80 p-2 rounded border border-zinc-800 text-[11px] truncate select-all">
            {project.current_commit_hash || 'N/A'}
          </p>
        </div>

        <div className="space-y-1 md:col-span-2">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <HardDrive className="h-3 w-3 text-indigo-400" />
            <span>Absolute Repository Clone Path</span>
          </span>
          <p className="text-zinc-200 bg-zinc-950/80 p-2 rounded border border-zinc-800 text-[11px] truncate select-all">
            {project.clone_path || 'Not cloned'}
          </p>
        </div>

        <div className="space-y-1 md:col-span-2">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Database className="h-3 w-3 text-cyan-400" />
            <span>Absolute Chroma Vector Store Path</span>
          </span>
          <p className="text-zinc-200 bg-zinc-950/80 p-2 rounded border border-zinc-800 text-[11px] truncate select-all">
            {project.chroma_path || 'Not indexed'}
          </p>
        </div>
      </div>

      {project.error_message && (
        <div className="p-3 rounded bg-red-950/40 border border-red-900 text-xs text-red-300 space-y-1 font-mono">
          <div className="flex items-center gap-1.5 font-bold text-red-400">
            <ShieldAlert className="h-4 w-4" />
            <span>Raw Provisioning Traceback</span>
          </div>
          <p className="text-[11px] leading-relaxed select-all">{project.error_message}</p>
        </div>
      )}
    </div>
  )
}
