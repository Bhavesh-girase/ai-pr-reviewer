export type PRState = 'OPEN' | 'CLOSED' | 'MERGED' | 'DRAFT'

export interface PullRequestAuthor {
  login: string
  avatar_url?: string | null
  html_url?: string | null
}

export interface PullRequest {
  number: number
  title: string
  author: PullRequestAuthor
  state: PRState
  is_draft: boolean
  created_at: string | null
  updated_at: string | null
  closed_at: string | null
  merged_at: string | null
  source_branch: string
  target_branch: string
  base_commit_sha?: string | null
  head_commit_sha?: string | null
  html_url: string
  additions: number
  deletions: number
  changed_files_count: number
  comments_count: number
  commits_count: number
  review_status: string
}

export interface PullRequestListResponse {
  pull_requests: PullRequest[]
  page: number
  per_page: number
  total_count: number
}

export interface PullRequestDetail {
  number: number
  title: string
  body?: string | null
  author: PullRequestAuthor
  state: PRState
  is_draft: boolean
  created_at: string | null
  updated_at: string | null
  closed_at: string | null
  merged_at: string | null
  source_branch: string
  target_branch: string
  base_commit_sha?: string | null
  head_commit_sha?: string | null
  source_sha?: string | null
  target_sha?: string | null
  html_url: string
  additions: number
  deletions: number
  changed_files_count: number
  comments_count: number
  commits_count: number
  mergeable?: boolean | null
}

export interface PullRequestFile {
  sha?: string | null
  filename: string
  status: 'added' | 'modified' | 'removed' | 'renamed' | string
  additions: number
  deletions: number
  changes: number
  patch?: string | null
  raw_url?: string | null
  contents_url?: string | null
  previous_filename?: string | null
}

export interface PullRequestDiff {
  raw_diff: string
  files_count: number
  additions: number
  deletions: number
}

export interface PullRequestFilterParams {
  state?: 'all' | 'open' | 'closed' | 'merged' | 'draft'
  page?: number
  per_page?: number
  sort?: 'created' | 'updated' | 'popularity' | 'long-running'
  direction?: 'desc' | 'asc'
  search?: string
}
