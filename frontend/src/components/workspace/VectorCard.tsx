import type { Project } from '@/types/project'
import { Database, CheckCircle2, Clock, ShieldCheck, Layers, FileCode } from 'lucide-react'

interface VectorCardProps {
  project: Project
}

export default function VectorCard({ project }: VectorCardProps) {
  const isIndexed = project.status === 'READY'

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Not indexed yet'
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
        <div className="flex items-center gap-2">
          <Database className="h-4.5 w-4.5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Vector Search Index</h3>
        </div>
        {isIndexed ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="h-3 w-3" />
            <span>Indexed</span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/60">
            <Clock className="h-3 w-3 animate-pulse" />
            <span>Processing</span>
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <FileCode className="h-3 w-3 text-indigo-400" />
            <span>Indexed Code Files</span>
          </span>
          <p className="text-white font-mono font-semibold">{isIndexed ? 'Complete Workspace' : 'Processing...'}</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <Layers className="h-3 w-3 text-emerald-400" />
            <span>Chunking Strategy</span>
          </span>
          <p className="text-white font-semibold">AST & Token Chunker</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-cyan-400" />
            <span>Collection Isolation</span>
          </span>
          <p className="text-white font-semibold">Multi-Tenant UUID Scoped</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Collection Health</span>
          <p className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
            <span>Persisted & Synchronized</span>
          </p>
        </div>

        <div className="space-y-1 sm:col-span-2">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Last Index Synchronization</span>
          <p className="text-zinc-300 flex items-center gap-1.5 font-mono">
            <Clock className="h-3.5 w-3.5 text-zinc-500" />
            <span>{formatDate(project.last_indexed_at || project.last_synced_at)}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
