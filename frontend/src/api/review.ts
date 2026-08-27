import { api } from './client'
import { type ReviewFormValues, type ReviewResponse } from '@/types/review'

/**
 * Submits a pull request review request to the FastAPI backend.
 * Dynamically builds the GitHub URL if not provided by the user.
 */
export async function reviewPullRequest(values: ReviewFormValues): Promise<ReviewResponse> {
  const repoUrl =
    values.url && values.url.trim() !== ''
      ? values.url.trim()
      : `https://github.com/${values.owner.trim()}/${values.repo.trim()}`

  const payload = {
    repo_url: repoUrl,
    owner: values.owner.trim(),
    repository: values.repo.trim(),
    pull_number: values.pullNumber,
  }

  const response = await api.post<ReviewResponse>('/review-pr', payload)
  return response.data
}

/**
 * Queries the backend health check endpoint.
 */
export async function checkApiHealth(): Promise<{ status: string }> {
  const response = await api.get<{ status: string }>('/health')
  return response.data
}
