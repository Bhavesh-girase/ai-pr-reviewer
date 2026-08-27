import React from 'react'
import { Link } from 'react-router-dom'
import type { ReviewItem } from '@/types/review'
import { ReviewStatusBadge } from './ReviewStatusBadge'
import {
  ChevronRight,
  Clock,
  FileCode,
  AlertTriangle,
  GitCommit,
  Bot,
  ArrowUpRight,
} from 'lucide-react'

interface ReviewCardProps {
  review: ReviewItem
  projectId: string
}

export const ReviewCard: React.FC<ReviewCardProps> = ({ review, projectId }) => {
  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Just now'
    try {
      return new Date(isoString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return String(isoString)
    }
  }

  const durationSec = review.review_duration_ms ? (review.review_duration_ms / 1000).toFixed(1) : null

  return (
    <div className="group rounded-xl border border-zinc-800/80 bg-zinc-950/40 hover:bg-zinc-900/40 hover:border-zinc-700/80 p-5 transition-all space-y-4 shadow-sm text-left">
      {/* Header row: PR Number + Title, Status, and Link */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <Link
            to={`/projects/${projectId}/pull-requests/${review.github_pr_number}`}
            className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-indigo-400 hover:text-indigo-300 bg-indigo-950/30 border border-indigo-500/20 px-2 py-0.5 rounded-md transition-colors"
          >
            <span>PR #{review.github_pr_number}</span>
            <ArrowUpRight className="h-3 w-3" />
          </Link>

          <ReviewStatusBadge status={review.status} />

          {review.pr_title && (
            <h4 className="text-sm font-semibold text-white truncate max-w-md">
              {review.pr_title}
            </h4>
          )}
        </div>

        <Link
          to={`/projects/${projectId}/reviews/${review.id}`}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-zinc-900 group-hover:bg-indigo-600 border border-zinc-800 group-hover:border-indigo-500 text-xs font-semibold text-zinc-300 group-hover:text-white transition-all self-start sm:self-auto cursor-pointer"
        >
          <span>Open Review</span>
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Summary preview */}
      {review.summary ? (
        <p className="text-xs text-zinc-300 leading-relaxed line-clamp-2">
          {review.summary}
        </p>
      ) : review.error_message ? (
        <p className="text-xs text-red-400/90 leading-relaxed font-mono">
          {review.error_message}
        </p>
      ) : (
        <p className="text-xs text-zinc-500 italic">No summary recorded for this review.</p>
      )}

      {/* Metrics & Metadata Grid Strip */}
      <div className="flex items-center gap-4 flex-wrap text-xs text-zinc-400 pt-1 border-t border-zinc-900">
        {/* Severity counts */}
        <div className="flex items-center gap-1.5 font-mono text-[11px]">
          <AlertTriangle className="h-3.5 w-3.5 text-zinc-500" />
          <span className="font-bold text-white">{review.issues_count} Issues:</span>
          {review.high_count > 0 && (
            <span className="text-red-400 font-semibold">{review.high_count} High</span>
          )}
          {review.medium_count > 0 && (
            <span className="text-amber-400 font-semibold">{review.medium_count} Med</span>
          )}
          {review.low_count > 0 && (
            <span className="text-blue-400 font-semibold">{review.low_count} Low</span>
          )}
          {review.issues_count === 0 && (
            <span className="text-emerald-400 font-semibold">0 Clean</span>
          )}
        </div>

        {/* Files reviewed */}
        {review.files_reviewed > 0 && (
          <div className="flex items-center gap-1 font-mono text-[11px] text-zinc-400">
            <FileCode className="h-3.5 w-3.5 text-zinc-500" />
            <span>{review.files_reviewed} files</span>
          </div>
        )}

        {/* Duration */}
        {durationSec && (
          <div className="flex items-center gap-1 font-mono text-[11px] text-zinc-400">
            <Clock className="h-3.5 w-3.5 text-zinc-500" />
            <span>{durationSec}s</span>
          </div>
        )}

        {/* Model */}
        {review.model_name && (
          <div className="flex items-center gap-1 text-[11px] text-zinc-400">
            <Bot className="h-3.5 w-3.5 text-indigo-400" />
            <span>{review.model_name}</span>
          </div>
        )}

        {/* Commit Hash */}
        {review.head_commit_sha && (
          <div className="flex items-center gap-1 font-mono text-[11px] text-zinc-500">
            <GitCommit className="h-3.5 w-3.5 text-zinc-600" />
            <span>{review.head_commit_sha.slice(0, 7)}</span>
          </div>
        )}

        {/* Created timestamp */}
        <div className="ml-auto text-[11px] font-mono text-zinc-500">
          {formatDate(review.created_at)}
        </div>
      </div>
    </div>
  )
}
