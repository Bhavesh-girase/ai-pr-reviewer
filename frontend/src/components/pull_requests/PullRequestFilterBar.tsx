import React from 'react'
import { Search, X, RefreshCw, ArrowUpDown } from 'lucide-react'

interface PullRequestFilterBarProps {
  search: string
  onSearchChange: (value: string) => void
  selectedState: 'all' | 'open' | 'closed' | 'merged' | 'draft'
  onStateChange: (state: 'all' | 'open' | 'closed' | 'merged' | 'draft') => void
  sort: 'created' | 'updated' | 'popularity' | 'long-running'
  onSortChange: (sort: 'created' | 'updated' | 'popularity' | 'long-running') => void
  perPage: number
  onPerPageChange: (perPage: number) => void
  onRefresh: () => void
  isRefreshing?: boolean
}

export const PullRequestFilterBar: React.FC<PullRequestFilterBarProps> = ({
  search,
  onSearchChange,
  selectedState,
  onStateChange,
  sort,
  onSortChange,
  perPage,
  onPerPageChange,
  onRefresh,
  isRefreshing = false,
}) => {
  const stateTabs: Array<{ id: 'all' | 'open' | 'closed' | 'merged' | 'draft'; label: string }> = [
    { id: 'all', label: 'All PRs' },
    { id: 'open', label: 'Open' },
    { id: 'draft', label: 'Drafts' },
    { id: 'merged', label: 'Merged' },
    { id: 'closed', label: 'Closed' },
  ]

  return (
    <div className="space-y-3 bg-zinc-950/60 p-3.5 rounded-xl border border-zinc-850">
      {/* Top row: Search and Actions */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        {/* Search input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Search by PR #, title, author, or branch..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-zinc-900/90 border border-zinc-800 rounded-lg pl-9 pr-8 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
          />
          {search && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 p-0.5 cursor-pointer"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Controls: Sort, Per Page, Refresh */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          {/* Sort selector */}
          <div className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1 text-xs text-zinc-400">
            <ArrowUpDown className="h-3 w-3 text-zinc-500" />
            <select
              value={sort}
              onChange={(e) => onSortChange(e.target.value as any)}
              className="bg-transparent text-zinc-300 text-xs focus:outline-none cursor-pointer"
            >
              <option value="created" className="bg-zinc-900 text-white">Newest Created</option>
              <option value="updated" className="bg-zinc-900 text-white">Recently Updated</option>
              <option value="popularity" className="bg-zinc-900 text-white">Most Active</option>
              <option value="long-running" className="bg-zinc-900 text-white">Oldest First</option>
            </select>
          </div>

          {/* Per-page selector */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg px-2 py-1 text-xs text-zinc-400">
            <select
              value={perPage}
              onChange={(e) => onPerPageChange(Number(e.target.value))}
              className="bg-transparent text-zinc-300 text-xs focus:outline-none cursor-pointer"
            >
              <option value={20} className="bg-zinc-900 text-white">20 / page</option>
              <option value={50} className="bg-zinc-900 text-white">50 / page</option>
              <option value={100} className="bg-zinc-900 text-white">100 / page</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Refresh Pull Requests from GitHub"
            className="flex items-center justify-center p-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-lg text-zinc-400 hover:text-white transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* State Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pt-1 border-t border-zinc-900">
        {stateTabs.map((tab) => {
          const isActive = selectedState === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => onStateChange(tab.id)}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 border border-transparent'
              }`}
            >
              {tab.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
