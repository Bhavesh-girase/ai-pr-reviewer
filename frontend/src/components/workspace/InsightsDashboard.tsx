import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import type { Project } from '@/types/project'
import type { DateRangeFilter } from '@/types/insights'
import { getProjectInsights } from '@/api/insights'
import { Skeleton } from '@/components/ui/skeleton'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import {
  Sparkles,
  ShieldAlert,
  Activity,
  AlertTriangle,
  BarChart3,
  FileCode,
  CheckCircle2,
  Clock,
  Zap,
  GitPullRequest,
  TrendingUp,
  RotateCw,
  Info,
} from 'lucide-react'

interface InsightsDashboardProps {
  project: Project
}

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
}

const CATEGORY_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#14b8a6', '#f43f5e']

export default function InsightsDashboard({ project }: InsightsDashboardProps) {
  const [range, setRange] = useState<DateRangeFilter>('30d')

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['projectInsights', project.id, range],
    queryFn: () => getProjectInsights(project.id, range),
    enabled: !!project.id,
    staleTime: 60 * 1000, // 1 minute stale time for insights
  })

  const overview = data?.overview
  const hasData = data?.has_data || false

  // Format date labels
  const formatShortDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  // Severity Pie Data
  const severityPieData = data?.severity_distribution
    ? [
        { name: 'Critical', value: data.severity_distribution.critical_count, color: SEVERITY_COLORS.critical },
        { name: 'High', value: data.severity_distribution.high_count, color: SEVERITY_COLORS.high },
        { name: 'Medium', value: data.severity_distribution.medium_count, color: SEVERITY_COLORS.medium },
        { name: 'Low', value: data.severity_distribution.low_count, color: SEVERITY_COLORS.low },
      ].filter((item) => item.value > 0)
    : []

  return (
    <div className="space-y-6 animate-fade-in text-left">
      {/* Top Header & Date Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-900 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white tracking-tight">
              AI Code Insights & Review Analytics
            </h2>
            {isFetching && <RotateCw className="h-3.5 w-3.5 text-indigo-400 animate-spin" />}
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Deterministic code quality trends, vulnerability tracking, and review performance for <span className="font-semibold text-zinc-300">{project.project_name || project.name}</span>.
          </p>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-1 bg-zinc-950 p-1 rounded-xl border border-zinc-800/80 self-start sm:self-auto">
          {[
            { id: '7d', label: '7 Days' },
            { id: '30d', label: '30 Days' },
            { id: '90d', label: '90 Days' },
            { id: 'all', label: 'All Time' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setRange(item.id as DateRangeFilter)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                range === item.id
                  ? 'bg-zinc-800 text-white shadow-sm'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-72 rounded-2xl" />
            <Skeleton className="h-72 rounded-2xl" />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-8 rounded-2xl border border-red-950 bg-red-950/20 text-center space-y-3 max-w-md mx-auto">
          <ShieldAlert className="h-8 w-8 text-red-400 mx-auto" />
          <h4 className="font-bold text-white text-sm">Failed to Load Insights</h4>
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
      {!isLoading && !error && !hasData && (
        <div className="rounded-2xl border border-zinc-850 bg-zinc-950/30 p-12 text-center space-y-4 max-w-md mx-auto my-8">
          <div className="h-12 w-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
            <Sparkles className="h-6 w-6" />
          </div>
          <div className="space-y-1.5">
            <h4 className="text-base font-bold text-white">No Insights Yet</h4>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Insights will appear after your first completed AI review on a Pull Request.
            </p>
          </div>
          <Link
            to={`/projects/${project.id}/pull-requests`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <GitPullRequest className="h-3.5 w-3.5" />
            <span>Review a Pull Request</span>
          </Link>
        </div>
      )}

      {/* Main Dashboard Content */}
      {!isLoading && !error && hasData && (
        <div className="space-y-6">
          {/* Top Overview KPI Cards Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Total Pull Requests */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <GitPullRequest className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Pull Requests</span>
                </span>
                <span className="text-[10px] font-mono text-zinc-500">{range}</span>
              </div>
              <p className="text-2xl font-bold text-white font-mono">{overview?.total_pull_requests || 0}</p>
              <div className="flex items-center gap-2 text-[11px] font-mono">
                <span className="text-emerald-400">{overview?.open_pull_requests || 0} Open</span>
                <span className="text-zinc-600">•</span>
                <span className="text-purple-400">{overview?.merged_pull_requests || 0} Merged</span>
              </div>
            </div>

            {/* Card 2: AI Reviews Executed */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>AI Reviews</span>
                </span>
                <span className="text-[10px] font-mono text-zinc-500">{range}</span>
              </div>
              <p className="text-2xl font-bold text-white font-mono">{overview?.total_reviews || 0}</p>
              <div className="flex items-center gap-2 text-[11px] font-mono">
                <span className="text-emerald-400">{overview?.completed_reviews || 0} Done</span>
                {overview && overview.failed_reviews > 0 && (
                  <>
                    <span className="text-zinc-600">•</span>
                    <span className="text-red-400">{overview.failed_reviews} Failed</span>
                  </>
                )}
              </div>
            </div>

            {/* Card 3: Issues Detected */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                  <span>Issues Detected</span>
                </span>
                <span className="text-[10px] font-mono text-zinc-500">{range}</span>
              </div>
              <p className="text-2xl font-bold text-white font-mono">{overview?.total_issues_detected || 0}</p>
              <div className="flex items-center gap-1.5 text-[11px] font-mono">
                <span className="text-red-400 font-bold">{data?.severity_distribution.critical_count || 0}C</span>
                <span className="text-zinc-600">/</span>
                <span className="text-orange-400 font-bold">{data?.severity_distribution.high_count || 0}H</span>
                <span className="text-zinc-600">/</span>
                <span className="text-yellow-400 font-bold">{data?.severity_distribution.medium_count || 0}M</span>
              </div>
            </div>

            {/* Card 4: Average Duration */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-zinc-400" />
                  <span>Avg Duration</span>
                </span>
                <span className="text-[10px] font-mono text-zinc-500">{range}</span>
              </div>
              <p className="text-2xl font-bold text-white font-mono">
                {overview?.avg_review_duration_ms ? `${(overview.avg_review_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
              </p>
              <div className="flex items-center gap-1 text-[11px] text-zinc-400">
                <Zap className="h-3 w-3 text-indigo-400" />
                <span>Fastest: {data?.review_performance.fastest_duration_ms ? `${(data.review_performance.fastest_duration_ms / 1000).toFixed(1)}s` : 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Row 1: Time Series Charts (Review Activity & Severity Trend) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Review Activity */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Review Activity</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">Daily Execution Volume</span>
              </div>

              {data?.review_activity && data.review_activity.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.review_activity} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                        </linearGradient>
                        <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" tickFormatter={formatShortDate} stroke="#71717a" fontSize={11} />
                      <YAxis stroke="#71717a" fontSize={11} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '0.75rem', fontSize: '12px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Area type="monotone" dataKey="completed_reviews" name="Completed" stroke="#10b981" fillOpacity={1} fill="url(#colorCompleted)" />
                      <Area type="monotone" dataKey="failed_reviews" name="Failed" stroke="#ef4444" fillOpacity={1} fill="url(#colorFailed)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-zinc-500">
                  No review activity recorded in this date range.
                </div>
              )}
            </div>

            {/* Chart 2: Issue Severity Trends */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-amber-400" />
                  <h3 className="text-sm font-bold text-white">Issue Severity Trends</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">Findings Over Time</span>
              </div>

              {data?.severity_trends && data.severity_trends.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.severity_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                      <XAxis dataKey="date" tickFormatter={formatShortDate} stroke="#71717a" fontSize={11} />
                      <YAxis stroke="#71717a" fontSize={11} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '0.75rem', fontSize: '12px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                      <Area type="monotone" dataKey="critical_count" name="Critical" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                      <Area type="monotone" dataKey="high_count" name="High" stroke="#f97316" fill="#f97316" fillOpacity={0.2} />
                      <Area type="monotone" dataKey="medium_count" name="Medium" stroke="#eab308" fill="#eab308" fillOpacity={0.2} />
                      <Area type="monotone" dataKey="low_count" name="Low" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-zinc-500">
                  No issues detected in completed reviews in this date range.
                </div>
              )}
            </div>
          </div>

          {/* Row 2: Severity Distribution Donut & Dynamic Issue Categories */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 3: Severity Breakdown Donut */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-400" />
                  <h3 className="text-sm font-bold text-white">Severity Distribution</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">Total: {data?.severity_distribution.total_issues || 0}</span>
              </div>

              {severityPieData.length > 0 ? (
                <div className="h-64 w-full flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={severityPieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={85}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {severityPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '0.75rem', fontSize: '12px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-zinc-500">
                  Zero issues detected. Codebase is clean in this window.
                </div>
              )}
            </div>

            {/* Chart 4: Dynamic Issue Categories Bar Chart */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">Issue Categories</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">Derived from Review Findings</span>
              </div>

              {data?.issue_categories && data.issue_categories.length > 0 ? (
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={data.issue_categories}
                      layout="vertical"
                      margin={{ top: 10, right: 20, left: 35, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                      <XAxis type="number" stroke="#71717a" fontSize={11} allowDecimals={false} />
                      <YAxis type="category" dataKey="category" stroke="#71717a" fontSize={11} width={80} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '0.75rem', fontSize: '12px' }}
                      />
                      <Bar dataKey="count" name="Issues" radius={[0, 4, 4, 0]}>
                        {data.issue_categories.map((_, index) => (
                          <Cell key={`cat-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-xs text-zinc-500">
                  No categorized findings recorded.
                </div>
              )}
            </div>
          </div>

          {/* Row 3: Top Problematic Files & Repository Review Health */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Table: Most Problematic Files */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <FileCode className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Top Problematic Files</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">Highest Issue Density</span>
              </div>

              {data?.problematic_files && data.problematic_files.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-900 text-[11px] text-zinc-500 uppercase font-mono">
                        <th className="py-2 pr-3">File</th>
                        <th className="py-2 px-3 text-right">Issues</th>
                        <th className="py-2 px-3 text-right">High/Crit</th>
                        <th className="py-2 pl-3 text-right">Reviews</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-900/60 font-mono">
                      {data.problematic_files.map((file, idx) => (
                        <tr key={idx} className="hover:bg-zinc-900/30 transition-colors">
                          <td className="py-2.5 pr-3 text-zinc-300 truncate max-w-[200px]" title={file.filename}>
                            {file.filename}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-white">
                            {file.total_issues}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {file.high_critical_count > 0 ? (
                              <span className="text-red-400 font-bold">{file.high_critical_count}</span>
                            ) : (
                              <span className="text-zinc-600">0</span>
                            )}
                          </td>
                          <td className="py-2.5 pl-3 text-right text-zinc-400">
                            {file.review_count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-xs text-zinc-500">
                  No problematic files detected in this time range.
                </div>
              )}
            </div>

            {/* Health Card: Repository Review Health */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-emerald-400" />
                    <h3 className="text-sm font-bold text-white">Repository Review Health</h3>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      data?.repository_health.status === 'Strong'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : data?.repository_health.status === 'Good'
                        ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    <CheckCircle2 className="h-3 w-3" />
                    <span>{data?.repository_health.status}</span>
                  </span>
                </div>

                <div className="py-4 space-y-3">
                  <p className="text-xs text-zinc-300 leading-relaxed font-medium">
                    {data?.repository_health.summary_text}
                  </p>

                  {/* Evaluation Factor List */}
                  <div className="space-y-2 pt-2 border-t border-zinc-900">
                    <span className="text-[11px] font-bold uppercase text-zinc-500 tracking-wider">
                      Evaluation Factors ({range}):
                    </span>
                    <ul className="space-y-1.5">
                      {data?.repository_health.factors.map((factor, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-zinc-400">
                          <Info className="h-3.5 w-3.5 text-indigo-400 shrink-0 mt-0.5" />
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Sync check strip */}
              <div className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-850 flex items-center justify-between text-xs font-mono">
                <span className="text-zinc-400">ChromaDB & Git State:</span>
                <span className={data?.repository_health.sync_status === 'READY' ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
                  {data?.repository_health.sync_status === 'READY' ? 'SYNCHRONIZED' : 'ATTENTION REQUIRED'}
                </span>
              </div>
            </div>
          </div>

          {/* Row 4: Review Performance & Pull Request Lifecycle Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Review Performance Card */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Review Engine Performance</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">
                  Success Rate: <strong className="text-emerald-400">{data?.review_performance.success_rate}%</strong>
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-zinc-900/40 border border-zinc-850 space-y-1">
                  <span className="text-[10px] uppercase text-zinc-500 font-bold">Avg Time</span>
                  <p className="text-sm font-bold text-white font-mono">
                    {data?.review_performance.avg_duration_ms ? `${(data.review_performance.avg_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-zinc-900/40 border border-zinc-850 space-y-1">
                  <span className="text-[10px] uppercase text-zinc-500 font-bold">Fastest</span>
                  <p className="text-sm font-bold text-emerald-400 font-mono">
                    {data?.review_performance.fastest_duration_ms ? `${(data.review_performance.fastest_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-zinc-900/40 border border-zinc-850 space-y-1">
                  <span className="text-[10px] uppercase text-zinc-500 font-bold">Slowest</span>
                  <p className="text-sm font-bold text-amber-400 font-mono">
                    {data?.review_performance.slowest_duration_ms ? `${(data.review_performance.slowest_duration_ms / 1000).toFixed(1)}s` : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Progress bar for success rate */}
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-[11px] text-zinc-400 font-mono">
                  <span>Execution Reliability</span>
                  <span>{data?.review_performance.completed_reviews} / {data?.review_performance.total_reviews} completed</span>
                </div>
                <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 transition-all"
                    style={{ width: `${data?.review_performance.success_rate || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* PR Statistics Card */}
            <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <div className="flex items-center gap-2">
                  <GitPullRequest className="h-4 w-4 text-purple-400" />
                  <h3 className="text-sm font-bold text-white">PR Lifecycle Statistics</h3>
                </div>
                <span className="text-[11px] font-mono text-zinc-500">
                  Total: {data?.pull_request_statistics.total_prs || 0}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-850">
                  <span className="text-[10px] text-emerald-400 font-bold">OPEN</span>
                  <p className="text-base font-bold text-white font-mono mt-0.5">{data?.pull_request_statistics.open_prs || 0}</p>
                </div>
                <div className="p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-850">
                  <span className="text-[10px] text-purple-400 font-bold">MERGED</span>
                  <p className="text-base font-bold text-white font-mono mt-0.5">{data?.pull_request_statistics.merged_prs || 0}</p>
                </div>
                <div className="p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-850">
                  <span className="text-[10px] text-zinc-400 font-bold">CLOSED</span>
                  <p className="text-base font-bold text-white font-mono mt-0.5">{data?.pull_request_statistics.closed_prs || 0}</p>
                </div>
                <div className="p-2.5 rounded-xl bg-zinc-900/40 border border-zinc-850">
                  <span className="text-[10px] text-amber-400 font-bold">DRAFT</span>
                  <p className="text-base font-bold text-white font-mono mt-0.5">{data?.pull_request_statistics.draft_prs || 0}</p>
                </div>
              </div>

              <div className="flex justify-between items-center text-xs text-zinc-400 font-mono pt-2 border-t border-zinc-900">
                <span>Avg Changes / PR:</span>
                <span className="text-white font-bold">
                  +{data?.pull_request_statistics.avg_additions || 0} / -{data?.pull_request_statistics.avg_deletions || 0} lines ({data?.pull_request_statistics.avg_changed_files || 0} files)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
