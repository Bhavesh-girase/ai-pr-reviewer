import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getProjectById } from '@/api/projects'
import { getReviewById, reviewProjectPullRequest } from '@/api/reviews'
import { ReviewStatusBadge } from '@/components/reviews/ReviewStatusBadge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ChevronRight,
  ArrowLeft,
  Sparkles,
  GitPullRequest,
  Clock,
  Bot,
  GitCommit,
  AlertTriangle,
  FileCode,
  CheckCircle2,
  Layers,
  Zap,
  ArrowUpRight,
  ShieldAlert,
} from 'lucide-react'
import { toast } from 'sonner'

export default function ReviewDetailsPage() {
  const { projectId, reviewId } = useParams<{ projectId: string; reviewId: string }>()
  const navigate = useNavigate()
  const [selectedFileFilter, setSelectedFileFilter] = useState<string>('all')

  // 1. Fetch Project data
  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProjectById(projectId || ''),
    enabled: !!projectId,
  })

  // 2. Fetch Review details
  const {
    data: review,
    isLoading: isReviewLoading,
    error: reviewError,
    refetch,
  } = useQuery({
    queryKey: ['reviewDetail', projectId, reviewId],
    queryFn: () => getReviewById(projectId || '', reviewId || ''),
    enabled: !!projectId && !!reviewId,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'RUNNING' || status === 'QUEUED' ? 2500 : false
    },
  })

  // Review Again mutation
  const reReviewMutation = useMutation({
    mutationFn: () => reviewProjectPullRequest(projectId || '', review?.github_pr_number || 0),
    onSuccess: (data) => {
      toast.success('New AI review completed successfully!')
      if (data.review_id) {
        navigate(`/projects/${projectId}/reviews/${data.review_id}`)
      } else {
        refetch()
      }
    },
    onError: (err: Error) => {
      toast.error(`Re-review failed: ${err.message}`)
    },
  })

  const projectName = project?.project_name || project?.name || 'Project'

  if (isReviewLoading) {
    return (
      <div className="space-y-6 text-left animate-fade-in max-w-5xl mx-auto">
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Skeleton className="h-4 w-16" />
          <ChevronRight className="h-3 w-3" />
          <Skeleton className="h-4 w-24" />
          <ChevronRight className="h-3 w-3" />
          <Skeleton className="h-4 w-20" />
        </div>
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    )
  }

  if (reviewError || !review) {
    return (
      <div className="p-8 rounded-2xl border border-red-950 bg-red-950/20 text-center space-y-4 max-w-md mx-auto mt-12 text-left">
        <ShieldAlert className="h-10 w-10 text-red-400 mx-auto" />
        <h3 className="font-bold text-white text-base">Review Not Found</h3>
        <p className="text-xs text-red-300">
          {(reviewError as Error)?.message || `Could not find review record with ID ${reviewId}.`}
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

  // Extract all issues
  const allIssues: Array<{ filename: string; issue: any }> = []
  if (review.review_result?.reviews) {
    review.review_result.reviews.forEach((r) => {
      if (r.review?.issues) {
        r.review.issues.forEach((iss) => {
          allIssues.push({ filename: r.filename, issue: iss })
        })
      }
    })
  }

  const filteredIssues =
    selectedFileFilter === 'all'
      ? allIssues
      : allIssues.filter((i) => i.filename === selectedFileFilter)

  const durationSec = review.review_duration_ms
    ? (review.review_duration_ms / 1000).toFixed(1)
    : review.review_result?.metadata?.duration
    ? String(review.review_result.metadata.duration)
    : null

  return (
    <div className="space-y-6 text-left animate-fade-in max-w-5xl mx-auto">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <Link to="/projects" className="hover:text-white transition-colors">
          Projects
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <Link to={`/projects/${projectId}`} className="hover:text-white transition-colors">
          {projectName}
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <span className="text-zinc-500">Reviews</span>
        <ChevronRight className="h-3.5 w-3.5 text-zinc-600" />
        <span className="text-zinc-300 font-mono font-semibold">#{review.id.slice(0, 8)}</span>
      </div>

      {/* Header Card */}
      <div className="rounded-2xl border border-zinc-850 bg-zinc-950/80 p-6 space-y-5 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <button
                onClick={() => navigate(`/projects/${projectId}`)}
                className="p-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-white transition-colors cursor-pointer mr-1"
                title="Back to Project"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>

              <ReviewStatusBadge status={review.status} />

              <Link
                to={`/projects/${projectId}/pull-requests/${review.github_pr_number}`}
                className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-indigo-400 hover:text-indigo-300 bg-indigo-950/30 border border-indigo-500/20 px-2.5 py-0.5 rounded-md transition-colors"
              >
                <GitPullRequest className="h-3 w-3" />
                <span>PR #{review.github_pr_number}</span>
                <ArrowUpRight className="h-3 w-3" />
              </Link>

              {review.head_commit_sha && (
                <span className="flex items-center gap-1 font-mono text-xs text-zinc-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-md">
                  <GitCommit className="h-3 w-3 text-zinc-500" />
                  <span>{review.head_commit_sha.slice(0, 7)}</span>
                </span>
              )}
            </div>

            <h1 className="text-xl font-bold text-white tracking-tight">
              {review.pr_title || `Pull Request #${review.github_pr_number} AI Review`}
            </h1>

            {/* Meta tags */}
            <div className="flex items-center gap-4 text-xs text-zinc-400 flex-wrap pt-0.5">
              <span className="flex items-center gap-1 text-zinc-400">
                <Bot className="h-3.5 w-3.5 text-indigo-400" />
                <span>{review.model_name || 'Gemini 2.5 Flash'}</span>
              </span>

              {durationSec && (
                <span className="flex items-center gap-1 text-zinc-400 font-mono">
                  <Clock className="h-3.5 w-3.5 text-zinc-500" />
                  <span>{durationSec}s duration</span>
                </span>
              )}

              {review.created_at && (
                <span className="text-zinc-500 font-mono">
                  Reviewed on {new Date(review.created_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 shrink-0">
            <Link
              to={`/projects/${projectId}/pull-requests/${review.github_pr_number}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-zinc-300 hover:text-white transition-colors cursor-pointer"
            >
              <GitPullRequest className="h-3.5 w-3.5 text-indigo-400" />
              <span>View Pull Request</span>
            </Link>

            <button
              onClick={() => reReviewMutation.mutate()}
              disabled={reReviewMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all cursor-pointer hover:scale-105"
            >
              <Sparkles className="h-4 w-4" />
              <span>{reReviewMutation.isPending ? 'Running Review...' : 'Review Again'}</span>
            </button>
          </div>
        </div>

        {/* Quick Stats Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-zinc-900 text-xs">
          <div className="bg-zinc-900/60 border border-zinc-850 p-3 rounded-xl space-y-1">
            <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-amber-400" />
              <span>Issues Detected</span>
            </span>
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
              <span className="text-red-400">{review.high_count || 0}H</span>
              <span className="text-zinc-600">/</span>
              <span className="text-amber-400">{review.medium_count || 0}M</span>
              <span className="text-zinc-600">/</span>
              <span className="text-blue-400">{review.low_count || 0}L</span>
            </div>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-850 p-3 rounded-xl space-y-1">
            <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
              <FileCode className="h-3 w-3 text-zinc-400" />
              <span>Files Reviewed</span>
            </span>
            <p className="text-sm font-mono font-bold text-white">
              {review.files_reviewed || review.review_result?.reviews?.length || 0}
            </p>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-850 p-3 rounded-xl space-y-1">
            <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
              <Zap className="h-3 w-3 text-indigo-400" />
              <span>Confidence</span>
            </span>
            <p className="text-sm font-mono font-bold text-indigo-400">
              {review.review_result?.metadata?.confidence || 92}%
            </p>
          </div>

          <div className="bg-zinc-900/60 border border-zinc-850 p-3 rounded-xl space-y-1">
            <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
              <Layers className="h-3 w-3 text-emerald-400" />
              <span>RAG Chunks</span>
            </span>
            <p className="text-sm font-mono font-bold text-emerald-400">
              {review.review_result?.metadata?.chunks_retrieved || 0} retrieved
            </p>
          </div>
        </div>
      </div>

      {/* Summary Section */}
      {review.summary && (
        <div className="p-5 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
            <Sparkles className="h-4 w-4" />
            <span>AI Review Summary</span>
          </div>
          <p className="text-xs text-zinc-200 leading-relaxed">
            {review.summary}
          </p>
        </div>
      )}

      {/* Issues Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Detected Issues ({allIssues.length})
            </h3>
          </div>

          {/* File Filter Dropdown */}
          {review.review_result?.reviews && review.review_result.reviews.length > 1 && (
            <select
              value={selectedFileFilter}
              onChange={(e) => setSelectedFileFilter(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded-md text-xs text-zinc-300 px-2.5 py-1 focus:outline-none"
            >
              <option value="all">All Files ({allIssues.length})</option>
              {review.review_result.reviews.map((r) => (
                <option key={r.filename} value={r.filename}>
                  {r.filename} ({r.review?.issues?.length || 0})
                </option>
              ))}
            </select>
          )}
        </div>

        {filteredIssues.length === 0 ? (
          <div className="p-10 text-center rounded-2xl bg-zinc-950/40 border border-zinc-850 text-zinc-400 text-xs space-y-2">
            <CheckCircle2 className="h-8 w-8 text-emerald-400 mx-auto" />
            <p className="font-semibold text-white">No issues detected!</p>
            <p className="text-zinc-500">The analyzed changes passed code quality and security checks.</p>
          </div>
        ) : (
          <div className="space-y-3.5">
            {filteredIssues.map((item, index) => {
              const { filename, issue } = item
              const isHigh = issue.severity === 'HIGH' || issue.severity === 'CRITICAL'
              const isMedium = issue.severity === 'MEDIUM'

              return (
                <div
                  key={index}
                  className={`rounded-xl border p-4 text-xs space-y-3 transition-all ${
                    isHigh
                      ? 'border-red-900/50 bg-red-950/10'
                      : isMedium
                      ? 'border-amber-900/50 bg-amber-950/10'
                      : 'border-zinc-800 bg-zinc-950/40'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                            isHigh
                              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                              : isMedium
                              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}
                        >
                          {issue.severity}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
                          {issue.category}
                        </span>
                        <span className="font-mono text-zinc-400 text-xs flex items-center gap-1">
                          <FileCode className="h-3.5 w-3.5 text-zinc-500" />
                          <span>{filename}</span>
                          {issue.line && <span className="text-indigo-400">:{issue.line}</span>}
                        </span>
                      </div>
                      <h4 className="font-bold text-white text-sm pt-0.5">{issue.title}</h4>
                    </div>

                    <Link
                      to={`/projects/${projectId}/pull-requests/${review.github_pr_number}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white font-semibold text-[11px] transition-colors cursor-pointer shrink-0"
                    >
                      <span>Inspect in Diff</span>
                      <ChevronRight className="h-3 w-3" />
                    </Link>
                  </div>

                  <p className="text-zinc-300 leading-relaxed">{issue.description}</p>

                  {issue.suggestion && (
                    <div className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-indigo-400">
                        Recommendation:
                      </span>
                      <p className="text-[11px] text-zinc-300 font-mono whitespace-pre-wrap">
                        {issue.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
