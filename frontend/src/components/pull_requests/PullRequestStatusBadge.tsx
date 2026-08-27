import React from 'react'
import type { PRState } from '@/types/pullRequest'
import { GitPullRequest, CheckCircle2, XCircle, FileCode } from 'lucide-react'

interface PullRequestStatusBadgeProps {
  state: PRState
  className?: string
  showIcon?: boolean
}

export const PullRequestStatusBadge: React.FC<PullRequestStatusBadgeProps> = ({
  state,
  className = '',
  showIcon = true,
}) => {
  switch (state) {
    case 'OPEN':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ${className}`}
        >
          {showIcon && <GitPullRequest className="h-3 w-3" />}
          <span>Open</span>
        </span>
      )
    case 'MERGED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 ${className}`}
        >
          {showIcon && <CheckCircle2 className="h-3 w-3" />}
          <span>Merged</span>
        </span>
      )
    case 'DRAFT':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700 border-dashed ${className}`}
        >
          {showIcon && <FileCode className="h-3 w-3" />}
          <span>Draft</span>
        </span>
      )
    case 'CLOSED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 ${className}`}
        >
          {showIcon && <XCircle className="h-3 w-3" />}
          <span>Closed</span>
        </span>
      )
  }
}
