import { supabase } from '@/lib/supabase'
import type {
  Project,
  CreateProjectInput,
  UpdateProjectInput,
  ProjectSyncResponse,
  ProjectSyncStatusResponse,
} from '@/types/project'

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

export async function getProjects(): Promise<Project[]> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch projects' }))
    throw new Error(errorData.detail || 'Failed to fetch projects')
  }

  const data = await response.json()
  return data
}

export async function getProjectById(id: string): Promise<Project> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Project not found' }))
    throw new Error(errorData.detail || `Project with ID ${id} not found`)
  }

  const data = await response.json()
  return data
}

export async function createProject(input: CreateProjectInput): Promise<Project> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers,
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create project' }))
    throw new Error(errorData.detail || 'Failed to create project')
  }

  const data = await response.json()
  return data
}

export async function updateProject(id: string, input: UpdateProjectInput): Promise<Project> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(input),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to update project' }))
    throw new Error(errorData.detail || 'Failed to update project')
  }

  const data = await response.json()
  return data
}

export async function deleteProject(id: string): Promise<void> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
    method: 'DELETE',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete project' }))
    throw new Error(errorData.detail || 'Failed to delete project')
  }
}

export async function syncProjectRepository(projectId: string): Promise<ProjectSyncResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sync`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Repository synchronization failed.' }))
    throw new Error(errorData.detail || 'Repository synchronization failed.')
  }

  return response.json()
}

export async function getProjectSyncStatus(projectId: string): Promise<ProjectSyncStatusResponse> {
  const headers = await getAuthHeader()
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sync-status`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch sync status.' }))
    throw new Error(errorData.detail || 'Failed to fetch sync status.')
  }

  return response.json()
}
