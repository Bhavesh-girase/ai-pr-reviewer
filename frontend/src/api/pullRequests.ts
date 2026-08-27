import { supabase } from '@/lib/supabase'
import type {
  PullRequestListResponse,
  PullRequestDetail,
  PullRequestFile,
  PullRequestDiff,
  PullRequestFilterParams,
} from '@/types/pullRequest'
import type { ReviewResponse } from '@/types/review'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function getAuthHeader(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session?.access_token) {
    throw new Error('User is not authenticated. Please log in.')
  }
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  }
}

export async function getPullRequests(
  projectId: string,
  params?: PullRequestFilterParams
): Promise<PullRequestListResponse> {
  const headers = await getAuthHeader()
  const query = new URLSearchParams()

  if (params?.state) query.set('state', params.state)
  if (params?.page) query.set('page', params.page.toString())
  if (params?.per_page) query.set('per_page', params.per_page.toString())
  if (params?.sort) query.set('sort', params.sort)
  if (params?.direction) query.set('direction', params.direction)
  if (params?.search && params.search.trim()) query.set('search', params.search.trim())

  const queryString = query.toString() ? `?${query.toString()}` : ''
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests${queryString}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch pull requests.' }))
    throw new Error(errorData.detail || 'Failed to fetch pull requests from GitHub.')
  }

  return response.json()
}

export async function getPullRequestById(
  projectId: string,
  prNumber: number
): Promise<PullRequestDetail> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Pull Request #${prNumber} not found.` }))
    throw new Error(errorData.detail || `Failed to fetch PR #${prNumber}.`)
  }

  return response.json()
}

export async function getPullRequestFiles(
  projectId: string,
  prNumber: number
): Promise<PullRequestFile[]> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}/files`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch changed files.' }))
    throw new Error(errorData.detail || 'Failed to fetch changed files.')
  }

  return response.json()
}

export async function getPullRequestDiff(
  projectId: string,
  prNumber: number
): Promise<PullRequestDiff> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}/diff`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch PR diff.' }))
    throw new Error(errorData.detail || 'Failed to fetch PR diff.')
  }

  return response.json()
}

export async function reviewProjectPullRequest(
  projectId: string,
  prNumber: number,
  notes?: string
): Promise<ReviewResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/pull-requests/${prNumber}/review`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ notes }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'AI review failed.' }))
    throw new Error(errorData.detail || 'Failed to execute AI review pipeline.')
  }

  return response.json()
}
