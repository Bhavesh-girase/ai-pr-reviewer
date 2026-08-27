import type { Project } from '@/types/project'
import { Activity, CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react'

interface HealthCardProps {
  project: Project
}

export default function HealthCard({ project }: HealthCardProps) {
  const isReady = project.status === 'READY'
  const isPending = ['CREATING', 'CLONING', 'INDEXING'].includes(project.status)

  const overallHealth = isReady ? 'Healthy' : isPending ? 'Degraded (Provisioning)' : 'Requires Attention'
  const healthVariant = isReady ? 'emerald' : isPending ? 'amber' : 'red'

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-4 shadow-sm">
      <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4.5 w-4.5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Workspace Health</h3>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
            healthVariant === 'emerald'
              ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
              : healthVariant === 'amber'
              ? 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
              : 'bg-red-950/60 text-red-400 border border-red-800/60'
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${healthVariant === 'emerald' ? 'bg-emerald-400' : healthVariant === 'amber' ? 'bg-amber-400 animate-pulse' : 'bg-red-400'}`}></span>
          <span>{overallHealth}</span>
        </span>
      </div>

      <div className="space-y-2.5 text-xs">
        <div className="flex items-center justify-between py-1 border-b border-zinc-900/60">
          <span className="text-zinc-400">Repository Tunnel</span>
          <span className="flex items-center gap-1.5 font-medium text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Connected</span>
          </span>
        </div>

        <div className="flex items-center justify-between py-1 border-b border-zinc-900/60">
          <span className="text-zinc-400">GitHub Authentication</span>
          <span className="flex items-center gap-1.5 font-medium text-emerald-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>Verified</span>
          </span>
        </div>

        <div className="flex items-center justify-between py-1 border-b border-zinc-900/60">
          <span className="text-zinc-400">Vector Index Engine</span>
          {isReady ? (
            <span className="flex items-center gap-1.5 font-medium text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>ChromaDB Ready</span>
            </span>
          ) : isPending ? (
            <span className="flex items-center gap-1.5 font-medium text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5 animate-pulse" />
              <span>Indexing Code...</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 font-medium text-red-400">
              <XCircle className="h-3.5 w-3.5" />
              <span>Index Error</span>
            </span>
          )}
        </div>

        <div className="flex items-center justify-between py-1 border-b border-zinc-900/60">
          <span className="text-zinc-400">AI Review Pipeline</span>
          <span className="flex items-center gap-1.5 font-medium text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Operational</span>
          </span>
        </div>
      </div>
    </div>
  )
}
