import React from 'react'
import { GitPullRequest, SearchX, ExternalLink, RefreshCw } from 'lucide-react'

interface PullRequestEmptyStateProps {
  isFiltered: boolean
  onClearFilters?: () => void
  onRefresh?: () => void
  githubUrl?: string
}

export const PullRequestEmptyState: React.FC<PullRequestEmptyStateProps> = ({
  isFiltered,
  onClearFilters,
  onRefresh,
  githubUrl,
}) => {
  return (
    <div className="rounded-xl border border-zinc-850 bg-zinc-950/30 p-8 text-center flex flex-col items-center justify-center min-h-[280px] space-y-4 animate-fade-in text-left">
      <div className="h-12 w-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500">
        {isFiltered ? <SearchX className="h-6 w-6" /> : <GitPullRequest className="h-6 w-6" />}
      </div>

      <div className="space-y-1.5 max-w-sm text-center">
        <h3 className="text-base font-bold text-white">
          {isFiltered ? 'No Matching Pull Requests' : 'No Pull Requests Yet'}
        </h3>
        <p className="text-xs text-zinc-400 leading-relaxed">
          {isFiltered
            ? 'No pull requests matched your current filters or search keywords. Try adjusting your search query or state filters.'
            : 'This GitHub repository does not currently have any pull requests matching this criteria.'}
        </p>
      </div>

      <div className="flex items-center gap-3 pt-2 flex-wrap justify-center">
        {isFiltered && onClearFilters && (
          <button
            onClick={onClearFilters}
            className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-xs font-semibold text-white transition-colors cursor-pointer"
          >
            Clear Filters
          </button>
        )}

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-xs font-semibold text-zinc-300 hover:text-white transition-colors cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
        )}

        {githubUrl && !isFiltered && (
          <a
            href={githubUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
          >
            <span>Open on GitHub</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
      </div>
    </div>
  )
}
