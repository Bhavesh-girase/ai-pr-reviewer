import type { Project } from '@/types/project'
import StatusBadge from './StatusBadge'
import {
  GitBranch,
  ExternalLink,
  RefreshCw,
  ArrowLeft,
  Globe,
  Code2,
} from 'lucide-react'

function GithubIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
    </svg>
  )
}

interface WorkspaceHeaderProps {
  project: Project
  onBack: () => void
  onSync: () => void
  isSyncing: boolean
}

export default function WorkspaceHeader({
  project,
  onBack,
  onSync,
  isSyncing,
}: WorkspaceHeaderProps) {
  const name = project.project_name || project.name || 'Untitled Project'
  const owner = project.github_owner || project.repoOwner || 'owner'
  const repo = project.github_repository || project.repoName || 'repo'
  const branch = project.default_branch || project.defaultBranch || 'main'

  const formatRelativeTime = (isoString?: string) => {
    if (!isoString) return 'Never'
    try {
      const now = new Date().getTime()
      const past = new Date(isoString).getTime()
      const diffMinutes = Math.floor((now - past) / (1000 * 60))

      if (diffMinutes < 1) return 'Just now'
      if (diffMinutes < 60) return `${diffMinutes}m ago`
      const diffHours = Math.floor(diffMinutes / 60)
      if (diffHours < 24) return `${diffHours}h ago`
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays}d ago`
    } catch {
      return isoString
    }
  }

  const lastSyncText = formatRelativeTime(project.last_synced_at || project.last_indexed_at)

  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-900 pb-6">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          {/* Owner Avatar */}
          <div className="h-9 w-9 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-white shadow-sm overflow-hidden shrink-0">
            <img
              src={`https://github.com/${owner}.png`}
              alt={owner}
              className="h-full w-full object-cover"
              onError={(e) => {
                // Fallback icon on error
                e.currentTarget.style.display = 'none'
              }}
            />
            <GithubIcon className="h-4.5 w-4.5 text-zinc-300" />
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white">{name}</h1>
              <StatusBadge status={project.status} errorMessage={project.error_message} />
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-900 border border-zinc-800 text-zinc-400">
                <Globe className="h-3 w-3 text-zinc-400" />
                <span>Public Repo</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 font-mono mt-1">
              <a
                href={`https://github.com/${owner}/${repo}`}
                target="_blank"
                rel="noreferrer"
                className="hover:underline hover:text-white flex items-center gap-1.5"
              >
                <span>{owner}/{repo}</span>
                <ExternalLink className="h-3 w-3 text-zinc-500" />
              </a>
              <span className="text-zinc-700">•</span>
              <span className="flex items-center gap-1 text-zinc-300">
                <GitBranch className="h-3.5 w-3.5 text-zinc-500" />
                <span>{branch}</span>
              </span>
              <span className="text-zinc-700">•</span>
              <span className="flex items-center gap-1 text-zinc-300">
                <Code2 className="h-3.5 w-3.5 text-indigo-400" />
                <span>Polyglot</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons & Sync indicator */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="text-[11px] text-zinc-400 font-mono hidden sm:block text-right">
          <span className="text-zinc-500">Last Sync:</span>{' '}
          <span className="text-zinc-300">{lastSyncText}</span>
        </div>

        <button
          onClick={onBack}
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2 text-xs font-semibold text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back</span>
        </button>

        <a
          href={`https://github.com/${owner}/${repo}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900 px-3.5 py-2 text-xs font-semibold text-zinc-200 hover:text-white hover:bg-zinc-800 transition-colors"
        >
          <GithubIcon className="h-3.5 w-3.5" />
          <span>Open on GitHub</span>
        </a>

        <button
          onClick={onSync}
          disabled={isSyncing}
          className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-white px-3.5 py-2 text-xs font-bold text-zinc-950 hover:bg-zinc-200 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Syncing...' : 'Sync Repository'}</span>
        </button>
      </div>
    </div>
  )
}
