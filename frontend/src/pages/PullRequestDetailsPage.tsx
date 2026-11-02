import React, { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getProjectById } from '@/api/projects'
import {
  getPullRequestById,
  getPullRequestFiles,
  getPullRequestDiff,
} from '@/api/pullRequests'
import { getPullRequestReviews, getReviewById, reviewProjectPullRequest } from '@/api/reviews'
import type { PullRequestFile } from '@/types/pullRequest'
import type { ReviewDetail } from '@/types/review'
import { PullRequestStatusBadge } from '@/components/pull_requests/PullRequestStatusBadge'
import { ReviewStatusBadge } from '@/components/reviews/ReviewStatusBadge'
import { PRDiffViewer } from '@/components/pull_requests/PRDiffViewer'
import { PRReviewModal } from '@/components/pull_requests/PRReviewModal'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ChevronRight,
  ArrowLeft,
  GitBranch,
  ExternalLink,
  Sparkles,
  FileCode,
  Plus,
  Minus,
  GitCommit,
  Clock,
  Search,
  AlertCircle,
  FileText,
  CheckCircle2,
  AlertTriangle,
  History,
  RefreshCw,
} from 'lucide-react'
import { toast } from 'sonner'

export default function PullRequestDetailsPage() {
  const { projectId, prNumber } = useParams<{ projectId: string; prNumber: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const prNum = parseInt(prNumber || '0', 10)

  const [selectedFilename, setSelectedFilename] = useState<string | null>(null)
  const [fileSearch, setFileSearch] = useState<string>('')
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null)
  const [isFilePanelOpen, setIsFilePanelOpen] = useState(true)
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false)
  const [focusLine, setFocusLine] = useState<number | null>(null)

  // 1. Fetch Project data
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId || ''),
    enabled: !!projectId,
  })

  // 2. Fetch Pull Request metadata
  const {
    data: pr,
    isLoading: isPrLoading,
    error: prError,
  } = useQuery({
    queryKey: ['pullRequest', projectId, prNum],
    queryFn: () => getPullRequestById(projectId || '', prNum),
    enabled: !!projectId && prNum > 0,
  })

  // 3. Fetch Changed Files
  const {
    data: files = [],
    isLoading: isFilesLoading,
  } = useQuery({
    queryKey: ['pullRequestFiles', projectId, prNum],
    queryFn: () => getPullRequestFiles(projectId || '', prNum),
    enabled: !!projectId && prNum > 0,
  })

  // 4. Fetch Full PR Diff (optional fallback)
  const {
    data: diffData,
    isLoading: isDiffLoading,
  } = useQuery({
    queryKey: ['pullRequestDiff', projectId, prNum],
    queryFn: () => getPullRequestDiff(projectId || '', prNum),
    enabled: !!projectId && prNum > 0,
  })

  // 5. Fetch PR Review History
  const {
    data: prReviews = [],
  } = useQuery({
    queryKey: ['pullRequestReviews', projectId, prNum],
    queryFn: () => getPullRequestReviews(projectId || '', prNum),
    enabled: !!projectId && prNum > 0,
  })

  const latestReview = prReviews.length > 0 ? prReviews[0] : null
  const hasNewCommitsSinceReview = Boolean(
    latestReview?.head_commit_sha &&
    pr?.head_commit_sha &&
    latestReview.head_commit_sha !== pr.head_commit_sha
  )

  // Set default selected file on first load
  React.useEffect(() => {
    if (files.length > 0 && !selectedFilename) {
      setSelectedFilename(files[0].filename)
    }
  }, [files, selectedFilename])

  // Review PR mutation
  const reviewMutation = useMutation({
    mutationFn: () => reviewProjectPullRequest(projectId || '', prNum),
    onSuccess: (result) => {
      setActiveReviewId(result.review_id)
      queryClient.invalidateQueries({ queryKey: ['pullRequestReviews', projectId, prNum] })
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] })
      queryClient.invalidateQueries({ queryKey: ['pullRequests', projectId] })
      toast.success('AI review queued. It will start when a worker is available.')
    },
    onError: (err: Error) => {
      toast.error(`Review failed: ${err.message}`)
    },
  })

  const reviewJobQuery = useQuery<ReviewDetail>({
    queryKey: ['reviewDetail', projectId, activeReviewId],
    queryFn: () => getReviewById(projectId || '', activeReviewId || ''),
    enabled: !!projectId && !!activeReviewId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'QUEUED' || status === 'RUNNING' ? 2000 : false
    },
  })

  const activeReview = reviewJobQuery.data
  const reviewData = activeReview?.status === 'COMPLETED'
    ? activeReview.review_result || null
    : null
  const jobStatus: 'QUEUED' | 'RUNNING' | undefined = activeReview?.status === 'QUEUED'
    ? 'QUEUED'
    : activeReview?.status === 'RUNNING'
    ? 'RUNNING'
    : undefined
  const reviewError = reviewMutation.error || reviewJobQuery.error || (
    activeReview?.status === 'FAILED'
      ? new Error(activeReview.error_message || 'The queued review failed.')
      : null
  )
  const isReviewLoading = reviewMutation.isPending || reviewJobQuery.isLoading || Boolean(jobStatus)

  React.useEffect(() => {
    if (activeReview?.status === 'COMPLETED') {
      queryClient.invalidateQueries({ queryKey: ['pullRequestReviews', projectId, prNum] })
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] })
      queryClient.invalidateQueries({ queryKey: ['pullRequests', projectId] })
      toast.success('AI review completed and saved to history!')
    } else if (activeReview?.status === 'FAILED') {
      queryClient.invalidateQueries({ queryKey: ['pullRequestReviews', projectId, prNum] })
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] })
      toast.error(activeReview.error_message || 'AI review failed.')
    }
  }, [activeReview?.id, activeReview?.status, activeReview?.error_message, projectId, prNum, queryClient])

  const handleStartReview = () => {
    setActiveReviewId(null)
    reviewMutation.reset()
    reviewMutation.mutate()
  }

  const handleSelectIssueLine = (filename: string, line: number) => {
    setSelectedFilename(filename)
    setFocusLine(line)
  }

  const selectedFile: PullRequestFile | null =
    files.find((f) => f.filename === selectedFilename) || files[0] || null

  const filteredFiles = files.filter((f) =>
    f.filename.toLowerCase().includes(fileSearch.toLowerCase())
  )

  const projectName = project?.project_name || project?.name || 'Project'

  // Extract issue lines for current selected file if review data is available
  const issueLinesForSelectedFile: number[] = []
  if (reviewData?.reviews) {
    const fileReview = reviewData.reviews.find(
      (r) => r.filename === selectedFilename
    )
    if (fileReview?.review?.issues) {
      fileReview.review.issues.forEach((iss) => {
        if (iss.line && iss.line > 0) {
          issueLinesForSelectedFile.push(iss.line)
        }
      })
    }
  }

  // Loading state
  if (isPrLoading) {
    return (
      <div className="space-y-6 animate-fade-in text-left">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Skeleton className="h-4 w-16" />
          <ChevronRight className="h-3 w-3" />
          <Skeleton className="h-4 w-24" />
          <ChevronRight className="h-3 w-3" />
          <Skeleton className="h-4 w-16" />
        </div>
        <div className="space-y-2 border-b border-zinc-900 pb-6">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-5 w-1/3" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Skeleton className="h-96 rounded-xl" />
          <Skeleton className="h-96 md:col-span-3 rounded-xl" />
        </div>
      </div>
    )
  }

  // Error state
  if (prError || !pr) {
    return (
      <div className="rounded-xl border border-red-950 bg-red-950/20 p-8 text-center space-y-4 max-w-md mx-auto mt-12 text-left">
        <AlertCircle className="h-9 w-9 text-red-400 mx-auto" />
        <h3 className="font-bold text-white text-base">Pull Request Not Found</h3>
        <p className="text-xs text-red-300 leading-relaxed">
          {(prError as Error)?.message || `Could not find PR #${prNum} in this repository.`}
        </p>
        <button
          onClick={() => navigate(`/projects/${projectId}`)}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-900 border border-zinc-800 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors cursor-pointer w-full"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Project</span>
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in text-left">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <Link to="/projects" className="hover:text-white transition-colors">
          Projects
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <Link to={`/projects/${projectId}`} className="hover:text-white transition-colors">
          {projectName}
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <span className="text-zinc-500">Pull Requests</span>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <span className="text-zinc-300 font-semibold font-mono">#{pr.number}</span>
      </div>

      {/* Header Container */}
      <div className="rounded-2xl border border-zinc-850 bg-zinc-950/70 p-6 space-y-5 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Title & Metadata */}
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <button
                onClick={() => navigate(`/projects/${projectId}`)}
                className="p-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer mr-1"
                title="Back to Project"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>

              <PullRequestStatusBadge state={pr.state} />
              <span className="font-mono text-sm font-bold text-zinc-400">#{pr.number}</span>

              {/* Branch flow */}
              <div className="flex items-center gap-1.5 font-mono text-xs bg-zinc-900 border border-zinc-800 px-2.5 py-0.5 rounded-md text-zinc-400">
                <GitBranch className="h-3 w-3 text-zinc-500" />
                <span className="text-zinc-300 font-semibold">{pr.source_branch}</span>
                <span className="text-zinc-600">→</span>
                <span className="text-zinc-400 font-semibold">{pr.target_branch}</span>
              </div>
            </div>

            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              {pr.title}
            </h1>

            {/* Author info & timestamps */}
            <div className="flex items-center gap-4 text-xs text-zinc-400 flex-wrap pt-0.5">
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
                <span className="text-zinc-300 font-semibold">{pr.author.login}</span>
              </div>

              {pr.created_at && (
                <span className="flex items-center gap-1 text-zinc-500">
                  <Clock className="h-3 w-3" />
                  <span>
                    Opened on {new Date(pr.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </span>
              )}
            </div>
          </div>

          {/* Actions: Review PR & GitHub External Link */}
          <div className="flex items-center gap-3 shrink-0">
            <a
              href={pr.html_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-zinc-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>GitHub</span>
              <ExternalLink className="h-3.5 w-3.5 text-zinc-400" />
            </a>

            <button
              onClick={() => setIsReviewModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-600/25 transition-all cursor-pointer hover:scale-105"
            >
              <Sparkles className="h-4 w-4" />
              <span>{prReviews.length > 0 ? 'Review Again' : 'Review PR'}</span>
            </button>
          </div>
        </div>

        {/* PR Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-3 border-t border-zinc-900/90 text-xs">
          <div className="flex items-center gap-2 text-zinc-400 font-mono">
            <FileCode className="h-3.5 w-3.5 text-zinc-500" />
            <span>
              <strong className="text-white">{pr.changed_files_count || files.length}</strong> files
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono">
            <span className="text-emerald-400 font-bold flex items-center">
              <Plus className="h-3 w-3" />
              {pr.additions}
            </span>
            <span className="text-zinc-600">/</span>
            <span className="text-red-400 font-bold flex items-center">
              <Minus className="h-3 w-3" />
              {pr.deletions}
            </span>
          </div>

          <div className="flex items-center gap-2 text-zinc-400 font-mono">
            <GitCommit className="h-3.5 w-3.5 text-zinc-500" />
            <span>
              <strong className="text-white">{pr.commits_count || 1}</strong> commits
            </span>
          </div>

          <div className="flex items-center gap-2 text-zinc-400 font-mono">
            <History className="h-3.5 w-3.5 text-indigo-400" />
            <span>
              <strong className="text-white">{prReviews.length}</strong> reviews
            </span>
          </div>

          {latestReview && (
            <div className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Reviewed</span>
            </div>
          )}
        </div>

        {/* PR Body / Description (if available) */}
        {pr.body && (
          <div className="bg-zinc-900/40 border border-zinc-850/80 rounded-xl p-3.5 space-y-1 text-xs">
            <div className="flex items-center gap-1.5 text-zinc-400 font-semibold text-[11px]">
              <FileText className="h-3.5 w-3.5" />
              <span>Description</span>
            </div>
            <p className="text-zinc-300 leading-relaxed whitespace-pre-wrap line-clamp-3">
              {pr.body}
            </p>
          </div>
        )}
      </div>

      {/* Commit Snapshot Warning Banner */}
      {hasNewCommitsSinceReview && (
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5 text-amber-300">
            <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold text-white">PR Updated with New Commits</span>
              <p className="text-zinc-300 text-[11px] mt-0.5">
                This Pull Request has received new commits since the last review. Run a fresh review to analyze the latest changes.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsReviewModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs transition-colors cursor-pointer shrink-0"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Review Again</span>
          </button>
        </div>
      )}

      {/* Latest AI Review Card Banner */}
      {latestReview && (
        <div className="p-5 rounded-xl border border-indigo-500/20 bg-indigo-950/20 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">Latest AI Review</h3>
                  <ReviewStatusBadge status={latestReview.status} />
                </div>
                <span className="text-[11px] text-zinc-400 font-mono">
                  Completed {new Date(latestReview.created_at || '').toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to={`/projects/${projectId}/reviews/${latestReview.id}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors cursor-pointer"
              >
                <span>View Full Review</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>

          {/* Quick summary & issues breakdown */}
          <div className="flex items-center gap-4 text-xs text-zinc-300 flex-wrap pt-2 border-t border-indigo-500/20">
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              <span className="text-zinc-400 font-semibold">{latestReview.issues_count} Issues Detected:</span>
              <span className="text-red-400 font-bold">{latestReview.high_count} High</span>
              <span className="text-zinc-600">/</span>
              <span className="text-amber-400 font-bold">{latestReview.medium_count} Med</span>
              <span className="text-zinc-600">/</span>
              <span className="text-blue-400 font-bold">{latestReview.low_count} Low</span>
            </div>

            {latestReview.summary && (
              <p className="text-zinc-300 text-xs italic line-clamp-1 flex-1">
                "{latestReview.summary}"
              </p>
            )}
          </div>
        </div>
      )}

      {/* Main Diff & Files Split Layout */}
      <div className={`grid grid-cols-1 gap-6 items-start ${isFilePanelOpen ? 'lg:grid-cols-4' : ''}`}>
        {/* Left Column: Changed Files List */}
        <div
          id="pr-changed-files-panel"
          hidden={!isFilePanelOpen}
          className="rounded-xl border border-zinc-850 bg-zinc-950/70 p-4 space-y-3 lg:sticky lg:top-4 text-left"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <FileCode className="h-3.5 w-3.5 text-indigo-400" />
              <span>Changed Files ({files.length})</span>
            </h3>
          </div>

          {/* Search files filter */}
          {files.length > 5 && (
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-zinc-500" />
              <input
                type="text"
                placeholder="Filter files..."
                value={fileSearch}
                onChange={(e) => setFileSearch(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-md pl-7 pr-2 py-1 text-[11px] text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {/* Files List */}
          {isFilesLoading ? (
            <div className="space-y-2 py-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full rounded-lg" />
              ))}
            </div>
          ) : filteredFiles.length === 0 ? (
            <p className="text-xs text-zinc-500 py-4 text-center">No matching files found.</p>
          ) : (
            <div className="space-y-1 max-h-[580px] overflow-y-auto pr-1">
              {filteredFiles.map((file) => {
                const isSelected = file.filename === selectedFilename
                const statusColor =
                  file.status === 'added'
                    ? 'text-emerald-400'
                    : file.status === 'removed'
                    ? 'text-red-400'
                    : 'text-amber-400'

                return (
                  <button
                    key={file.filename}
                    onClick={() => {
                      setSelectedFilename(file.filename)
                      setFocusLine(null)
                    }}
                    className={`w-full text-left p-2 rounded-lg text-xs transition-all flex items-center justify-between gap-2 cursor-pointer ${
                      isSelected
                        ? 'bg-indigo-600/20 border border-indigo-500/30 text-white font-medium'
                        : 'hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`text-[10px] font-bold font-mono ${statusColor}`}>
                        {file.status === 'added' ? 'A' : file.status === 'removed' ? 'D' : 'M'}
                      </span>
                      <span className="font-mono text-[11px] truncate">{file.filename}</span>
                    </div>

                    <div className="flex items-center gap-1 font-mono text-[10px] shrink-0">
                      {file.additions > 0 && <span className="text-emerald-400">+{file.additions}</span>}
                      {file.deletions > 0 && <span className="text-red-400">-{file.deletions}</span>}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Right Column: Monaco PR Diff Viewer */}
        <div className={isFilePanelOpen ? 'lg:col-span-3' : ''}>
          <PRDiffViewer
            file={selectedFile}
            rawDiff={diffData?.raw_diff}
            isLoading={isFilesLoading || isDiffLoading}
            issueLines={issueLinesForSelectedFile}
            focusLine={focusLine}
            isFilePanelOpen={isFilePanelOpen}
            onToggleFilePanel={() => setIsFilePanelOpen((open) => !open)}
          />
        </div>
      </div>

      {/* Review Modal */}
      <PRReviewModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        prNumber={pr.number}
        prTitle={pr.title}
        isLoading={isReviewLoading}
        jobStatus={jobStatus}
        reviewData={reviewData}
        error={reviewError}
        onStartReview={handleStartReview}
        onSelectIssueLine={handleSelectIssueLine}
      />
    </div>
  )
}
