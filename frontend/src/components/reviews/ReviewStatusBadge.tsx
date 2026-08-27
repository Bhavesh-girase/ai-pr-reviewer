import React from 'react'
import type { ReviewStatus } from '@/types/review'
import { CheckCircle2, Loader2, AlertCircle, Clock } from 'lucide-react'

interface ReviewStatusBadgeProps {
  status: ReviewStatus
  className?: string
}

export const ReviewStatusBadge: React.FC<ReviewStatusBadgeProps> = ({ status, className = '' }) => {
  const normalized = (status || 'QUEUED').toUpperCase()

  switch (normalized) {
    case 'COMPLETED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 ${className}`}
        >
          <CheckCircle2 className="h-3 w-3 text-emerald-400" />
          <span>Completed</span>
        </span>
      )
    case 'RUNNING':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 ${className}`}
        >
          <Loader2 className="h-3 w-3 text-indigo-400 animate-spin" />
          <span>Running</span>
        </span>
      )
    case 'FAILED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 ${className}`}
        >
          <AlertCircle className="h-3 w-3 text-red-400" />
          <span>Failed</span>
        </span>
      )
    case 'QUEUED':
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-zinc-800/80 text-zinc-400 border border-zinc-700/50 ${className}`}
        >
          <Clock className="h-3 w-3 text-zinc-400" />
          <span>Queued</span>
        </span>
      )
  }
}
