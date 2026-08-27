import type { Project } from '@/types/project'
import { Badge } from '@/components/ui/badge'
import { DropdownMenu, DropdownMenuItem } from '@/components/ui/dropdown-menu'
import {
  Folder,
  GitBranch,
  MoreVertical,
  ExternalLink,
  Pencil,
  Trash2,
  Clock,
  Calendar,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Key,
  ShieldCheck,
  GitCommit,
  Loader2,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface ProjectCardProps {
  project: Project
  onEdit: (project: Project) => void
  onDelete: (project: Project) => void
}

export default function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
  const navigate = useNavigate()

  const projectName = project.project_name || project.name || 'Untitled Project'
  const owner = project.github_owner || project.repoOwner || 'owner'
  const repo = project.github_repository || project.repoName || 'repo'
  const branch = project.default_branch || project.defaultBranch || 'main'
  const authType = project.auth_type || project.authType || 'connected_account'
  const commitHash = project.current_commit_hash ? project.current_commit_hash.slice(0, 7) : null

  // Format date helper
  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Never'
    try {
      const d = new Date(isoString)
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      }).format(d)
    } catch {
      return isoString
    }
  }

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

  // Provisioning Status Badge mapping
  const renderStatusBadge = () => {
    switch (project.status) {
      case 'READY':
        return (
          <Badge variant="success">
            <CheckCircle2 className="h-3 w-3" />
            <span>Ready</span>
          </Badge>
        )
      case 'CLONING':
        return (
          <Badge variant="warning">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Cloning Repo</span>
          </Badge>
        )
      case 'INDEXING':
        return (
          <Badge variant="info">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Indexing Code</span>
          </Badge>
        )
      case 'CREATING':
        return (
          <Badge variant="secondary">
            <Clock className="h-3 w-3 animate-pulse" />
            <span>Provisioning</span>
          </Badge>
        )
      case 'FAILED':
      default:
        return (
          <Badge variant="destructive" title={project.error_message || 'Provisioning failed'}>
            <AlertCircle className="h-3 w-3" />
            <span>Provisioning Failed</span>
          </Badge>
        )
    }
  }

  return (
    <div className="group relative rounded-xl border border-zinc-800 bg-zinc-950/60 p-5 hover:border-zinc-700 hover:bg-zinc-900/40 transition-all duration-200 shadow-sm flex flex-col justify-between">
      {/* Top row: Name & Actions */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="h-9 w-9 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300 group-hover:border-zinc-700 group-hover:text-white transition-colors shrink-0">
              <Folder className="h-4.5 w-4.5" />
            </div>
            <div className="overflow-hidden">
              <h3
                onClick={() => navigate(`/projects/${project.id}`)}
                className="text-sm font-bold text-white tracking-tight truncate hover:underline cursor-pointer"
              >
                {projectName}
              </h3>
              <p className="text-xs text-zinc-400 font-mono truncate mt-0.5">
                {owner}/{repo}
              </p>
            </div>
          </div>

          <DropdownMenu
            trigger={
              <button
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors border border-transparent hover:border-zinc-700 cursor-pointer"
                aria-label="Project actions"
              >
                <MoreVertical className="h-4 w-4" />
              </button>
            }
          >
            <DropdownMenuItem onClick={() => navigate(`/projects/${project.id}`)}>
              <ExternalLink className="h-3.5 w-3.5" />
              <span>Open Project</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onEdit(project)}>
              <Pencil className="h-3.5 w-3.5" />
              <span>Edit Details</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onDelete(project)} destructive>
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete Project</span>
            </DropdownMenuItem>
          </DropdownMenu>
        </div>

        {/* Status badges */}
        <div className="flex flex-wrap items-center gap-2 mt-4">
          {renderStatusBadge()}

          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-zinc-900/80 border border-zinc-800 text-zinc-400">
            {authType === 'custom_token' ? (
              <>
                <Key className="h-3 w-3 text-amber-400" />
                <span>Custom Token</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-3 w-3 text-indigo-400" />
                <span>Connected Account</span>
              </>
            )}
          </span>

          {commitHash && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono text-zinc-300 bg-zinc-900/60 border border-zinc-800">
              <GitCommit className="h-3 w-3 text-emerald-400" />
              <span>{commitHash}</span>
            </span>
          )}
        </div>
      </div>

      {/* Error detail if status == FAILED */}
      {project.status === 'FAILED' && project.error_message && (
        <div className="mt-3 p-2 rounded bg-red-950/30 border border-red-900/50 text-[11px] text-red-300 truncate">
          {project.error_message}
        </div>
      )}

      {/* Footer details: Branch, Sync time, Created date */}
      <div className="mt-5 pt-4 border-t border-zinc-900/80 flex flex-wrap items-center justify-between gap-3 text-[11px] text-zinc-400">
        <div className="flex items-center gap-1.5 font-mono text-zinc-300">
          <GitBranch className="h-3.5 w-3.5 text-zinc-500" />
          <span>{branch}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1" title="Last Indexed Time">
            <Clock className="h-3 w-3 text-zinc-500" />
            <span>Indexed: {formatRelativeTime(project.last_indexed_at || project.last_synced_at)}</span>
          </div>
          <div className="flex items-center gap-1" title="Created Date">
            <Calendar className="h-3 w-3 text-zinc-500" />
            <span>{formatDate(project.created_at || project.createdAt)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
