import React from 'react'
import { Skeleton } from '@/components/ui/skeleton'

export const PullRequestListSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="space-y-3 animate-fade-in">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-zinc-850 bg-zinc-950/40 p-4 space-y-3 text-left"
        >
          {/* Header */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-4 w-10" />
              <Skeleton className="h-3 w-20" />
            </div>
            <Skeleton className="h-4 w-4 rounded" />
          </div>

          {/* Title */}
          <Skeleton className="h-5 w-3/4" />

          {/* Author & branch */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded-full" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-5 w-44 rounded" />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-2 border-t border-zinc-900">
            <div className="flex items-center gap-3">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-7 w-24 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  )
}
