import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import type { Project } from '@/types/project'
import type { ReviewFilterParams } from '@/types/review'
import { listProjectReviews } from '@/api/reviews'
import { ReviewCard } from './ReviewCard'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Sparkles,
  Search,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  GitPullRequest,
} from 'lucide-react'

interface ReviewListProps {
  project: Project
}

type TabStatus = 'ALL' | 'COMPLETED' | 'RUNNING' | 'FAILED'

export const ReviewList: React.FC<ReviewListProps> = ({ project }) => {
  const [activeStatus, setActiveStatus] = useState<TabStatus>('ALL')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [currentPage, setCurrentPage] = useState<number>(1)
  const perPage = 10

  const queryParams: ReviewFilterParams = {
    page: currentPage,
    per_page: perPage,
    status: activeStatus === 'ALL' ? undefined : activeStatus,
    search: searchQuery.trim() || undefined,
  }

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['projectReviews', project.id, queryParams],
    queryFn: () => listProjectReviews(project.id, queryParams),
    enabled: !!project.id,
    refetchInterval: (query) => {
      // Poll faster if there are any reviews in RUNNING or QUEUED status
      const hasRunning = query.state.data?.reviews.some(
        (r) => r.status === 'RUNNING' || r.status === 'QUEUED'
      )
      return hasRunning ? 3000 : false
    },
  })

  const reviews = data?.reviews || []
  const totalCount = data?.total_count || 0
  const totalPages = Math.ceil(totalCount / perPage) || 1

  return (
    <div className="space-y-6 text-left">
      {/* Top Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800/80">
          {(['ALL', 'COMPLETED', 'RUNNING', 'FAILED'] as TabStatus[]).map((tab) => {
            const isActive = activeStatus === tab
            return (
              <button
                key={tab}
                onClick={() => {
                  setActiveStatus(tab)
                  setCurrentPage(1)
                }}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  isActive
                    ? 'bg-zinc-800 text-white shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50'
                }`}
              >
                {tab === 'ALL' && 'All Reviews'}
                {tab === 'COMPLETED' && 'Completed'}
                {tab === 'RUNNING' && 'Running'}
                {tab === 'FAILED' && 'Failed'}
              </button>
            )
          })}
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search review summaries..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setCurrentPage(1)
            }}
            className="w-full bg-zinc-900/80 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Loading Skeleton State */}
      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="p-5 rounded-xl border border-zinc-850 bg-zinc-950/40 space-y-3"
            >
              <div className="flex justify-between items-center">
                <Skeleton className="h-5 w-40 rounded" />
                <Skeleton className="h-5 w-24 rounded-full" />
              </div>
              <Skeleton className="h-4 w-3/4 rounded" />
              <div className="flex gap-4 pt-2 border-t border-zinc-900">
                <Skeleton className="h-4 w-28 rounded" />
                <Skeleton className="h-4 w-20 rounded" />
                <Skeleton className="h-4 w-20 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-8 rounded-2xl border border-red-950 bg-red-950/20 text-center space-y-3 max-w-md mx-auto">
          <AlertCircle className="h-8 w-8 text-red-400 mx-auto" />
          <h4 className="font-bold text-white text-sm">Failed to Load Reviews</h4>
          <p className="text-xs text-red-300">{(error as Error).message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-white transition-colors cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && reviews.length === 0 && (
        <div className="rounded-2xl border border-zinc-850 bg-zinc-950/30 p-12 text-center space-y-4 max-w-md mx-auto">
          <div className="h-12 w-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-1.5">
            <h4 className="text-base font-bold text-white">No Reviews Yet</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Your AI Pull Request Reviews will appear here after you run a review on a Pull Request.
            </p>
          </div>
          <Link
            to={`/projects/${project.id}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <GitPullRequest className="h-3.5 w-3.5" />
            <span>Review a Pull Request</span>
          </Link>
        </div>
      )}

      {/* Reviews Cards List */}
      {!isLoading && !error && reviews.length > 0 && (
        <div className="space-y-3.5">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} projectId={project.id} />
          ))}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-zinc-900 text-xs text-zinc-400">
              <span className="font-mono">
                Showing {((currentPage - 1) * perPage) + 1}–{Math.min(currentPage * perPage, totalCount)} of {totalCount} reviews
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                  disabled={currentPage <= 1}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed text-zinc-300 cursor-pointer"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="font-mono px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                  disabled={currentPage >= totalPages}
                  className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed text-zinc-300 cursor-pointer"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
