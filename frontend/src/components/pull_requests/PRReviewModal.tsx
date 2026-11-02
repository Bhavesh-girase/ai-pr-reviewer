import React, { useState } from 'react'
import type { ReviewResponse, ReviewIssue } from '@/types/review'
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ChevronRight,
  Zap,
  Layers,
  Clock,
  X,
  FileCode,
} from 'lucide-react'

interface PRReviewModalProps {
  isOpen: boolean
  onClose: () => void
  prNumber: number
  prTitle: string
  isLoading: boolean
  reviewData: ReviewResponse | null
  jobStatus?: 'QUEUED' | 'RUNNING'
  error: Error | null
  onStartReview: () => void
  onSelectIssueLine?: (filename: string, line: number) => void
}

export const PRReviewModal: React.FC<PRReviewModalProps> = ({
  isOpen,
  onClose,
  prNumber,
  prTitle,
  isLoading,
  reviewData,
  jobStatus,
  error,
  onStartReview,
  onSelectIssueLine,
}) => {
  const [selectedFileFilter, setSelectedFileFilter] = useState<string>('all')

  if (!isOpen) return null

  // Flatten all issues across files
  const allIssues: Array<{ filename: string; issue: ReviewIssue }> = []
  if (reviewData?.reviews) {
    reviewData.reviews.forEach((r) => {
      if (r.review?.issues) {
        r.review.issues.forEach((iss) => {
          allIssues.push({ filename: r.filename, issue: iss })
        })
      }
    })
  }

  const criticalSeverityCount = allIssues.filter((i) => i.issue.severity === 'CRITICAL').length
  const highSeverityCount = allIssues.filter((i) => i.issue.severity === 'HIGH').length
  const mediumSeverityCount = allIssues.filter((i) => i.issue.severity === 'MEDIUM').length
  const lowSeverityCount = allIssues.filter((i) => i.issue.severity === 'LOW').length

  const filteredIssues = selectedFileFilter === 'all'
    ? allIssues
    : allIssues.filter((i) => i.filename === selectedFileFilter)

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-fade-in text-left">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden relative">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-900 bg-zinc-950/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-indigo-400">PR #{prNumber}</span>
                <span className="text-zinc-600">•</span>
                <h3 className="text-sm font-bold text-white truncate max-w-md">{prTitle}</h3>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                AI Pull Request Review Engine (Hybrid RAG)
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* Initial State: Confirmation before triggering review */}
          {!isLoading && !reviewData && !error && (
            <div className="text-center py-8 space-y-5 max-w-lg mx-auto">
              <div className="h-16 w-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
                <Sparkles className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h4 className="text-base font-bold text-white">Execute Full AI Review</h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  This will analyze changed files, extract context from the indexed ChromaDB vector store, rerank using CrossEncoder, and generate a comprehensive security, performance, and bug review.
                </p>
              </div>
              <div className="pt-2 flex justify-center gap-3">
                <button
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-zinc-300 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={onStartReview}
                  className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all cursor-pointer hover:scale-105"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>Start Review</span>
                </button>
              </div>
            </div>
          )}

          {/* Queue / worker state */}
          {isLoading && (
            <div className="py-12 space-y-4 max-w-xl mx-auto text-center">
              <div className="space-y-2">
                <Loader2 className="h-8 w-8 text-indigo-400 animate-spin mx-auto" />
                <h4 className="text-sm font-bold text-white">
                  {jobStatus === 'QUEUED'
                    ? 'Review queued'
                    : jobStatus === 'RUNNING'
                    ? `Analyzing Pull Request #${prNumber}`
                    : 'Submitting review request'}
                </h4>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  {jobStatus === 'QUEUED'
                    ? 'Your review is waiting for an available worker and will start automatically.'
                    : jobStatus === 'RUNNING'
                    ? 'A review worker is processing the code changes. This view will update automatically.'
                    : 'Adding your review to the shared queue…'}
                </p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="p-6 rounded-xl border border-red-950 bg-red-950/20 text-center space-y-4 max-w-lg mx-auto">
              <ShieldAlert className="h-10 w-10 text-red-400 mx-auto" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-white">AI Review Execution Failed</h4>
                <p className="text-xs text-red-300 leading-relaxed">{error.message}</p>
              </div>
              <button
                onClick={onStartReview}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold text-white transition-colors cursor-pointer"
              >
                Retry Review
              </button>
            </div>
          )}

          {/* Review Results */}
          {reviewData && !isLoading && (
            <div className="space-y-6">
              {/* Metadata & Quick Stats Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-zinc-900/70 border border-zinc-850 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>Duration</span>
                  </span>
                  <p className="text-sm font-mono font-bold text-white">
                    {reviewData.metadata?.duration ? `${reviewData.metadata.duration}s` : 'N/A'}
                  </p>
                </div>

                <div className="bg-zinc-900/70 border border-zinc-850 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
                    <Zap className="h-3 w-3 text-indigo-400" />
                    <span>Confidence</span>
                  </span>
                  <p className="text-sm font-mono font-bold text-indigo-400">
                    {reviewData.metadata?.confidence || 92}%
                  </p>
                </div>

                <div className="bg-zinc-900/70 border border-zinc-850 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
                    <Layers className="h-3 w-3 text-emerald-400" />
                    <span>Chunks RAG</span>
                  </span>
                  <p className="text-sm font-mono font-bold text-emerald-400">
                    {reviewData.metadata?.chunks_retrieved || 0} retrieved
                  </p>
                </div>

                <div className="bg-zinc-900/70 border border-zinc-850 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3 text-amber-400" />
                    <span>Issues Found</span>
                  </span>
                  <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
                    <span className="text-red-300">{criticalSeverityCount}C</span>
                    <span className="text-zinc-600">/</span>
                    <span className="text-red-400">{highSeverityCount}H</span>
                    <span className="text-zinc-600">/</span>
                    <span className="text-amber-400">{mediumSeverityCount}M</span>
                    <span className="text-zinc-600">/</span>
                    <span className="text-blue-400">{lowSeverityCount}L</span>
                  </div>
                </div>
              </div>

              {/* Summary Section */}
              {reviewData.reviews?.[0]?.review?.summary && (
                <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 space-y-1.5">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Review Summary</span>
                  </div>
                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {reviewData.reviews[0].review.summary}
                  </p>
                </div>
              )}

              {/* Issues Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                      Detected Issues ({allIssues.length})
                    </h4>
                  </div>

                  {/* File Filter Dropdown */}
                  {reviewData.reviews && reviewData.reviews.length > 1 && (
                    <select
                      value={selectedFileFilter}
                      onChange={(e) => setSelectedFileFilter(e.target.value)}
                      className="bg-zinc-900 border border-zinc-800 rounded-md text-[11px] text-zinc-300 px-2 py-1 focus:outline-none"
                    >
                      <option value="all">All Files ({allIssues.length})</option>
                      {reviewData.reviews.map((r) => (
                        <option key={r.filename} value={r.filename}>
                          {r.filename} ({r.review?.issues?.length || 0})
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {filteredIssues.length === 0 ? (
                  <div className="p-6 text-center rounded-xl bg-zinc-900/30 border border-zinc-850 text-zinc-400 text-xs">
                    <CheckCircle2 className="h-6 w-6 text-emerald-400 mx-auto mb-2" />
                    <span>No critical issues detected in the reviewed files!</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredIssues.map((item, index) => {
                      const { filename, issue } = item
                      const isCritical = issue.severity === 'CRITICAL'
                      const isHigh = issue.severity === 'HIGH'
                      const isMedium = issue.severity === 'MEDIUM'

                      return (
                        <div
                          key={index}
                          className={`rounded-xl border p-4 text-xs space-y-2.5 transition-all ${
                            isCritical
                              ? 'border-red-700/70 bg-red-950/30'
                              : isHigh
                              ? 'border-red-900/50 bg-red-950/10'
                              : isMedium
                              ? 'border-amber-900/50 bg-amber-950/10'
                              : 'border-zinc-800 bg-zinc-900/30'
                          }`}
                        >
                          {/* Issue Header */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                                    isCritical
                                      ? 'bg-red-500/30 text-red-200 border border-red-400/50'
                                      : isHigh
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
                                <span className="font-mono text-zinc-400 text-[11px] flex items-center gap-1">
                                  <FileCode className="h-3 w-3 text-zinc-500" />
                                  <span>{filename}</span>
                                  {issue.line && <span className="text-indigo-400">:{issue.line}</span>}
                                </span>
                              </div>
                              <h5 className="font-bold text-white text-sm">{issue.title}</h5>
                            </div>

                            {issue.line && onSelectIssueLine && (
                              <button
                                onClick={() => {
                                  onSelectIssueLine(filename, issue.line!)
                                  onClose()
                                }}
                                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white font-semibold text-[11px] transition-colors cursor-pointer shrink-0"
                              >
                                <span>Inspect Line</span>
                                <ChevronRight className="h-3 w-3" />
                              </button>
                            )}
                          </div>

                          {/* Description */}
                          <p className="text-zinc-300 leading-relaxed">{issue.description}</p>

                          {/* Suggestion block */}
                          {issue.suggestion && (
                            <div className="p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800 space-y-1">
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
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-zinc-900 bg-zinc-950">
          <span className="text-[11px] text-zinc-500">
            {reviewData
              ? 'Review complete.'
              : jobStatus === 'QUEUED'
              ? 'Queued reviews run automatically when a worker is available.'
              : 'AI review execution will not modify any files.'}
          </span>
          <div className="flex items-center gap-2">
            {reviewData && (
              <button
                onClick={onStartReview}
                className="px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-semibold text-zinc-300 hover:text-white transition-colors cursor-pointer"
              >
                Re-run Review
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
