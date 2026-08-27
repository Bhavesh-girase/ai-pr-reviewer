import type { Project } from '@/types/project'
import { Folder, GitBranch, Key, Clock, Calendar, ShieldCheck, GitCommit, Globe } from 'lucide-react'

interface RepositoryCardProps {
  project: Project
}

export default function RepositoryCard({ project }: RepositoryCardProps) {
  const owner = project.github_owner || project.repoOwner || 'owner'
  const repo = project.github_repository || project.repoName || 'repo'
  const branch = project.default_branch || project.defaultBranch || 'main'
  const authType = project.auth_type || project.authType || 'connected_account'
  const commitHash = project.current_commit_hash ? project.current_commit_hash.slice(0, 7) : 'HEAD'

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Never'
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/45 p-5 space-y-4 shadow-sm">
      <div className="flex items-center gap-2 border-b border-zinc-900 pb-3">
        <Folder className="h-4.5 w-4.5 text-indigo-400" />
        <h3 className="text-sm font-semibold text-white">Repository Connection</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Repository</span>
          <p className="text-white font-mono font-semibold">{repo}</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Owner</span>
          <p className="text-white font-mono font-semibold">{owner}</p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Default Branch</span>
          <p className="text-white font-mono font-semibold flex items-center gap-1.5">
            <GitBranch className="h-3.5 w-3.5 text-zinc-500" />
            <span>{branch}</span>
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Visibility</span>
          <p className="text-white font-semibold flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5 text-emerald-400" />
            <span>Public Repository</span>
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Authentication</span>
          <p className="text-white font-semibold flex items-center gap-1.5">
            {authType === 'custom_token' ? (
              <>
                <Key className="h-3.5 w-3.5 text-amber-400" />
                <span>Custom GitHub Token</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                <span>Connected Account</span>
              </>
            )}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Current Commit</span>
          <p className="text-emerald-400 font-mono font-semibold flex items-center gap-1.5">
            <GitCommit className="h-3.5 w-3.5 text-emerald-400" />
            <span>{commitHash}</span>
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Last Indexed</span>
          <p className="text-zinc-300 flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-zinc-500" />
            <span>{formatDate(project.last_indexed_at || project.lastSyncTime)}</span>
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-[10px] uppercase font-bold text-zinc-500">Last Synced</span>
          <p className="text-zinc-300 flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-zinc-500" />
            <span>{formatDate(project.last_synced_at || project.lastSyncTime)}</span>
          </p>
        </div>
      </div>
    </div>
  )
}
