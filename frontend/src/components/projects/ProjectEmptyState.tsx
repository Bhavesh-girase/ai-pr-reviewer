import { Plus, FolderPlus, Layers, GitBranch, ShieldCheck } from 'lucide-react'

interface ProjectEmptyStateProps {
  onCreateProject: () => void
}

export default function ProjectEmptyState({ onCreateProject }: ProjectEmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/40 p-8 md:p-12 text-center flex flex-col items-center justify-center min-h-[380px] animate-fade-in select-none">
      {/* Modern SaaS visual illustration block */}
      <div className="relative mb-6">
        <div className="h-16 w-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-white shadow-xl">
          <FolderPlus className="h-8 w-8 text-indigo-400" />
        </div>
        <div className="absolute -bottom-2 -right-2 h-7 w-7 rounded-lg bg-zinc-950 border border-zinc-800 flex items-center justify-center text-emerald-400 shadow-md">
          <GitBranch className="h-4 w-4" />
        </div>
        <div className="absolute -top-2 -left-2 h-6 w-6 rounded-lg bg-zinc-950 border border-zinc-800 flex items-center justify-center text-amber-400 shadow-md">
          <ShieldCheck className="h-3.5 w-3.5" />
        </div>
      </div>

      <h2 className="text-xl font-bold text-white tracking-tight">No projects yet</h2>
      <p className="text-xs text-zinc-400 mt-2 max-w-md leading-relaxed">
        Projects are the central hub for repository registration, webhook management, automated PR updates, and AI code reviews.
      </p>

      {/* Feature pill list */}
      <div className="flex flex-wrap items-center justify-center gap-3 mt-6 mb-8 text-[11px] font-medium text-zinc-400">
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/60 border border-zinc-800">
          <Layers className="h-3 w-3 text-indigo-400" />
          <span>Multi-Repo Support</span>
        </span>
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/60 border border-zinc-800">
          <GitBranch className="h-3 w-3 text-emerald-400" />
          <span>Branch Sync</span>
        </span>
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900/60 border border-zinc-800">
          <ShieldCheck className="h-3 w-3 text-amber-400" />
          <span>AI PR Reviews</span>
        </span>
      </div>

      <button
        onClick={onCreateProject}
        className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-xs font-bold text-zinc-950 hover:bg-zinc-200 transition-all shadow-lg hover:shadow-indigo-500/10 cursor-pointer"
      >
        <Plus className="h-4 w-4" />
        <span>Create Your First Project</span>
      </button>
    </div>
  )
}
