import { supabase } from '@/lib/supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface WebhookStatusResponse {
  project_id: string
  webhook_status: 'NOT_REGISTERED' | 'REGISTERING' | 'ACTIVE' | 'FAILED' | 'DISABLED' | string
  webhook_registered_at: string | null
  last_webhook_event_at: string | null
  github_webhook_id: number | null
  webhook_url: string | null
}

export interface WebhookRegisterResponse {
  message: string
  github_webhook_id?: number | null
  webhook_status: string
  synced_prs_count: number
}

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

export async function getProjectWebhookStatus(projectId: string): Promise<WebhookStatusResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/webhook`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch webhook status.' }))
    throw new Error(errorData.detail || 'Failed to fetch webhook status.')
  }

  return response.json()
}

export async function registerProjectWebhook(projectId: string): Promise<WebhookRegisterResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/webhook`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to register webhook.' }))
    throw new Error(errorData.detail || 'Failed to register GitHub webhook.')
  }

  return response.json()
}

export async function retryProjectWebhook(projectId: string): Promise<WebhookRegisterResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/webhook/retry`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to retry webhook registration.' }))
    throw new Error(errorData.detail || 'Failed to retry webhook registration.')
  }

  return response.json()
}

export async function deleteProjectWebhook(projectId: string): Promise<{ message: string }> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/webhook`, {
    method: 'DELETE',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete webhook.' }))
    throw new Error(errorData.detail || 'Failed to delete webhook.')
  }

  return response.json()
}

export async function syncProjectPullRequests(projectId: string): Promise<{ message: string; synced_prs_count: number }> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sync-prs`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to sync pull requests.' }))
    throw new Error(errorData.detail || 'Failed to synchronize pull requests.')
  }

  return response.json()
}
