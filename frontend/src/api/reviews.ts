import { supabase } from '@/lib/supabase'
import type {
  ReviewItem,
  ReviewDetail,
  ReviewListResponse,
  ReviewFilterParams,
  ReviewQueueResponse,
} from '@/types/review'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function getAuthHeader(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session?.access_token) {
    throw new Error('User is not authenticated')
  }
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  }
}

/**
 * List paginated review history for a project
 */
export async function listProjectReviews(
  projectId: string,
  params: ReviewFilterParams = {}
): Promise<ReviewListResponse> {
  const headers = await getAuthHeader()
  const searchParams = new URLSearchParams()

  if (params.page) searchParams.set('page', params.page.toString())
  if (params.per_page) searchParams.set('per_page', params.per_page.toString())
  if (params.status && params.status !== 'ALL') searchParams.set('status', params.status)
  if (params.pr_number) searchParams.set('pr_number', params.pr_number.toString())
  if (params.sort) searchParams.set('sort', params.sort)
  if (params.direction) searchParams.set('direction', params.direction)
  if (params.search) searchParams.set('search', params.search)

  const url = `${API_BASE_URL}/projects/${projectId}/reviews?${searchParams.toString()}`
  const response = await fetch(url, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch reviews' }))
    throw new Error(errorData.detail || 'Failed to fetch reviews')
  }

  return response.json()
}

/**
 * Get full review details with complete structured JSON result
 */
export async function getReviewById(
  projectId: string,
  reviewId: string
): Promise<ReviewDetail> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/reviews/${reviewId}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Review not found' }))
    throw new Error(errorData.detail || `Review with ID ${reviewId} not found`)
  }

  return response.json()
}

/**
 * Get all historical reviews for a specific Pull Request
 */
export async function getPullRequestReviews(
  projectId: string,
  prNumber: number
): Promise<ReviewItem[]> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}/reviews`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch PR reviews' }))
    throw new Error(errorData.detail || 'Failed to fetch PR reviews')
  }

  return response.json()
}

/**
 * Execute an AI Review and persist the review record
 */
export async function reviewProjectPullRequest(
  projectId: string,
  prNumber: number
): Promise<ReviewQueueResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}/review`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Review execution failed.' }))
    throw new Error(errorData.detail || 'Review execution failed.')
  }

  return response.json()
}
