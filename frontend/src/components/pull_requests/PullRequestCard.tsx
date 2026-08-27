import React from 'react'
import { useNavigate } from 'react-router-dom'
import type { PullRequest } from '@/types/pullRequest'
import { PullRequestStatusBadge } from './PullRequestStatusBadge'
import {
  GitBranch,
  FileCode2,
  MessageSquare,
  Sparkles,
  ExternalLink,
  Clock,
  ArrowRight,
} from 'lucide-react'

interface PullRequestCardProps {
  projectId: string
  pr: PullRequest
  onReviewClick?: (pr: PullRequest) => void
}

export const PullRequestCard: React.FC<PullRequestCardProps> = ({
  projectId,
  pr,
  onReviewClick,
}) => {
  const navigate = useNavigate()

  const handleCardClick = (e: React.MouseEvent) => {
    // Avoid routing if user clicked direct interactive sub-buttons
    if ((e.target as HTMLElement).closest('a, button')) return
    navigate(`/projects/${projectId}/pull-requests/${pr.number}`)
  }

  const formatTimeAgo = (dateStr: string | null) => {
    if (!dateStr) return 'unknown'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays === 1) return 'yesterday'
    if (diffDays < 30) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div
      onClick={handleCardClick}
      className="group relative rounded-xl border border-zinc-850 bg-zinc-950/40 p-4 hover:border-zinc-700 hover:bg-zinc-900/30 transition-all duration-200 cursor-pointer shadow-sm flex flex-col justify-between gap-3 text-left"
    >
      {/* Top Header: Title, Number, Status Badge */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <PullRequestStatusBadge state={pr.state} />
            <span className="font-mono text-xs font-bold text-zinc-500 group-hover:text-indigo-400 transition-colors">
              #{pr.number}
            </span>
            <span className="text-[11px] text-zinc-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span>{formatTimeAgo(pr.created_at)}</span>
            </span>
          </div>

          <h4 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition-colors leading-snug line-clamp-2">
            {pr.title}
          </h4>
        </div>

        {/* Quick External Link to GitHub */}
        <a
          href={pr.html_url}
          target="_blank"
          rel="noreferrer"
          title="Open in GitHub"
          className="p-1 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 rounded-md transition-colors shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      {/* Middle: Author & Branches */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-400 pt-1">
        {/* Author info */}
        <div className="flex items-center gap-1.5">
          {pr.author.avatar_url ? (
            <img
              src={pr.author.avatar_url}
              alt={pr.author.login}
              className="h-4 w-4 rounded-full border border-zinc-700 object-cover"
            />
          ) : (
            <div className="h-4 w-4 rounded-full bg-zinc-800 flex items-center justify-center text-[9px] text-zinc-300 font-bold">
              {pr.author.login.charAt(0).toUpperCase()}
            </div>
          )}
          <span className="text-zinc-300 font-medium">{pr.author.login}</span>
        </div>

        {/* Branch flow */}
        <div className="flex items-center gap-1.5 font-mono text-[11px] bg-zinc-900/90 border border-zinc-800/80 px-2 py-0.5 rounded-md text-zinc-400">
          <GitBranch className="h-3 w-3 text-zinc-500" />
          <span className="text-zinc-300 truncate max-w-[120px]">{pr.source_branch}</span>
          <span className="text-zinc-600">→</span>
          <span className="text-zinc-400 truncate max-w-[100px]">{pr.target_branch}</span>
        </div>
      </div>

      {/* Bottom Footer: Stats + Action Buttons */}
      <div className="flex items-center justify-between gap-2 pt-2 border-t border-zinc-900/80 text-xs">
        {/* Diff Stats & Changed Files */}
        <div className="flex items-center gap-3 text-zinc-400 font-mono text-[11px]">
          {/* Additions / Deletions */}
          {(pr.additions > 0 || pr.deletions > 0) && (
            <div className="flex items-center gap-1">
              <span className="text-emerald-400 font-bold">+{pr.additions}</span>
              <span className="text-red-400 font-bold">-{pr.deletions}</span>
            </div>
          )}

          {/* Files Changed */}
          {pr.changed_files_count > 0 && (
            <div className="flex items-center gap-1 text-zinc-400" title={`${pr.changed_files_count} files changed`}>
              <FileCode2 className="h-3 w-3 text-zinc-500" />
              <span>{pr.changed_files_count}</span>
            </div>
          )}

          {/* Comments */}
          {pr.comments_count > 0 && (
            <div className="flex items-center gap-1 text-zinc-400" title={`${pr.comments_count} comments`}>
              <MessageSquare className="h-3 w-3 text-zinc-500" />
              <span>{pr.comments_count}</span>
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-2">
          {onReviewClick ? (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onReviewClick(pr)
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 text-xs font-semibold transition-all cursor-pointer shadow-sm hover:scale-[1.02]"
            >
              <Sparkles className="h-3 w-3 text-indigo-400" />
              <span>Review PR</span>
            </button>
          ) : (
            <button
              onClick={() => navigate(`/projects/${projectId}/pull-requests/${pr.number}`)}
              className="inline-flex items-center gap-1 text-xs font-semibold text-zinc-400 group-hover:text-white transition-colors cursor-pointer"
            >
              <span>Inspect</span>
              <ArrowRight className="h-3.5 w-3.5 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
