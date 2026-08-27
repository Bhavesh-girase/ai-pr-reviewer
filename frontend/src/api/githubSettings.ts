import { supabase } from '@/lib/supabase'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface GitHubStatus {
  connected: boolean
  username: string | null
  avatar_url: string | null
  name: string | null
}

export interface GitHubTestResult {
  success: boolean
  username: string
  name: string
  avatar: string
}

export interface GitHubConnectResult {
  message: string
  connected: boolean
  username: string
  name: string
  avatar_url: string
}

export interface GitHubDisconnectResult {
  message: string
  connected: boolean
}

/**
 * Gets the current Supabase session JWT access token.
 */
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
 * Fetches current GitHub integration status for logged in user.
 */
export async function getGitHubStatus(): Promise<GitHubStatus> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/settings/github`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch GitHub status' }))
    throw new Error(errorData.detail || 'Failed to fetch GitHub status')
  }

  return response.json()
}

/**
 * Tests a GitHub Personal Access Token without saving it.
 */
export async function testGitHubConnection(token: string): Promise<GitHubTestResult> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/settings/github/test`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ token }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Token verification failed' }))
    throw new Error(errorData.detail || 'Failed to test GitHub connection')
  }

  return response.json()
}

/**
 * Connects and securely saves the GitHub Personal Access Token.
 */
export async function connectGitHubAccount(token: string): Promise<GitHubConnectResult> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/settings/github/connect`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ token }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to connect GitHub account' }))
    throw new Error(errorData.detail || 'Failed to connect GitHub account')
  }

  return response.json()
}

/**
 * Disconnects the GitHub account.
 */
export async function disconnectGitHubAccount(): Promise<GitHubDisconnectResult> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/settings/github`, {
    method: 'DELETE',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to disconnect GitHub account' }))
    throw new Error(errorData.detail || 'Failed to disconnect GitHub account')
  }

  return response.json()
}
