import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import type { Project } from '@/types/project'
import type { PullRequest } from '@/types/pullRequest'
import { getPullRequests, reviewProjectPullRequest } from '@/api/pullRequests'
import { PullRequestCard } from './PullRequestCard'
import { PullRequestFilterBar } from './PullRequestFilterBar'
import { PullRequestListSkeleton } from './PullRequestListSkeleton'
import { PullRequestEmptyState } from './PullRequestEmptyState'
import { PRReviewModal } from './PRReviewModal'
import { AlertCircle, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

interface PullRequestListProps {
  project: Project
}

export const PullRequestList: React.FC<PullRequestListProps> = ({ project }) => {
  const [selectedState, setSelectedState] = useState<'all' | 'open' | 'closed' | 'merged' | 'draft'>('open')
  const [search, setSearch] = useState<string>('')
  const [sort, setSort] = useState<'created' | 'updated' | 'popularity' | 'long-running'>('created')
  const [direction, setDirection] = useState<'desc' | 'asc'>('desc')
  const [page, setPage] = useState<number>(1)
  const [perPage, setPerPage] = useState<number>(20)

  // Review modal state
  const [reviewingPr, setReviewingPr] = useState<PullRequest | null>(null)
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false)

  // Query pull requests from backend
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: ['pullRequests', project.id, selectedState, page, perPage, sort, direction, search],
    queryFn: () =>
      getPullRequests(project.id, {
        state: selectedState,
        page,
        per_page: perPage,
        sort,
        direction,
        search,
      }),
    staleTime: 30000,
  })

  // Review PR mutation
  const reviewMutation = useMutation({
    mutationFn: (prNumber: number) => reviewProjectPullRequest(project.id, prNumber),
    onSuccess: () => {
      toast.success('AI Review completed successfully!')
    },
    onError: (err: Error) => {
      toast.error(`Review failed: ${err.message}`)
    },
  })

  const handleOpenReviewModal = (pr: PullRequest) => {
    setReviewingPr(pr)
    setIsReviewModalOpen(true)
  }

  const handleStartReview = () => {
    if (reviewingPr) {
      reviewMutation.mutate(reviewingPr.number)
    }
  }

  const handleStateChange = (state: 'all' | 'open' | 'closed' | 'merged' | 'draft') => {
    setSelectedState(state)
    setPage(1)
  }

  const handleSearchChange = (val: string) => {
    setSearch(val)
    setPage(1)
  }

  const handleSortChange = (newSort: 'created' | 'updated' | 'popularity' | 'long-running') => {
    setSort(newSort)
    setDirection(newSort === 'long-running' ? 'asc' : 'desc')
    setPage(1)
  }

  const handlePerPageChange = (newPerPage: number) => {
    setPerPage(newPerPage)
    setPage(1)
  }

  const owner = project.github_owner || project.repoOwner || ''
  const repo = project.github_repository || project.repoName || ''
  const githubRepoUrl = owner && repo ? `https://github.com/${owner}/${repo}/pulls` : undefined

  const pullRequests = data?.pull_requests || []
  const totalCount = data?.total_count || 0
  const totalPages = Math.max(1, Math.ceil(totalCount / perPage))

  return (
    <div className="space-y-4 animate-fade-in text-left">
      {/* Top Filter Bar */}
      <PullRequestFilterBar
        search={search}
        onSearchChange={handleSearchChange}
        selectedState={selectedState}
        onStateChange={handleStateChange}
        sort={sort}
        onSortChange={handleSortChange}
        perPage={perPage}
        onPerPageChange={handlePerPageChange}
        onRefresh={() => refetch()}
        isRefreshing={isFetching}
      />

      {/* Error state */}
      {error && (
        <div className="rounded-xl border border-red-950 bg-red-950/20 p-5 text-center space-y-3 max-w-lg mx-auto animate-fade-in">
          <AlertCircle className="h-7 w-7 text-red-400 mx-auto" />
          <h4 className="font-bold text-white text-sm">Failed to Load Pull Requests</h4>
          <p className="text-xs text-red-300 leading-relaxed">
            {(error as Error).message || 'Could not fetch pull requests from GitHub.'}
          </p>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-white rounded-lg transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3 w-3" />
            <span>Try Again</span>
          </button>
        </div>
      )}

      {/* Loading state */}
      {isLoading && <PullRequestListSkeleton count={4} />}

      {/* Empty state */}
      {!isLoading && !error && pullRequests.length === 0 && (
        <PullRequestEmptyState
          isFiltered={Boolean(search || selectedState !== 'open')}
          onClearFilters={() => {
            setSelectedState('open')
            setSearch('')
            setPage(1)
          }}
          onRefresh={() => refetch()}
          githubUrl={githubRepoUrl}
        />
      )}

      {/* PR Cards Grid */}
      {!isLoading && !error && pullRequests.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
            <span>
              Showing <strong className="text-white">{pullRequests.length}</strong> pull request
              {pullRequests.length !== 1 ? 's' : ''}
            </span>
            <span className="text-[11px] text-zinc-500 font-mono">Page {page} of {totalPages}</span>
          </div>

          <div className="grid gap-3">
            {pullRequests.map((pr) => (
              <PullRequestCard
                key={pr.number}
                projectId={project.id}
                pr={pr}
                onReviewClick={handleOpenReviewModal}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-zinc-900 text-xs">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || isFetching}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-zinc-300 hover:text-white transition-colors disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <span>Previous</span>
              </button>

              <span className="font-mono text-zinc-400 text-xs">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || isFetching}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-zinc-300 hover:text-white transition-colors disabled:opacity-40 cursor-pointer"
              >
                <span>Next</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Review Modal */}
      {reviewingPr && (
        <PRReviewModal
          isOpen={isReviewModalOpen}
          onClose={() => setIsReviewModalOpen(false)}
          prNumber={reviewingPr.number}
          prTitle={reviewingPr.title}
          isLoading={reviewMutation.isPending}
          reviewData={reviewMutation.data || null}
          error={reviewMutation.error}
          onStartReview={handleStartReview}
        />
      )}
    </div>
  )
}
