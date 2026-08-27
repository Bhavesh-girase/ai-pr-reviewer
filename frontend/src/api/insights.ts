import { supabase } from '@/lib/supabase'
import type { InsightsResponse, DateRangeFilter } from '@/types/insights'

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
 * Fetch project insights and analytics for a specified date range
 */
export async function getProjectInsights(
  projectId: string,
  range: DateRangeFilter = '30d'
): Promise<InsightsResponse> {
  const headers = await getAuthHeader()
  const url = `${API_BASE_URL}/projects/${projectId}/insights?range=${range}`

  const response = await fetch(url, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch project insights' }))
    throw new Error(errorData.detail || 'Failed to fetch project insights')
  }

  return response.json()
}
