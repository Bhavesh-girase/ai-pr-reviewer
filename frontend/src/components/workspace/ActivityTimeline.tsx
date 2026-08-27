import type { Project } from '@/types/project'
import { Activity, CheckCircle2, Zap, GitBranch, RefreshCw, AlertTriangle, Loader2 } from 'lucide-react'

interface ActivityTimelineProps {
  project: Project
}

export default function ActivityTimeline({ project }: ActivityTimelineProps) {
  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Just now'
    try {
      return new Date(isoString).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return String(isoString)
    }
  }

  const isReady = project.status === 'READY'
  const isSyncing = project.sync_status === 'SYNCING'
  const isSyncFailed = project.sync_status === 'SYNC_FAILED'
  const hasSyncHistory = Boolean(project.last_sync_completed_at && project.last_sync_completed_at !== project.created_at)

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/20 p-6 space-y-4 shadow-sm text-left">
      <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4.5 w-4.5 text-zinc-400" />
          <h3 className="text-sm font-semibold text-white">Activity Timeline</h3>
        </div>
        <span className="text-[11px] font-mono text-zinc-500">Live Event Feed</span>
      </div>

      <div className="flow-root">
        <ul className="-mb-8">
          {/* Event 1: Workspace Created */}
          <li>
            <div className="relative pb-8">
              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-zinc-800" aria-hidden="true" />
              <div className="relative flex space-x-3">
                <div>
                  <span className="h-8 w-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center ring-8 ring-zinc-950 text-indigo-400">
                    <CheckCircle2 className="h-4 w-4" />
                  </span>
                </div>
                <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                  <div>
                    <p className="text-xs text-zinc-300">
                      Workspace Created <span className="font-semibold text-white">"{project.project_name || project.name}"</span>
                    </p>
                  </div>
                  <div className="text-right text-[10px] whitespace-nowrap text-zinc-500 font-mono">
                    {formatDate(project.created_at)}
                  </div>
                </div>
              </div>
            </div>
          </li>

          {/* Event 2: Repository Cloned */}
          <li>
            <div className="relative pb-8">
              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-zinc-800" aria-hidden="true" />
              <div className="relative flex space-x-3">
                <div>
                  <span className="h-8 w-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center ring-8 ring-zinc-950 text-emerald-400">
                    <GitBranch className="h-4 w-4" />
                  </span>
                </div>
                <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                  <div>
                    <p className="text-xs text-zinc-300">
                      Repository Cloned <span className="font-mono text-zinc-400">({project.github_owner || project.repoOwner}/{project.github_repository || project.repoName})</span>
                    </p>
                  </div>
                  <div className="text-right text-[10px] whitespace-nowrap text-zinc-500 font-mono">
                    {formatDate(project.created_at)}
                  </div>
                </div>
              </div>
            </div>
          </li>

          {/* Event 3: Repository Initial Vector Indexing */}
          <li>
            <div className="relative pb-8">
              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-zinc-800" aria-hidden="true" />
              <div className="relative flex space-x-3">
                <div>
                  <span className="h-8 w-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center ring-8 ring-zinc-950 text-cyan-400">
                    <Zap className="h-4 w-4" />
                  </span>
                </div>
                <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                  <div>
                    <p className="text-xs text-zinc-300">
                      ChromaDB Vector Store Initialized & Indexed
                    </p>
                  </div>
                  <div className="text-right text-[10px] whitespace-nowrap text-zinc-500 font-mono">
                    {formatDate(project.last_indexed_at)}
                  </div>
                </div>
              </div>
            </div>
          </li>

          {/* Event 4: Active Sync in Progress */}
          {isSyncing && (
            <li>
              <div className="relative pb-8">
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-zinc-800" aria-hidden="true" />
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-zinc-900 border border-indigo-500/30 flex items-center justify-center ring-8 ring-zinc-950 text-indigo-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-xs text-indigo-300 font-medium">
                        Repository & ChromaDB Synchronization in progress...
                      </p>
                    </div>
                    <div className="text-right text-[10px] whitespace-nowrap text-indigo-400 font-mono">
                      {formatDate(project.last_sync_started_at)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          )}

          {/* Event 5: Sync Failed */}
          {isSyncFailed && (
            <li>
              <div className="relative pb-8">
                <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-zinc-800" aria-hidden="true" />
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-zinc-900 border border-red-500/30 flex items-center justify-center ring-8 ring-zinc-950 text-red-400">
                      <AlertTriangle className="h-4 w-4" />
                    </span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-xs text-red-300 font-medium">
                        Repository Sync Failed: {project.sync_error_message || 'Check connection/credentials'}
                      </p>
                    </div>
                    <div className="text-right text-[10px] whitespace-nowrap text-red-400 font-mono">
                      {formatDate(project.last_sync_completed_at)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          )}

          {/* Event 6: Incremental Synchronization Completed */}
          {hasSyncHistory && !isSyncing && (
            <li>
              <div className="relative pb-8">
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-zinc-900 border border-emerald-500/30 flex items-center justify-center ring-8 ring-zinc-950 text-emerald-400">
                      <RefreshCw className="h-4 w-4" />
                    </span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-xs text-zinc-300">
                        Incremental Git & ChromaDB Synchronization Completed{' '}
                        {project.current_commit_hash && (
                          <span className="font-mono text-zinc-400">({project.current_commit_hash.slice(0, 7)})</span>
                        )}
                      </p>
                    </div>
                    <div className="text-right text-[10px] whitespace-nowrap text-zinc-500 font-mono">
                      {formatDate(project.last_sync_completed_at || project.last_synced_at)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          )}

          {/* Event 7: Initial Workspace Provisioned (if no later sync) */}
          {!hasSyncHistory && isReady && (
            <li>
              <div className="relative pb-8">
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center ring-8 ring-zinc-950 text-emerald-400">
                      <RefreshCw className="h-4 w-4" />
                    </span>
                  </div>
                  <div className="flex-1 min-w-0 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p className="text-xs text-zinc-300">
                        Workspace Provisioned & Ready
                      </p>
                    </div>
                    <div className="text-right text-[10px] whitespace-nowrap text-zinc-500 font-mono">
                      {formatDate(project.last_synced_at || project.created_at)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
