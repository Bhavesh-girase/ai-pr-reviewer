import { z } from 'zod'

// Schema validation using Zod
export const reviewSchema = z.object({
  url: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  owner: z.string().min(1, 'Repository owner is required'),
  repo: z.string().min(1, 'Repository name is required'),
  pullNumber: z.number({ message: 'Pull number must be a valid number' })
    .int('Pull number must be an integer')
    .positive('Pull number must be a positive integer'),
})

export type ReviewFormValues = z.infer<typeof reviewSchema>

// Severity & Category Enums
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type Category =
  | 'Bug'
  | 'Security'
  | 'Performance'
  | 'Maintainability'
  | 'Style'
  | 'Best Practice'

export type ReviewStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | string

export interface ReviewIssue {
  severity: Severity
  category: Category
  title: string
  description: string
  suggestion: string
  file: string
  line: number | null
}

export interface ReviewResult {
  summary: string
  issues: ReviewIssue[]
}

export interface RetrievedContextChunk {
  page_content: string
  metadata: {
    chunk_id?: string
    repository?: string
    chunk_index?: number
    relative_path?: string
    language?: string
    [key: string]: any
  }
  rerank_score: number
  retrieval_source: string
}

export interface ReviewFileResult {
  filename: string
  patch?: string
  original_code?: string
  modified_code?: string
  review: ReviewResult
  retrieved_context?: RetrievedContextChunk[]
}

export interface ReviewMetadata {
  duration: number
  llm: string
  chunks_retrieved: number
  repository: string
  base_branch: string
  head_branch: string
  confidence: number
}

export interface ReviewApiResponse {
  reviews: ReviewFileResult[]
  metadata: ReviewMetadata
}

export type ReviewResponse = ReviewApiResponse

// Phase 6 Domain Entity: Persistent Review Models
export interface ReviewItem {
  id: string
  project_id: string
  pull_request_id: string
  github_pr_number: number
  status: ReviewStatus
  summary?: string | null
  issues_count: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  files_reviewed: number
  lines_analyzed: number
  model_name?: string | null
  review_duration_ms?: number | null
  base_commit_sha?: string | null
  head_commit_sha?: string | null
  created_by?: string | null
  created_at?: string | null
  completed_at?: string | null
  error_message?: string | null
  pr_title?: string | null
}

export interface ReviewDetail extends ReviewItem {
  review_result?: ReviewApiResponse | null
  pr_source_branch?: string | null
  pr_target_branch?: string | null
  pr_author?: {
    login: string
    avatar_url?: string
    html_url?: string
  } | null
  pr_html_url?: string | null
}

export interface ReviewListResponse {
  reviews: ReviewItem[]
  page: number
  per_page: number
  total_count: number
}

export interface ReviewFilterParams {
  pr_number?: number
  status?: string
  page?: number
  per_page?: number
  sort?: string
  direction?: 'asc' | 'desc'
  search?: string
}
