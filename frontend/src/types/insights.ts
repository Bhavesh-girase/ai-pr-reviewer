export type DateRangeFilter = '7d' | '30d' | '90d' | 'all'

export interface InsightsOverview {
  total_pull_requests: number
  open_pull_requests: number
  merged_pull_requests: number
  closed_pull_requests: number
  total_reviews: number
  completed_reviews: number
  failed_reviews: number
  total_issues_detected: number
  avg_review_duration_ms?: number | null
}

export interface ReviewActivityPoint {
  date: string
  total_reviews: number
  completed_reviews: number
  failed_reviews: number
}

export interface SeverityDistribution {
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  total_issues: number
}

export interface SeverityTrendPoint {
  date: string
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
}

export interface IssueCategoryPoint {
  category: string
  count: number
  percentage: number
}

export interface ProblematicFile {
  filename: string
  total_issues: number
  high_critical_count: number
  review_count: number
}

export interface PullRequestStatistics {
  total_prs: number
  open_prs: number
  merged_prs: number
  closed_prs: number
  draft_prs: number
  avg_changed_files: number
  avg_additions: number
  avg_deletions: number
}

export interface ReviewPerformance {
  avg_duration_ms?: number | null
  fastest_duration_ms?: number | null
  slowest_duration_ms?: number | null
  completed_reviews: number
  failed_reviews: number
  total_reviews: number
  success_rate: number
}

export interface RepositoryHealth {
  status: 'Strong' | 'Good' | 'Needs Attention' | string
  summary_text: string
  critical_issues_recent: number
  high_issues_recent: number
  failure_rate_percentage: number
  sync_status: string
  last_synced_at?: string | null
  factors: string[]
}

export interface LatestReviewSummary {
  id: string
  github_pr_number: number
  pr_title?: string | null
  status: string
  issues_count: number
  high_count: number
  critical_count: number
  head_commit_sha?: string | null
  created_at?: string | null
}

export interface LatestPullRequestSummary {
  github_pr_number: number
  title: string
  state: string
  author_login: string
  changed_files_count: number
  updated_at?: string | null
}

export interface InsightsResponse {
  project_id: string
  date_range: DateRangeFilter
  overview: InsightsOverview
  review_activity: ReviewActivityPoint[]
  severity_distribution: SeverityDistribution
  severity_trends: SeverityTrendPoint[]
  issue_categories: IssueCategoryPoint[]
  problematic_files: ProblematicFile[]
  pull_request_statistics: PullRequestStatistics
  review_performance: ReviewPerformance
  repository_health: RepositoryHealth
  latest_reviews: LatestReviewSummary[]
  latest_pull_requests: LatestPullRequestSummary[]
  has_data: boolean
}
